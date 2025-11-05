"""
Enhanced autonomous orchestrator with intelligent query processing and comparative analysis.
"""
from typing import List, Dict, Optional
import logging

from app.services.web_automation.fda_scraper import FDAScraper
from app.services.web_automation.ema_scraper import EMAScraper
from app.services.document_processing import DocumentProcessor
from app.services.vector_store import VectorStoreService
from app.services.rag_service import RAGService
from app.services.query_analyzer import QueryAnalyzer
from app.services.context_manager import ContextManager
from app.services.comparative_analysis import ComparativeAnalysisService
from app.core.config import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AutonomousOrchestrator:
    """
    Enhanced orchestrator with autonomous query processing.
    
    Automatically:
    - Extracts drug names from queries
    - Determines if documents need to be retrieved
    - Downloads and indexes documents
    - Generates answers with comparative analysis
    - Manages conversation context
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.doc_processor = DocumentProcessor()
        self.vector_store = VectorStoreService()
        self.rag_service = RAGService()
        self.query_analyzer = QueryAnalyzer()
        self.context_manager = ContextManager()
        self.comparative_service = ComparativeAnalysisService()
        
        # Initialize scrapers
        self.scrapers = {
            'FDA': FDAScraper(self.settings.download_dir),
            'EMA': EMAScraper(self.settings.download_dir),
        }
        
        logger.info("✓ Autonomous Orchestrator initialized")
    
    def process_query(
        self,
        query: str,
        session_id: str = "default",
        selected_agencies: Optional[List[str]] = None,
        model: Optional[str] = None
    ) -> Dict:
        """
        Process a user query autonomously.
        
        This is the main entry point that handles the entire workflow:
        1. Analyze query to extract drug names and intent
        2. Check if documents need to be retrieved
        3. Download and index documents if needed
        4. Generate answer (with comparative analysis if multiple agencies)
        5. Update conversation context
        
        Args:
            query: User's query
            session_id: Session identifier for context tracking
            selected_agencies: List of agencies to use (None = use context default)
            model: OpenAI model to use
            
        Returns:
            Dictionary with answer and metadata
        """
        try:
            logger.info(f"\n{'='*70}")
            logger.info(f"Processing query: {query}")
            logger.info(f"{'='*70}\n")
            
            # Get conversation context
            context = self.context_manager.get_context(session_id)
            
            # Update agencies if provided
            if selected_agencies:
                context.set_agencies(selected_agencies)
            
            # Step 1: Analyze query
            logger.info("Step 1: Analyzing query...")
            analysis = self.query_analyzer.analyze_query(query, context.to_dict())
            
            # Step 2: Check if clarification needed
            if analysis['clarification_needed']:
                logger.info("Clarification needed from user")
                return {
                    'status': 'clarification_needed',
                    'question': analysis['clarification_question'],
                    'analysis': analysis
                }
            
            # Step 3: Extract drug name
            drug_names = analysis.get('drug_names', [])
            if not drug_names and context.current_drug:
                # Use drug from context
                drug_names = [context.current_drug]
                logger.info(f"Using drug from context: {context.current_drug}")
            
            if not drug_names:
                return {
                    'status': 'error',
                    'answer': "I couldn't identify which drug you're asking about. Could you please specify the drug name?",
                    'analysis': analysis
                }
            
            drug_name = drug_names[0]  # Use first drug mentioned
            
            # Update context
            context.update_drug(drug_name)
            context.add_topics(analysis.get('topics', []))
            
            # Step 4: Determine agencies to use
            agencies_to_use = analysis.get('agencies', [])
            if not agencies_to_use:
                agencies_to_use = context.agencies  # Use context default
            
            logger.info(f"Drug: {drug_name}")
            logger.info(f"Agencies: {', '.join(agencies_to_use)}")
            logger.info(f"Topics: {', '.join(analysis.get('topics', []))}")
            
            # Step 5: Check if documents need to be retrieved
            needs_docs = analysis.get('needs_documents', False)
            
            # Override if context says we need docs
            if context.needs_new_documents(drug_name):
                needs_docs = True
                logger.info("Context indicates new documents needed")
            
            # Step 6: Retrieve and index documents if needed
            if needs_docs:
                logger.info(f"\nStep 2: Retrieving documents for {drug_name}...")
                
                retrieval_result = self._retrieve_and_index(
                    drug_name=drug_name,
                    agencies=agencies_to_use,
                    max_docs_per_agency=3
                )
                
                if retrieval_result['status'] == 'error':
                    return retrieval_result
                
                # Update context with indexed documents
                for doc_path in retrieval_result.get('documents_downloaded', []):
                    context.add_document(doc_path)
                
                logger.info(f"✓ Indexed {retrieval_result['documents_indexed']} documents")
            else:
                logger.info("\nStep 2: Using existing indexed documents")
            
            # Step 7: Generate answer
            logger.info(f"\nStep 3: Generating answer...")
            
            # Check if comparative analysis is needed
            if len(agencies_to_use) > 1:
                logger.info("Multiple agencies selected - generating comparative analysis")
                answer_result = self._generate_comparative_answer(
                    query=query,
                    drug_name=drug_name,
                    agencies=agencies_to_use,
                    model=model
                )
            else:
                logger.info("Single agency - generating standard answer")
                answer_result = self.rag_service.generate_answer(
                    query=query,
                    model=model,
                    k=5
                )
            
            # Step 8: Update context with query and response
            context.add_query(query, answer_result.get('answer', ''), analysis)
            
            # Add context summary to result
            answer_result['context_summary'] = context.get_context_summary()
            answer_result['analysis'] = analysis
            
            logger.info(f"\n{'='*70}")
            logger.info(f"Query processing complete")
            logger.info(f"{'='*70}\n")
            
            return answer_result
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'status': 'error',
                'error': str(e),
                'answer': f"I encountered an error while processing your query: {str(e)}"
            }
    
    def _retrieve_and_index(
        self,
        drug_name: str,
        agencies: List[str],
        max_docs_per_agency: int = 3
    ) -> Dict:
        """
        Retrieve and index documents from agencies.
        
        Args:
            drug_name: Name of the drug
            agencies: List of agencies
            max_docs_per_agency: Maximum documents per agency
            
        Returns:
            Summary of retrieval results
        """
        results = {
            'status': 'success',
            'drug_name': drug_name,
            'agencies_searched': [],
            'documents_downloaded': [],
            'documents_indexed': 0,
            'errors': []
        }
        
        for agency in agencies:
            if agency not in self.scrapers:
                logger.warning(f"Scraper not available for {agency}")
                results['errors'].append(f"{agency}: Scraper not implemented")
                continue
            
            try:
                logger.info(f"Searching {agency} for {drug_name}...")
                results['agencies_searched'].append(agency)
                
                # Search and download
                scraper = self.scrapers[agency]
                downloaded_files = scraper.search_and_download(
                    drug_name,
                    max_documents=max_docs_per_agency
                )
                
                if not downloaded_files:
                    logger.warning(f"No documents from {agency}")
                    results['errors'].append(f"{agency}: No documents found")
                    continue
                
                results['documents_downloaded'].extend(downloaded_files)
                
                # Index documents
                for file_path in downloaded_files:
                    try:
                        chunks, metadata = self.doc_processor.process_document(file_path)
                        
                        # Add agency to metadata
                        metadata['agency'] = agency
                        
                        self.vector_store.add_documents(chunks, metadata)
                        results['documents_indexed'] += 1
                        
                    except Exception as e:
                        logger.error(f"Error indexing {file_path}: {str(e)}")
                        results['errors'].append(f"Indexing error: {str(e)}")
                
            except Exception as e:
                logger.error(f"Error with {agency}: {str(e)}")
                results['errors'].append(f"{agency}: {str(e)}")
        
        return results
    
    def _generate_comparative_answer(
        self,
        query: str,
        drug_name: str,
        agencies: List[str],
        model: Optional[str] = None
    ) -> Dict:
        """
        Generate a comparative answer across multiple agencies.
        
        Args:
            query: User's query
            drug_name: Drug name
            agencies: List of agencies
            model: OpenAI model
            
        Returns:
            Answer with comparative analysis
        """
        try:
            # Retrieve contexts
            contexts = self.vector_store.search(query, k=10)  # Get more for comparison
            
            if not contexts:
                return {
                    'status': 'error',
                    'answer': f"No documents found for {drug_name}. Please try retrieving documents first."
                }
            
            # Generate comparative analysis
            result = self.comparative_service.generate_comparative_analysis(
                query=query,
                contexts=contexts,
                agencies=agencies,
                model=model
            )
            
            return {
                'status': 'success',
                'answer': result['analysis'],
                'type': 'comparative',
                'agencies_compared': agencies,
                'num_chunks_retrieved': len(contexts),
                'model_used': result.get('model_used', model)
            }
            
        except Exception as e:
            logger.error(f"Error generating comparative answer: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'answer': f"Error generating comparative analysis: {str(e)}"
            }
    
    def reset_context(self, session_id: str = "default"):
        """Reset conversation context for a session."""
        self.context_manager.reset_context(session_id)
        logger.info(f"Reset context for session: {session_id}")
    
    def get_system_status(self) -> Dict:
        """Get system status."""
        try:
            stats = self.vector_store.get_stats()
            
            return {
                'status': 'online',
                'vector_store': {
                    'total_vectors': stats['total_vectors'],
                    'unique_documents': stats['unique_documents'],
                    'dimension': stats['dimension']
                },
                'available_agencies': list(self.scrapers.keys()),
                'models': {
                    'embedding': self.settings.embedding_model,
                    'chat': self.settings.chat_model
                },
                'features': {
                    'autonomous_query_processing': True,
                    'comparative_analysis': True,
                    'context_tracking': True
                }
            }
        except Exception as e:
            logger.error(f"Error getting system status: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }

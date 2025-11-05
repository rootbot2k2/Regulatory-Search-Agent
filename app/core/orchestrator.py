"""
Agentic orchestrator that coordinates all services.
"""
from typing import List, Dict, Optional
import logging

from app.services.web_automation.fda_scraper import FDAScraper
from app.services.web_automation.ema_scraper import EMAScraper
from app.services.document_processing import DocumentProcessor
from app.services.vector_store import VectorStoreService
from app.services.rag_service import RAGService
from app.core.config import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgenticOrchestrator:
    """Main orchestrator for the Regulatory Search Agent."""
    
    def __init__(self):
        self.settings = get_settings()
        self.doc_processor = DocumentProcessor()
        self.vector_store = VectorStoreService()
        self.rag_service = RAGService()
        
        # Initialize scrapers
        self.scrapers = {
            'FDA': FDAScraper(self.settings.download_dir),
            'EMA': EMAScraper(self.settings.download_dir),
        }
        
        logger.info("✓ Orchestrator initialized with all services")
    
    def retrieve_and_index(
        self, 
        drug_name: str, 
        agencies: Optional[List[str]] = None,
        max_docs_per_agency: int = 3
    ) -> Dict:
        """
        Retrieve documents from agencies and index them.
        
        Args:
            drug_name: Name of the drug to search for
            agencies: List of agencies to search (defaults to all)
            max_docs_per_agency: Maximum documents to download per agency
            
        Returns:
            Summary of processing results
        """
        if agencies is None:
            agencies = list(self.scrapers.keys())
        
        # Validate agencies
        invalid_agencies = [a for a in agencies if a not in self.scrapers]
        if invalid_agencies:
            logger.warning(f"Unknown agencies: {invalid_agencies}")
            agencies = [a for a in agencies if a in self.scrapers]
        
        if not agencies:
            return {
                'status': 'error',
                'error': 'No valid agencies specified',
                'drug_name': drug_name,
                'agencies_searched': [],
                'documents_downloaded': [],
                'documents_indexed': 0
            }
        
        results = {
            'status': 'success',
            'drug_name': drug_name,
            'agencies_searched': [],
            'documents_downloaded': [],
            'documents_indexed': 0,
            'errors': []
        }
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Starting document retrieval for: {drug_name}")
        logger.info(f"Agencies: {', '.join(agencies)}")
        logger.info(f"{'='*60}\n")
        
        for agency in agencies:
            try:
                logger.info(f"\n--- Processing {agency} ---")
                results['agencies_searched'].append(agency)
                
                # Search and download documents
                scraper = self.scrapers[agency]
                downloaded_files = scraper.search_and_download(
                    drug_name, 
                    max_documents=max_docs_per_agency
                )
                
                if not downloaded_files:
                    logger.warning(f"No documents downloaded from {agency}")
                    results['errors'].append(f"{agency}: No documents found")
                    continue
                
                results['documents_downloaded'].extend(downloaded_files)
                
                # Index each downloaded document
                for file_path in downloaded_files:
                    try:
                        logger.info(f"Indexing: {file_path}")
                        
                        # Process document
                        chunks, metadata = self.doc_processor.process_document(file_path)
                        
                        # Add to vector store
                        self.vector_store.add_documents(chunks, metadata)
                        
                        results['documents_indexed'] += 1
                        logger.info(f"✓ Successfully indexed: {metadata['file_name']}")
                        
                    except Exception as e:
                        error_msg = f"Error indexing {file_path}: {str(e)}"
                        logger.error(error_msg)
                        results['errors'].append(error_msg)
                        continue
                
            except Exception as e:
                error_msg = f"Error processing {agency}: {str(e)}"
                logger.error(error_msg)
                results['errors'].append(error_msg)
                continue
        
        # Get final stats
        stats = self.vector_store.get_stats()
        results['total_vectors_in_index'] = stats['total_vectors']
        results['unique_documents_in_index'] = stats['unique_documents']
        
        logger.info(f"\n{'='*60}")
        logger.info(f"Retrieval and indexing complete!")
        logger.info(f"  Agencies searched: {len(results['agencies_searched'])}")
        logger.info(f"  Documents downloaded: {len(results['documents_downloaded'])}")
        logger.info(f"  Documents indexed: {results['documents_indexed']}")
        logger.info(f"  Total vectors in index: {results['total_vectors_in_index']}")
        logger.info(f"  Errors: {len(results['errors'])}")
        logger.info(f"{'='*60}\n")
        
        return results
    
    def query(
        self, 
        question: str, 
        model: Optional[str] = None,
        k: int = 5
    ) -> Dict:
        """
        Answer a question using RAG.
        
        Args:
            question: User's question
            model: OpenAI model to use
            k: Number of context chunks to retrieve
            
        Returns:
            Answer with sources and metadata
        """
        try:
            logger.info(f"Processing query: {question[:100]}...")
            
            # Check if clarification is needed
            clarification = self.rag_service.ask_for_clarification(question)
            
            if clarification['needs_clarification']:
                logger.info("Query may need clarification")
                # Still proceed but include clarification suggestions
            
            # Generate answer
            result = self.rag_service.generate_answer(question, model=model, k=k)
            
            # Add clarification info if applicable
            if clarification['needs_clarification']:
                result['clarification_suggestions'] = clarification['suggestions']
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'answer': f"Error processing query: {str(e)}",
                'sources': []
            }
    
    def get_system_status(self) -> Dict:
        """Get the current status of the system."""
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
                }
            }
        except Exception as e:
            logger.error(f"Error getting system status: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }

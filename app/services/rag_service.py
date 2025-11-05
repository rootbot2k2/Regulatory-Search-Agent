"""
Retrieval-Augmented Generation (RAG) service for question answering.
"""
from typing import List, Dict, Optional
from openai import OpenAI
import logging

from app.core.config import get_settings
from app.services.vector_store import VectorStoreService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RAGService:
    """Service for Retrieval-Augmented Generation."""
    
    def __init__(self):
        self.settings = get_settings()
        self.client = OpenAI(
            api_key=self.settings.openai_api_key,
            base_url='https://api.openai.com/v1'
        )
        self.vector_store = VectorStoreService()
    
    def generate_answer(
        self, 
        query: str, 
        model: Optional[str] = None,
        k: int = 5
    ) -> Dict:
        """
        Generate an answer to a query using RAG.
        
        Args:
            query: User's question
            model: OpenAI model to use (defaults to settings)
            k: Number of context chunks to retrieve
            
        Returns:
            Dictionary with answer, sources, and metadata
            
        Raises:
            Exception: If answer generation fails
        """
        try:
            if not query or not query.strip():
                raise ValueError("Query cannot be empty")
            
            if model is None:
                model = self.settings.chat_model
            
            logger.info(f"Generating answer for query: {query[:100]}...")
            
            # Check if index has documents
            stats = self.vector_store.get_stats()
            if stats['total_vectors'] == 0:
                return {
                    "answer": "I don't have any regulatory documents indexed yet. Please retrieve and index documents first using the 'Retrieve Documents' section.",
                    "sources": [],
                    "model_used": model,
                    "num_chunks_retrieved": 0,
                    "status": "no_documents"
                }
            
            # Retrieve relevant context
            search_results = self.vector_store.search(query, k=k)
            
            if not search_results:
                return {
                    "answer": "I couldn't find relevant information in the indexed documents. Please try rephrasing your question or index more documents.",
                    "sources": [],
                    "model_used": model,
                    "num_chunks_retrieved": 0,
                    "status": "no_results"
                }
            
            # Build context string
            context_parts = []
            sources = []
            
            for i, result in enumerate(search_results):
                context_parts.append(
                    f"[Document {i+1}: {result['source_document']}]\n"
                    f"{result['chunk_text']}\n"
                )
                sources.append({
                    "document": result['source_document'],
                    "chunk_index": result['chunk_index'],
                    "similarity_score": result.get('similarity_score', 0),
                    "distance": result.get('distance', 0)
                })
            
            context = "\n".join(context_parts)
            
            # Build prompt
            system_prompt = """You are a helpful regulatory affairs assistant specializing in drug product regulation. 
You have access to regulatory documents from major health agencies including FDA, EMA, Health Canada, TGA, NHRA, and Swissmedic.

Your task is to answer questions based on the provided regulatory documents. Always:
1. Base your answer on the provided context
2. Cite specific documents when making claims (use the document names provided in brackets)
3. If the context doesn't contain enough information to fully answer the question, say so clearly
4. Provide clear, professional responses suitable for regulatory professionals
5. When appropriate, note any differences between regulatory agencies
6. Be precise about regulatory requirements and guidelines
7. If you're uncertain about something, acknowledge it

Remember: Accuracy is critical in regulatory matters. Never make up information."""

            user_prompt = f"""Context from regulatory documents:

{context}

Question: {query}

Please provide a detailed answer based on the context above. Cite the specific documents you're referencing."""

            # Generate response
            logger.info(f"Calling OpenAI API with model: {model}")
            
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            answer = response.choices[0].message.content
            
            logger.info(f"✓ Generated answer ({len(answer)} characters)")
            
            return {
                "answer": answer,
                "sources": sources,
                "model_used": model,
                "num_chunks_retrieved": len(search_results),
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}")
            return {
                "answer": f"Error generating answer: {str(e)}",
                "sources": [],
                "model_used": model or "unknown",
                "num_chunks_retrieved": 0,
                "status": "error",
                "error": str(e)
            }
    
    def ask_for_clarification(self, query: str) -> Dict:
        """
        Determine if a query needs clarification.
        
        Args:
            query: User's question
            
        Returns:
            Dictionary with clarification status and suggestions
        """
        try:
            # Simple heuristics for now
            clarification_needed = False
            suggestions = []
            
            # Check if query is too short
            if len(query.split()) < 3:
                clarification_needed = True
                suggestions.append("Your question seems quite brief. Could you provide more details?")
            
            # Check if query is too vague
            vague_terms = ["this", "that", "it", "thing", "stuff"]
            if any(term in query.lower() for term in vague_terms):
                clarification_needed = True
                suggestions.append("Your question contains vague terms. Could you be more specific?")
            
            return {
                "needs_clarification": clarification_needed,
                "suggestions": suggestions
            }
            
        except Exception as e:
            logger.error(f"Error checking clarification: {str(e)}")
            return {
                "needs_clarification": False,
                "suggestions": []
            }

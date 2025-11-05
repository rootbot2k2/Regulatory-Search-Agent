"""
FAISS vector store service for document indexing and similarity search.
"""
import faiss
import numpy as np
import json
from pathlib import Path
from typing import List, Tuple, Dict, Optional
from openai import OpenAI
import logging

from app.core.config import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VectorStoreService:
    """Service for managing FAISS vector index."""
    
    def __init__(self):
        self.settings = get_settings()
        self.client = OpenAI(
            api_key=self.settings.openai_api_key,
            base_url='https://api.openai.com/v1'
        )
        self.index: Optional[faiss.Index] = None
        self.metadata: List[Dict] = []
        self.dimension = 1536  # Dimension for text-embedding-ada-002
        
        # Load existing index if available
        self._load_index()
    
    def _load_index(self):
        """Load existing FAISS index and metadata from disk."""
        index_path = Path(self.settings.faiss_index_path)
        metadata_path = Path(self.settings.faiss_metadata_path)
        
        try:
            if index_path.exists() and metadata_path.exists():
                self.index = faiss.read_index(str(index_path))
                with open(metadata_path, 'r') as f:
                    self.metadata = json.load(f)
                logger.info(f"✓ Loaded existing index with {len(self.metadata)} vectors")
            else:
                # Create new index
                self.index = faiss.IndexFlatL2(self.dimension)
                self.metadata = []
                logger.info("✓ Created new FAISS index")
        except Exception as e:
            logger.error(f"Error loading index: {str(e)}")
            # Create new index on error
            self.index = faiss.IndexFlatL2(self.dimension)
            self.metadata = []
            logger.info("✓ Created new FAISS index (after load error)")
    
    def _save_index(self):
        """Save FAISS index and metadata to disk."""
        try:
            index_path = Path(self.settings.faiss_index_path)
            metadata_path = Path(self.settings.faiss_metadata_path)
            
            # Create directories if they don't exist
            index_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save index
            faiss.write_index(self.index, str(index_path))
            
            # Save metadata
            with open(metadata_path, 'w') as f:
                json.dump(self.metadata, f, indent=2)
            
            logger.info(f"✓ Saved index with {len(self.metadata)} vectors")
        except Exception as e:
            logger.error(f"Error saving index: {str(e)}")
            raise
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a text using OpenAI API.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
            
        Raises:
            Exception: If embedding generation fails
        """
        try:
            # Truncate text if too long (max 8191 tokens for ada-002)
            max_chars = 30000  # Approximate, ~8000 tokens
            if len(text) > max_chars:
                text = text[:max_chars]
                logger.warning(f"Text truncated to {max_chars} characters")
            
            response = self.client.embeddings.create(
                model=self.settings.embedding_model,
                input=text
            )
            
            embedding = response.data[0].embedding
            logger.debug(f"Generated embedding with {len(embedding)} dimensions")
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise Exception(f"Failed to generate embedding: {str(e)}")
    
    def add_documents(
        self, 
        chunks: List[str], 
        doc_metadata: Dict
    ):
        """
        Add document chunks to the vector store.
        
        Args:
            chunks: List of text chunks
            doc_metadata: Metadata about the source document
            
        Raises:
            Exception: If indexing fails
        """
        try:
            if not chunks:
                raise ValueError("No chunks provided")
            
            logger.info(f"Indexing {len(chunks)} chunks from {doc_metadata.get('file_name', 'unknown')}")
            
            embeddings = []
            
            for i, chunk in enumerate(chunks):
                try:
                    # Generate embedding
                    embedding = self.generate_embedding(chunk)
                    embeddings.append(embedding)
                    
                    # Store metadata
                    self.metadata.append({
                        "chunk_id": len(self.metadata),
                        "chunk_text": chunk,
                        "chunk_index": i,
                        "source_document": doc_metadata.get("file_name", "unknown"),
                        "file_path": doc_metadata.get("file_path", "unknown"),
                        "total_chunks": doc_metadata.get("num_chunks", len(chunks))
                    })
                    
                    if (i + 1) % 10 == 0:
                        logger.info(f"  Processed {i + 1}/{len(chunks)} chunks")
                        
                except Exception as e:
                    logger.error(f"Error processing chunk {i}: {str(e)}")
                    # Continue with next chunk
                    continue
            
            if not embeddings:
                raise Exception("No embeddings generated successfully")
            
            # Add to FAISS index
            embeddings_array = np.array(embeddings).astype('float32')
            self.index.add(embeddings_array)
            
            # Save to disk
            self._save_index()
            
            logger.info(f"✓ Successfully indexed {len(embeddings)} chunks")
            
        except Exception as e:
            logger.error(f"Error adding documents: {str(e)}")
            raise
    
    def search(
        self, 
        query: str, 
        k: int = 5
    ) -> List[Dict]:
        """
        Search for similar chunks given a query.
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of similar chunks with metadata
            
        Raises:
            Exception: If search fails
        """
        try:
            if not self.metadata:
                logger.warning("Index is empty, no results to return")
                return []
            
            # Ensure k doesn't exceed available vectors
            k = min(k, len(self.metadata))
            
            # Generate query embedding
            query_embedding = self.generate_embedding(query)
            query_vector = np.array([query_embedding]).astype('float32')
            
            # Search FAISS index
            distances, indices = self.index.search(query_vector, k)
            
            # Retrieve metadata for results
            results = []
            for i, idx in enumerate(indices[0]):
                if idx < len(self.metadata) and idx >= 0:
                    result = self.metadata[idx].copy()
                    result["distance"] = float(distances[0][i])
                    result["similarity_score"] = 1 / (1 + float(distances[0][i]))  # Convert distance to similarity
                    results.append(result)
            
            logger.info(f"✓ Found {len(results)} similar chunks for query")
            return results
            
        except Exception as e:
            logger.error(f"Error searching index: {str(e)}")
            raise
    
    def get_stats(self) -> Dict:
        """Get statistics about the vector store."""
        return {
            "total_vectors": len(self.metadata),
            "dimension": self.dimension,
            "index_type": type(self.index).__name__,
            "unique_documents": len(set(m.get("source_document", "") for m in self.metadata))
        }

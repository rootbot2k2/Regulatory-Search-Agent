# Regulatory Search Agent: Implementation Guide

**Author:** Manus AI
**Date:** November 4, 2025

## 1. Getting Started

This guide provides step-by-step instructions and code examples for implementing the Regulatory Search Agent. It is designed to be followed sequentially, starting with the initial project setup and progressing through each milestone.

## 2. Prerequisites

Before beginning, ensure you have the following installed on your development machine:

- **Python 3.9 or higher**
- **Git** for version control
- **Poetry** or **Pipenv** for dependency management
- **Google Chrome** and **ChromeDriver** for Selenium web automation
- **OpenAI API Key** (obtain from https://platform.openai.com/)

## 3. Initial Project Setup

### 3.1. Create the Git Repository

First, create a new Git repository on GitHub or another platform. Name it `Regulatory-Search-Agent`. Clone the repository to your local machine:

```bash
git clone https://github.com/your-username/Regulatory-Search-Agent.git
cd Regulatory-Search-Agent
```

### 3.2. Initialize Python Environment

Use Poetry to initialize the project and manage dependencies:

```bash
poetry init
```

Follow the prompts to set up the project metadata. Then, add the required dependencies:

```bash
poetry add fastapi uvicorn python-dotenv openai faiss-cpu pymupdf selenium
poetry add --dev pytest black flake8
```

Alternatively, if using pip and a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install fastapi uvicorn python-dotenv openai faiss-cpu pymupdf selenium
pip install pytest black flake8
```

### 3.3. Create Project Structure

Create the following directory structure:

```bash
mkdir -p app/api app/core app/services/web_automation app/gui data/downloaded_docs data/faiss_index
touch app/__init__.py app/api/__init__.py app/api/endpoints.py
touch app/core/__init__.py app/core/config.py app/core/orchestrator.py
touch app/services/__init__.py app/services/document_processing.py
touch app/services/rag_service.py app/services/vector_store.py
touch app/services/web_automation/__init__.py app/services/web_automation/base_scraper.py
touch app/services/web_automation/fda_scraper.py
touch app/gui/__init__.py app/gui/chat_interface.py
touch main.py .env.template .gitignore README.md
```

### 3.4. Configure Environment Variables

Create a `.env.template` file with the following content:

```
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Model Configuration
EMBEDDING_MODEL=text-embedding-ada-002
CHAT_MODEL=gpt-4

# FAISS Configuration
FAISS_INDEX_PATH=./data/faiss_index/regulatory_docs.index
FAISS_METADATA_PATH=./data/faiss_index/metadata.json

# Document Storage
DOWNLOAD_DIR=./data/downloaded_docs/

# Server Configuration
HOST=0.0.0.0
PORT=8000
```

Copy this file to `.env` and fill in your actual OpenAI API key:

```bash
cp .env.template .env
```

Update the `.gitignore` file to exclude the `.env` file and other sensitive or generated files:

```
# Environment
.env
venv/
__pycache__/

# Data
data/downloaded_docs/*
data/faiss_index/*

# IDE
.vscode/
.idea/
```

## 4. Core Configuration Module

Create the configuration module in `app/core/config.py`:

```python
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # OpenAI Configuration
    openai_api_key: str
    embedding_model: str = "text-embedding-ada-002"
    chat_model: str = "gpt-4"
    
    # FAISS Configuration
    faiss_index_path: str = "./data/faiss_index/regulatory_docs.index"
    faiss_metadata_path: str = "./data/faiss_index/metadata.json"
    
    # Document Storage
    download_dir: str = "./data/downloaded_docs/"
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
```

## 5. Document Processing Services

### 5.1. PDF Parser Service

Create `app/services/document_processing.py`:

```python
import fitz  # PyMuPDF
from pathlib import Path
from typing import List, Tuple

class PDFParserService:
    """Service for extracting text from PDF documents."""
    
    @staticmethod
    def extract_text(pdf_path: str) -> str:
        """
        Extract text content from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text as a single string
        """
        try:
            doc = fitz.open(pdf_path)
            text = ""
            
            for page in doc:
                text += page.get_text()
            
            doc.close()
            return text
        except Exception as e:
            raise Exception(f"Error extracting text from PDF: {str(e)}")

class TextChunkingService:
    """Service for chunking text into smaller segments."""
    
    @staticmethod
    def chunk_text(
        text: str, 
        chunk_size: int = 1000, 
        overlap: int = 100
    ) -> List[str]:
        """
        Split text into overlapping chunks.
        
        Args:
            text: The text to chunk
            chunk_size: Maximum size of each chunk in characters
            overlap: Number of characters to overlap between chunks
            
        Returns:
            List of text chunks
        """
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start += chunk_size - overlap
        
        return chunks

class DocumentProcessor:
    """Main document processing pipeline."""
    
    def __init__(self):
        self.pdf_parser = PDFParserService()
        self.text_chunker = TextChunkingService()
    
    def process_document(
        self, 
        file_path: str, 
        chunk_size: int = 1000, 
        overlap: int = 100
    ) -> Tuple[List[str], dict]:
        """
        Process a document and return chunks with metadata.
        
        Args:
            file_path: Path to the document
            chunk_size: Size of text chunks
            overlap: Overlap between chunks
            
        Returns:
            Tuple of (chunks, metadata)
        """
        # Extract text
        text = self.pdf_parser.extract_text(file_path)
        
        # Chunk text
        chunks = self.text_chunker.chunk_text(text, chunk_size, overlap)
        
        # Create metadata
        metadata = {
            "file_path": file_path,
            "file_name": Path(file_path).name,
            "num_chunks": len(chunks),
            "total_length": len(text)
        }
        
        return chunks, metadata
```

### 5.2. Vector Store Service

Create `app/services/vector_store.py`:

```python
import faiss
import numpy as np
import json
from pathlib import Path
from typing import List, Tuple, Dict
from openai import OpenAI
from app.core.config import get_settings

class VectorStoreService:
    """Service for managing FAISS vector index."""
    
    def __init__(self):
        self.settings = get_settings()
        self.client = OpenAI(api_key=self.settings.openai_api_key)
        self.index = None
        self.metadata = []
        self.dimension = 1536  # Dimension for text-embedding-ada-002
        
        # Load existing index if available
        self._load_index()
    
    def _load_index(self):
        """Load existing FAISS index and metadata from disk."""
        index_path = Path(self.settings.faiss_index_path)
        metadata_path = Path(self.settings.faiss_metadata_path)
        
        if index_path.exists() and metadata_path.exists():
            self.index = faiss.read_index(str(index_path))
            with open(metadata_path, 'r') as f:
                self.metadata = json.load(f)
        else:
            # Create new index
            self.index = faiss.IndexFlatL2(self.dimension)
            self.metadata = []
    
    def _save_index(self):
        """Save FAISS index and metadata to disk."""
        index_path = Path(self.settings.faiss_index_path)
        metadata_path = Path(self.settings.faiss_metadata_path)
        
        # Create directories if they don't exist
        index_path.parent.mkdir(parents=True, exist_ok=True)
        
        faiss.write_index(self.index, str(index_path))
        with open(metadata_path, 'w') as f:
            json.dump(self.metadata, f, indent=2)
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a text using OpenAI API.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        response = self.client.embeddings.create(
            model=self.settings.embedding_model,
            input=text
        )
        return response.data[0].embedding
    
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
        """
        embeddings = []
        
        for i, chunk in enumerate(chunks):
            # Generate embedding
            embedding = self.generate_embedding(chunk)
            embeddings.append(embedding)
            
            # Store metadata
            self.metadata.append({
                "chunk_id": len(self.metadata),
                "chunk_text": chunk,
                "chunk_index": i,
                "source_document": doc_metadata["file_name"],
                "file_path": doc_metadata["file_path"]
            })
        
        # Add to FAISS index
        embeddings_array = np.array(embeddings).astype('float32')
        self.index.add(embeddings_array)
        
        # Save to disk
        self._save_index()
    
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
        """
        # Generate query embedding
        query_embedding = self.generate_embedding(query)
        query_vector = np.array([query_embedding]).astype('float32')
        
        # Search FAISS index
        distances, indices = self.index.search(query_vector, k)
        
        # Retrieve metadata for results
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(self.metadata):
                result = self.metadata[idx].copy()
                result["distance"] = float(distances[0][i])
                results.append(result)
        
        return results
```

## 6. RAG Service

Create `app/services/rag_service.py`:

```python
from typing import List, Dict
from openai import OpenAI
from app.core.config import get_settings
from app.services.vector_store import VectorStoreService

class RAGService:
    """Service for Retrieval-Augmented Generation."""
    
    def __init__(self):
        self.settings = get_settings()
        self.client = OpenAI(api_key=self.settings.openai_api_key)
        self.vector_store = VectorStoreService()
    
    def generate_answer(
        self, 
        query: str, 
        model: str = None,
        k: int = 5
    ) -> Dict:
        """
        Generate an answer to a query using RAG.
        
        Args:
            query: User's question
            model: OpenAI model to use (defaults to settings)
            k: Number of context chunks to retrieve
            
        Returns:
            Dictionary with answer and sources
        """
        if model is None:
            model = self.settings.chat_model
        
        # Retrieve relevant context
        search_results = self.vector_store.search(query, k=k)
        
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
                "chunk_index": result['chunk_index']
            })
        
        context = "\n".join(context_parts)
        
        # Build prompt
        system_prompt = """You are a helpful regulatory affairs assistant specializing in drug product regulation. 
You have access to regulatory documents from major health agencies including FDA, EMA, Health Canada, TGA, NHRA, and Swissmedic.

Your task is to answer questions based on the provided regulatory documents. Always:
1. Base your answer on the provided context
2. Cite specific documents when making claims
3. If the context doesn't contain enough information, say so
4. Provide clear, professional responses suitable for regulatory professionals
5. When appropriate, note any differences between regulatory agencies"""

        user_prompt = f"""Context from regulatory documents:

{context}

Question: {query}

Please provide a detailed answer based on the context above."""

        # Generate response
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
        
        return {
            "answer": answer,
            "sources": sources,
            "model_used": model,
            "num_chunks_retrieved": len(search_results)
        }
```

## 7. FastAPI Backend

Create `main.py`:

```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from app.core.config import get_settings
from app.services.document_processing import DocumentProcessor
from app.services.vector_store import VectorStoreService
from app.services.rag_service import RAGService

app = FastAPI(title="Regulatory Search Agent API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
settings = get_settings()
doc_processor = DocumentProcessor()
vector_store = VectorStoreService()
rag_service = RAGService()

# Request/Response models
class QueryRequest(BaseModel):
    query: str
    model: Optional[str] = None
    k: Optional[int] = 5

class QueryResponse(BaseModel):
    answer: str
    sources: List[dict]
    model_used: str
    num_chunks_retrieved: int

class IndexDocumentRequest(BaseModel):
    file_path: str
    chunk_size: Optional[int] = 1000
    overlap: Optional[int] = 100

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

@app.post("/api/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    Answer a query using RAG.
    """
    try:
        result = rag_service.generate_answer(
            query=request.query,
            model=request.model,
            k=request.k
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/index-document")
async def index_document(request: IndexDocumentRequest):
    """
    Index a document into the vector store.
    """
    try:
        # Process document
        chunks, metadata = doc_processor.process_document(
            file_path=request.file_path,
            chunk_size=request.chunk_size,
            overlap=request.overlap
        )
        
        # Add to vector store
        vector_store.add_documents(chunks, metadata)
        
        return {
            "status": "success",
            "num_chunks": len(chunks),
            "document": metadata["file_name"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.host, port=settings.port)
```

## 8. Running the Application

To start the FastAPI backend:

```bash
python main.py
```

Or using uvicorn directly:

```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`. You can access the interactive API documentation at `http://localhost:8000/docs`.

## 9. Testing the System

Create a test script `test_indexing.py`:

```python
import requests

# Test indexing a document
response = requests.post(
    "http://localhost:8000/api/index-document",
    json={
        "file_path": "./data/downloaded_docs/sample_document.pdf"
    }
)
print("Indexing response:", response.json())

# Test querying
response = requests.post(
    "http://localhost:8000/api/query",
    json={
        "query": "What are the safety considerations for this drug?",
        "model": "gpt-4",
        "k": 5
    }
)
print("Query response:", response.json())
```

## 10. Next Steps

After completing the basic backend, proceed to implement:

1. **Web Automation Module** - See the next section for FDA scraper implementation
2. **GUI Interface** - Use Streamlit or Gradio to create the chat interface
3. **Orchestrator** - Implement the agentic core to coordinate all modules
4. **Additional Agency Scrapers** - Extend to EMA, Health Canada, TGA, NHRA, and Swissmedic

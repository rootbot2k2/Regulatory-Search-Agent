"""
Main FastAPI application for the Regulatory Search Agent.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import get_settings
from app.core.orchestrator import AgenticOrchestrator

# Initialize FastAPI app
app = FastAPI(
    title="Regulatory Search Agent API",
    description="API for automated regulatory document retrieval and analysis",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get settings
settings = get_settings()

# Initialize orchestrator
orchestrator = AgenticOrchestrator()


# Request/Response models
class QueryRequest(BaseModel):
    query: str
    model: Optional[str] = None
    k: Optional[int] = 5


class RetrieveRequest(BaseModel):
    drug_name: str
    agencies: Optional[List[str]] = None
    max_docs_per_agency: Optional[int] = 3


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Regulatory Search Agent API",
        "version": "1.0.0",
        "status": "online"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "services": {
            "api": "online",
            "openai": "configured" if settings.openai_api_key else "not configured"
        }
    }


@app.get("/status")
async def system_status():
    """Get system status."""
    try:
        status = orchestrator.get_system_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/retrieve")
async def retrieve_documents(request: RetrieveRequest):
    """
    Retrieve and index regulatory documents.
    """
    try:
        result = orchestrator.retrieve_and_index(
            drug_name=request.drug_name,
            agencies=request.agencies,
            max_docs_per_agency=request.max_docs_per_agency
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/query")
async def query(request: QueryRequest):
    """
    Answer a query using RAG.
    """
    try:
        result = orchestrator.query(
            question=request.query,
            model=request.model,
            k=request.k
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    print(f"🚀 Starting Regulatory Search Agent API on {settings.host}:{settings.port}")
    uvicorn.run(app, host=settings.host, port=settings.port)

"""
Configuration management for the Regulatory Search Agent.
Loads settings from environment variables.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path
from dotenv import load_dotenv
import os

# Load .env file explicitly before anything else
load_dotenv(override=True)


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
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Ensure data directories exist
def ensure_directories():
    """Create necessary directories if they don't exist."""
    settings = get_settings()
    
    # Create FAISS index directory
    Path(settings.faiss_index_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Create download directory
    Path(settings.download_dir).mkdir(parents=True, exist_ok=True)
    
    print(f"✓ Data directories initialized")


# Initialize directories on import
ensure_directories()

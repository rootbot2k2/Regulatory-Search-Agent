"""
Base scraper interface for all regulatory agency scrapers.
"""
from abc import ABC, abstractmethod
from typing import List, Dict
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Abstract base class for all agency scrapers."""
    
    def __init__(self, download_dir: str):
        """
        Initialize the scraper.
        
        Args:
            download_dir: Directory to save downloaded documents
        """
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"✓ Initialized scraper with download directory: {self.download_dir}")
    
    @abstractmethod
    def search_drug(self, drug_name: str) -> List[Dict]:
        """
        Search for a drug and return available documents.
        
        Args:
            drug_name: Name of the drug to search for
            
        Returns:
            List of document metadata dictionaries
        """
        pass
    
    @abstractmethod
    def download_document(self, document_metadata: Dict) -> str:
        """
        Download a specific document.
        
        Args:
            document_metadata: Metadata about the document to download
            
        Returns:
            Path to the downloaded file
        """
        pass
    
    def search_and_download(self, drug_name: str, max_documents: int = 5) -> List[str]:
        """
        Search for a drug and download all available documents.
        
        Args:
            drug_name: Name of the drug to search for
            max_documents: Maximum number of documents to download
            
        Returns:
            List of paths to downloaded files
        """
        logger.info(f"Searching for {drug_name}...")
        
        try:
            documents = self.search_drug(drug_name)
            
            if not documents:
                logger.warning(f"No documents found for {drug_name}")
                return []
            
            logger.info(f"Found {len(documents)} documents")
            
            # Limit number of documents
            documents = documents[:max_documents]
            
            downloaded_files = []
            
            for i, doc_metadata in enumerate(documents, 1):
                try:
                    logger.info(f"Downloading document {i}/{len(documents)}: {doc_metadata.get('title', 'Unknown')}")
                    file_path = self.download_document(doc_metadata)
                    downloaded_files.append(file_path)
                except Exception as e:
                    logger.error(f"Error downloading {doc_metadata.get('title', 'document')}: {str(e)}")
                    # Continue with next document
                    continue
            
            logger.info(f"✓ Successfully downloaded {len(downloaded_files)} documents")
            return downloaded_files
            
        except Exception as e:
            logger.error(f"Error in search_and_download: {str(e)}")
            return []
    
    def _sanitize_filename(self, filename: str, max_length: int = 200) -> str:
        """
        Sanitize filename to remove invalid characters.
        
        Args:
            filename: Original filename
            max_length: Maximum filename length
            
        Returns:
            Sanitized filename
        """
        # Remove invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Limit length
        if len(filename) > max_length:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            name = name[:max_length - len(ext) - 1]
            filename = f"{name}.{ext}" if ext else name
        
        return filename

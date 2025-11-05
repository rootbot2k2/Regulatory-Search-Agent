"""
Document processing services for PDF parsing and text chunking.
"""
import fitz  # PyMuPDF
from pathlib import Path
from typing import List, Tuple, Dict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
            
        Raises:
            FileNotFoundError: If PDF file doesn't exist
            Exception: If PDF extraction fails
        """
        pdf_file = Path(pdf_path)
        
        if not pdf_file.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        if not pdf_file.suffix.lower() == '.pdf':
            raise ValueError(f"File is not a PDF: {pdf_path}")
        
        try:
            doc = fitz.open(pdf_path)
            text = ""
            
            for page_num, page in enumerate(doc, 1):
                page_text = page.get_text()
                text += page_text
                logger.debug(f"Extracted page {page_num}/{len(doc)}")
            
            doc.close()
            
            if not text.strip():
                raise ValueError("No text content extracted from PDF")
            
            logger.info(f"✓ Extracted {len(text)} characters from {pdf_file.name}")
            return text
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            raise Exception(f"Failed to extract text from PDF: {str(e)}")


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
            
        Raises:
            ValueError: If parameters are invalid
        """
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        
        if overlap < 0:
            raise ValueError("overlap cannot be negative")
        
        if overlap >= chunk_size:
            raise ValueError("overlap must be less than chunk_size")
        
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + chunk_size
            chunk = text[start:end]
            
            # Only add non-empty chunks
            if chunk.strip():
                chunks.append(chunk)
            
            start += chunk_size - overlap
        
        logger.info(f"✓ Created {len(chunks)} chunks from {text_length} characters")
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
    ) -> Tuple[List[str], Dict]:
        """
        Process a document and return chunks with metadata.
        
        Args:
            file_path: Path to the document
            chunk_size: Size of text chunks
            overlap: Overlap between chunks
            
        Returns:
            Tuple of (chunks, metadata)
            
        Raises:
            Exception: If processing fails
        """
        try:
            logger.info(f"Processing document: {file_path}")
            
            # Extract text
            text = self.pdf_parser.extract_text(file_path)
            
            # Chunk text
            chunks = self.text_chunker.chunk_text(text, chunk_size, overlap)
            
            # Create metadata
            file_path_obj = Path(file_path)
            metadata = {
                "file_path": str(file_path),
                "file_name": file_path_obj.name,
                "num_chunks": len(chunks),
                "total_length": len(text),
                "chunk_size": chunk_size,
                "overlap": overlap
            }
            
            logger.info(f"✓ Successfully processed {file_path_obj.name}: {len(chunks)} chunks")
            return chunks, metadata
            
        except Exception as e:
            logger.error(f"Error processing document: {str(e)}")
            raise

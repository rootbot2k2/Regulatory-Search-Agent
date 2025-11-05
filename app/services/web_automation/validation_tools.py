"""
Validation tools for AI-powered web navigation.
These tools help the browser-use agent verify it's downloading the correct documents.
"""

import os
import logging
from pathlib import Path
from typing import Dict, List
import fitz  # PyMuPDF
from openai import OpenAI

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class DocumentValidator:
    """Validates regulatory documents using AI."""
    
    def __init__(self):
        settings = get_settings()
        self.client = OpenAI(
            api_key=settings.openai_api_key,
            base_url="https://api.openai.com/v1"
        )
    
    def validate_regulatory_document(
        self, 
        file_path: str, 
        drug_name: str,
        expected_type: str = "medical_review"
    ) -> Dict:
        """
        Validate that a downloaded file is a regulatory review document.
        
        Args:
            file_path: Path to the downloaded file
            drug_name: Expected drug name
            expected_type: Expected document type (medical_review, clinical_review, etc.)
        
        Returns:
            Dict with validation results
        """
        try:
            if not os.path.exists(file_path):
                return {
                    'is_valid': False,
                    'reason': 'File does not exist',
                    'confidence': 0.0
                }
            
            # Check file extension
            if not file_path.lower().endswith('.pdf'):
                return {
                    'is_valid': False,
                    'reason': 'Not a PDF file',
                    'confidence': 0.0
                }
            
            # Extract first page text
            text = self._extract_first_page(file_path)
            
            if not text or len(text) < 100:
                return {
                    'is_valid': False,
                    'reason': 'Could not extract text from PDF',
                    'confidence': 0.0
                }
            
            # Use GPT-4 to validate
            validation = self._ai_validate(text, drug_name, expected_type)
            
            return validation
            
        except Exception as e:
            logger.error(f"Error validating document: {e}")
            return {
                'is_valid': False,
                'reason': f'Validation error: {str(e)}',
                'confidence': 0.0
            }
    
    def _extract_first_page(self, file_path: str) -> str:
        """Extract text from first page of PDF."""
        try:
            doc = fitz.open(file_path)
            if len(doc) == 0:
                return ""
            
            first_page = doc[0]
            text = first_page.get_text()
            doc.close()
            
            return text
            
        except Exception as e:
            logger.error(f"Error extracting PDF text: {e}")
            return ""
    
    def _ai_validate(
        self, 
        text: str, 
        drug_name: str, 
        expected_type: str
    ) -> Dict:
        """Use GPT-4 to validate document content."""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a regulatory document validator. 
                        Analyze the provided text and determine if it's a regulatory 
                        review document for the specified drug."""
                    },
                    {
                        "role": "user",
                        "content": f"""Is this a {expected_type} document for {drug_name}?

Document preview (first page):
{text[:2000]}

Respond with JSON:
{{
    "is_valid": true/false,
    "document_type": "medical_review" | "clinical_review" | "label" | "patient_info" | "other",
    "mentions_drug": true/false,
    "confidence": 0.0-1.0,
    "reason": "brief explanation"
}}"""
                    }
                ],
                temperature=0.0
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            
            # Determine if valid
            is_valid = (
                result.get('is_valid', False) and 
                result.get('mentions_drug', False) and
                result.get('confidence', 0.0) > 0.7
            )
            
            return {
                'is_valid': is_valid,
                'document_type': result.get('document_type', 'unknown'),
                'confidence': result.get('confidence', 0.0),
                'reason': result.get('reason', 'AI validation completed')
            }
            
        except Exception as e:
            logger.error(f"AI validation error: {e}")
            return {
                'is_valid': False,
                'reason': f'AI validation failed: {str(e)}',
                'confidence': 0.0
            }
    
    def check_duplicate(self, file_path: str, download_dir: str) -> bool:
        """
        Check if file already exists in download directory.
        
        Args:
            file_path: Path to the file to check
            download_dir: Directory to check for duplicates
        
        Returns:
            True if duplicate exists, False otherwise
        """
        try:
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            
            # Check for exact filename match
            for existing_file in Path(download_dir).glob('*.pdf'):
                if existing_file.name == file_name:
                    # Check if file sizes match
                    if existing_file.stat().st_size == file_size:
                        logger.info(f"Duplicate found: {file_name}")
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking for duplicates: {e}")
            return False
    
    def get_document_metadata(self, file_path: str) -> Dict:
        """
        Extract metadata from PDF document.
        
        Args:
            file_path: Path to the PDF file
        
        Returns:
            Dict with document metadata
        """
        try:
            doc = fitz.open(file_path)
            metadata = doc.metadata
            
            return {
                'title': metadata.get('title', ''),
                'author': metadata.get('author', ''),
                'subject': metadata.get('subject', ''),
                'pages': len(doc),
                'file_size': os.path.getsize(file_path),
                'file_name': os.path.basename(file_path)
            }
            
        except Exception as e:
            logger.error(f"Error extracting metadata: {e}")
            return {}


def create_validation_tools_for_browser_use():
    """
    Create custom tools for browser-use Agent.
    These tools can be called by the AI agent during navigation.
    """
    from browser_use import Tools
    
    tools = Tools()
    validator = DocumentValidator()
    
    @tools.action(
        description='Validate that a downloaded PDF is a regulatory review document for the specified drug'
    )
    def validate_document(file_path: str, drug_name: str) -> Dict:
        """
        Validate downloaded document.
        
        Args:
            file_path: Path to the downloaded file
            drug_name: Name of the drug
        
        Returns:
            Validation results
        """
        return validator.validate_regulatory_document(file_path, drug_name)
    
    @tools.action(
        description='Check if a file has already been downloaded to avoid duplicates'
    )
    def check_duplicate_file(file_path: str) -> bool:
        """
        Check for duplicate files.
        
        Args:
            file_path: Path to the file
        
        Returns:
            True if duplicate exists
        """
        settings = get_settings()
        download_dir = settings.download_dir
        return validator.check_duplicate(file_path, download_dir)
    
    @tools.action(
        description='Extract metadata from a PDF document'
    )
    def get_pdf_metadata(file_path: str) -> Dict:
        """
        Get PDF metadata.
        
        Args:
            file_path: Path to the PDF
        
        Returns:
            Metadata dict
        """
        return validator.get_document_metadata(file_path)
    
    return tools

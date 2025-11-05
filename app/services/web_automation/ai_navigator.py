"""
AI-Powered Web Navigator using Browser-Use.
Replaces all Selenium-based scrapers with a single intelligent agent.
"""

import asyncio
import logging
import os
from typing import List, Dict, Optional
from pathlib import Path

from browser_use import Agent, Browser, ChatBrowserUse

from app.core.config import get_settings
from app.services.web_automation.validation_tools import create_validation_tools_for_browser_use

logger = logging.getLogger(__name__)


class AIWebNavigator:
    """
    Intelligent web navigator that can autonomously navigate regulatory agency websites
    and download relevant documents.
    
    This single class replaces all agency-specific Selenium scrapers.
    """
    
    # Agency website URLs
    AGENCY_URLS = {
        'FDA': 'https://www.accessdata.fda.gov/scripts/cder/daf/',
        'EMA': 'https://www.ema.europa.eu/en/medicines/field_ema_web_categories%253Aname_field/Human/ema_group_types/ema_medicine',
        'Health Canada': 'https://dhpp.hpfb-dgpsa.ca/review-documents',
        'TGA': 'https://www.tga.gov.au/products/medicines',
        'Swissmedic': 'https://www.swissmedic.ch/swissmedic/en/home/humanarzneimittel/authorisations/new-medicines.html',
        'NHRA': 'https://www.nhra.bh/'
    }
    
    # Document type descriptions for each agency
    DOCUMENT_TYPES = {
        'FDA': 'medical review, clinical review, pharmacology review, approval letter',
        'EMA': 'EPAR (European Public Assessment Report), CHMP assessment report',
        'Health Canada': 'Regulatory Decision Summary (RDS), Clinical Review',
        'TGA': 'Australian Public Assessment Report (AusPAR)',
        'Swissmedic': 'Public Assessment Report',
        'NHRA': 'Regulatory approval documents'
    }
    
    def __init__(self):
        """Initialize the AI navigator."""
        settings = get_settings()
        self.download_dir = settings.download_dir
        os.makedirs(self.download_dir, exist_ok=True)
        
        # Initialize browser (will be created per session)
        self.browser = None
        
        # Initialize LLM for the agent
        # Use ChatBrowserUse which is optimized for browser automation
        self.llm = ChatBrowserUse()
        
        # Create validation tools
        self.tools = create_validation_tools_for_browser_use()
        
        logger.info("AI Web Navigator initialized")
    
    async def retrieve_documents(
        self,
        drug_name: str,
        agencies: List[str],
        document_types: Optional[List[str]] = None
    ) -> Dict[str, List[str]]:
        """
        Retrieve regulatory documents for a drug from specified agencies.
        
        Args:
            drug_name: Name of the drug
            agencies: List of agency names (FDA, EMA, etc.)
            document_types: Optional list of specific document types to retrieve
        
        Returns:
            Dict mapping agency names to lists of downloaded file paths
        """
        results = {}
        
        for agency in agencies:
            logger.info(f"Retrieving documents from {agency} for {drug_name}")
            
            try:
                files = await self._retrieve_from_agency(
                    drug_name=drug_name,
                    agency=agency,
                    document_types=document_types
                )
                results[agency] = files
                logger.info(f"Retrieved {len(files)} documents from {agency}")
                
            except Exception as e:
                logger.error(f"Error retrieving from {agency}: {e}")
                results[agency] = []
        
        return results
    
    async def _retrieve_from_agency(
        self,
        drug_name: str,
        agency: str,
        document_types: Optional[List[str]] = None
    ) -> List[str]:
        """
        Retrieve documents from a specific agency.
        
        Args:
            drug_name: Name of the drug
            agency: Agency name
            document_types: Optional specific document types
        
        Returns:
            List of downloaded file paths
        """
        if agency not in self.AGENCY_URLS:
            logger.error(f"Unknown agency: {agency}")
            return []
        
        # Build the task description
        task = self._build_task_description(drug_name, agency, document_types)
        
        # Create browser instance
        browser = Browser(
            headless=True,  # Run in headless mode
            disable_security=False
        )
        
        try:
            # Create agent
            agent = Agent(
                task=task,
                llm=self.llm,
                browser=browser,
                tools=self.tools,
                max_actions_per_step=10
            )
            
            # Run the agent
            logger.info(f"Starting AI agent for {agency}")
            history = await agent.run()
            
            # Extract downloaded files from history
            downloaded_files = self._extract_downloaded_files(history)
            
            logger.info(f"Agent completed. Downloaded {len(downloaded_files)} files")
            return downloaded_files
            
        except Exception as e:
            logger.error(f"Error in AI agent for {agency}: {e}")
            return []
        
        finally:
            # Close browser
            if browser:
                try:
                    await browser.close()
                except:
                    pass
    
    def _build_task_description(
        self,
        drug_name: str,
        agency: str,
        document_types: Optional[List[str]] = None
    ) -> str:
        """
        Build a detailed task description for the AI agent.
        
        Args:
            drug_name: Name of the drug
            agency: Agency name
            document_types: Optional specific document types
        
        Returns:
            Task description string
        """
        agency_url = self.AGENCY_URLS[agency]
        default_doc_types = self.DOCUMENT_TYPES.get(agency, 'regulatory review documents')
        doc_types_str = ', '.join(document_types) if document_types else default_doc_types
        
        task = f"""
Navigate to the {agency} website at {agency_url}.

Your goal is to find and download regulatory review documents for the drug "{drug_name}".

Specific steps:
1. Go to the {agency} website
2. Find the search functionality (search box, search page, or drug database)
3. Search for "{drug_name}" (try variations if needed: generic name, brand name)
4. Locate the drug's approval or assessment page
5. Navigate to the documents section
6. Download PDF files for: {doc_types_str}
7. Avoid downloading: patient information leaflets, product labels, or prescribing information
8. Validate each downloaded file using the validate_document tool
9. Skip files that fail validation or are duplicates (use check_duplicate_file tool)

Important:
- Focus on regulatory REVIEW documents, not labels or patient information
- Download only PDF files
- Save files to the default download directory
- If you encounter multiple documents, download all relevant ones
- If the drug is not found, try alternative names or spellings

Return a summary of downloaded files.
"""
        
        return task.strip()
    
    def _extract_downloaded_files(self, agent_history) -> List[str]:
        """
        Extract list of downloaded files from agent execution history.
        
        Args:
            agent_history: History object from agent.run()
        
        Returns:
            List of file paths
        """
        # Check download directory for new PDF files
        download_path = Path(self.download_dir)
        
        # Get all PDF files (sorted by modification time, newest first)
        pdf_files = sorted(
            download_path.glob('*.pdf'),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        # Return paths as strings
        return [str(f) for f in pdf_files]
    
    async def test_navigation(self, agency: str = 'FDA') -> bool:
        """
        Test the AI navigator with a simple task.
        
        Args:
            agency: Agency to test with
        
        Returns:
            True if test successful
        """
        try:
            logger.info(f"Testing AI navigator with {agency}")
            
            # Simple test task
            task = f"Go to {self.AGENCY_URLS[agency]} and tell me what you see on the page."
            
            browser = Browser(headless=True)
            
            agent = Agent(
                task=task,
                llm=self.llm,
                browser=browser
            )
            
            history = await agent.run()
            
            await browser.close()
            
            logger.info("Test navigation successful")
            return True
            
        except Exception as e:
            logger.error(f"Test navigation failed: {e}")
            return False


# Convenience function for backward compatibility
async def retrieve_documents_for_drug(
    drug_name: str,
    agencies: List[str]
) -> Dict[str, List[str]]:
    """
    Retrieve regulatory documents for a drug.
    
    Args:
        drug_name: Name of the drug
        agencies: List of agencies to search
    
    Returns:
        Dict mapping agency names to lists of downloaded file paths
    """
    navigator = AIWebNavigator()
    return await navigator.retrieve_documents(drug_name, agencies)

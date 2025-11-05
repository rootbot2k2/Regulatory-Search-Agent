"""
EMA (European Medicines Agency) scraper.
"""
import requests
import time
from pathlib import Path
from typing import List, Dict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import logging

from .base_scraper import BaseScraper

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EMAScraper(BaseScraper):
    """Scraper for EMA (European Medicines Agency)."""
    
    SEARCH_URL = "https://www.ema.europa.eu/en/medicines/field_ema_web_categories%253Aname_field/Human"
    
    def __init__(self, download_dir: str):
        super().__init__(download_dir)
        self.driver = None
    
    def _init_driver(self):
        """Initialize Selenium WebDriver with Chrome."""
        if self.driver is None:
            try:
                logger.info("Initializing Chrome WebDriver for EMA...")
                
                options = Options()
                options.add_argument('--headless')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--disable-gpu')
                options.add_argument('--window-size=1920,1080')
                
                # Use webdriver-manager (auto-detect version)
                from webdriver_manager.core.os_manager import ChromeType
                service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
                self.driver = webdriver.Chrome(service=service, options=options)
                
                logger.info("✓ Chrome WebDriver initialized for EMA")
                
            except Exception as e:
                logger.error(f"Error initializing WebDriver: {str(e)}")
                raise
    
    def search_drug(self, drug_name: str) -> List[Dict]:
        """
        Search for a drug on EMA website.
        
        Args:
            drug_name: Name of the drug
            
        Returns:
            List of document metadata
        """
        self._init_driver()
        
        try:
            logger.info(f"Navigating to EMA medicines search...")
            self.driver.get(self.SEARCH_URL)
            
            # Wait for page to load
            time.sleep(3)
            
            # Find search box
            logger.info(f"Searching for: {drug_name}")
            
            try:
                # Try to find the search input
                search_box = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "edit-search-api-fulltext"))
                )
                
                search_box.clear()
                search_box.send_keys(drug_name)
                search_box.submit()
                
                # Wait for results
                time.sleep(3)
                
            except Exception as e:
                logger.warning(f"Could not find standard search box: {str(e)}")
                # Try alternative search method
                try:
                    search_box = self.driver.find_element(By.NAME, "search_api_fulltext")
                    search_box.clear()
                    search_box.send_keys(drug_name)
                    search_box.submit()
                    time.sleep(3)
                except Exception as e2:
                    logger.error(f"Could not find alternative search box: {str(e2)}")
                    return []
            
            documents = []
            
            # Look for search results
            try:
                # Find medicine links in results
                result_links = self.driver.find_elements(By.XPATH, "//article//h3/a | //div[contains(@class, 'search-result')]//a")
                
                logger.info(f"Found {len(result_links)} potential results")
                
                # Get first result and navigate to it
                if result_links:
                    first_result_url = result_links[0].get_attribute('href')
                    first_result_title = result_links[0].text.strip()
                    
                    logger.info(f"Navigating to: {first_result_title}")
                    self.driver.get(first_result_url)
                    time.sleep(3)
                    
                    # Look for EPAR documents
                    pdf_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, '.pdf')]")
                    
                    logger.info(f"Found {len(pdf_links)} PDF links on medicine page")
                    
                    for link in pdf_links[:10]:  # Limit to 10 documents
                        try:
                            title = link.text.strip()
                            url = link.get_attribute('href')
                            
                            # Filter for EPAR and assessment reports
                            if any(keyword in title.lower() for keyword in ['epar', 'assessment', 'review', 'summary']):
                                if title and url:
                                    documents.append({
                                        'title': title,
                                        'url': url,
                                        'drug_name': drug_name,
                                        'medicine_page': first_result_url,
                                        'agency': 'EMA'
                                    })
                        except Exception as e:
                            logger.debug(f"Error parsing PDF link: {str(e)}")
                            continue
                    
                    logger.info(f"✓ Found {len(documents)} relevant documents")
                
            except Exception as e:
                logger.error(f"Error parsing search results: {str(e)}")
            
            return documents
            
        except Exception as e:
            logger.error(f"Error searching EMA: {str(e)}")
            return []
    
    def download_document(self, document_metadata: Dict) -> str:
        """
        Download a document from EMA.
        
        Args:
            document_metadata: Metadata containing the document URL
            
        Returns:
            Path to downloaded file
        """
        try:
            url = document_metadata['url']
            title = document_metadata.get('title', 'document')
            drug_name = document_metadata.get('drug_name', 'unknown')
            
            logger.info(f"Downloading: {title}")
            
            # Download the file
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Generate filename
            filename = f"EMA_{drug_name}_{title}.pdf"
            filename = self._sanitize_filename(filename)
            
            file_path = self.download_dir / filename
            
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"✓ Downloaded: {filename}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Error downloading document: {str(e)}")
            raise
    
    def __del__(self):
        """Clean up WebDriver."""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("✓ EMA WebDriver closed")
            except Exception as e:
                logger.debug(f"Error closing WebDriver: {str(e)}")

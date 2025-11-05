"""
FDA scraper for Drugs@FDA database.
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


class FDAScraper(BaseScraper):
    """Scraper for FDA Drugs@FDA database using Selenium."""
    
    SEARCH_URL = "https://www.accessdata.fda.gov/scripts/cder/daf/index.cfm"
    
    def __init__(self, download_dir: str):
        super().__init__(download_dir)
        self.driver = None
    
    def _init_driver(self):
        """Initialize Selenium WebDriver with Chrome."""
        if self.driver is None:
            try:
                logger.info("Initializing Chrome WebDriver...")
                
                options = Options()
                options.add_argument('--headless')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--disable-gpu')
                options.add_argument('--window-size=1920,1080')
                
                # Set download directory
                prefs = {
                    "download.default_directory": str(self.download_dir.absolute()),
                    "download.prompt_for_download": False,
                    "download.directory_upgrade": True,
                    "plugins.always_open_pdf_externally": True
                }
                options.add_experimental_option("prefs", prefs)
                
                # Use webdriver-manager to handle ChromeDriver (auto-detect version)
                from webdriver_manager.core.os_manager import ChromeType
                service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
                self.driver = webdriver.Chrome(service=service, options=options)
                
                logger.info("✓ Chrome WebDriver initialized")
                
            except Exception as e:
                logger.error(f"Error initializing WebDriver: {str(e)}")
                raise
    
    def search_drug(self, drug_name: str) -> List[Dict]:
        """
        Search for a drug on FDA Drugs@FDA website.
        
        Args:
            drug_name: Name of the drug
            
        Returns:
            List of document metadata
        """
        self._init_driver()
        
        try:
            logger.info(f"Navigating to FDA Drugs@FDA search page...")
            self.driver.get(self.SEARCH_URL)
            
            # Wait for page to load
            time.sleep(2)
            
            # Find and fill the drug name search box
            logger.info(f"Searching for: {drug_name}")
            search_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "DrugName"))
            )
            
            search_box.clear()
            search_box.send_keys(drug_name)
            
            # Click search button
            search_button = self.driver.find_element(By.XPATH, "//input[@type='submit' and @value='Submit']")
            search_button.click()
            
            # Wait for results
            time.sleep(3)
            
            # Check if we got results or a specific drug page
            documents = []
            
            # Try to find the drug details page
            try:
                # Look for approval documents section
                approval_link = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.LINK_TEXT, "Approval History, Letters, Reviews, and Related Documents"))
                )
                
                logger.info("Found drug page, navigating to approval documents...")
                approval_link.click()
                time.sleep(2)
                
                # Get all document links
                doc_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, '.pdf')]")
                
                for link in doc_links[:10]:  # Limit to first 10 documents
                    try:
                        title = link.text.strip()
                        url = link.get_attribute('href')
                        
                        if title and url:
                            documents.append({
                                'title': title,
                                'url': url,
                                'drug_name': drug_name,
                                'agency': 'FDA'
                            })
                    except Exception as e:
                        logger.debug(f"Error parsing link: {str(e)}")
                        continue
                
                logger.info(f"✓ Found {len(documents)} documents")
                
            except Exception as e:
                logger.warning(f"Could not find approval documents section: {str(e)}")
                
                # Try alternative: look for results table
                try:
                    result_rows = self.driver.find_elements(By.XPATH, "//table[@class='resultsTable']//tr")[1:]
                    
                    if result_rows:
                        logger.info(f"Found {len(result_rows)} results in table")
                        
                        # Click on first result
                        if result_rows:
                            first_link = result_rows[0].find_element(By.TAG_NAME, "a")
                            first_link.click()
                            time.sleep(2)
                            
                            # Try again to find approval documents
                            try:
                                approval_link = self.driver.find_element(By.LINK_TEXT, "Approval History, Letters, Reviews, and Related Documents")
                                approval_link.click()
                                time.sleep(2)
                                
                                doc_links = self.driver.find_elements(By.XPATH, "//a[contains(@href, '.pdf')]")
                                
                                for link in doc_links[:10]:
                                    try:
                                        title = link.text.strip()
                                        url = link.get_attribute('href')
                                        
                                        if title and url:
                                            documents.append({
                                                'title': title,
                                                'url': url,
                                                'drug_name': drug_name,
                                                'agency': 'FDA'
                                            })
                                    except Exception as e:
                                        continue
                                
                                logger.info(f"✓ Found {len(documents)} documents")
                            except Exception as e:
                                logger.warning(f"Could not find approval documents: {str(e)}")
                
                except Exception as e:
                    logger.warning(f"Could not find results table: {str(e)}")
            
            return documents
            
        except Exception as e:
            logger.error(f"Error searching FDA: {str(e)}")
            return []
    
    def download_document(self, document_metadata: Dict) -> str:
        """
        Download a document from FDA.
        
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
            filename = f"FDA_{drug_name}_{title}.pdf"
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
                logger.info("✓ WebDriver closed")
            except Exception as e:
                logger.debug(f"Error closing WebDriver: {str(e)}")

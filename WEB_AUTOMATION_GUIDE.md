# Web Automation Guide for Regulatory Search Agent

**Author:** Manus AI
**Date:** November 4, 2025

## 1. Overview

This guide provides detailed instructions and code examples for implementing the web automation module that retrieves regulatory documents from the six target agencies. Each agency has unique website structures and access patterns, requiring customized scraping logic.

## 2. Base Scraper Interface

First, create a base interface that all agency scrapers will implement. This ensures a consistent API for the orchestrator.

Create `app/services/web_automation/base_scraper.py`:

```python
from abc import ABC, abstractmethod
from typing import List, Dict
from pathlib import Path

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
    
    def search_and_download(self, drug_name: str) -> List[str]:
        """
        Search for a drug and download all available documents.
        
        Args:
            drug_name: Name of the drug to search for
            
        Returns:
            List of paths to downloaded files
        """
        documents = self.search_drug(drug_name)
        downloaded_files = []
        
        for doc_metadata in documents:
            try:
                file_path = self.download_document(doc_metadata)
                downloaded_files.append(file_path)
            except Exception as e:
                print(f"Error downloading {doc_metadata.get('title', 'document')}: {e}")
        
        return downloaded_files
```

## 3. FDA Scraper Implementation

The FDA provides structured data files that can be downloaded and parsed. Create `app/services/web_automation/fda_scraper.py`:

```python
import requests
import zipfile
import io
import pandas as pd
from pathlib import Path
from typing import List, Dict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .base_scraper import BaseScraper

class FDAScraper(BaseScraper):
    """Scraper for FDA Drugs@FDA database."""
    
    DATA_FILE_URL = "https://www.fda.gov/media/89850/download"
    DRUGSFDA_BASE_URL = "https://www.accessdata.fda.gov/scripts/cder/daf/"
    
    def __init__(self, download_dir: str):
        super().__init__(download_dir)
        self.data_cache = None
        self._load_fda_data()
    
    def _load_fda_data(self):
        """Download and parse the FDA data files."""
        try:
            print("Downloading FDA data file...")
            response = requests.get(self.DATA_FILE_URL)
            
            # Extract ZIP file
            with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                # Read the ApplicationDocs table
                with z.open('ApplicationDocs.txt') as f:
                    self.data_cache = pd.read_csv(f, sep='\t', encoding='latin-1')
            
            print(f"Loaded {len(self.data_cache)} FDA document records")
        except Exception as e:
            print(f"Error loading FDA data: {e}")
            self.data_cache = pd.DataFrame()
    
    def search_drug(self, drug_name: str) -> List[Dict]:
        """
        Search for documents related to a drug.
        
        Args:
            drug_name: Name of the drug
            
        Returns:
            List of document metadata
        """
        if self.data_cache is None or self.data_cache.empty:
            return []
        
        # Search in the data cache
        # Note: This is a simplified search; in production, you'd want to
        # also search the Applications and Products tables
        results = self.data_cache[
            self.data_cache['ApplicationDocsTitle'].str.contains(
                drug_name, 
                case=False, 
                na=False
            )
        ]
        
        documents = []
        for _, row in results.iterrows():
            if pd.notna(row.get('ApplicationDocsURL')):
                documents.append({
                    'title': row['ApplicationDocsTitle'],
                    'url': row['ApplicationDocsURL'],
                    'appl_no': row['ApplNo'],
                    'submission_type': row['SubmissionType'],
                    'agency': 'FDA'
                })
        
        return documents
    
    def download_document(self, document_metadata: Dict) -> str:
        """
        Download a document from FDA.
        
        Args:
            document_metadata: Metadata containing the document URL
            
        Returns:
            Path to downloaded file
        """
        url = document_metadata['url']
        
        # Construct full URL if needed
        if not url.startswith('http'):
            url = f"https://www.accessdata.fda.gov{url}"
        
        # Download the file
        response = requests.get(url)
        response.raise_for_status()
        
        # Generate filename
        filename = f"FDA_{document_metadata['appl_no']}_{document_metadata['title'][:50]}.pdf"
        filename = "".join(c for c in filename if c.isalnum() or c in (' ', '_', '-', '.')).rstrip()
        
        file_path = self.download_dir / filename
        
        with open(file_path, 'wb') as f:
            f.write(response.content)
        
        print(f"Downloaded: {filename}")
        return str(file_path)

class FDAWebScraper(BaseScraper):
    """Alternative FDA scraper using Selenium for web interface."""
    
    SEARCH_URL = "https://www.accessdata.fda.gov/scripts/cder/daf/index.cfm"
    
    def __init__(self, download_dir: str):
        super().__init__(download_dir)
        self.driver = None
    
    def _init_driver(self):
        """Initialize Selenium WebDriver."""
        if self.driver is None:
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            
            # Set download directory
            prefs = {
                "download.default_directory": str(self.download_dir),
                "download.prompt_for_download": False,
            }
            options.add_experimental_option("prefs", prefs)
            
            self.driver = webdriver.Chrome(options=options)
    
    def search_drug(self, drug_name: str) -> List[Dict]:
        """Search for a drug using the web interface."""
        self._init_driver()
        
        try:
            self.driver.get(self.SEARCH_URL)
            
            # Wait for search box to load
            search_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, "DrugName"))
            )
            
            # Enter drug name and search
            search_box.clear()
            search_box.send_keys(drug_name)
            
            # Click search button
            search_button = self.driver.find_element(By.XPATH, "//input[@type='submit']")
            search_button.click()
            
            # Wait for results
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "resultsTable"))
            )
            
            # Parse results
            documents = []
            result_rows = self.driver.find_elements(By.XPATH, "//table[@class='resultsTable']//tr")[1:]
            
            for row in result_rows:
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) >= 3:
                    documents.append({
                        'title': cells[0].text,
                        'appl_no': cells[1].text,
                        'link_element': cells[0].find_element(By.TAG_NAME, "a"),
                        'agency': 'FDA'
                    })
            
            return documents
        
        except Exception as e:
            print(f"Error searching FDA: {e}")
            return []
    
    def download_document(self, document_metadata: Dict) -> str:
        """Download document via web interface."""
        # Implementation depends on specific document page structure
        # This is a placeholder
        pass
    
    def __del__(self):
        """Clean up WebDriver."""
        if self.driver:
            self.driver.quit()
```

## 4. EMA Scraper Implementation

Create `app/services/web_automation/ema_scraper.py`:

```python
import requests
import pandas as pd
from pathlib import Path
from typing import List, Dict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .base_scraper import BaseScraper

class EMAScraper(BaseScraper):
    """Scraper for EMA (European Medicines Agency)."""
    
    MEDICINES_DATA_URL = "https://www.ema.europa.eu/en/medicines/download-medicine-data"
    SEARCH_URL = "https://www.ema.europa.eu/en/medicines/field_ema_web_categories%253Aname_field/Human"
    
    def __init__(self, download_dir: str):
        super().__init__(download_dir)
        self.driver = None
    
    def _init_driver(self):
        """Initialize Selenium WebDriver."""
        if self.driver is None:
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            self.driver = webdriver.Chrome(options=options)
    
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
            self.driver.get(self.SEARCH_URL)
            
            # Wait for search box
            search_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "edit-search-api-fulltext"))
            )
            
            # Enter drug name
            search_box.clear()
            search_box.send_keys(drug_name)
            
            # Submit search
            search_box.submit()
            
            # Wait for results
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "search-results"))
            )
            
            # Parse results
            documents = []
            result_items = self.driver.find_elements(By.CLASS_NAME, "search-result")
            
            for item in result_items:
                try:
                    title_element = item.find_element(By.TAG_NAME, "h3")
                    link = title_element.find_element(By.TAG_NAME, "a")
                    
                    documents.append({
                        'title': link.text,
                        'url': link.get_attribute('href'),
                        'agency': 'EMA'
                    })
                except Exception as e:
                    print(f"Error parsing result item: {e}")
            
            return documents
        
        except Exception as e:
            print(f"Error searching EMA: {e}")
            return []
    
    def download_document(self, document_metadata: Dict) -> str:
        """
        Navigate to medicine page and download EPAR documents.
        
        Args:
            document_metadata: Metadata containing the medicine page URL
            
        Returns:
            Path to downloaded file
        """
        self._init_driver()
        
        try:
            # Navigate to medicine page
            self.driver.get(document_metadata['url'])
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "ecl-file"))
            )
            
            # Find EPAR PDF links
            pdf_links = self.driver.find_elements(
                By.XPATH, 
                "//a[contains(@href, '.pdf') and contains(text(), 'EPAR')]"
            )
            
            if pdf_links:
                pdf_url = pdf_links[0].get_attribute('href')
                
                # Download the PDF
                response = requests.get(pdf_url)
                response.raise_for_status()
                
                # Generate filename
                filename = f"EMA_{document_metadata['title'][:50]}.pdf"
                filename = "".join(c for c in filename if c.isalnum() or c in (' ', '_', '-', '.')).rstrip()
                
                file_path = self.download_dir / filename
                
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                
                print(f"Downloaded: {filename}")
                return str(file_path)
            else:
                raise Exception("No EPAR PDF found on page")
        
        except Exception as e:
            print(f"Error downloading from EMA: {e}")
            raise
    
    def __del__(self):
        """Clean up WebDriver."""
        if self.driver:
            self.driver.quit()
```

## 5. Health Canada Scraper Implementation

Create `app/services/web_automation/health_canada_scraper.py`:

```python
import requests
from pathlib import Path
from typing import List, Dict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .base_scraper import BaseScraper

class HealthCanadaScraper(BaseScraper):
    """Scraper for Health Canada Drug and Health Products Portal."""
    
    SEARCH_URL = "https://dhpp.hpfb-dgpsa.ca/review-documents"
    
    def __init__(self, download_dir: str):
        super().__init__(download_dir)
        self.driver = None
    
    def _init_driver(self):
        """Initialize Selenium WebDriver."""
        if self.driver is None:
            options = webdriver.ChromeOptions()
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            self.driver = webdriver.Chrome(options=options)
    
    def search_drug(self, drug_name: str) -> List[Dict]:
        """
        Search for regulatory decision summaries.
        
        Args:
            drug_name: Name of the drug
            
        Returns:
            List of document metadata
        """
        self._init_driver()
        
        try:
            self.driver.get(self.SEARCH_URL)
            
            # Wait for search interface to load
            search_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "search-input"))
            )
            
            # Enter drug name
            search_input.clear()
            search_input.send_keys(drug_name)
            
            # Click search button
            search_button = self.driver.find_element(By.ID, "search-button")
            search_button.click()
            
            # Wait for results
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "review-document"))
            )
            
            # Parse results
            documents = []
            result_items = self.driver.find_elements(By.CLASS_NAME, "review-document")
            
            for item in result_items:
                try:
                    title = item.find_element(By.CLASS_NAME, "document-title").text
                    link = item.find_element(By.TAG_NAME, "a").get_attribute('href')
                    
                    documents.append({
                        'title': title,
                        'url': link,
                        'agency': 'Health Canada'
                    })
                except Exception as e:
                    print(f"Error parsing result: {e}")
            
            return documents
        
        except Exception as e:
            print(f"Error searching Health Canada: {e}")
            return []
    
    def download_document(self, document_metadata: Dict) -> str:
        """
        Download RDS document from Health Canada.
        
        Args:
            document_metadata: Metadata containing document URL
            
        Returns:
            Path to downloaded file
        """
        self._init_driver()
        
        try:
            # Navigate to document page
            self.driver.get(document_metadata['url'])
            
            # Wait for PDF link
            pdf_link = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '.pdf')]"))
            )
            
            pdf_url = pdf_link.get_attribute('href')
            
            # Download PDF
            response = requests.get(pdf_url)
            response.raise_for_status()
            
            # Generate filename
            filename = f"HealthCanada_{document_metadata['title'][:50]}.pdf"
            filename = "".join(c for c in filename if c.isalnum() or c in (' ', '_', '-', '.')).rstrip()
            
            file_path = self.download_dir / filename
            
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            print(f"Downloaded: {filename}")
            return str(file_path)
        
        except Exception as e:
            print(f"Error downloading from Health Canada: {e}")
            raise
    
    def __del__(self):
        """Clean up WebDriver."""
        if self.driver:
            self.driver.quit()
```

## 6. Orchestrator Integration

Update `app/core/orchestrator.py` to coordinate the scrapers:

```python
from typing import List, Dict
from app.services.web_automation.fda_scraper import FDAScraper
from app.services.web_automation.ema_scraper import EMAScraper
from app.services.web_automation.health_canada_scraper import HealthCanadaScraper
from app.services.document_processing import DocumentProcessor
from app.services.vector_store import VectorStoreService
from app.core.config import get_settings

class AgenticOrchestrator:
    """Main orchestrator for the Regulatory Search Agent."""
    
    def __init__(self):
        self.settings = get_settings()
        self.doc_processor = DocumentProcessor()
        self.vector_store = VectorStoreService()
        
        # Initialize scrapers
        self.scrapers = {
            'FDA': FDAScraper(self.settings.download_dir),
            'EMA': EMAScraper(self.settings.download_dir),
            'Health Canada': HealthCanadaScraper(self.settings.download_dir),
            # Add other scrapers as implemented
        }
    
    def process_query(self, drug_name: str, agencies: List[str] = None) -> Dict:
        """
        Process a user query by searching agencies and indexing documents.
        
        Args:
            drug_name: Name of the drug to search for
            agencies: List of agencies to search (defaults to all)
            
        Returns:
            Summary of processing results
        """
        if agencies is None:
            agencies = list(self.scrapers.keys())
        
        results = {
            'drug_name': drug_name,
            'agencies_searched': [],
            'documents_downloaded': [],
            'documents_indexed': 0
        }
        
        for agency in agencies:
            if agency not in self.scrapers:
                print(f"Skipping unknown agency: {agency}")
                continue
            
            print(f"\nSearching {agency} for {drug_name}...")
            results['agencies_searched'].append(agency)
            
            try:
                # Search and download documents
                scraper = self.scrapers[agency]
                downloaded_files = scraper.search_and_download(drug_name)
                results['documents_downloaded'].extend(downloaded_files)
                
                # Index each downloaded document
                for file_path in downloaded_files:
                    try:
                        chunks, metadata = self.doc_processor.process_document(file_path)
                        self.vector_store.add_documents(chunks, metadata)
                        results['documents_indexed'] += 1
                        print(f"Indexed: {metadata['file_name']}")
                    except Exception as e:
                        print(f"Error indexing {file_path}: {e}")
            
            except Exception as e:
                print(f"Error processing {agency}: {e}")
        
        return results
```

## 7. Usage Example

```python
from app.core.orchestrator import AgenticOrchestrator

# Initialize orchestrator
orchestrator = AgenticOrchestrator()

# Process a query
results = orchestrator.process_query(
    drug_name="Keytruda",
    agencies=["FDA", "EMA", "Health Canada"]
)

print(f"\nProcessing complete:")
print(f"- Searched {len(results['agencies_searched'])} agencies")
print(f"- Downloaded {len(results['documents_downloaded'])} documents")
print(f"- Indexed {results['documents_indexed']} documents")
```

## 8. Best Practices for Web Scraping

1. **Respect robots.txt**: Always check the website's robots.txt file before scraping
2. **Rate Limiting**: Implement delays between requests to avoid overwhelming servers
3. **Error Handling**: Gracefully handle network errors, timeouts, and missing elements
4. **User-Agent**: Set a descriptive user-agent string
5. **Logging**: Log all scraping activities for debugging and monitoring
6. **Headless Mode**: Use headless browser mode for efficiency in production
7. **Caching**: Cache search results to avoid redundant requests

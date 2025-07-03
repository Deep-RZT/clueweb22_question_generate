import os
import time
import json
import requests
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from tqdm import tqdm
import pandas as pd
from config import CRAWLER_CONFIG, OUTPUT_DIRS
from utils.logger import setup_logger, log_progress

class BaseCrawler(ABC):
    """
    Base class for all academic paper crawlers
    """
    
    def __init__(self, source_name: str):
        self.source_name = source_name
        self.logger = setup_logger(f"{source_name}_crawler")
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': CRAWLER_CONFIG['user_agent']
        })
        self.papers_collected = []
        self.max_papers = CRAWLER_CONFIG['max_papers_per_source']
        
        # Create output directories
        for dir_path in OUTPUT_DIRS.values():
            os.makedirs(dir_path, exist_ok=True)
    
    @abstractmethod
    def search_papers(self, keywords: List[str]) -> List[Dict]:
        """
        Search for papers using given keywords
        Returns list of paper metadata dictionaries
        """
        pass
    
    @abstractmethod
    def download_paper(self, paper_info: Dict) -> Optional[str]:
        """
        Download paper content (PDF or text)
        Returns path to downloaded file or None if failed
        """
        pass
    
    def is_energy_related(self, title: str, abstract: str = "") -> bool:
        """
        Check if paper is energy-related based on title and abstract
        """
        from config import ALL_KEYWORDS
        
        # Handle None values
        title = title or ""
        abstract = abstract or ""
        text = (title + " " + abstract).lower()
        
        # Check if any energy keyword is present
        for keyword in ALL_KEYWORDS:
            if keyword.lower() in text:
                return True
        return False
    
    def save_metadata(self, papers: List[Dict]):
        """
        Save paper metadata to JSON and CSV files
        """
        if not papers:
            return
            
        # Save as JSON
        json_path = os.path.join(
            OUTPUT_DIRS['metadata'], 
            f"{self.source_name}_metadata.json"
        )
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(papers, f, indent=2, ensure_ascii=False)
        
        # Save as CSV
        csv_path = os.path.join(
            OUTPUT_DIRS['metadata'], 
            f"{self.source_name}_metadata.csv"
        )
        df = pd.DataFrame(papers)
        df.to_csv(csv_path, index=False, encoding='utf-8')
        
        self.logger.info(f"Saved metadata for {len(papers)} papers to {json_path} and {csv_path}")
    
    def rate_limit(self):
        """
        Apply rate limiting between requests
        """
        time.sleep(CRAWLER_CONFIG['delay_between_requests'])
    
    def make_request(self, url: str, params: Dict = None, retries: int = None) -> Optional[requests.Response]:
        """
        Make HTTP request with retry logic
        """
        if retries is None:
            retries = CRAWLER_CONFIG['max_retries']
        
        for attempt in range(retries + 1):
            try:
                response = self.session.get(
                    url, 
                    params=params, 
                    timeout=CRAWLER_CONFIG['timeout']
                )
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                if attempt == retries:
                    self.logger.error(f"Failed to fetch {url} after {retries + 1} attempts: {e}")
                    return None
                else:
                    self.logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}. Retrying...")
                    time.sleep(2 ** attempt)  # Exponential backoff
        
        return None
    
    def run_crawler(self, keywords: List[str]) -> List[Dict]:
        """
        Main method to run the crawler
        """
        self.logger.info(f"Starting {self.source_name} crawler with {len(keywords)} keywords")
        
        all_papers = []
        
        for i, keyword in enumerate(keywords):
            if len(all_papers) >= self.max_papers:
                break
                
            self.logger.info(f"Searching for keyword: '{keyword}' ({i+1}/{len(keywords)})")
            
            try:
                papers = self.search_papers([keyword])
                
                # Filter energy-related papers
                energy_papers = []
                for paper in papers:
                    if self.is_energy_related(paper.get('title', ''), paper.get('abstract', '')):
                        energy_papers.append(paper)
                
                all_papers.extend(energy_papers)
                self.logger.info(f"Found {len(energy_papers)} energy-related papers for keyword '{keyword}'")
                
                log_progress(self.logger, len(all_papers), self.max_papers, self.source_name)
                
            except Exception as e:
                self.logger.error(f"Error searching for keyword '{keyword}': {e}")
            
            self.rate_limit()
        
        # Remove duplicates based on title
        unique_papers = []
        seen_titles = set()
        for paper in all_papers:
            title = paper.get('title', '').strip().lower()
            if title and title not in seen_titles:
                seen_titles.add(title)
                unique_papers.append(paper)
        
        self.logger.info(f"Collected {len(unique_papers)} unique energy papers from {self.source_name}")
        
        # Save metadata
        self.save_metadata(unique_papers)
        
        return unique_papers[:self.max_papers] 
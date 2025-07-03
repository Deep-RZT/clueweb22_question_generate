import os
import json
from typing import List, Dict, Optional
from urllib.parse import quote
from .base_crawler import BaseCrawler
from config import OUTPUT_DIRS

class CrossRefCrawler(BaseCrawler):
    """
    Crawler for CrossRef academic database
    """
    
    def __init__(self):
        super().__init__("crossref")
        self.base_url = "https://api.crossref.org"
        # Add polite pool identifier (optional email for courtesy)
        self.session.headers.update({
            'User-Agent': 'energy-fasttext-crawler (mailto:researcher@university.edu)'
        })
    
    def search_papers(self, keywords: List[str]) -> List[Dict]:
        """
        Search CrossRef for papers matching keywords
        """
        papers = []
        
        for keyword in keywords:
            try:
                # Construct search query
                query_params = {
                    'query': keyword,
                    'rows': 50,  # Results per page
                    'offset': 0,
                    'sort': 'relevance',
                    'filter': 'type:journal-article,has-abstract:true'  # Only journal articles with abstracts
                }
                
                url = f"{self.base_url}/works"
                
                self.logger.info(f"CrossRef query: {keyword}")
                
                response = self.make_request(url, params=query_params)
                if not response:
                    continue
                
                data = response.json()
                
                for work in data.get('message', {}).get('items', []):
                    # Extract paper information
                    paper_info = {
                        'source': 'crossref',
                        'id': work.get('DOI'),
                        'title': self._extract_title(work),
                        'abstract': work.get('abstract'),
                        'authors': self._extract_authors(work),
                        'published': self._extract_date(work),
                        'doi': work.get('DOI'),
                        'journal': self._extract_journal(work),
                        'publisher': work.get('publisher'),
                        'type': work.get('type'),
                        'url': work.get('URL'),
                        'citation_count': work.get('is-referenced-by-count', 0),
                        'keyword_matched': keyword
                    }
                    
                    # Only include papers with titles and abstracts
                    if paper_info['title'] and paper_info['abstract']:
                        papers.append(paper_info)
                
                self.logger.info(f"Found {len(papers)} papers for keyword '{keyword}' on CrossRef")
                
            except Exception as e:
                self.logger.error(f"Error searching CrossRef for keyword '{keyword}': {e}")
        
        return papers
    
    def _extract_title(self, work: Dict) -> Optional[str]:
        """
        Extract title from CrossRef work data
        """
        titles = work.get('title', [])
        return titles[0] if titles else None
    
    def _extract_authors(self, work: Dict) -> List[str]:
        """
        Extract authors from CrossRef work data
        """
        authors = []
        for author in work.get('author', []):
            given = author.get('given', '')
            family = author.get('family', '')
            if given and family:
                authors.append(f"{given} {family}")
            elif family:
                authors.append(family)
        return authors
    
    def _extract_date(self, work: Dict) -> Optional[str]:
        """
        Extract publication date from CrossRef work data
        """
        date_parts = work.get('published-print', {}).get('date-parts')
        if not date_parts:
            date_parts = work.get('published-online', {}).get('date-parts')
        
        if date_parts and date_parts[0]:
            parts = date_parts[0]
            if len(parts) >= 3:
                return f"{parts[0]}-{parts[1]:02d}-{parts[2]:02d}"
            elif len(parts) >= 2:
                return f"{parts[0]}-{parts[1]:02d}"
            elif len(parts) >= 1:
                return str(parts[0])
        
        return None
    
    def _extract_journal(self, work: Dict) -> Optional[str]:
        """
        Extract journal name from CrossRef work data
        """
        container_titles = work.get('container-title', [])
        return container_titles[0] if container_titles else None
    
    def download_paper(self, paper_info: Dict) -> Optional[str]:
        """
        CrossRef doesn't provide direct PDF downloads, but we can save metadata
        """
        try:
            # Create filename based on DOI
            doi = paper_info.get('doi', '').replace('/', '_').replace(':', '_')
            safe_title = "".join(c for c in paper_info['title'][:50] if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filename = f"crossref_{doi}_{safe_title}.json"
            filepath = os.path.join(OUTPUT_DIRS['raw_papers'], filename)
            
            # Skip if already saved
            if os.path.exists(filepath):
                self.logger.info(f"Paper metadata already saved: {filename}")
                return filepath
            
            # Save metadata as JSON
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(paper_info, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Saved metadata: {filename}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Failed to save paper metadata {paper_info.get('doi', 'unknown')}: {e}")
            return None
    
    def search_by_subject(self, subjects: List[str], max_results: int = 200) -> List[Dict]:
        """
        Search papers by subject areas
        """
        papers = []
        
        for subject in subjects:
            try:
                query_params = {
                    'query.container-title': subject,
                    'rows': min(max_results // len(subjects), 50),
                    'offset': 0,
                    'sort': 'is-referenced-by-count',
                    'filter': 'type:journal-article,has-abstract:true'
                }
                
                url = f"{self.base_url}/works"
                
                self.logger.info(f"Searching by subject: {subject}")
                
                response = self.make_request(url, params=query_params)
                if not response:
                    continue
                
                data = response.json()
                
                for work in data.get('message', {}).get('items', []):
                    paper_info = {
                        'source': 'crossref_subject',
                        'id': work.get('DOI'),
                        'title': self._extract_title(work),
                        'abstract': work.get('abstract'),
                        'authors': self._extract_authors(work),
                        'published': self._extract_date(work),
                        'doi': work.get('DOI'),
                        'journal': self._extract_journal(work),
                        'publisher': work.get('publisher'),
                        'type': work.get('type'),
                        'url': work.get('URL'),
                        'citation_count': work.get('is-referenced-by-count', 0),
                        'keyword_matched': f'subject:{subject}'
                    }
                    
                    if paper_info['title'] and paper_info['abstract']:
                        papers.append(paper_info)
                
                self.logger.info(f"Found {len(papers)} papers for subject '{subject}'")
                
            except Exception as e:
                self.logger.error(f"Error searching by subject '{subject}': {e}")
        
        return papers 
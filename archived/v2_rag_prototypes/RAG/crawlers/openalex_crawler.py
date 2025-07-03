import os
import json
from typing import List, Dict, Optional
from urllib.parse import quote
from .base_crawler import BaseCrawler
from config import OUTPUT_DIRS, OPENALEX_CONCEPTS

class OpenAlexCrawler(BaseCrawler):
    """
    Crawler for OpenAlex academic database
    """
    
    def __init__(self):
        super().__init__("openalex")
        self.base_url = "https://api.openalex.org"
        # Add polite pool identifier (optional email for courtesy)
        self.session.headers.update({
            'User-Agent': 'energy-fasttext-crawler (mailto:researcher@university.edu)'
        })
    
    def search_papers(self, keywords: List[str]) -> List[Dict]:
        """
        Search OpenAlex for papers matching keywords
        """
        papers = []
        
        for keyword in keywords:
            try:
                # Construct search query
                query_params = {
                    'search': keyword,
                    'filter': 'type:article,has_doi:true,is_oa:true',  # Open access articles with DOI
                    'per-page': 50,  # Results per page
                    'page': 1,
                    'sort': 'relevance_score:desc'
                }
                
                # Add concept filters if available
                if OPENALEX_CONCEPTS:
                    concept_filter = '|'.join(OPENALEX_CONCEPTS)
                    query_params['filter'] += f',concepts.id:{concept_filter}'
                
                url = f"{self.base_url}/works"
                
                self.logger.info(f"OpenAlex query: {keyword}")
                
                response = self.make_request(url, params=query_params)
                if not response:
                    continue
                
                data = response.json()
                
                for work in data.get('results', []):
                    # Extract paper information
                    paper_info = {
                        'source': 'openalex',
                        'id': work.get('id'),
                        'title': work.get('title'),
                        'abstract': work.get('abstract'),
                        'authors': [
                            author.get('author', {}).get('display_name', 'Unknown')
                            for author in work.get('authorships', [])
                        ],
                        'published': work.get('publication_date'),
                        'doi': work.get('doi'),
                        'journal': work.get('primary_location', {}).get('source', {}).get('display_name'),
                        'open_access': work.get('open_access', {}).get('is_oa', False),
                        'pdf_url': self._extract_pdf_url(work),
                        'concepts': [
                            concept.get('display_name') 
                            for concept in work.get('concepts', [])
                        ],
                        'citation_count': work.get('cited_by_count', 0),
                        'keyword_matched': keyword
                    }
                    
                    # Only include papers with abstracts or substantial titles
                    if paper_info['abstract'] or (paper_info['title'] and len(paper_info['title']) > 20):
                        papers.append(paper_info)
                
                self.logger.info(f"Found {len(papers)} papers for keyword '{keyword}' on OpenAlex")
                
            except Exception as e:
                self.logger.error(f"Error searching OpenAlex for keyword '{keyword}': {e}")
        
        return papers
    
    def _extract_pdf_url(self, work: Dict) -> Optional[str]:
        """
        Extract PDF URL from OpenAlex work data
        """
        # Check primary location
        primary_location = work.get('primary_location', {})
        if primary_location.get('pdf_url'):
            return primary_location['pdf_url']
        
        # Check other locations
        for location in work.get('locations', []):
            if location.get('pdf_url'):
                return location['pdf_url']
        
        # Check open access sources
        open_access = work.get('open_access', {})
        if open_access.get('oa_url'):
            return open_access['oa_url']
        
        return None
    
    def download_paper(self, paper_info: Dict) -> Optional[str]:
        """
        Download paper content (usually PDF or HTML)
        """
        try:
            pdf_url = paper_info.get('pdf_url')
            if not pdf_url:
                self.logger.warning(f"No PDF URL for paper: {paper_info.get('title', 'Unknown')}")
                return None
            
            # Create filename
            safe_title = "".join(c for c in paper_info['title'][:50] if c.isalnum() or c in (' ', '-', '_')).rstrip()
            paper_id = paper_info['id'].split('/')[-1] if paper_info['id'] else 'unknown'
            filename = f"openalex_{paper_id}_{safe_title}.pdf"
            filepath = os.path.join(OUTPUT_DIRS['raw_papers'], filename)
            
            # Skip if already downloaded
            if os.path.exists(filepath):
                self.logger.info(f"Paper already downloaded: {filename}")
                return filepath
            
            # Download the file
            response = self.make_request(pdf_url)
            if not response:
                return None
            
            # Save the file
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            self.logger.info(f"Downloaded: {filename}")
            return filepath
            
        except Exception as e:
            self.logger.error(f"Failed to download paper {paper_info.get('id', 'unknown')}: {e}")
            return None
    
    def search_by_concepts(self, concept_ids: List[str], max_results: int = 200) -> List[Dict]:
        """
        Search papers by OpenAlex concept IDs
        """
        papers = []
        
        try:
            concept_filter = '|'.join(concept_ids)
            query_params = {
                'filter': f'concepts.id:{concept_filter},type:article,has_doi:true',
                'per-page': min(max_results, 200),  # API limit
                'page': 1,
                'sort': 'cited_by_count:desc'  # Sort by citation count
            }
            
            url = f"{self.base_url}/works"
            
            self.logger.info(f"Searching by concepts: {concept_ids}")
            
            response = self.make_request(url, params=query_params)
            if not response:
                return papers
            
            data = response.json()
            
            for work in data.get('results', []):
                paper_info = {
                    'source': 'openalex_concepts',
                    'id': work.get('id'),
                    'title': work.get('title'),
                    'abstract': work.get('abstract'),
                    'authors': [
                        author.get('author', {}).get('display_name', 'Unknown')
                        for author in work.get('authorships', [])
                    ],
                    'published': work.get('publication_date'),
                    'doi': work.get('doi'),
                    'journal': work.get('primary_location', {}).get('source', {}).get('display_name'),
                    'open_access': work.get('open_access', {}).get('is_oa', False),
                    'pdf_url': self._extract_pdf_url(work),
                    'concepts': [
                        concept.get('display_name') 
                        for concept in work.get('concepts', [])
                    ],
                    'citation_count': work.get('cited_by_count', 0),
                    'keyword_matched': 'concept_search'
                }
                
                if paper_info['abstract'] or (paper_info['title'] and len(paper_info['title']) > 20):
                    papers.append(paper_info)
            
            self.logger.info(f"Found {len(papers)} papers by concept search")
            
        except Exception as e:
            self.logger.error(f"Error searching by concepts: {e}")
        
        return papers 
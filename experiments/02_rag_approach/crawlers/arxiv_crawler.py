import os
import arxiv
from typing import List, Dict, Optional
from .base_crawler import BaseCrawler
from config import OUTPUT_DIRS, ARXIV_CATEGORIES

class ArxivCrawler(BaseCrawler):
    """
    Crawler for arXiv papers
    """
    
    def __init__(self):
        super().__init__("arxiv")
        self.client = arxiv.Client()
    
    def search_papers(self, keywords: List[str]) -> List[Dict]:
        """
        Search arXiv for papers matching keywords
        """
        papers = []
        
        for keyword in keywords:
            try:
                # Construct search query
                query_parts = []
                
                # Search in title, abstract, and categories
                query_parts.append(f'ti:"{keyword}" OR abs:"{keyword}"')
                
                # Add category filters
                if ARXIV_CATEGORIES:
                    cat_query = " OR ".join([f'cat:{cat}' for cat in ARXIV_CATEGORIES])
                    query_parts.append(f'({cat_query})')
                
                query = " AND ".join(query_parts)
                
                self.logger.info(f"ArXiv query: {query}")
                
                # Search with pagination
                search = arxiv.Search(
                    query=query,
                    max_results=50,  # Limit per keyword
                    sort_by=arxiv.SortCriterion.Relevance
                )
                
                for result in self.client.results(search):
                    paper_info = {
                        'source': 'arxiv',
                        'id': result.entry_id,
                        'title': result.title,
                        'abstract': result.summary,
                        'authors': [author.name for author in result.authors],
                        'published': result.published.isoformat() if result.published else None,
                        'updated': result.updated.isoformat() if result.updated else None,
                        'categories': result.categories,
                        'pdf_url': result.pdf_url,
                        'doi': result.doi,
                        'journal_ref': result.journal_ref,
                        'keyword_matched': keyword
                    }
                    papers.append(paper_info)
                
                self.logger.info(f"Found {len(papers)} papers for keyword '{keyword}' on arXiv")
                
            except Exception as e:
                self.logger.error(f"Error searching arXiv for keyword '{keyword}': {e}")
        
        return papers
    
    def download_paper(self, paper_info: Dict) -> Optional[str]:
        """
        Download PDF from arXiv with better error handling
        """
        try:
            # Extract arXiv ID from entry_id
            arxiv_id = paper_info['id'].split('/')[-1]
            
            # Create filename
            safe_title = "".join(c for c in paper_info['title'][:50] if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filename = f"arxiv_{arxiv_id}_{safe_title}.pdf"
            filepath = os.path.join(OUTPUT_DIRS['raw_papers'], filename)
            
            # Skip if already downloaded
            if os.path.exists(filepath):
                self.logger.info(f"Paper already downloaded: {filename}")
                return filepath
            
            # Try multiple download methods
            success = False
            
            # Method 1: Direct URL download with requests
            try:
                import requests
                pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'application/pdf,*/*',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1'
                }
                
                response = requests.get(pdf_url, headers=headers, timeout=30, stream=True)
                
                if response.status_code == 200:
                    with open(filepath, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    if os.path.getsize(filepath) > 1000:  # At least 1KB
                        self.logger.info(f"Downloaded via requests: {filename}")
                        return filepath
                    else:
                        os.remove(filepath)
                        
            except Exception as e:
                self.logger.warning(f"Requests download failed: {e}")
            
            # Method 2: arxiv library (fallback)
            try:
                paper = next(arxiv.Client().results(arxiv.Search(id_list=[arxiv_id])))
                paper.download_pdf(dirpath=OUTPUT_DIRS['raw_papers'], filename=filename)
                
                if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
                    self.logger.info(f"Downloaded via arxiv library: {filename}")
                    return filepath
                    
            except Exception as e:
                self.logger.warning(f"Arxiv library download failed: {e}")
            
            # Method 3: wget command (if available)
            try:
                import subprocess
                pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
                
                result = subprocess.run([
                    'wget', '-q', '--timeout=30', '--tries=3',
                    '--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                    '-O', filepath, pdf_url
                ], capture_output=True, timeout=60)
                
                if result.returncode == 0 and os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
                    self.logger.info(f"Downloaded via wget: {filename}")
                    return filepath
                elif os.path.exists(filepath):
                    os.remove(filepath)
                    
            except Exception as e:
                self.logger.warning(f"Wget download failed: {e}")
            
            self.logger.error(f"All download methods failed for {arxiv_id}")
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to download paper {paper_info.get('id', 'unknown')}: {e}")
            return None
    
    def download_papers_batch(self, papers: List[Dict], max_downloads: int = 100) -> List[str]:
        """
        Download multiple papers in batch
        """
        downloaded_files = []
        
        for i, paper in enumerate(papers[:max_downloads]):
            self.logger.info(f"Downloading paper {i+1}/{min(len(papers), max_downloads)}: {paper['title'][:50]}...")
            
            filepath = self.download_paper(paper)
            if filepath:
                downloaded_files.append(filepath)
            
            # Rate limiting
            self.rate_limit()
        
        self.logger.info(f"Downloaded {len(downloaded_files)} papers from arXiv")
        return downloaded_files 
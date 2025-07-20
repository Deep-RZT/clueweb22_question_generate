"""
Web Search Extension System for Tree Extension Deep Query Framework
Implements web search-based extension to escape original document limitations.
"""

import logging
import json
import re
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

from config import get_config

# Setup logging
logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """Web search result structure"""
    query: str
    title: str
    content: str
    url: str
    relevance_score: float
    credibility_score: float
    extraction_timestamp: str

@dataclass
class ExtensionContext:
    """Extension context from web search"""
    original_keyword: str
    search_query: str
    search_results: List[SearchResult]
    synthesized_context: str
    confidence: float
    sources: List[str]

class WebSearchExtensionSystem:
    """Manages web search-based extension content generation"""
    
    def __init__(self, search_client=None, api_client=None):
        self.config = get_config()
        self.search_client = search_client  # Web search API client
        self.api_client = api_client  # LLM API client
        self.search_cache = {}
        self.max_search_calls = 1  # Limit per workflow requirement
        
    def set_search_client(self, search_client):
        """Set the web search API client"""
        self.search_client = search_client
        
    def set_api_client(self, api_client):
        """Set the LLM API client"""
        self.api_client = api_client
    
    def generate_extension_with_web_search(self, parent_keyword: str, parent_question: str, 
                                         parent_answer: str, extension_type: str = "series") -> Optional[ExtensionContext]:
        """
        Generate extension context using web search to escape original document limitations
        
        Workflow requirement: 确保每次问题的扩展都是基于新的搜索而不一定是原始文档
        (跳脱父问题原文，以web search获取新的扩展内容上下文)
        """
        logger.info(f"Generating extension with web search for keyword: {parent_keyword}")
        
        if not self.search_client or not self.api_client:
            logger.error("Missing required clients (search/API)")
            return None
        
        try:
            # 1. Generate strategic search query
            search_query = self._generate_strategic_search_query(
                parent_keyword, parent_question, parent_answer, extension_type
            )
            
            if not search_query:
                logger.warning("Failed to generate search query")
                return None
            
            # 2. Perform web search (限制1次调用)
            search_results = self._perform_web_search(search_query)
            
            if not search_results:
                logger.warning(f"No search results for query: {search_query}")
                return None
            
            # 3. Synthesize extension context from search results
            extension_context = self._synthesize_extension_context(
                parent_keyword, search_query, search_results, extension_type
            )
            
            if extension_context:
                logger.info(f"Generated extension context with {len(search_results)} sources")
                return extension_context
            else:
                logger.warning("Failed to synthesize extension context")
                return None
                
        except Exception as e:
            logger.error(f"Error generating extension with web search: {e}")
            return None
    
    def _generate_strategic_search_query(self, keyword: str, parent_question: str, 
                                       parent_answer: str, extension_type: str) -> Optional[str]:
        """
        Generate strategic search query to find relevant extension content
        
        The query should be designed to find information that extends beyond the original document
        """
        try:
            query_prompt = f"""You are generating a strategic web search query to find extension content for a keyword-based question tree.

PARENT CONTEXT:
- Question: {parent_question}
- Answer: {parent_answer}
- Target Keyword: {keyword}
- Extension Type: {extension_type}

SEARCH STRATEGY for {extension_type.upper()} EXTENSION:
"""

            if extension_type == "series":
                query_prompt += f"""
SERIES EXTENSION: Find information that drills deeper into the keyword's technical aspects, applications, or detailed characteristics.

SEARCH FOCUS:
- Technical specifications or details about "{keyword}"
- Advanced applications or implementations of "{keyword}"
- Historical development or evolution of "{keyword}"
- Scientific/academic research related to "{keyword}"
- Comparative analysis involving "{keyword}"

EXAMPLE QUERY PATTERNS:
- "{keyword} technical specifications research"
- "{keyword} advanced applications academic study"
- "{keyword} development history scientific paper"
- "{keyword} comparative analysis research findings"
"""
            else:  # parallel
                query_prompt += f"""
PARALLEL EXTENSION: Find information that explores alternative aspects, related concepts, or comparative elements to the keyword.

SEARCH FOCUS:
- Related technologies or concepts similar to "{keyword}"
- Alternative approaches or competitors to "{keyword}"
- Broader category or field that includes "{keyword}"
- Cross-disciplinary applications of "{keyword}"
- Industry perspectives on "{keyword}"

EXAMPLE QUERY PATTERNS:
- "{keyword} alternatives comparison review"
- "{keyword} related technologies market analysis"
- "{keyword} industry applications case studies"
- "{keyword} competitive landscape research"
"""

            query_prompt += f"""
SEARCH QUERY REQUIREMENTS:
1. Must be specific enough to find relevant, detailed content
2. Should include academic/research keywords for credible sources
3. Must escape the original document's scope (find NEW information)
4. Should be 3-8 words for optimal search results
5. Must avoid generic terms that return too broad results

CRITICAL: Generate exactly ONE search query that will find the most relevant extension content:"""

            response = self.api_client.generate_response(
                prompt=query_prompt,
                temperature=0.3,
                max_tokens=100
            )
            
            # Extract search query from response
            query = self._extract_search_query(response)
            
            if query:
                logger.info(f"Generated search query: {query}")
                return query
            else:
                logger.warning("Failed to extract valid search query")
                return None
                
        except Exception as e:
            logger.error(f"Error generating search query: {e}")
            return None
    
    def _perform_web_search(self, search_query: str) -> List[SearchResult]:
        """
        Perform web search using the search client
        限制到1次搜索调用 per workflow requirement
        """
        try:
            # Check cache first
            if search_query in self.search_cache:
                logger.info(f"Using cached search results for: {search_query}")
                return self.search_cache[search_query]
            
            # Perform actual search
            logger.info(f"Performing web search: {search_query}")
            
            # Use the existing search client (assumed to be web_search_preview or similar)
            search_response = self.search_client(search_query)
            
            # Parse search response into SearchResult objects
            search_results = self._parse_search_response(search_response, search_query)
            
            # Cache results
            self.search_cache[search_query] = search_results
            
            logger.info(f"Search completed: {len(search_results)} results found")
            return search_results
            
        except Exception as e:
            logger.error(f"Web search failed for query '{search_query}': {e}")
            return []
    
    def _parse_search_response(self, search_response: Any, search_query: str) -> List[SearchResult]:
        """Parse search response into SearchResult objects"""
        results = []
        
        try:
            # Handle different search response formats
            if hasattr(search_response, 'results'):
                # Standard search response format
                search_data = search_response.results
            elif isinstance(search_response, dict):
                search_data = search_response.get('results', [])
            elif isinstance(search_response, list):
                search_data = search_response
            else:
                # Try to convert to string and parse
                search_data = str(search_response)
                return self._parse_text_search_response(search_data, search_query)
            
            # Process search results
            for i, result in enumerate(search_data[:5]):  # Limit to top 5 results
                try:
                    if isinstance(result, dict):
                        title = result.get('title', f'Result {i+1}')
                        content = result.get('content', result.get('snippet', ''))
                        url = result.get('url', f'search-result-{i+1}')
                    else:
                        # Handle other formats
                        title = f'Search Result {i+1}'
                        content = str(result)
                        url = f'search-result-{i+1}'
                    
                    # Calculate relevance and credibility scores
                    relevance_score = self._calculate_relevance_score(content, search_query)
                    credibility_score = self._calculate_credibility_score(url, title, content)
                    
                    search_result = SearchResult(
                        query=search_query,
                        title=title,
                        content=content,
                        url=url,
                        relevance_score=relevance_score,
                        credibility_score=credibility_score,
                        extraction_timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
                    )
                    
                    results.append(search_result)
                    
                except Exception as e:
                    logger.warning(f"Error parsing search result {i}: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error parsing search response: {e}")
        
        return results
    
    def _parse_text_search_response(self, search_text: str, search_query: str) -> List[SearchResult]:
        """Parse text-based search response"""
        results = []
        
        # Split into chunks that look like separate results
        chunks = re.split(r'\n\s*\n|\n-|\d+\.', search_text)
        
        for i, chunk in enumerate(chunks[:5]):
            if len(chunk.strip()) > 50:  # Only process substantial chunks
                # Extract title (usually first line or sentence)
                lines = chunk.strip().split('\n')
                title = lines[0][:100] if lines else f'Search Result {i+1}'
                
                content = chunk.strip()
                
                # Calculate scores
                relevance_score = self._calculate_relevance_score(content, search_query)
                credibility_score = 0.7  # Default for text responses
                
                search_result = SearchResult(
                    query=search_query,
                    title=title,
                    content=content,
                    url=f'text-search-result-{i+1}',
                    relevance_score=relevance_score,
                    credibility_score=credibility_score,
                    extraction_timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
                )
                
                results.append(search_result)
        
        return results
    
    def _synthesize_extension_context(self, keyword: str, search_query: str, 
                                    search_results: List[SearchResult], extension_type: str) -> Optional[ExtensionContext]:
        """
        Synthesize extension context from search results for question generation
        """
        try:
            # Filter and rank search results by relevance and credibility
            ranked_results = sorted(
                search_results, 
                key=lambda r: (r.relevance_score + r.credibility_score) / 2, 
                reverse=True
            )[:3]  # Top 3 results
            
            if not ranked_results:
                return None
            
            # Create synthesis prompt
            synthesis_prompt = f"""You are synthesizing web search results to create extension context for a keyword-based question tree.

TARGET KEYWORD: {keyword}
SEARCH QUERY: {search_query}
EXTENSION TYPE: {extension_type}

SEARCH RESULTS TO SYNTHESIZE:
"""

            for i, result in enumerate(ranked_results):
                synthesis_prompt += f"""
Result {i+1} (Relevance: {result.relevance_score:.2f}, Credibility: {result.credibility_score:.2f}):
Title: {result.title}
Content: {result.content[:500]}...
URL: {result.url}
"""

            synthesis_prompt += f"""
SYNTHESIS REQUIREMENTS:
1. Extract key information relevant to "{keyword}" that goes BEYOND basic definitions
2. Focus on {extension_type} extension aspects (deeper details for series, parallel perspectives for parallel)
3. Identify specific facts, numbers, names, or technical details that could serve as question answers
4. Ensure information is verifiable and comes from credible sources
5. Create coherent context that enables focused question generation

SYNTHESIS TASKS:
1. Identify 2-3 specific facts or details about "{keyword}" from the search results
2. Note any technical specifications, research findings, or expert insights
3. Extract any names, dates, numbers, or specific terms related to "{keyword}"
4. Summarize the most relevant extension information in 2-3 paragraphs

Respond in JSON format:
{{
    "synthesized_context": "coherent 2-3 paragraph summary of extension information",
    "key_facts": ["specific fact 1", "specific fact 2", "specific fact 3"],
    "technical_details": ["detail 1", "detail 2"],
    "potential_answers": ["answer 1", "answer 2", "answer 3"],
    "confidence": 0.0-1.0,
    "sources_used": ["source 1", "source 2"]
}}"""

            response = self.api_client.generate_response(
                prompt=synthesis_prompt,
                temperature=0.3,
                max_tokens=800
            )
            
            # Parse synthesis response
            synthesis_data = self._parse_synthesis_response(response)
            
            if synthesis_data:
                extension_context = ExtensionContext(
                    original_keyword=keyword,
                    search_query=search_query,
                    search_results=ranked_results,
                    synthesized_context=synthesis_data['synthesized_context'],
                    confidence=synthesis_data['confidence'],
                    sources=[r.url for r in ranked_results]
                )
                
                return extension_context
            
        except Exception as e:
            logger.error(f"Error synthesizing extension context: {e}")
        
        return None
    
    def _extract_search_query(self, response: str) -> Optional[str]:
        """Extract search query from LLM response"""
        # Look for quoted strings or clear query patterns
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines or headers
            if not line or line.startswith('Query:') or line.startswith('Search:'):
                continue
            
            # Look for quoted queries
            quoted_match = re.search(r'"([^"]+)"', line)
            if quoted_match and len(quoted_match.group(1)) > 3:
                return quoted_match.group(1)
            
            # Look for clear query patterns (avoiding full sentences)
            if len(line.split()) <= 8 and len(line) > 10 and not line.endswith('.'):
                return line
        
        # Fallback: extract from entire response
        quoted_match = re.search(r'"([^"]+)"', response)
        if quoted_match:
            return quoted_match.group(1)
        
        return None
    
    def _calculate_relevance_score(self, content: str, search_query: str) -> float:
        """Calculate relevance score based on content and query match"""
        if not content or not search_query:
            return 0.0
        
        content_lower = content.lower()
        query_lower = search_query.lower()
        query_words = query_lower.split()
        
        # Count query word matches
        matches = sum(1 for word in query_words if word in content_lower)
        
        # Calculate relevance score
        relevance = matches / len(query_words) if query_words else 0.0
        
        # Bonus for exact query phrase
        if query_lower in content_lower:
            relevance += 0.2
        
        # Bonus for technical content indicators
        technical_indicators = ['research', 'study', 'analysis', 'technical', 'specification', 'academic']
        if any(indicator in content_lower for indicator in technical_indicators):
            relevance += 0.1
        
        return min(1.0, relevance)
    
    def _calculate_credibility_score(self, url: str, title: str, content: str) -> float:
        """Calculate credibility score based on source characteristics"""
        score = 0.5  # Base score
        
        # URL-based credibility
        credible_domains = [
            '.edu', '.gov', '.org', 'wikipedia', 'arxiv', 'pubmed', 
            'ieee', 'acm', 'nature', 'science', 'springer', 'elsevier'
        ]
        
        if any(domain in url.lower() for domain in credible_domains):
            score += 0.3
        
        # Content-based credibility indicators
        credible_content = [
            'research', 'study', 'journal', 'paper', 'publication',
            'university', 'institute', 'laboratory', 'peer-reviewed'
        ]
        
        content_lower = (title + ' ' + content).lower()
        credibility_matches = sum(1 for indicator in credible_content if indicator in content_lower)
        
        score += min(0.2, credibility_matches * 0.05)
        
        return min(1.0, score)
    
    def _parse_synthesis_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse synthesis response from LLM"""
        try:
            # Extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_text = response[json_start:json_end]
                data = json.loads(json_text)
                
                return {
                    'synthesized_context': data.get('synthesized_context', ''),
                    'key_facts': data.get('key_facts', []),
                    'technical_details': data.get('technical_details', []),
                    'potential_answers': data.get('potential_answers', []),
                    'confidence': data.get('confidence', 0.0),
                    'sources_used': data.get('sources_used', [])
                }
            
        except Exception as e:
            logger.warning(f"Failed to parse synthesis response: {e}")
        
        return None
    
    def get_extension_statistics(self) -> Dict[str, Any]:
        """Get statistics about web search extension usage"""
        return {
            'total_searches_performed': len(self.search_cache),
            'cached_queries': list(self.search_cache.keys()),
            'max_search_calls_per_extension': self.max_search_calls
        } 
"""
Web Search Module for Tree Extension Deep Query Framework
Provides web search functionality using OpenAI's web_search_preview tool.
"""

import logging
import json
import time
from typing import Dict, List, Optional, Any
import openai

logger = logging.getLogger(__name__)

def web_search(query: str, max_results: int = 5, api_key: str = None) -> Dict[str, Any]:
    """
    Perform web search using OpenAI's web_search_preview tool
    
    Args:
        query: Search query string
        max_results: Maximum number of results to return (not directly used but kept for compatibility)
        api_key: OpenAI API key, if not provided will try to get from environment
        
    Returns:
        Dictionary with search results in standardized format
    """
    try:
        logger.info(f"🔍 执行OpenAI Web Search: {query}")
        
        # 初始化OpenAI客户端
        if api_key:
            client = openai.OpenAI(api_key=api_key)
        else:
            client = openai.OpenAI()  # 使用环境变量中的API key
        
        # 使用Responses API + web_search_preview工具 (官方文档标准实现)
        response = client.responses.create(
            model="gpt-4.1",  # 支持web search的模型
            tools=[{"type": "web_search_preview"}],
            input=f"Search for information about: {query}. Provide comprehensive details and relevant facts."
        )
        
        # 解析Responses API响应 (按官方文档格式)
        search_results = []
        web_search_calls = []
        output_text = ""
        citations = []
        
        # 处理响应中的各个部分
        for item in response.output:
            if item.type == "web_search_call":
                web_search_calls.append({
                    'id': item.id,
                    'status': item.status,
                    'action': getattr(item, 'action', 'search')
                })
                logger.info(f"✅ Web search call: {item.id} - {item.status}")
                
            elif item.type == "message":
                if hasattr(item, 'content') and item.content:
                    for content_item in item.content:
                        if content_item.type == "output_text":
                            output_text = content_item.text
                            
                            # 提取引用信息
                            if hasattr(content_item, 'annotations') and content_item.annotations:
                                for annotation in content_item.annotations:
                                    if annotation.type == "url_citation":
                                        citations.append({
                                            'url': annotation.url,
                                            'title': getattr(annotation, 'title', ''),
                                            'start_index': annotation.start_index,
                                            'end_index': annotation.end_index
                                        })
        
        # 构建搜索结果（从引用中创建结果项）
        unique_urls = {}
        for citation in citations:
            url = citation['url']
            if url not in unique_urls:
                # 提取引用对应的文本内容
                start_idx = citation.get('start_index', 0)
                end_idx = citation.get('end_index', len(output_text))
                content_snippet = output_text[start_idx:end_idx] if start_idx and end_idx else citation['title']
                
                unique_urls[url] = {
                    'title': citation['title'] or f'Search result for {query}',
                    'url': url,
                    'content': content_snippet,
                    'snippet': content_snippet[:200] + '...' if len(content_snippet) > 200 else content_snippet
                }
        
        search_results = list(unique_urls.values())
        
        # 如果没有提取到具体的结果，但有输出文本，创建一个通用结果
        if not search_results and output_text:
            search_results = [{
                'title': f'Web Search Results for: {query}',
                'content': output_text,
                'url': 'https://openai.com/web-search',
                'snippet': output_text[:200] + '...' if len(output_text) > 200 else output_text
            }]
        
        result = {
            'query': query,
            'results': search_results,
            'total_results': len(search_results),
            'search_time': time.time(),
            'status': 'success',
            'output_text': output_text,
            'citations': citations,
            'web_search_calls': web_search_calls,
            'provider': 'openai_responses_api_web_search',
            'model_used': 'gpt-4.1'
        }
        
        logger.info(f"✅ OpenAI Web Search完成: {len(search_results)} 个结果, {len(citations)} 个引用")
        return result
        
    except Exception as e:
        logger.error(f"❌ OpenAI Web Search失败: {e}")
        # 直接返回失败，不使用mock数据避免污染
        return {
            'query': query,
            'results': [],
            'total_results': 0,
            'search_time': time.time(),
            'status': 'failed',
            'error': str(e),
            'provider': 'openai_responses_api_web_search'
        }

# 移除了fallback mock search函数 - 不再使用假数据污染结果

def search_with_openai_preview(query: str, api_key: str = None) -> Dict[str, Any]:
    """
    Use OpenAI's web_search_preview tool - now implemented
    
    Args:
        query: Search query
        api_key: OpenAI API key
        
    Returns:
        Search results from OpenAI web search
    """
    return web_search(query, api_key=api_key)

def validate_search_response(response: Dict[str, Any]) -> bool:
    """Validate that search response has expected structure"""
    required_fields = ['query', 'results', 'status']
    return all(field in response for field in required_fields)

# Main search function that tries different providers
def perform_web_search(query: str, provider: str = 'openai', api_key: str = None) -> Dict[str, Any]:
    """
    Main web search function with provider selection
    
    Args:
        query: Search query
        provider: Search provider ('openai' only - no fallback to avoid data pollution)
        api_key: OpenAI API key
        
    Returns:
        Search results dictionary (empty if failed)
    """
    if provider == 'openai':
        return search_with_openai_preview(query, api_key=api_key)
    else:
        return web_search(query, api_key=api_key)

# For backward compatibility
def web_search_preview(query: str, api_key: str = None) -> str:
    """Compatibility function that returns search results as string"""
    results = web_search(query, api_key=api_key)
    
    if results['status'] == 'success' and results['results']:
        # 优先使用完整的output_text如果可用
        if 'output_text' in results and results['output_text']:
            return f"Search Results for '{query}':\n\n{results['output_text']}"
        
        # Format results as text
        formatted_results = f"Search Results for '{query}':\n\n"
        for i, result in enumerate(results['results'], 1):
            formatted_results += f"{i}. {result['title']}\n"
            content = result['content'][:200] if len(result['content']) > 200 else result['content']
            formatted_results += f"   {content}...\n" if len(result['content']) > 200 else f"   {content}\n"
            formatted_results += f"   URL: {result['url']}\n\n"
        
        # 添加引用信息（如果有）
        if 'citations' in results and results['citations']:
            formatted_results += "\nCited Sources:\n"
            for citation in results['citations']:
                formatted_results += f"- {citation['title']}: {citation['url']}\n"
        
        return formatted_results
    else:
        # 返回空字符串表示没有搜索到结果，避免使用fake数据
        logger.warning(f"Web search failed for '{query}': {results.get('error', 'No results')}")
        return "" 
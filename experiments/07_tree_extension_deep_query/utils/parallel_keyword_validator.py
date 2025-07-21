#!/usr/bin/env python3
"""
并行关键词验证器
使用线程池并行验证多个关键词，大幅提升验证效率
"""

import time
import json
import logging
from typing import List, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class KeywordValidationResult:
    """关键词验证结果"""
    keyword: str
    is_necessary: bool
    necessity_score: float
    reasoning: str
    processing_time: float

class ParallelKeywordValidator:
    """并行关键词验证器"""
    
    def __init__(self, api_client, max_workers: int = 3):
        """
        初始化并行验证器
        
        Args:
            api_client: API客户端
            max_workers: 最大并行工作线程数（建议3-5个避免API限制）
        """
        self.api_client = api_client
        self.max_workers = max_workers
        
    def validate_keywords_parallel(self, keywords: List, query_text: str, answer: str) -> List:
        """
        并行验证关键词必要性
        
        Args:
            keywords: 关键词列表
            query_text: 查询文本
            answer: 目标答案
            
        Returns:
            必要的关键词列表
        """
        if not keywords:
            return keywords
        
        logger.info(f"🚀 开始并行验证 {len(keywords)} 个关键词 (最大并行数: {self.max_workers})")
        start_time = time.time()
        
        # 使用线程池并行验证
        validation_results = []
        necessary_keywords = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有验证任务
            future_to_keyword = {
                executor.submit(self._validate_single_keyword, keyword, query_text, answer): keyword
                for keyword in keywords
            }
            
            # 收集结果
            for future in as_completed(future_to_keyword):
                keyword = future_to_keyword[future]
                try:
                    result = future.result()
                    validation_results.append(result)
                    
                    if result.is_necessary:
                        # 更新原始关键词对象
                        keyword.necessity_score = result.necessity_score
                        necessary_keywords.append(keyword)
                        logger.info(f"✅ 关键词 '{result.keyword}' 是必要的 (分数: {result.necessity_score:.2f})")
                    else:
                        logger.info(f"❌ 关键词 '{result.keyword}' 不是必要的 (分数: {result.necessity_score:.2f})")
                        
                except Exception as e:
                    logger.error(f"验证关键词 '{keyword.keyword}' 时出错: {e}")
                    # 出错时保守地认为关键词是必要的
                    keyword.necessity_score = 0.8
                    necessary_keywords.append(keyword)
        
        total_time = time.time() - start_time
        logger.info(f"⚡ 并行验证完成: {len(necessary_keywords)}/{len(keywords)} 个关键词必要")
        logger.info(f"⏱️  总耗时: {total_time:.1f}秒 (平均每个关键词: {total_time/len(keywords):.1f}秒)")
        
        # 计算效率提升
        sequential_time_estimate = len(keywords) * 3  # 假设每个关键词串行需要3秒
        speedup = sequential_time_estimate / total_time
        logger.info(f"🚀 并行加速比: {speedup:.1f}x (预估节省 {sequential_time_estimate - total_time:.1f}秒)")
        
        return necessary_keywords
    
    def _validate_single_keyword(self, keyword, query_text: str, answer: str) -> KeywordValidationResult:
        """
        验证单个关键词的必要性
        
        Args:
            keyword: 关键词对象
            query_text: 查询文本
            answer: 目标答案
            
        Returns:
            验证结果
        """
        start_time = time.time()
        
        try:
            masking_prompt = f"""**TASK: Perform Minimum Keyword Check for Agent reasoning testing.**

**ORIGINAL QUERY:** {query_text}
**TARGET ANSWER:** {answer}
**KEYWORD TO TEST:** {keyword.keyword}

**MASKING TEST (Following WorkFlow):**
Mask the keyword "{keyword.keyword}" from the query and check if the remaining keywords and descriptions can still uniquely identify the answer "{answer}".

**MODIFIED QUERY (with keyword masked):** {query_text.replace(keyword.keyword, '[MASKED]')}

**EVALUATION CRITERIA:**
1. Can the modified query still **uniquely identify** the answer "{answer}"?
2. Are the **remaining keywords sufficient** to eliminate other possible answers?
3. Does masking this keyword create **ambiguity** or **multiple possible answers**?
4. Is this keyword **essential** for answer precision?

**NECESSITY LEVELS:**
- **ESSENTIAL** (1.0): Masking creates ambiguity, multiple answers possible
- **IMPORTANT** (0.8): Masking reduces precision significantly  
- **HELPFUL** (0.6): Masking has minor impact on precision
- **REDUNDANT** (0.3): Masking has no impact, other keywords sufficient

**Output Format (JSON):**
{{
    "is_necessary": true/false,
    "necessity_score": 0.0-1.0,
    "masking_impact": "essential/important/helpful/redundant",
    "reasoning": "detailed explanation of why this keyword is/isn't necessary",
    "alternative_answers_without_keyword": ["list", "of", "possible", "answers"]
}}

**TARGET: Determine if this keyword is essential for unique answer identification.**"""

            response = self.api_client.generate_response(
                prompt=masking_prompt,
                temperature=0.2,
                max_tokens=400
            )
            
            parsed_data = self._parse_json_response(response)
            processing_time = time.time() - start_time
            
            if parsed_data:
                is_necessary = parsed_data.get('is_necessary', True)
                necessity_score = float(parsed_data.get('necessity_score', 0.8))
                reasoning = parsed_data.get('reasoning', 'No reasoning provided')
                
                # 只保留必要的关键词（分数 > 0.5）
                is_necessary = is_necessary and necessity_score > 0.5
                
                return KeywordValidationResult(
                    keyword=keyword.keyword,
                    is_necessary=is_necessary,
                    necessity_score=necessity_score,
                    reasoning=reasoning,
                    processing_time=processing_time
                )
            else:
                # 解析失败时保守处理
                return KeywordValidationResult(
                    keyword=keyword.keyword,
                    is_necessary=True,
                    necessity_score=0.8,
                    reasoning="Failed to parse response, defaulting to necessary",
                    processing_time=time.time() - start_time
                )
                
        except Exception as e:
            logger.error(f"验证关键词 '{keyword.keyword}' 时出错: {e}")
            return KeywordValidationResult(
                keyword=keyword.keyword,
                is_necessary=True,
                necessity_score=0.8,
                reasoning=f"Error during validation: {e}",
                processing_time=time.time() - start_time
            )
    
    def _parse_json_response(self, response: str) -> Optional[Dict]:
        """解析JSON响应"""
        try:
            # 尝试找到JSON部分
            if '{' in response and '}' in response:
                start = response.find('{')
                end = response.rfind('}') + 1
                json_str = response[start:end]
                return json.loads(json_str)
            else:
                logger.warning("Response does not contain valid JSON")
                return None
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error parsing response: {e}")
            return None

def create_parallel_validator(api_client, max_workers: int = 3) -> ParallelKeywordValidator:
    """
    创建并行关键词验证器的工厂函数
    
    Args:
        api_client: API客户端
        max_workers: 最大并行工作线程数
        
    Returns:
        并行验证器实例
    """
    return ParallelKeywordValidator(api_client, max_workers) 
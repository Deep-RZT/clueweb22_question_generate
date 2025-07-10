"""
Answer Compression Optimizer for Short Answer Deep Query System
专门处理超长答案的智能压缩优化器
"""

import json
import logging
import time
import sys
import os
from typing import List, Dict, Any, Optional, Tuple

# 添加项目根目录到路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from core.llm_clients.llm_manager import llm_manager

logger = logging.getLogger(__name__)

class AnswerCompressionOptimizer:
    """答案压缩优化器 - 处理超长答案的二次压缩"""
    
    def __init__(self, llm_manager_instance=None):
        # 使用传入的llm_manager实例，如果没有则使用全局实例
        if llm_manager_instance:
            self.llm_manager = llm_manager_instance
        else:
            self.llm_manager = llm_manager
        self.compression_stats = {
            'processed_count': 0,
            'successful_compressions': 0,
            'failed_compressions': 0,
            'average_compression_ratio': 0.0,
            'quality_improvements': 0
        }
    
    def optimize_qa_pairs(self, qa_pairs: List[Dict[str, Any]], 
                         max_word_limit: int = 15,
                         max_char_limit: int = 100) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        优化QA对，对超长答案进行智能压缩
        
        Args:
            qa_pairs: 原始QA对列表
            max_word_limit: 最大词数限制
            max_char_limit: 最大字符限制
        
        Returns:
            (优化后的QA对列表, 优化统计信息)
        """
        logger.info(f"🔧 开始答案压缩优化: {len(qa_pairs)} 个QA对")
        
        optimized_pairs = []
        optimization_log = []
        
        for i, qa_pair in enumerate(qa_pairs):
            try:
                original_answer = qa_pair.get('answer', '')
                original_word_count = len(original_answer.split())
                original_char_count = len(original_answer)
                
                # 判断是否需要压缩
                needs_compression = (
                    original_word_count > max_word_limit or 
                    original_char_count > max_char_limit
                )
                
                if needs_compression:
                    logger.info(f"  🎯 压缩第{i+1}个答案 (原: {original_word_count}词/{original_char_count}字符)")
                    
                    # 执行智能压缩
                    compressed_result = self._compress_answer(
                        qa_pair['question'], 
                        original_answer,
                        max_word_limit,
                        max_char_limit
                    )
                    
                    if compressed_result['success']:
                        # 更新QA对
                        optimized_qa = qa_pair.copy()
                        optimized_qa['answer'] = compressed_result['compressed_answer']
                        optimized_qa['answer_word_count'] = compressed_result['word_count']
                        optimized_qa['answer_length'] = compressed_result['char_count']
                        optimized_qa['compression_applied'] = True
                        optimized_qa['original_answer'] = original_answer
                        optimized_qa['compression_ratio'] = compressed_result['compression_ratio']
                        
                        optimized_pairs.append(optimized_qa)
                        self.compression_stats['successful_compressions'] += 1
                        
                        logger.info(f"    ✅ 压缩成功: {compressed_result['word_count']}词/{compressed_result['char_count']}字符 "
                                  f"(压缩率: {compressed_result['compression_ratio']:.1%})")
                        
                        optimization_log.append({
                            'qa_id': qa_pair.get('question_id', f'q_{i+1}'),
                            'action': 'compressed',
                            'original_words': original_word_count,
                            'compressed_words': compressed_result['word_count'],
                            'compression_ratio': compressed_result['compression_ratio'],
                            'quality_preserved': compressed_result.get('quality_preserved', True)
                        })
                        
                    else:
                        # 压缩失败，保留原答案但标记
                        optimized_qa = qa_pair.copy()
                        optimized_qa['compression_failed'] = True
                        optimized_qa['compression_error'] = compressed_result.get('error', 'Unknown error')
                        optimized_pairs.append(optimized_qa)
                        self.compression_stats['failed_compressions'] += 1
                        
                        logger.warning(f"    ❌ 压缩失败: {compressed_result.get('error', 'Unknown error')}")
                        
                        optimization_log.append({
                            'qa_id': qa_pair.get('question_id', f'q_{i+1}'),
                            'action': 'compression_failed',
                            'error': compressed_result.get('error', 'Unknown error')
                        })
                else:
                    # 无需压缩
                    optimized_pairs.append(qa_pair)
                    optimization_log.append({
                        'qa_id': qa_pair.get('question_id', f'q_{i+1}'),
                        'action': 'no_compression_needed',
                        'word_count': original_word_count
                    })
                
                self.compression_stats['processed_count'] += 1
                
            except Exception as e:
                logger.error(f"处理QA对{i+1}时出错: {e}")
                optimized_pairs.append(qa_pair)  # 保留原始数据
                optimization_log.append({
                    'qa_id': qa_pair.get('question_id', f'q_{i+1}'),
                    'action': 'error',
                    'error': str(e)
                })
        
        # 计算整体统计
        total_compressions = self.compression_stats['successful_compressions']
        if total_compressions > 0:
            compression_ratios = [log['compression_ratio'] for log in optimization_log 
                                if log['action'] == 'compressed']
            self.compression_stats['average_compression_ratio'] = sum(compression_ratios) / len(compression_ratios)
        
        optimization_summary = {
            'total_processed': self.compression_stats['processed_count'],
            'successful_compressions': self.compression_stats['successful_compressions'],
            'failed_compressions': self.compression_stats['failed_compressions'],
            'average_compression_ratio': self.compression_stats['average_compression_ratio'],
            'optimization_log': optimization_log
        }
        
        logger.info(f"🎯 答案压缩优化完成: {self.compression_stats['successful_compressions']}/{len(qa_pairs)} 成功压缩")
        
        return optimized_pairs, optimization_summary
    
    def _compress_answer(self, question: str, original_answer: str, 
                        max_words: int, max_chars: int) -> Dict[str, Any]:
        """
        执行单个答案的智能压缩
        
        Args:
            question: 问题文本
            original_answer: 原始答案
            max_words: 最大词数
            max_chars: 最大字符数
        
        Returns:
            压缩结果字典
        """
        try:
            # 构建专业的压缩提示词
            system_prompt = """You are an expert answer compression specialist for academic BrowseComp-style questions.

CORE MISSION: Compress verbose answers to ESSENTIAL CORE FACTS while maintaining 100% factual accuracy.

🎯 COMPRESSION PRINCIPLES:
1. PRESERVE CORE FACT: Keep the essential answer unchanged
2. ELIMINATE REDUNDANCY: Remove all explanatory text, background, context
3. MAINTAIN PRECISION: Keep technical terms, numbers, names exact
4. ENSURE VERIFIABILITY: Answer must remain independently verifiable
5. ACADEMIC BREVITY: Use standard academic/technical abbreviations

📋 COMPRESSION TECHNIQUES:

FOR QUANTITATIVE ANSWERS:
- Keep exact numbers: "94.2% accuracy" → "94.2%"
- Preserve units: "500 participants" → "500"
- Maintain precision: "p < 0.001" → "p < 0.001"

FOR NAME/ATTRIBUTION ANSWERS:
- Essential names only: "Smith et al. (2023)" → "Smith et al."
- Institution abbreviations: "Stanford University" → "Stanford"
- Year when crucial: "proposed in 2019" → "2019" (if year is the answer)

FOR TECHNICAL TERMS:
- Standard abbreviations: "Convolutional Neural Network" → "CNN"
- Algorithm names: "Random Forest classifier" → "Random Forest"
- Keep critical modifiers: "pre-trained BERT model" → "pre-trained BERT"

❌ NEVER COMPRESS:
- Core factual content (the actual answer)
- Technical precision (exact numbers, statistical values)
- Essential qualifiers (if part of the answer)
- Proper nouns when they ARE the answer

✅ ALWAYS REMOVE:
- Explanatory phrases ("The study found that...")
- Background context ("In the context of...")
- Hedging language ("approximately", "around")
- Redundant descriptors
- Introductory text"""

            prompt = f"""COMPRESSION TASK:

Original Question: {question}

Original Answer (needs compression): {original_answer}

REQUIREMENTS:
- Maximum {max_words} words
- Maximum {max_chars} characters
- Preserve 100% factual accuracy
- Maintain technical precision
- Keep answer independently verifiable

COMPRESSION INSTRUCTIONS:
1. Identify the CORE FACT being asked for in the question
2. Extract ONLY that essential information from the original answer
3. Use technical abbreviations where appropriate
4. Eliminate ALL explanatory or contextual text
5. Ensure the compressed answer directly answers the question

COMPRESSED ANSWER (max {max_words} words, {max_chars} chars):"""

            # 使用更严格的参数 - 使用实例的llm_manager
            response = self.llm_manager.generate_text(
                prompt=prompt,
                max_tokens=100,  # 严格限制
                temperature=0.1,  # 确保一致性
                system_prompt=system_prompt,
                provider="openai"  # 明确指定OpenAI提供商
            )
            
            if response.success and response.content:
                compressed_answer = response.content.strip()
                
                # 验证压缩结果
                word_count = len(compressed_answer.split())
                char_count = len(compressed_answer)
                
                # 计算压缩率
                original_words = len(original_answer.split())
                compression_ratio = 1 - (word_count / max(original_words, 1))
                
                # 质量检查
                quality_preserved = self._validate_compression_quality(
                    question, original_answer, compressed_answer
                )
                
                if word_count <= max_words and char_count <= max_chars:
                    return {
                        'success': True,
                        'compressed_answer': compressed_answer,
                        'word_count': word_count,
                        'char_count': char_count,
                        'compression_ratio': compression_ratio,
                        'quality_preserved': quality_preserved
                    }
                else:
                    # 尝试进一步压缩
                    if word_count > max_words:
                        # 激进压缩策略
                        aggressive_result = self._aggressive_compression(
                            compressed_answer, max_words, max_chars
                        )
                        if aggressive_result['success']:
                            aggressive_result['compression_ratio'] = compression_ratio
                            return aggressive_result
                    
                    return {
                        'success': False,
                        'error': f'压缩后仍超限: {word_count}词/{char_count}字符 > {max_words}词/{max_chars}字符',
                        'compressed_answer': compressed_answer,
                        'word_count': word_count,
                        'char_count': char_count
                    }
            else:
                return {
                    'success': False,
                    'error': f'LLM压缩失败: {response.error}' if hasattr(response, 'error') else 'LLM响应失败'
                }
        
        except Exception as e:
            return {
                'success': False,
                'error': f'压缩处理异常: {str(e)}'
            }
    
    def _aggressive_compression(self, text: str, max_words: int, max_chars: int) -> Dict[str, Any]:
        """激进压缩策略 - 针对仍然超长的文本"""
        try:
            words = text.split()
            
            # 策略1: 保留最核心的词汇
            if len(words) > max_words:
                # 保留前几个最重要的词
                core_words = words[:max_words]
                compressed = ' '.join(core_words)
                
                # 检查字符限制
                if len(compressed) <= max_chars:
                    return {
                        'success': True,
                        'compressed_answer': compressed,
                        'word_count': len(core_words),
                        'char_count': len(compressed),
                        'method': 'aggressive_truncation'
                    }
            
            # 策略2: 字符级截断
            if len(text) > max_chars:
                # 截断到字符限制，确保不在单词中间
                truncated = text[:max_chars]
                last_space = truncated.rfind(' ')
                if last_space > max_chars * 0.8:  # 如果空格位置合理
                    truncated = truncated[:last_space]
                
                word_count = len(truncated.split())
                if word_count <= max_words:
                    return {
                        'success': True,
                        'compressed_answer': truncated,
                        'word_count': word_count,
                        'char_count': len(truncated),
                        'method': 'character_truncation'
                    }
            
            return {
                'success': False,
                'error': '激进压缩策略也无法满足限制'
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': f'激进压缩异常: {str(e)}'
            }
    
    def _validate_compression_quality(self, question: str, original: str, compressed: str) -> bool:
        """验证压缩质量 - 确保核心信息保留"""
        try:
            # 基本检查：压缩答案不能为空
            if not compressed or len(compressed.strip()) == 0:
                return False
            
            # 检查关键信息保留
            # 1. 数字信息
            import re
            original_numbers = re.findall(r'\d+\.?\d*', original)
            compressed_numbers = re.findall(r'\d+\.?\d*', compressed)
            
            # 如果原答案有数字，压缩答案应该保留主要数字
            if original_numbers and not compressed_numbers:
                return False
            
            # 2. 专有名词（大写开头的词）
            original_proper_nouns = re.findall(r'\b[A-Z][a-z]+\b', original)
            compressed_proper_nouns = re.findall(r'\b[A-Z][a-z]+\b', compressed)
            
            # 如果原答案有专有名词，压缩答案应该保留
            if len(original_proper_nouns) > 0 and len(compressed_proper_nouns) == 0:
                return False
            
            # 3. 技术术语保留检查
            technical_terms = ['accuracy', 'precision', 'recall', 'f1', 'score', 'rate', 'ratio', '%']
            original_has_tech = any(term in original.lower() for term in technical_terms)
            compressed_has_tech = any(term in compressed.lower() for term in technical_terms)
            
            if original_has_tech and not compressed_has_tech:
                # 可能是技术答案，需要保留技术信息
                return len(compressed_numbers) > 0  # 至少保留数字
            
            return True
        
        except Exception as e:
            logger.warning(f"质量验证异常: {e}")
            return True  # 默认认为质量可接受
    
    def get_compression_statistics(self) -> Dict[str, Any]:
        """获取压缩统计信息"""
        return self.compression_stats.copy()
    
    def reset_statistics(self):
        """重置统计信息"""
        self.compression_stats = {
            'processed_count': 0,
            'successful_compressions': 0,
            'failed_compressions': 0,
            'average_compression_ratio': 0.0,
            'quality_improvements': 0
        }


class EnhancedAnswerValidator:
    """增强的答案验证器 - 更智能的答案质量评估"""
    
    def __init__(self):
        self.validation_criteria = {
            'max_word_count': 15,
            'max_char_count': 100,
            'min_information_density': 0.5,  # 信息密度最小要求
            'required_precision': True  # 是否需要精确性
        }
    
    def validate_answer_quality(self, question: str, answer: str) -> Dict[str, Any]:
        """
        全面验证答案质量
        
        Returns:
            验证结果字典，包含通过状态和详细分析
        """
        validation_result = {
            'passed': True,
            'issues': [],
            'metrics': {},
            'suggestions': []
        }
        
        # 基本长度检查
        word_count = len(answer.split())
        char_count = len(answer)
        
        validation_result['metrics']['word_count'] = word_count
        validation_result['metrics']['char_count'] = char_count
        
        # 长度验证
        if word_count > self.validation_criteria['max_word_count']:
            validation_result['passed'] = False
            validation_result['issues'].append(f"答案词数超限: {word_count} > {self.validation_criteria['max_word_count']}")
            validation_result['suggestions'].append("考虑使用答案压缩优化")
        
        if char_count > self.validation_criteria['max_char_count']:
            validation_result['passed'] = False
            validation_result['issues'].append(f"答案字符数超限: {char_count} > {self.validation_criteria['max_char_count']}")
        
        # 信息密度检查
        info_density = self._calculate_information_density(answer)
        validation_result['metrics']['information_density'] = info_density
        
        if info_density < self.validation_criteria['min_information_density']:
            validation_result['issues'].append(f"信息密度过低: {info_density:.2f}")
            validation_result['suggestions'].append("增加核心信息，减少冗余表达")
        
        # 精确性检查
        precision_score = self._evaluate_precision(question, answer)
        validation_result['metrics']['precision_score'] = precision_score
        
        if precision_score < 0.7:
            validation_result['issues'].append(f"答案精确性不足: {precision_score:.2f}")
        
        return validation_result
    
    def _calculate_information_density(self, text: str) -> float:
        """计算文本的信息密度"""
        import re
        
        # 信息性词汇: 数字、专有名词、技术术语
        information_patterns = [
            r'\d+\.?\d*',  # 数字
            r'\b[A-Z][a-z]+\b',  # 专有名词
            r'\b\w+(?:ing|ed|er|est|ly)\b',  # 派生词
            r'%|percent|ratio|rate|score',  # 度量词
        ]
        
        total_words = len(text.split())
        information_words = 0
        
        for pattern in information_patterns:
            matches = re.findall(pattern, text)
            information_words += len(matches)
        
        return min(information_words / max(total_words, 1), 1.0)
    
    def _evaluate_precision(self, question: str, answer: str) -> float:
        """评估答案的精确性"""
        # 简化的精确性评估
        question_lower = question.lower()
        answer_lower = answer.lower()
        
        precision_indicators = [
            'exact', 'precise', 'specific', 'how many', 'what percentage',
            'which', 'who', 'when', 'where'
        ]
        
        # 如果问题要求精确答案
        requires_precision = any(indicator in question_lower for indicator in precision_indicators)
        
        if requires_precision:
            # 检查答案是否包含具体信息
            import re
            has_numbers = bool(re.search(r'\d+', answer))
            has_names = bool(re.search(r'\b[A-Z][a-z]+\b', answer))
            has_specific_terms = len(answer.split()) <= 5  # 简洁通常意味着精确
            
            precision_score = sum([has_numbers, has_names, has_specific_terms]) / 3.0
            return precision_score
        else:
            return 0.8  # 非精确性问题的默认分数


def test_answer_compression():
    """测试答案压缩功能"""
    print("=== 答案压缩优化器测试 ===")
    
    # 测试数据
    test_qa_pairs = [
        {
            'question_id': 'test_1',
            'question': 'What was the exact accuracy achieved by the model?',
            'answer': 'The model achieved an accuracy of 94.2% which was significantly higher than the baseline performance of 87.3% that was established in previous studies. This represents a substantial improvement in the classification task.',
            'type': 'quantitative'
        },
        {
            'question_id': 'test_2',
            'question': 'Who first proposed this methodology?',
            'answer': 'This methodology was first proposed by Smith and Brown in their groundbreaking 2022 paper published in Nature Machine Intelligence, which has since become the standard approach in the field.',
            'type': 'attribution'
        }
    ]
    
    # 创建优化器
    optimizer = AnswerCompressionOptimizer()
    
    # 执行优化
    optimized_pairs, summary = optimizer.optimize_qa_pairs(test_qa_pairs, max_word_limit=10, max_char_limit=50)
    
    print(f"优化结果:")
    for pair in optimized_pairs:
        print(f"问题: {pair['question']}")
        print(f"原答案: {pair.get('original_answer', pair['answer'])}")
        print(f"优化答案: {pair['answer']}")
        print(f"词数: {pair.get('answer_word_count', len(pair['answer'].split()))}")
        print(f"压缩: {'是' if pair.get('compression_applied') else '否'}")
        print("-" * 50)
    
    print(f"优化统计: {summary}")

if __name__ == "__main__":
    test_answer_compression() 
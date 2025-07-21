#!/usr/bin/env python3
"""
循环问题处理器
实现智能循环检测和重新生成策略
"""

import time
import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class CircularRisk:
    """循环风险评估结果"""
    similarity_score: float
    risk_level: str  # 'low', 'medium', 'high', 'critical'
    should_skip: bool
    recommended_action: str
    reason: str

class CircularProblemHandler:
    """循环问题处理器"""
    
    def __init__(self):
        # 相似度阈值设置
        self.similarity_threshold_skip = 0.85      # 直接跳过
        self.similarity_threshold_retry = 0.7      # 轻量重试
        self.similarity_threshold_multi = 0.5      # 多角度尝试
        
        # 统计信息
        self.stats = {
            'total_checks': 0,
            'skipped_high_risk': 0,
            'retry_attempts': 0,
            'successful_regenerations': 0,
            'failed_regenerations': 0
        }
        
        # 关键词域扩展模板
        self.expansion_templates = [
            "{keyword} applications",
            "{keyword} history", 
            "{keyword} technology",
            "{keyword} development",
            "{keyword} types",
            "{keyword} methods",
            "{keyword} examples",
            "{keyword} principles"
        ]
        
        # 多角度搜索模板
        self.angle_templates = [
            "historical aspects of {keyword}",
            "technical details of {keyword}",
            "practical applications of {keyword}",
            "scientific principles behind {keyword}",
            "development timeline of {keyword}",
            "impact and influence of {keyword}"
        ]
    
    def assess_circular_risk(self, keyword: str, parent_question: str, parent_answer: str, 
                           search_results: Optional[List[Dict[str, Any]]] = None) -> CircularRisk:
        """评估循环风险 - 基于知识内容而非词汇相似度"""
        self.stats['total_checks'] += 1
        
        # 1. 检查搜索结果内容循环（如果有搜索结果）
        content_similarity = 0.0
        if search_results:
            content_similarity = self._calculate_content_similarity(search_results, parent_question, parent_answer)
        
        # 2. 检查知识循环模式
        knowledge_risk = self._detect_knowledge_circularity(keyword, parent_question, parent_answer)
        
        # 3. 综合风险评估
        max_risk = max(content_similarity, knowledge_risk)
        
        # 4. 确定风险级别和行动
        if max_risk > 0.8:
            risk_level = 'critical'
            should_skip = True
            action = 'skip'
            reason = f"检测到知识循环 (风险: {max_risk:.3f}) - 不同表述问同一知识点"
        elif max_risk > 0.6:
            risk_level = 'high'
            should_skip = False
            action = 'keyword_expansion'
            reason = f"高循环风险 (风险: {max_risk:.3f}) - 建议关键词扩展寻找新角度"
        elif max_risk > 0.4:
            risk_level = 'medium'
            should_skip = False
            action = 'multi_angle_search'
            reason = f"中等循环风险 (风险: {max_risk:.3f}) - 可尝试多角度搜索"
        else:
            risk_level = 'low'
            should_skip = False
            action = 'proceed'
            reason = f"低循环风险 (风险: {max_risk:.3f}) - 可正常处理"
        
        return CircularRisk(
            similarity_score=max_risk,
            risk_level=risk_level,
            should_skip=should_skip,
            recommended_action=action,
            reason=reason
        )
    
    def handle_circular_risk(self, keyword: str, parent_question: str, parent_answer: str, 
                           web_search_system) -> Optional[List[Dict[str, Any]]]:
        """处理循环风险"""
        
        # 1. 先进行初步风险评估（不包含搜索结果）
        initial_risk = self.assess_circular_risk(keyword, parent_question, parent_answer)
        
        logger.info(f"初步循环风险评估: {keyword} -> {initial_risk.risk_level} ({initial_risk.similarity_score:.3f})")
        
        # 2. 如果初步评估风险极高，直接跳过
        if initial_risk.should_skip:
            self.stats['skipped_high_risk'] += 1
            logger.warning(f"跳过高风险关键词: {keyword} - {initial_risk.reason}")
            return None
        
        # 3. 进行搜索并基于搜索结果重新评估
        try:
            search_results = web_search_system.search(keyword)
            
            # 4. 基于搜索结果重新评估循环风险
            final_risk = self.assess_circular_risk(keyword, parent_question, parent_answer, search_results)
            
            logger.info(f"最终循环风险评估: {keyword} -> {final_risk.risk_level} ({final_risk.similarity_score:.3f})")
            logger.info(f"建议行动: {final_risk.recommended_action} - {final_risk.reason}")
            
            # 5. 根据最终风险级别采取行动
            if final_risk.should_skip:
                self.stats['skipped_high_risk'] += 1
                logger.warning(f"搜索结果显示循环风险，跳过: {keyword}")
                return None
            elif final_risk.recommended_action == 'keyword_expansion':
                return self._keyword_domain_expansion(keyword, parent_question, web_search_system)
            elif final_risk.recommended_action == 'multi_angle_search':
                return self._multi_angle_search(keyword, parent_question, web_search_system)
            else:
                # 搜索结果通过循环检测，返回结果
                return search_results
                
        except Exception as e:
            logger.error(f"搜索失败: {keyword} - {e}")
            # 搜索失败时，根据初步评估决定是否尝试其他方法
            if initial_risk.recommended_action == 'keyword_expansion':
                return self._keyword_domain_expansion(keyword, parent_question, web_search_system)
            else:
                return None
    
    def _calculate_content_similarity(self, search_results: List[Dict[str, Any]], 
                                    parent_question: str, parent_answer: str) -> float:
        """计算搜索结果内容与父问题的相似度"""
        if not search_results:
            return 0.0
        
        # 合并所有搜索结果的内容
        search_content = ""
        for result in search_results[:3]:  # 只检查前3个结果
            search_content += f" {result.get('snippet', '')} {result.get('title', '')}"
        
        if not search_content.strip():
            return 0.0
        
        # 计算搜索内容与父问题/答案的相似度
        parent_content = f"{parent_question} {parent_answer}"
        
        # 文本预处理
        search_words = set(self._preprocess_text(search_content))
        parent_words = set(self._preprocess_text(parent_content))
        
        # Jaccard相似度
        intersection = search_words.intersection(parent_words)
        union = search_words.union(parent_words)
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)
    
    def _detect_knowledge_circularity(self, keyword: str, parent_question: str, parent_answer: str) -> float:
        """检测知识循环模式 - 识别不同表述问同一知识点的情况"""
        
        # 提取关键信息元素
        parent_entities = self._extract_key_entities(parent_question, parent_answer)
        keyword_entities = self._extract_key_entities(keyword, "")
        
        # 1. 检查实体重叠度
        entity_overlap = self._calculate_entity_overlap(parent_entities, keyword_entities)
        
        # 2. 检查知识结构模式
        pattern_risk = self._detect_knowledge_patterns(keyword, parent_question, parent_answer)
        
        # 3. 检查问答对称性（A事件-B年的情况）
        symmetry_risk = self._detect_qa_symmetry(keyword, parent_question, parent_answer)
        
        return max(entity_overlap, pattern_risk, symmetry_risk)
    
    def _extract_key_entities(self, question: str, answer: str) -> Dict[str, List[str]]:
        """提取关键实体"""
        text = f"{question} {answer}".lower()
        
        entities = {
            'numbers': re.findall(r'\b\d+\b', text),
            'years': re.findall(r'\b(19|20)\d{2}\b', text),
            'proper_nouns': [],  # 简化版本，实际应使用NER
            'technical_terms': []
        }
        
        # 简单的专有名词识别（大写开头的词）
        words = re.findall(r'\b[A-Z][a-z]+\b', question + " " + answer)
        entities['proper_nouns'] = list(set(words))
        
        return entities
    
    def _calculate_entity_overlap(self, parent_entities: Dict, keyword_entities: Dict) -> float:
        """计算实体重叠度"""
        total_overlap = 0
        total_entities = 0
        
        for entity_type in parent_entities:
            parent_set = set(parent_entities[entity_type])
            keyword_set = set(keyword_entities[entity_type])
            
            if parent_set or keyword_set:
                union = parent_set.union(keyword_set)
                intersection = parent_set.intersection(keyword_set)
                if union:
                    total_overlap += len(intersection)
                    total_entities += len(union)
        
        return total_overlap / total_entities if total_entities > 0 else 0.0
    
    def _detect_knowledge_patterns(self, keyword: str, parent_question: str, parent_answer: str) -> float:
        """检测知识循环模式"""
        
        # 模式1: 时间-事件循环 (A事件发生于B年)
        time_event_risk = self._check_time_event_pattern(keyword, parent_question, parent_answer)
        
        # 模式2: 定义循环 (什么是X vs X是什么)
        definition_risk = self._check_definition_pattern(keyword, parent_question, parent_answer)
        
        # 模式3: 属性循环 (X的Y属性 vs Y属性是什么)
        attribute_risk = self._check_attribute_pattern(keyword, parent_question, parent_answer)
        
        return max(time_event_risk, definition_risk, attribute_risk)
    
    def _detect_qa_symmetry(self, keyword: str, parent_question: str, parent_answer: str) -> float:
        """检测问答对称性"""
        
        # 检查是否存在对称的知识关系
        # 例如: "A事件发生于B年" 的对称问题可能是 "B年发生了什么" 或 "A事件发生于哪一年"
        
        parent_text = f"{parent_question} {parent_answer}".lower()
        keyword_lower = keyword.lower()
        
        # 简化检测：如果关键词和父内容共享核心概念但表述不同
        parent_words = set(self._preprocess_text(parent_text))
        keyword_words = set(self._preprocess_text(keyword_lower))
        
        # 计算核心概念重叠
        intersection = parent_words.intersection(keyword_words)
        
        # 如果有重叠但不是完全相同，可能是对称问题
        if len(intersection) > 0:
            union = parent_words.union(keyword_words)
            overlap_ratio = len(intersection) / len(union)
            
            # 中等重叠度表明可能存在知识对称性
            if 0.3 < overlap_ratio < 0.7:
                return overlap_ratio + 0.2  # 增加风险权重
        
        return 0.0
    
    def _check_time_event_pattern(self, keyword: str, parent_question: str, parent_answer: str) -> float:
        """检查时间-事件循环模式"""
        text = f"{parent_question} {parent_answer} {keyword}".lower()
        
        # 检查是否包含年份和事件
        has_year = bool(re.search(r'\b(19|20)\d{2}\b', text))
        has_event_words = any(word in text for word in ['event', 'happen', 'occur', 'year', 'when', 'time'])
        
        if has_year and has_event_words:
            return 0.6  # 中高风险
        
        return 0.0
    
    def _check_definition_pattern(self, keyword: str, parent_question: str, parent_answer: str) -> float:
        """检查定义循环模式"""
        text = f"{parent_question} {keyword}".lower()
        
        # 检查定义模式的关键词
        definition_indicators = ['what is', 'what are', 'define', 'definition', 'meaning']
        
        indicator_count = sum(1 for indicator in definition_indicators if indicator in text)
        
        if indicator_count >= 2:
            return 0.7  # 高风险
        elif indicator_count == 1:
            return 0.3  # 低风险
        
        return 0.0
    
    def _check_attribute_pattern(self, keyword: str, parent_question: str, parent_answer: str) -> float:
        """检查属性循环模式"""
        text = f"{parent_question} {parent_answer} {keyword}".lower()
        
        # 检查属性相关的词汇
        attribute_words = ['property', 'characteristic', 'feature', 'attribute', 'aspect']
        
        if any(word in text for word in attribute_words):
            return 0.5  # 中等风险
        
        return 0.0
    
    def _preprocess_text(self, text: str) -> List[str]:
        """文本预处理"""
        # 转换为小写，移除标点，分词
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        words = text.split()
        
        # 过滤停用词
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                      'of', 'with', 'by', 'is', 'are', 'was', 'were', 'what', 'which', 'how'}
        
        return [word for word in words if word not in stop_words and len(word) > 2]
    
    def _keyword_domain_expansion(self, keyword: str, parent_question: str, 
                                web_search_system) -> Optional[List[Dict[str, Any]]]:
        """关键词域扩展策略"""
        
        logger.info(f"尝试关键词域扩展: {keyword}")
        self.stats['retry_attempts'] += 1
        
        for template in self.expansion_templates:
            expanded_query = template.format(keyword=keyword)
            
            try:
                results = web_search_system.search(expanded_query)
                
                if results and self._validate_search_results(results, parent_question):
                    logger.info(f"关键词扩展成功: {expanded_query} -> {len(results)} 个结果")
                    self.stats['successful_regenerations'] += 1
                    return results
                    
            except Exception as e:
                logger.warning(f"关键词扩展搜索失败 {expanded_query}: {e}")
                continue
        
        logger.warning(f"关键词域扩展失败: {keyword}")
        self.stats['failed_regenerations'] += 1
        return None
    
    def _multi_angle_search(self, keyword: str, parent_question: str, 
                          web_search_system) -> Optional[List[Dict[str, Any]]]:
        """多角度搜索策略"""
        
        logger.info(f"尝试多角度搜索: {keyword}")
        self.stats['retry_attempts'] += 1
        
        all_results = []
        
        for template in self.angle_templates:
            angle_query = template.format(keyword=keyword)
            
            try:
                results = web_search_system.search(angle_query)
                
                if results:
                    # 过滤高相似度结果
                    filtered_results = self._filter_by_semantic_distance(results, parent_question)
                    all_results.extend(filtered_results)
                    
            except Exception as e:
                logger.warning(f"多角度搜索失败 {angle_query}: {e}")
                continue
        
        if all_results:
            # 去重并限制数量
            unique_results = self._deduplicate_results(all_results)[:5]  # 最多5个结果
            
            if self._validate_search_results(unique_results, parent_question):
                logger.info(f"多角度搜索成功: {keyword} -> {len(unique_results)} 个结果")
                self.stats['successful_regenerations'] += 1
                return unique_results
        
        logger.warning(f"多角度搜索失败: {keyword}")
        self.stats['failed_regenerations'] += 1
        return None
    
    def _validate_search_results(self, results: List[Dict[str, Any]], parent_question: str) -> bool:
        """验证搜索结果质量"""
        
        if not results:
            return False
        
        # 简单验证：检查结果是否包含有效内容
        for result in results:
            content = result.get('content', '') or result.get('snippet', '')
            if len(content) > 50:  # 至少50个字符
                return True
        
        return False
    
    def _filter_by_semantic_distance(self, results: List[Dict[str, Any]], 
                                   parent_question: str) -> List[Dict[str, Any]]:
        """基于语义距离过滤结果"""
        
        filtered = []
        
        for result in results:
            content = result.get('content', '') or result.get('snippet', '')
            
            # 计算与父问题的相似度
            similarity = self._calculate_text_similarity(content, parent_question)
            
            # 过滤高相似度结果
            if similarity < 0.8:  # 保留相似度低于0.8的结果
                filtered.append(result)
        
        return filtered
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """计算两个文本的相似度"""
        
        words1 = set(self._preprocess_text(text1))
        words2 = set(self._preprocess_text(text2))
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    def _deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去重搜索结果"""
        
        seen = set()
        unique_results = []
        
        for result in results:
            content = result.get('content', '') or result.get('snippet', '')
            
            # 使用内容的前100个字符作为去重标识
            content_signature = content[:100]
            
            if content_signature not in seen:
                seen.add(content_signature)
                unique_results.append(result)
        
        return unique_results
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        
        success_rate = 0.0
        if self.stats['retry_attempts'] > 0:
            success_rate = self.stats['successful_regenerations'] / self.stats['retry_attempts']
        
        return {
            **self.stats,
            'success_rate': success_rate,
            'skip_rate': self.stats['skipped_high_risk'] / max(self.stats['total_checks'], 1)
        }
    
    def log_statistics(self):
        """记录统计信息"""
        
        stats = self.get_statistics()
        
        logger.info("=== 循环问题处理统计 ===")
        logger.info(f"总检查次数: {stats['total_checks']}")
        logger.info(f"跳过高风险: {stats['skipped_high_risk']} ({stats['skip_rate']:.1%})")
        logger.info(f"重试尝试: {stats['retry_attempts']}")
        logger.info(f"成功重新生成: {stats['successful_regenerations']}")
        logger.info(f"失败重新生成: {stats['failed_regenerations']}")
        logger.info(f"重新生成成功率: {stats['success_rate']:.1%}")
        logger.info("=" * 25) 
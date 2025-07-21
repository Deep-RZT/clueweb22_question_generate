#!/usr/bin/env python3
"""
循环提问检测系统
防止生成重复或循环的问题，如"A事件发生于B年"和"A事件发生于哪一年"
"""

import logging
import re
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

@dataclass
class QuestionPattern:
    """问题模式"""
    question: str
    answer: str
    normalized_question: str
    keywords: Set[str]
    question_type: str  # what, when, where, who, which
    semantic_signature: str

@dataclass
class CircularDetectionResult:
    """循环检测结果"""
    is_circular: bool
    similarity_score: float
    conflict_reason: str
    conflicting_question: Optional[str] = None
    suggestions: List[str] = None

class CircularQuestionDetector:
    """循环提问检测器"""
    
    def __init__(self):
        self.question_history: List[QuestionPattern] = []
        self.similarity_threshold = 0.75  # 相似度阈值
        self.keyword_overlap_threshold = 0.6  # 关键词重叠阈值
        
    def add_question(self, question: str, answer: str) -> None:
        """添加问题到历史记录"""
        pattern = self._create_question_pattern(question, answer)
        self.question_history.append(pattern)
        logger.debug(f"添加问题到检测历史: {question[:50]}...")
    
    def detect_circular_pattern(self, new_question: str, new_answer: str) -> CircularDetectionResult:
        """检测新问题是否与历史问题形成循环"""
        new_pattern = self._create_question_pattern(new_question, new_answer)
        
        # 检查各种循环模式
        for existing_pattern in self.question_history:
            # 1. 检查直接重复
            direct_result = self._check_direct_repetition(new_pattern, existing_pattern)
            if direct_result.is_circular:
                return direct_result
            
            # 2. 检查语义循环
            semantic_result = self._check_semantic_circular(new_pattern, existing_pattern)
            if semantic_result.is_circular:
                return semantic_result
            
            # 3. 检查反向循环 (A->B, B->A)
            reverse_result = self._check_reverse_circular(new_pattern, existing_pattern)
            if reverse_result.is_circular:
                return reverse_result
            
            # 4. 检查关键词循环
            keyword_result = self._check_keyword_circular(new_pattern, existing_pattern)
            if keyword_result.is_circular:
                return keyword_result
        
        # 没有检测到循环
        return CircularDetectionResult(
            is_circular=False,
            similarity_score=0.0,
            conflict_reason="No circular pattern detected"
        )
    
    def _create_question_pattern(self, question: str, answer: str) -> QuestionPattern:
        """创建问题模式"""
        # 规范化问题
        normalized = self._normalize_question(question)
        
        # 提取关键词
        keywords = self._extract_keywords(question, answer)
        
        # 确定问题类型
        question_type = self._determine_question_type(question)
        
        # 创建语义签名
        semantic_signature = self._create_semantic_signature(question, answer)
        
        return QuestionPattern(
            question=question,
            answer=answer,
            normalized_question=normalized,
            keywords=keywords,
            question_type=question_type,
            semantic_signature=semantic_signature
        )
    
    def _normalize_question(self, question: str) -> str:
        """规范化问题文本"""
        # 转小写
        normalized = question.lower().strip()
        
        # 移除标点符号
        normalized = re.sub(r'[^\w\s]', ' ', normalized)
        
        # 移除多余空格
        normalized = ' '.join(normalized.split())
        
        # 移除常见停用词但保留重要疑问词
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'was', 'are', 'were'}
        words = [w for w in normalized.split() if w not in stop_words or w in {'what', 'when', 'where', 'who', 'which', 'how', 'why'}]
        
        return ' '.join(words)
    
    def _extract_keywords(self, question: str, answer: str) -> Set[str]:
        """提取问题和答案的关键词"""
        combined_text = f"{question} {answer}".lower()
        
        # 移除常见词汇
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'was', 'are', 'were', 'what', 'when', 'where', 'who', 'which', 'how', 'why'}
        
        # 提取有意义的词汇
        words = re.findall(r'\b\w{3,}\b', combined_text)  # 至少3个字符
        keywords = {word for word in words if word not in stop_words}
        
        return keywords
    
    def _determine_question_type(self, question: str) -> str:
        """确定问题类型"""
        question_lower = question.lower().strip()
        
        if question_lower.startswith('what'):
            return 'what'
        elif question_lower.startswith('when'):
            return 'when'
        elif question_lower.startswith('where'):
            return 'where'
        elif question_lower.startswith('who'):
            return 'who'
        elif question_lower.startswith('which'):
            return 'which'
        elif question_lower.startswith('how'):
            return 'how'
        elif question_lower.startswith('why'):
            return 'why'
        else:
            return 'other'
    
    def _create_semantic_signature(self, question: str, answer: str) -> str:
        """创建语义签名用于快速比较"""
        # 提取核心概念
        keywords = sorted(list(self._extract_keywords(question, answer)))
        question_type = self._determine_question_type(question)
        
        # 创建签名
        signature = f"{question_type}:{':'.join(keywords[:5])}"  # 限制前5个关键词
        return signature
    
    def _check_direct_repetition(self, new_pattern: QuestionPattern, existing_pattern: QuestionPattern) -> CircularDetectionResult:
        """检查直接重复"""
        # 计算问题相似度
        similarity = SequenceMatcher(None, new_pattern.normalized_question, existing_pattern.normalized_question).ratio()
        
        if similarity >= 0.9:  # 90%以上相似认为是直接重复
            return CircularDetectionResult(
                is_circular=True,
                similarity_score=similarity,
                conflict_reason="Direct question repetition detected",
                conflicting_question=existing_pattern.question,
                suggestions=["Generate a different question with distinct focus", "Change question type or approach"]
            )
        
        return CircularDetectionResult(is_circular=False, similarity_score=similarity, conflict_reason="No direct repetition")
    
    def _check_semantic_circular(self, new_pattern: QuestionPattern, existing_pattern: QuestionPattern) -> CircularDetectionResult:
        """检查语义循环"""
        # 检查语义签名相似度
        if new_pattern.semantic_signature == existing_pattern.semantic_signature:
            return CircularDetectionResult(
                is_circular=True,
                similarity_score=1.0,
                conflict_reason="Identical semantic signature detected",
                conflicting_question=existing_pattern.question,
                suggestions=["Focus on different aspects of the topic", "Use different question types"]
            )
        
        # 检查关键词重叠
        keyword_overlap = len(new_pattern.keywords & existing_pattern.keywords) / max(len(new_pattern.keywords | existing_pattern.keywords), 1)
        
        if keyword_overlap >= self.keyword_overlap_threshold and new_pattern.question_type == existing_pattern.question_type:
            return CircularDetectionResult(
                is_circular=True,
                similarity_score=keyword_overlap,
                conflict_reason=f"High keyword overlap ({keyword_overlap:.1%}) with same question type",
                conflicting_question=existing_pattern.question,
                suggestions=["Change question type", "Focus on different keywords", "Explore alternative aspects"]
            )
        
        return CircularDetectionResult(is_circular=False, similarity_score=keyword_overlap, conflict_reason="No semantic circular")
    
    def _check_reverse_circular(self, new_pattern: QuestionPattern, existing_pattern: QuestionPattern) -> CircularDetectionResult:
        """检查反向循环 (如: Q1->A1, Q2->A2, 但A1包含Q2关键词，A2包含Q1关键词)"""
        # 检查新问题的答案是否出现在旧问题中
        new_answer_in_old_question = new_pattern.answer.lower() in existing_pattern.question.lower()
        old_answer_in_new_question = existing_pattern.answer.lower() in new_pattern.question.lower()
        
        if new_answer_in_old_question and old_answer_in_new_question:
            return CircularDetectionResult(
                is_circular=True,
                similarity_score=0.8,
                conflict_reason="Reverse circular pattern: answers appear in opposite questions",
                conflicting_question=existing_pattern.question,
                suggestions=["Generate questions with non-overlapping focus", "Avoid using previous answers as question elements"]
            )
        
        # 检查典型的时间循环: "A发生于B年" vs "A发生于哪一年"
        if self._check_temporal_circular(new_pattern, existing_pattern):
            return CircularDetectionResult(
                is_circular=True,
                similarity_score=0.9,
                conflict_reason="Temporal circular pattern detected (event-year relationship)",
                conflicting_question=existing_pattern.question,
                suggestions=["Focus on different aspects of the event", "Ask about participants, location, or impact instead of timing"]
            )
        
        return CircularDetectionResult(is_circular=False, similarity_score=0.0, conflict_reason="No reverse circular")
    
    def _check_temporal_circular(self, new_pattern: QuestionPattern, existing_pattern: QuestionPattern) -> bool:
        """检查时间相关的循环模式"""
        # 检查是否一个问when另一个答案包含年份
        new_when = new_pattern.question_type == 'when'
        old_when = existing_pattern.question_type == 'when'
        
        # 检查年份模式
        year_pattern = r'\b(19|20)\d{2}\b'
        new_has_year = bool(re.search(year_pattern, new_pattern.answer))
        old_has_year = bool(re.search(year_pattern, existing_pattern.answer))
        
        # 检查事件关键词重叠
        event_overlap = len(new_pattern.keywords & existing_pattern.keywords) > 2
        
        # 时间循环判断条件
        temporal_circular = (
            (new_when and old_has_year and event_overlap) or
            (old_when and new_has_year and event_overlap) or
            (new_when and old_when and event_overlap)
        )
        
        return temporal_circular
    
    def _check_keyword_circular(self, new_pattern: QuestionPattern, existing_pattern: QuestionPattern) -> CircularDetectionResult:
        """检查关键词级别的循环"""
        # 检查关键词完全包含关系
        new_keywords = new_pattern.keywords
        old_keywords = existing_pattern.keywords
        
        # 如果新问题的关键词是旧问题关键词的子集或超集
        if new_keywords <= old_keywords or old_keywords <= new_keywords:
            if len(new_keywords) > 0 and len(old_keywords) > 0:
                return CircularDetectionResult(
                    is_circular=True,
                    similarity_score=0.7,
                    conflict_reason="Keyword subset/superset relationship detected",
                    conflicting_question=existing_pattern.question,
                    suggestions=["Introduce new keywords", "Focus on different aspects", "Change the scope of inquiry"]
                )
        
        return CircularDetectionResult(is_circular=False, similarity_score=0.0, conflict_reason="No keyword circular")
    
    def get_detection_summary(self) -> Dict[str, int]:
        """获取检测统计摘要"""
        total_questions = len(self.question_history)
        question_types = {}
        
        for pattern in self.question_history:
            question_types[pattern.question_type] = question_types.get(pattern.question_type, 0) + 1
        
        return {
            'total_questions': total_questions,
            'question_types': question_types,
            'similarity_threshold': self.similarity_threshold,
            'keyword_overlap_threshold': self.keyword_overlap_threshold
        }
    
    def clear_history(self) -> None:
        """清除检测历史"""
        self.question_history.clear()
        logger.info("循环检测历史已清除") 
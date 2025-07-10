"""
Report Quality Evaluation System
独立的报告质量评估系统 - 针对简化报告优化的质量判断
"""

import json
import re
import math
import logging
from typing import Dict, List, Any, Tuple, Set
from dataclasses import dataclass
from collections import Counter
import numpy as np
from pathlib import Path
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

@dataclass
class QualityMetrics:
    """质量指标数据类"""
    relevance_score: float          # 相关性分数 (0-1)
    information_density: float      # 信息密度 (0-1)
    coherence_score: float         # 连贯性分数 (0-1)
    factual_richness: float        # 事实丰富度 (0-1)
    technical_depth: float         # 技术深度 (0-1)
    structural_quality: float      # 结构质量 (0-1)
    overall_score: float           # 综合分数 (0-1)
    grade: str                     # 质量等级 (A/B/C/D/F)

class ReportQualityEvaluator:
    """报告质量评估器 - 针对简化报告优化的评估系统"""
    
    def __init__(self):
        self.initialize_nlp_resources()
        # 调整质量阈值 - 对简化报告更友好
        self.quality_thresholds = {
            'excellent': 0.75,  # A级 (降低)
            'good': 0.60,       # B级 (降低)
            'acceptable': 0.45,  # C级 (降低)
            'poor': 0.30,       # D级 (降低)
            # < 0.30 = F级
        }
        # 调整权重配置 - 更重视内容质量而非相关性匹配
        self.weight_config = {
            'relevance': 0.15,          # 降低相关性权重
            'information_density': 0.25, # 提高信息密度权重
            'coherence': 0.20,          # 提高连贯性权重
            'factual_richness': 0.25,   # 提高事实丰富度权重
            'technical_depth': 0.10,    # 降低技术深度权重
            'structural_quality': 0.05   # 保持结构质量权重
        }
        
        # 扩展技术术语词典
        self.technical_terms = {
            'research': ['study', 'research', 'investigation', 'analysis', 'experiment', 'trial', 'survey', 'examination'],
            'methodology': ['method', 'approach', 'technique', 'procedure', 'algorithm', 'framework', 'model', 'strategy'],
            'data': ['data', 'dataset', 'sample', 'population', 'measurement', 'observation', 'variable', 'metric'],
            'statistics': ['significant', 'correlation', 'regression', 'p-value', 'confidence', 'statistical', 'analysis'],
            'technology': ['system', 'technology', 'platform', 'architecture', 'infrastructure', 'implementation', 'software'],
            'performance': ['performance', 'efficiency', 'optimization', 'accuracy', 'precision', 'recall', 'effectiveness'],
            'academic': ['published', 'journal', 'conference', 'peer-reviewed', 'citation', 'bibliography', 'findings'],
            'domain_specific': ['healthcare', 'medical', 'clinical', 'patient', 'treatment', 'diagnosis', 'therapy']
        }
        
        # 数值模式 (用于识别具体数据)
        self.numerical_patterns = [
            r'\d+\.?\d*\s*%',           # 百分比
            r'\d+\.?\d*\s*[a-zA-Z]+',   # 数字+单位
            r'\$\d+\.?\d*[KMB]?',       # 金额
            r'\d{4}年?',                # 年份
            r'\d+\.?\d*\s*倍',          # 倍数
            r'[+-]?\d+\.?\d*',          # 一般数字
        ]
    
    def initialize_nlp_resources(self):
        """初始化NLP资源"""
        try:
            # 尝试下载必要的NLTK数据
            import ssl
            try:
                _create_unverified_https_context = ssl._create_unverified_context
            except AttributeError:
                pass
            else:
                ssl._create_default_https_context = _create_unverified_https_context
            
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
            self.stop_words = set(stopwords.words('english'))
        except Exception as e:
            logger.warning(f"NLTK资源初始化失败: {e}")
            # 使用简单的停用词列表作为后备
            self.stop_words = set(['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'])
    
    def evaluate_report_quality(self, report_content: str, topic_documents: List[Dict[str, Any]],
                               topic_id: str = None) -> Tuple[QualityMetrics, Dict[str, Any]]:
        """
        综合评估报告质量 - 简化报告友好版本
        
        Args:
            report_content: 报告内容
            topic_documents: 原始主题文档
            topic_id: 主题ID (可选)
        
        Returns:
            (QualityMetrics, 详细分析结果)
        """
        logger.info(f"🔍 开始评估报告质量: {topic_id}")
        
        detailed_analysis = {
            'topic_id': topic_id,
            'report_stats': self._analyze_basic_stats(report_content),
            'relevance_analysis': {},
            'information_analysis': {},
            'coherence_analysis': {},
            'factual_analysis': {},
            'technical_analysis': {},
            'structural_analysis': {},
            'recommendations': []
        }
        
        # 1. 相关性评估 - 简化报告优化版本
        relevance_score, relevance_details = self._evaluate_relevance_optimized(report_content, topic_documents)
        detailed_analysis['relevance_analysis'] = relevance_details
        
        # 2. 信息密度评估 - 增强版本
        info_density, info_details = self._evaluate_information_density_enhanced(report_content)
        detailed_analysis['information_analysis'] = info_details
        
        # 3. 连贯性评估 - 更灵活的标准
        coherence_score, coherence_details = self._evaluate_coherence_flexible(report_content)
        detailed_analysis['coherence_analysis'] = coherence_details
        
        # 4. 事实丰富度评估 - 更注重质量而非数量
        factual_richness, factual_details = self._evaluate_factual_richness_enhanced(report_content)
        detailed_analysis['factual_analysis'] = factual_details
        
        # 5. 技术深度评估 - 降低要求
        technical_depth, technical_details = self._evaluate_technical_depth_balanced(report_content)
        detailed_analysis['technical_analysis'] = technical_details
        
        # 6. 结构质量评估 - 更适合简化报告
        structural_quality, structural_details = self._evaluate_structural_quality_simplified(report_content)
        detailed_analysis['structural_analysis'] = structural_details
        
        # 计算综合分数
        overall_score = (
            relevance_score * self.weight_config['relevance'] +
            info_density * self.weight_config['information_density'] +
            coherence_score * self.weight_config['coherence'] +
            factual_richness * self.weight_config['factual_richness'] +
            technical_depth * self.weight_config['technical_depth'] +
            structural_quality * self.weight_config['structural_quality']
        )
        
        # 确定质量等级
        grade = self._determine_quality_grade(overall_score)
        
        # 生成改进建议
        recommendations = self._generate_improvement_recommendations(detailed_analysis, overall_score)
        detailed_analysis['recommendations'] = recommendations
        
        metrics = QualityMetrics(
            relevance_score=relevance_score,
            information_density=info_density,
            coherence_score=coherence_score,
            factual_richness=factual_richness,
            technical_depth=technical_depth,
            structural_quality=structural_quality,
            overall_score=overall_score,
            grade=grade
        )
        
        logger.info(f"✅ 质量评估完成: {grade}级 (分数: {overall_score:.3f})")
        logger.info(f"  keyword_matching: {relevance_details.get('keyword_overlap_ratio', 0.0):.3f}")
        logger.info(f"  tfidf_similarity: {relevance_details.get('tfidf_similarity', 0.0):.3f}")
        logger.info(f"  semantic_overlap: {relevance_details.get('semantic_overlap', 0.0):.3f}")
        logger.info(f"  entity_consistency: {relevance_details.get('entity_consistency', 0.0):.3f}")
        
        return metrics, detailed_analysis
    
    def _analyze_basic_stats(self, text: str) -> Dict[str, Any]:
        """分析文本基本统计信息"""
        try:
            sentences = sent_tokenize(text)
            words = word_tokenize(text.lower())
            non_stop_words = [w for w in words if w.isalpha() and w not in self.stop_words]
        except:
            # NLTK故障时的简单后备方案
            sentences = text.split('.')
            words = text.lower().split()
            non_stop_words = [w for w in words if w.isalpha() and len(w) > 2]
        
        return {
            'total_chars': len(text),
            'total_words': len(words),
            'total_sentences': len(sentences),
            'unique_words': len(set(non_stop_words)),
            'avg_sentence_length': len(words) / max(len(sentences), 1),
            'vocabulary_richness': len(set(non_stop_words)) / max(len(non_stop_words), 1)
        }
    
    def _evaluate_relevance_optimized(self, report: str, documents: List[Dict[str, Any]]) -> Tuple[float, Dict[str, Any]]:
        """评估报告与原始文档的相关性 - 简化报告优化版本"""
        try:
            # 提取原始文档文本
            doc_texts = []
            for doc in documents:
                content = doc.get('content', '')
                if content:
                    doc_texts.append(content)
            
            if not doc_texts:
                return 0.5, {'error': '没有可用的原始文档', 'fallback_score': 0.5}
            
            # 合并所有文档
            combined_docs = ' '.join(doc_texts)
            
            # 1. 关键词重叠分析 - 更宽松
            report_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', report.lower()))
            doc_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', combined_docs.lower()))
            
            # 过滤常见词汇
            common_words = ['the', 'and', 'that', 'this', 'with', 'from', 'they', 'were', 'been', 'have']
            report_words -= set(common_words)
            doc_words -= set(common_words)
            
            if report_words and doc_words:
                overlap = len(report_words.intersection(doc_words))
                # 使用更友好的计算：重叠词 / 报告词汇数
                keyword_overlap_ratio = overlap / len(report_words)
            else:
                keyword_overlap_ratio = 0.0
            
            # 2. TF-IDF相似度 - 更宽松的参数
            tfidf_similarity = 0.0
            try:
                vectorizer = TfidfVectorizer(
                    max_features=300,  # 减少特征数
                    stop_words='english',
                    ngram_range=(1, 1),  # 只使用单词
                    min_df=1,  # 允许低频词
                    max_df=0.95  # 允许高频词
                )
                
                corpus = [report, combined_docs]
                tfidf_matrix = vectorizer.fit_transform(corpus)
                if tfidf_matrix.shape[0] >= 2:
                    tfidf_similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            except Exception as e:
                logger.warning(f"TF-IDF计算失败: {e}")
                tfidf_similarity = 0.0
            
            # 3. 语义重叠 - 基于概念而非字面匹配
            semantic_overlap = self._calculate_semantic_overlap(report, combined_docs)
            
            # 4. 实体一致性 - 专有名词匹配
            entity_consistency = self._calculate_entity_consistency(report, combined_docs)
            
            # 综合相关性分数 - 给语义重叠更高权重
            relevance_score = (
                keyword_overlap_ratio * 0.25 +
                tfidf_similarity * 0.25 +
                semantic_overlap * 0.35 +
                entity_consistency * 0.15
            )
            
            details = {
                'keyword_overlap_ratio': keyword_overlap_ratio,
                'tfidf_similarity': tfidf_similarity,
                'semantic_overlap': semantic_overlap,
                'entity_consistency': entity_consistency,
                'combined_relevance': relevance_score,
                'relevance_level': 'High' if relevance_score > 0.6 else 'Medium' if relevance_score > 0.3 else 'Low'
            }
            
            return min(relevance_score, 1.0), details
            
        except Exception as e:
            logger.error(f"相关性评估失败: {e}")
            return 0.4, {'error': str(e), 'fallback_used': True}
    
    def _calculate_semantic_overlap(self, report: str, documents: str) -> float:
        """计算语义重叠 - 基于概念而非字面匹配"""
        # 提取数字信息
        report_numbers = set(re.findall(r'\d+\.?\d*(?:\s*%)?', report))
        doc_numbers = set(re.findall(r'\d+\.?\d*(?:\s*%)?', documents))
        number_overlap = len(report_numbers.intersection(doc_numbers)) / max(len(report_numbers), 1) if report_numbers else 0
        
        # 提取技术概念
        tech_concepts = []
        for category, terms in self.technical_terms.items():
            tech_concepts.extend(terms)
        
        report_tech = set(word for word in tech_concepts if word in report.lower())
        doc_tech = set(word for word in tech_concepts if word in documents.lower())
        tech_overlap = len(report_tech.intersection(doc_tech)) / max(len(report_tech), 1) if report_tech else 0
        
        # 提取年份信息
        report_years = set(re.findall(r'\b(19|20)\d{2}\b', report))
        doc_years = set(re.findall(r'\b(19|20)\d{2}\b', documents))
        year_overlap = len(report_years.intersection(doc_years)) / max(len(report_years), 1) if report_years else 0
        
        # 综合语义重叠分数
        semantic_score = (number_overlap * 0.4 + tech_overlap * 0.4 + year_overlap * 0.2)
        return min(semantic_score, 1.0)
    
    def _calculate_entity_consistency(self, report: str, documents: str) -> float:
        """计算实体一致性"""
        # 提取专有名词
        report_entities = set(re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', report))
        doc_entities = set(re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', documents))
        
        if not report_entities:
            return 0.5  # 中性分数
        
        entity_overlap = len(report_entities.intersection(doc_entities))
        return entity_overlap / len(report_entities)
    
    def _evaluate_information_density_enhanced(self, text: str) -> Tuple[float, Dict[str, Any]]:
        """评估信息密度 - 增强版本"""
        # 识别信息性内容
        numerical_count = len(re.findall(r'\d+\.?\d*', text))
        factual_indicators = ['research', 'study', 'analysis', 'data', 'result', 'finding', 'evidence', 'showed', 'found']
        factual_count = sum(text.lower().count(word) for word in factual_indicators)
        
        # 识别具体细节
        specific_patterns = [
            r'\d{4}年?',           # 年份
            r'\d+\.?\d*\s*%',      # 百分比
            r'\d+\.?\d*\s*[a-zA-Z]+', # 数字+单位
            r'[A-Z][a-z]+\s+et\s+al\.', # 作者引用
            r'\b[A-Z][a-z]+\s+(University|Institute|Hospital)', # 机构名称
        ]
        
        specific_details = sum(len(re.findall(pattern, text)) for pattern in specific_patterns)
        
        # 计算密度分数 - 更友好的计算方式
        text_length = len(text.split())
        if text_length == 0:
            return 0.0, {'error': '文本为空'}
        
        # 基础信息密度
        base_density = (numerical_count + factual_count + specific_details) / text_length
        # 归一化到0-1区间，但给较小的文本更多容忍度
        info_density = min(base_density * 8, 1.0)  # 调整系数
        
        details = {
            'numerical_elements': numerical_count,
            'factual_indicators': factual_count,
            'specific_details': specific_details,
            'total_words': text_length,
            'density_ratio': info_density,
            'density_level': 'High' if info_density > 0.5 else 'Medium' if info_density > 0.25 else 'Low'
        }
        
        return info_density, details
    
    def _evaluate_coherence_flexible(self, text: str) -> Tuple[float, Dict[str, Any]]:
        """评估文本连贯性 - 更灵活的标准"""
        try:
            sentences = sent_tokenize(text)
        except:
            sentences = text.split('.')
        
        if len(sentences) < 2:
            return 0.7, {'warning': '句子数量不足，给予中等分数'}
        
        # 基础连贯性 - 简化报告通常较短，给予基础分数
        base_coherence = 0.6
        
        # 连接词分析 - 降低要求
        connectives = ['however', 'furthermore', 'moreover', 'therefore', 'thus', 'consequently', 
                      'additionally', 'meanwhile', 'similarly', 'also', 'but', 'and', 'while']
        connective_count = sum(text.lower().count(conn) for conn in connectives)
        connective_bonus = min(connective_count / len(sentences) * 0.3, 0.2)
        
        # 主题词重复分析 - 更宽松
        sentence_words = []
        for sent in sentences:
            try:
                words = word_tokenize(sent.lower())
            except:
                words = sent.lower().split()
            content_words = [w for w in words if w.isalpha() and w not in self.stop_words and len(w) > 3]
            sentence_words.append(set(content_words))
        
        # 计算相邻句子的词汇重叠
        overlaps = []
        for i in range(len(sentence_words) - 1):
            overlap = len(sentence_words[i].intersection(sentence_words[i + 1]))
            total_words = len(sentence_words[i].union(sentence_words[i + 1]))
            if total_words > 0:
                overlaps.append(overlap / total_words)
        
        avg_overlap = sum(overlaps) / max(len(overlaps), 1)
        overlap_bonus = avg_overlap * 0.2
        
        # 综合连贯性分数
        coherence_score = base_coherence + connective_bonus + overlap_bonus
        
        details = {
            'connective_count': connective_count,
            'avg_sentence_overlap': avg_overlap,
            'sentence_count': len(sentences),
            'base_coherence': base_coherence,
            'coherence_level': 'High' if coherence_score > 0.7 else 'Medium' if coherence_score > 0.5 else 'Low'
        }
        
        return min(coherence_score, 1.0), details
    
    def _evaluate_factual_richness_enhanced(self, text: str) -> Tuple[float, Dict[str, Any]]:
        """评估事实丰富度 - 更注重质量而非数量"""
        factual_elements = {
            'numbers': len(re.findall(r'\d+\.?\d*', text)),
            'percentages': len(re.findall(r'\d+\.?\d*\s*%', text)),
            'years': len(re.findall(r'\b(19|20)\d{2}\b', text)),
            'measurements': len(re.findall(r'\d+\.?\d*\s*(kg|km|cm|mm|ml|gb|mb|hz|mhz)', text, re.IGNORECASE)),
            'citations': len(re.findall(r'[A-Z][a-z]+\s+et\s+al\.', text)),
            'institutions': len(re.findall(r'\b(University|Institute|Laboratory|College|School|Hospital)\b', text, re.IGNORECASE)),
        }
        
        # 识别技术术语 - 更智能的计算
        tech_score = 0
        for category, terms in self.technical_terms.items():
            category_count = sum(1 for term in terms if term in text.lower())
            # 给每个类别最多贡献1分，避免单一类别过度计分
            tech_score += min(category_count, 1)
        
        factual_elements['technical_terms'] = tech_score
        
        # 计算总分 - 更平衡的计算方式
        # 给不同类型的事实元素不同权重
        weighted_elements = (
            factual_elements['numbers'] * 1.5 +
            factual_elements['percentages'] * 2.0 +
            factual_elements['years'] * 1.5 +
            factual_elements['measurements'] * 2.0 +
            factual_elements['citations'] * 2.5 +
            factual_elements['institutions'] * 2.0 +
            factual_elements['technical_terms'] * 1.0
        )
        
        text_length = len(text.split())
        if text_length == 0:
            return 0.0, {'error': '文本为空'}
        
        # 更友好的丰富度计算
        richness_score = min(weighted_elements / text_length * 3, 1.0)
        
        details = factual_elements.copy()
        details.update({
            'weighted_factual_score': weighted_elements,
            'text_length': text_length,
            'richness_ratio': richness_score,
            'richness_level': 'High' if richness_score > 0.4 else 'Medium' if richness_score > 0.2 else 'Low'
        })
        
        return richness_score, details
    
    def _evaluate_technical_depth_balanced(self, text: str) -> Tuple[float, Dict[str, Any]]:
        """评估技术深度 - 平衡要求，适合简化报告"""
        depth_indicators = {
            'methodology_terms': 0,
            'analysis_terms': 0,
            'research_terms': 0,
            'statistical_terms': 0,
            'domain_terms': 0
        }
        
        # 方法论术语 - 检查存在而非计数
        methodology_words = ['algorithm', 'framework', 'methodology', 'approach', 'technique', 'procedure', 'protocol', 'method']
        depth_indicators['methodology_terms'] = min(sum(1 for word in methodology_words if word in text.lower()), 3)
        
        # 分析术语
        analysis_words = ['analysis', 'evaluation', 'assessment', 'comparison', 'validation', 'verification', 'examined']
        depth_indicators['analysis_terms'] = min(sum(1 for word in analysis_words if word in text.lower()), 3)
        
        # 研究术语
        research_words = ['hypothesis', 'experiment', 'observation', 'measurement', 'investigation', 'study', 'research']
        depth_indicators['research_terms'] = min(sum(1 for word in research_words if word in text.lower()), 3)
        
        # 统计术语
        statistical_words = ['significant', 'correlation', 'regression', 'p-value', 'confidence', 'variance', 'statistical']
        depth_indicators['statistical_terms'] = min(sum(1 for word in statistical_words if word in text.lower()), 3)
        
        # 领域特定术语
        domain_words = ['clinical', 'medical', 'healthcare', 'patient', 'treatment', 'diagnosis', 'therapeutic']
        depth_indicators['domain_terms'] = min(sum(1 for word in domain_words if word in text.lower()), 3)
        
        # 计算技术深度分数 - 更宽松的标准
        total_depth_elements = sum(depth_indicators.values())
        
        # 基础技术深度分数
        base_depth = 0.4  # 给简化报告基础分数
        
        # 额外技术深度奖励
        if total_depth_elements > 0:
            depth_bonus = min(total_depth_elements / 10, 0.6)  # 最多奖励0.6分
        else:
            depth_bonus = 0
        
        depth_score = base_depth + depth_bonus
        
        details = depth_indicators.copy()
        details.update({
            'total_depth_elements': total_depth_elements,
            'base_depth': base_depth,
            'depth_bonus': depth_bonus,
            'depth_ratio': depth_score,
            'depth_level': 'High' if depth_score > 0.7 else 'Medium' if depth_score > 0.5 else 'Low'
        })
        
        return min(depth_score, 1.0), details
    
    def _evaluate_structural_quality_simplified(self, text: str) -> Tuple[float, Dict[str, Any]]:
        """评估结构质量 - 简化报告友好版本"""
        # 检查不良结构化标记 - 简化报告应该避免这些
        bad_structures = [
            'abstract:', 'introduction:', 'conclusion:', 'summary:',
            '## abstract', '## introduction', '## conclusion', '## summary',
            '1. introduction', '2. methodology', '3. results', '4. conclusion'
        ]
        
        bad_structure_count = sum(text.lower().count(marker) for marker in bad_structures)
        
        # 基础结构分数 - 简化报告给予更高基础分数
        base_structure_score = 0.8
        
        # 结构惩罚 - 每个学术结构标记扣分
        structure_penalty = min(bad_structure_count * 0.3, 0.6)
        
        # 句子长度分析 - 更宽松的标准
        try:
            sentences = sent_tokenize(text)
        except:
            sentences = [s.strip() for s in text.split('.') if s.strip()]
        
        if sentences:
            sentence_lengths = [len(s.split()) for s in sentences]
            avg_sentence_length = sum(sentence_lengths) / len(sentence_lengths)
            
            # 简化报告的理想句子长度：10-30词
            if 10 <= avg_sentence_length <= 30:
                sentence_bonus = 0.1
            elif 5 <= avg_sentence_length <= 35:
                sentence_bonus = 0.05
            else:
                sentence_bonus = 0
        else:
            avg_sentence_length = 0
            sentence_bonus = 0
        
        # 流畅性奖励 - 检查自然的连接
        flow_indicators = ['the', 'this', 'these', 'that', 'it', 'they', 'also', 'however', 'therefore']
        flow_count = sum(1 for indicator in flow_indicators if indicator in text.lower())
        flow_bonus = min(flow_count / len(text.split()) * 5, 0.1)
        
        # 计算最终结构质量分数
        structural_quality = base_structure_score - structure_penalty + sentence_bonus + flow_bonus
        
        details = {
            'bad_structure_count': bad_structure_count,
            'sentence_count': len(sentences),
            'avg_sentence_length': avg_sentence_length,
            'base_structure_score': base_structure_score,
            'structure_penalty': structure_penalty,
            'sentence_bonus': sentence_bonus,
            'flow_bonus': flow_bonus,
            'quality_level': 'High' if structural_quality > 0.8 else 'Medium' if structural_quality > 0.6 else 'Low'
        }
        
        return min(structural_quality, 1.0), details
    
    def _determine_quality_grade(self, score: float) -> str:
        """根据分数确定质量等级"""
        if score >= self.quality_thresholds['excellent']:
            return 'A'
        elif score >= self.quality_thresholds['good']:
            return 'B'
        elif score >= self.quality_thresholds['acceptable']:
            return 'C'
        elif score >= self.quality_thresholds['poor']:
            return 'D'
        else:
            return 'F'
    
    def _generate_improvement_recommendations(self, analysis: Dict[str, Any], overall_score: float) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        # 相关性建议
        if analysis['relevance_analysis'].get('cosine_similarity', 0) < 0.5:
            recommendations.append("提高内容相关性: 更多引用和整合原始文档的核心概念")
        
        # 信息密度建议
        if analysis['information_analysis'].get('density_ratio', 0) < 0.4:
            recommendations.append("增加信息密度: 添加更多具体数据、统计数字和事实细节")
        
        # 连贯性建议
        if analysis['coherence_analysis'].get('avg_sentence_overlap', 0) < 0.3:
            recommendations.append("改善文本连贯性: 使用更多连接词和保持主题一致性")
        
        # 事实丰富度建议
        if analysis['factual_analysis'].get('richness_ratio', 0) < 0.4:
            recommendations.append("增强事实丰富度: 包含更多数字、年份、机构名称等具体信息")
        
        # 技术深度建议
        if analysis['technical_analysis'].get('depth_ratio', 0) < 0.4:
            recommendations.append("提升技术深度: 使用更多专业术语和方法论概念")
        
        # 结构质量建议
        if analysis['structural_analysis'].get('bad_structure_count', 0) > 0:
            recommendations.append("改善结构质量: 避免使用正式学术结构标记，采用自然流畅的叙述")
        
        # 综合建议
        if overall_score < 0.6:
            recommendations.append("整体优化: 建议重新生成报告，重点关注内容相关性和信息密度")
        
        return recommendations if recommendations else ["质量良好，无需特别改进"]


class TopicRelevanceAnalyzer:
    """主题相关性分析器 - 专门分析内容与主题的相关度"""
    
    def __init__(self):
        self.relevance_algorithms = {
            'keyword_matching': self._keyword_matching_relevance,
            'tfidf_similarity': self._tfidf_similarity_relevance,
            'semantic_overlap': self._semantic_overlap_relevance,
            'entity_consistency': self._entity_consistency_relevance
        }
    
    def analyze_topic_relevance(self, report: str, documents: List[Dict], topic_id: str) -> Dict[str, Any]:
        """分析报告与主题的相关性"""
        relevance_scores = {}
        detailed_analysis = {
            'topic_id': topic_id,
            'algorithms_used': list(self.relevance_algorithms.keys()),
            'individual_scores': {},
            'weighted_average': 0.0,
            'relevance_level': 'Unknown'
        }
        
        # 应用所有相关性算法
        for algorithm_name, algorithm_func in self.relevance_algorithms.items():
            try:
                score = algorithm_func(report, documents)
                relevance_scores[algorithm_name] = score
                detailed_analysis['individual_scores'][algorithm_name] = score
                logger.info(f"  {algorithm_name}: {score:.3f}")
            except Exception as e:
                logger.error(f"相关性算法 {algorithm_name} 失败: {e}")
                relevance_scores[algorithm_name] = 0.0
                detailed_analysis['individual_scores'][algorithm_name] = 0.0
        
        # 计算加权平均
        weights = {
            'keyword_matching': 0.25,
            'tfidf_similarity': 0.35,
            'semantic_overlap': 0.25,
            'entity_consistency': 0.15
        }
        
        weighted_average = sum(
            relevance_scores.get(alg, 0) * weights.get(alg, 0) 
            for alg in weights.keys()
        )
        
        detailed_analysis['weighted_average'] = weighted_average
        detailed_analysis['relevance_level'] = (
            'High' if weighted_average > 0.7 else
            'Medium' if weighted_average > 0.4 else
            'Low'
        )
        
        return detailed_analysis
    
    def _keyword_matching_relevance(self, report: str, documents: List[Dict]) -> float:
        """基于关键词匹配的相关性分析 - 优化版本"""
        # 提取文档关键词 (优化：过滤常见词，关注实质内容)
        doc_words = set()
        for doc in documents:
            content = doc.get('content', '').lower()
            words = re.findall(r'\b[a-zA-Z]{4,}\b', content)  # 增加到4个字符以上
            # 过滤更多停用词
            filtered_words = [w for w in words if w not in {
                'that', 'this', 'with', 'from', 'they', 'were', 'been', 'have', 
                'their', 'would', 'there', 'could', 'other', 'after', 'first',
                'also', 'time', 'very', 'what', 'know', 'just', 'into', 'over',
                'think', 'about', 'through', 'should', 'before', 'here', 'how'
            }]
            doc_words.update(filtered_words)
        
        # 提取报告关键词
        report_words = set(re.findall(r'\b[a-zA-Z]{4,}\b', report.lower()))
        report_words = {w for w in report_words if w not in {
            'that', 'this', 'with', 'from', 'they', 'were', 'been', 'have', 
            'their', 'would', 'there', 'could', 'other', 'after', 'first',
            'also', 'time', 'very', 'what', 'know', 'just', 'into', 'over',
            'think', 'about', 'through', 'should', 'before', 'here', 'how'
        }}
        
        # 计算Jaccard相似度，但给重叠更高权重
        if not doc_words or not report_words:
            return 0.0
        
        overlap = len(doc_words.intersection(report_words))
        # 使用更友好的计算方式：重叠词 / 较小集合大小
        denominator = min(len(doc_words), len(report_words))
        
        return overlap / denominator if denominator > 0 else 0.0
    
    def _tfidf_similarity_relevance(self, report: str, documents: List[Dict]) -> float:
        """基于TF-IDF相似度的相关性分析"""
        try:
            doc_texts = [doc.get('content', '') for doc in documents if doc.get('content')]
            if not doc_texts:
                return 0.0
            
            combined_docs = ' '.join(doc_texts)
            corpus = [report, combined_docs]
            
            vectorizer = TfidfVectorizer(
                max_features=500,
                stop_words='english',
                ngram_range=(1, 2)
            )
            
            tfidf_matrix = vectorizer.fit_transform(corpus)
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            
            return similarity
        except Exception as e:
            logger.error(f"TF-IDF相似度计算失败: {e}")
            return 0.0
    
    def _semantic_overlap_relevance(self, report: str, documents: List[Dict]) -> float:
        """基于语义重叠的相关性分析"""
        # 简化的语义分析 - 基于命名实体和专业术语
        
        # 提取数字和专业概念
        numerical_entities = re.findall(r'\d+\.?\d*(?:\s*%|\s*[a-zA-Z]+)?', report)
        tech_terms = re.findall(r'\b(?:algorithm|method|system|analysis|study|research|data|model)\w*\b', 
                               report.lower())
        
        doc_numerical = []
        doc_tech = []
        for doc in documents:
            content = doc.get('content', '')
            doc_numerical.extend(re.findall(r'\d+\.?\d*(?:\s*%|\s*[a-zA-Z]+)?', content))
            doc_tech.extend(re.findall(r'\b(?:algorithm|method|system|analysis|study|research|data|model)\w*\b', 
                                     content.lower()))
        
        # 计算概念重叠
        numerical_overlap = len(set(numerical_entities).intersection(set(doc_numerical)))
        tech_overlap = len(set(tech_terms).intersection(set(doc_tech)))
        
        total_report_concepts = len(set(numerical_entities + tech_terms))
        total_overlaps = numerical_overlap + tech_overlap
        
        return total_overlaps / max(total_report_concepts, 1)
    
    def _entity_consistency_relevance(self, report: str, documents: List[Dict]) -> float:
        """基于实体一致性的相关性分析"""
        # 提取专有名词和机构名称
        report_entities = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', report)
        
        doc_entities = []
        for doc in documents:
            content = doc.get('content', '')
            entities = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', content)
            doc_entities.extend(entities)
        
        if not report_entities or not doc_entities:
            return 0.5  # 中性分数
        
        # 计算实体重叠
        common_entities = set(report_entities).intersection(set(doc_entities))
        total_entities = set(report_entities).union(set(doc_entities))
        
        return len(common_entities) / len(total_entities) if total_entities else 0.0


def test_report_quality_evaluation():
    """测试报告质量评估系统"""
    print("=== 报告质量评估系统测试 ===")
    
    # 测试数据
    test_report = """
    This study presents a comprehensive analysis of machine learning algorithms 
    for predictive modeling in healthcare applications. The research involved 
    1,200 patients from Stanford University Hospital and achieved 94.2% accuracy 
    using a deep neural network approach. The methodology included data preprocessing, 
    feature selection, and cross-validation techniques. Statistical significance 
    was confirmed with p < 0.001. The results demonstrate significant improvements 
    over traditional methods, with 15% better performance compared to logistic regression.
    """
    
    test_documents = [
        {"content": "Healthcare machine learning study with 1200 patients at Stanford Hospital"},
        {"content": "Deep neural networks achieved 94.2% accuracy in medical prediction tasks"},
        {"content": "Statistical analysis showed p < 0.001 significance in healthcare ML research"}
    ]
    
    # 创建评估器
    evaluator = ReportQualityEvaluator()
    
    # 执行评估
    metrics, analysis = evaluator.evaluate_report_quality(
        test_report, test_documents, "test_topic"
    )
    
    print(f"整体评分: {metrics.overall_score:.3f} ({metrics.grade}级)")
    print(f"相关性: {metrics.relevance_score:.3f}")
    print(f"信息密度: {metrics.information_density:.3f}")
    print(f"连贯性: {metrics.coherence_score:.3f}")
    print(f"事实丰富度: {metrics.factual_richness:.3f}")
    print(f"技术深度: {metrics.technical_depth:.3f}")
    print(f"结构质量: {metrics.structural_quality:.3f}")
    
    print("\n改进建议:")
    for i, rec in enumerate(analysis['recommendations'], 1):
        print(f"{i}. {rec}")

if __name__ == "__main__":
    test_report_quality_evaluation() 
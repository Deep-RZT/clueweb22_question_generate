#!/usr/bin/env python3
"""
Topic-Based Data Loader for ClueWeb22
=====================================

正确的topic-based数据加载器，支持：
1. 按topic组织数据（每个topic包含100个txt文档）
2. 智能文档过滤和清洗
3. 多文档融合预处理

作者: Assistant
日期: 2025-01-07
版本: v1.0 Topic-Based Implementation
"""

import os
import re
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict

from document_content_filter import DocumentContentFilter

logger = logging.getLogger(__name__)

class TopicBasedDataLoader:
    """基于Topic的ClueWeb22数据加载器"""
    
    def __init__(self, data_dir: str = None):
        """
        初始化数据加载器
        
        Args:
            data_dir: ClueWeb22数据目录路径，如果为None则自动计算
        """
        if data_dir is None:
            # 自动计算数据目录路径
            # 当前文件位于 experiments/06_short_answer_deep_query/topic_based_data_loader.py
            # 数据位于 data/task_file/clueweb22_query_results
            current_file = Path(__file__).resolve()
            project_root = current_file.parent.parent.parent  # 向上3层到项目根目录
            data_dir = project_root / "data" / "task_file" / "clueweb22_query_results"
        
        self.data_dir = Path(data_dir)
        self.content_filter = DocumentContentFilter()
        
        # 验证数据目录
        if not self.data_dir.exists():
            # 如果计算的路径不存在，尝试其他可能的路径
            alternative_paths = [
                "../../data/task_file/clueweb22_query_results",
                "../../../data/task_file/clueweb22_query_results", 
                "data/task_file/clueweb22_query_results",
                "./data/task_file/clueweb22_query_results"
            ]
            
            for alt_path in alternative_paths:
                alt_data_dir = Path(alt_path)
                if alt_data_dir.exists():
                    self.data_dir = alt_data_dir
                    break
            else:
                raise FileNotFoundError(f"数据目录不存在: {self.data_dir}")
        
        logger.info(f"Topic数据加载器初始化完成，数据目录: {self.data_dir}")
    
    def extract_topic_from_filename(self, filename: str) -> Optional[str]:
        """从文件名提取topic ID"""
        # 文件名格式: clueweb22-ja0009-18-07874_top000.txt
        pattern = r'^(clueweb22-[a-z]{2}\d{4}-\d{2}-\d{5})_top\d{3}\.txt$'
        match = re.match(pattern, filename)
        
        if match:
            return match.group(1)
        return None
    
    def get_available_topics(self) -> List[str]:
        """获取所有可用的topic列表"""
        topics = set()
        
        for txt_file in self.data_dir.glob("*.txt"):
            topic_id = self.extract_topic_from_filename(txt_file.name)
            if topic_id:
                topics.add(topic_id)
        
        sorted_topics = sorted(list(topics))
        logger.info(f"发现 {len(sorted_topics)} 个topics")
        
        return sorted_topics
    
    def load_topic_documents(self, topic_id: str) -> List[Dict[str, Any]]:
        """加载指定topic的所有文档"""
        documents = []
        
        # 查找该topic的所有文档文件
        topic_pattern = f"{topic_id}_top*.txt"
        topic_files = list(self.data_dir.glob(topic_pattern))
        
        if not topic_files:
            logger.warning(f"未找到topic {topic_id} 的文档文件")
            return documents
        
        logger.info(f"加载topic {topic_id}，找到 {len(topic_files)} 个文档文件")
        
        for txt_file in sorted(topic_files):
            try:
                # 从文件名提取文档序号
                doc_match = re.search(r'_top(\d{3})\.txt$', txt_file.name)
                doc_num = doc_match.group(1) if doc_match else "000"
                
                # 读取文档内容
                with open(txt_file, 'r', encoding='utf-8', errors='ignore') as f:
                    raw_content = f.read()
                
                # 基本内容验证
                if len(raw_content.strip()) < 50:  # 跳过太短的文档
                    logger.debug(f"跳过过短文档: {txt_file.name}")
                    continue
                
                # 构建文档对象
                document = {
                    'doc_id': f"{topic_id}_top{doc_num}",
                    'topic_id': topic_id,
                    'doc_number': int(doc_num),
                    'source_file': str(txt_file),
                    'content': raw_content,
                    'char_count': len(raw_content),
                    'word_count': len(raw_content.split())
                }
                
                documents.append(document)
                
            except Exception as e:
                logger.warning(f"加载文档失败 {txt_file}: {e}")
                continue
        
        logger.info(f"成功加载topic {topic_id} 的 {len(documents)} 个文档")
        return documents
    
    def filter_and_process_topic_documents(self, topic_id: str, 
                                         min_value_score: float = 0.1,
                                         target_total_length: int = 50000) -> Dict[str, Any]:
        """过滤和处理topic的所有文档"""
        # 加载原始文档
        raw_documents = self.load_topic_documents(topic_id)
        
        if not raw_documents:
            return {
                'topic_id': topic_id,
                'success': False,
                'error': 'No documents found',
                'documents': [],
                'filtered_documents': [],
                'processing_stats': {}
            }
        
        # 使用文档过滤器处理
        logger.info(f"开始过滤和处理topic {topic_id} 的 {len(raw_documents)} 个文档")
        
        try:
            # 应用文档过滤器
            filtered_documents = self.content_filter.filter_documents(
                raw_documents,
                min_value_score=min_value_score,
                target_length=target_total_length
            )
            
            # 计算处理统计
            processing_stats = self.content_filter.get_filtering_stats(raw_documents, filtered_documents)
            
            # 提取合并的关键信息
            merged_key_info = self._merge_key_information(filtered_documents)
            
            result = {
                'topic_id': topic_id,
                'success': True,
                'documents': raw_documents,
                'filtered_documents': filtered_documents,
                'processing_stats': processing_stats,
                'merged_key_information': merged_key_info,
                'total_original_chars': sum(doc.get('char_count', 0) for doc in raw_documents),
                'total_filtered_chars': sum(doc.get('char_count', 0) for doc in filtered_documents),
                'document_count': {
                    'original': len(raw_documents),
                    'filtered': len(filtered_documents)
                }
            }
            
            logger.info(f"Topic {topic_id} 处理完成:")
            logger.info(f"  原始文档: {len(raw_documents)} -> 过滤后: {len(filtered_documents)}")
            logger.info(f"  原始字符: {result['total_original_chars']:,} -> 过滤后: {result['total_filtered_chars']:,}")
            logger.info(f"  保留率: {processing_stats['retention_rate']:.1%}")
            
            return result
            
        except Exception as e:
            logger.error(f"处理topic {topic_id} 时出错: {e}")
            return {
                'topic_id': topic_id,
                'success': False,
                'error': str(e),
                'documents': raw_documents,
                'filtered_documents': [],
                'processing_stats': {}
            }
    
    def _merge_key_information(self, documents: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """合并多个文档的关键信息"""
        merged_info = {
            'numerical_data': set(),
            'technical_terms': set(),
            'institutions': set(),
            'methodologies': set(),
            'findings': set()
        }
        
        for doc in documents:
            key_info = doc.get('key_information', {})
            for category, items in key_info.items():
                if category in merged_info and isinstance(items, list):
                    merged_info[category].update(items)
        
        # 转换为列表并限制数量
        result = {}
        for category, items in merged_info.items():
            result[category] = list(items)[:20]  # 每类最多保留20个
        
        return result
    
    def load_multiple_topics(self, topic_ids: List[str], 
                           min_value_score: float = 0.1,
                           target_total_length: int = 50000) -> Dict[str, Dict[str, Any]]:
        """批量加载多个topics"""
        results = {}
        
        logger.info(f"开始批量加载 {len(topic_ids)} 个topics")
        
        for i, topic_id in enumerate(topic_ids, 1):
            logger.info(f"处理进度 {i}/{len(topic_ids)}: {topic_id}")
            
            topic_result = self.filter_and_process_topic_documents(
                topic_id, 
                min_value_score=min_value_score,
                target_total_length=target_total_length
            )
            
            results[topic_id] = topic_result
            
            if topic_result['success']:
                logger.info(f"✅ Topic {topic_id} 处理成功")
            else:
                logger.warning(f"❌ Topic {topic_id} 处理失败: {topic_result.get('error', 'Unknown error')}")
        
        success_count = sum(1 for result in results.values() if result['success'])
        logger.info(f"批量加载完成: {success_count}/{len(topic_ids)} 个topics成功")
        
        return results
    
    def get_topic_summary(self, topic_id: str) -> Dict[str, Any]:
        """获取topic的基本信息摘要"""
        topic_files = list(self.data_dir.glob(f"{topic_id}_top*.txt"))
        
        if not topic_files:
            return {
                'topic_id': topic_id,
                'exists': False,
                'document_count': 0
            }
        
        total_chars = 0
        total_words = 0
        
        for txt_file in topic_files:
            try:
                with open(txt_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    total_chars += len(content)
                    total_words += len(content.split())
            except Exception:
                continue
        
        return {
            'topic_id': topic_id,
            'exists': True,
            'document_count': len(topic_files),
            'total_chars': total_chars,
            'total_words': total_words,
            'avg_chars_per_doc': total_chars // len(topic_files) if topic_files else 0,
            'avg_words_per_doc': total_words // len(topic_files) if topic_files else 0
        }

    def get_topic_full_content_for_fusion(self, topic_id: str, max_total_chars: int = 100000) -> Dict[str, Any]:
        """
        获取topic的完整内容用于LLM融合（不过早丢弃文档）
        
        Args:
            topic_id: Topic ID
            max_total_chars: 最大总字符数限制
            
        Returns:
            包含所有文档内容的字典，用于LLM融合
        """
        # 加载所有原始文档
        raw_documents = self.load_topic_documents(topic_id)
        
        if not raw_documents:
            return {
                'topic_id': topic_id,
                'success': False,
                'error': 'No documents found',
                'full_content': '',
                'document_summaries': [],
                'processing_stats': {}
            }
        
        logger.info(f"准备topic {topic_id} 的完整内容融合，共 {len(raw_documents)} 个文档")
        
        try:
            # 对每个文档进行基本清洗（但不丢弃）
            cleaned_documents = []
            total_chars = 0
            
            for doc in raw_documents:
                # 基本清洗：移除HTML标签，规范化空白字符
                cleaned_content = self.content_filter.clean_text(doc['content'])
                
                # 跳过太短的文档（小于100字符）
                if len(cleaned_content) < 100:
                    continue
                
                # 检查是否超过总字符限制
                if total_chars + len(cleaned_content) > max_total_chars:
                    # 截取剩余部分
                    remaining_chars = max_total_chars - total_chars
                    if remaining_chars > 500:  # 至少保留500字符
                        cleaned_content = cleaned_content[:remaining_chars]
                        # 在句子边界截取
                        last_period = cleaned_content.rfind('.')
                        if last_period > remaining_chars * 0.8:
                            cleaned_content = cleaned_content[:last_period + 1]
                    else:
                        break
                
                doc_summary = {
                    'doc_id': doc['doc_id'],
                    'doc_number': doc['doc_number'],
                    'original_chars': doc['char_count'],
                    'cleaned_chars': len(cleaned_content),
                    'cleaned_content': cleaned_content,
                    'value_score': self.content_filter.calculate_content_value_score(cleaned_content)
                }
                
                cleaned_documents.append(doc_summary)
                total_chars += len(cleaned_content)
                
                # 如果达到限制就停止
                if total_chars >= max_total_chars:
                    break
            
            # 按价值分数排序，确保高质量内容优先
            cleaned_documents.sort(key=lambda x: x['value_score'], reverse=True)
            
            # 合并所有文档内容
            full_content_parts = []
            for i, doc in enumerate(cleaned_documents):
                full_content_parts.append(f"=== Document {i+1} (ID: {doc['doc_id']}) ===")
                full_content_parts.append(doc['cleaned_content'])
                full_content_parts.append("")  # 空行分隔
            
            full_content = '\n'.join(full_content_parts)
            
            # 提取整体关键信息
            overall_key_info = self.content_filter.extract_key_information(full_content)
            
            # 计算处理统计
            processing_stats = {
                'original_documents': len(raw_documents),
                'processed_documents': len(cleaned_documents),
                'retention_rate': len(cleaned_documents) / len(raw_documents) if raw_documents else 0,
                'total_original_chars': sum(doc['char_count'] for doc in raw_documents),
                'total_processed_chars': total_chars,
                'content_compression_rate': total_chars / sum(doc['char_count'] for doc in raw_documents) if raw_documents else 0,
                'avg_value_score': sum(doc['value_score'] for doc in cleaned_documents) / len(cleaned_documents) if cleaned_documents else 0
            }
            
            result = {
                'topic_id': topic_id,
                'success': True,
                'full_content': full_content,
                'document_summaries': cleaned_documents,
                'overall_key_information': overall_key_info,
                'processing_stats': processing_stats,
                'content_stats': {
                    'total_chars': len(full_content),
                    'total_words': len(full_content.split()),
                    'document_count': len(cleaned_documents)
                }
            }
            
            logger.info(f"Topic {topic_id} 内容融合准备完成:")
            logger.info(f"  文档数量: {len(raw_documents)} -> {len(cleaned_documents)}")
            logger.info(f"  总字符数: {processing_stats['total_original_chars']:,} -> {total_chars:,}")
            logger.info(f"  保留率: {processing_stats['retention_rate']:.1%}")
            logger.info(f"  平均价值分数: {processing_stats['avg_value_score']:.3f}")
            
            return result
            
        except Exception as e:
            logger.error(f"准备topic {topic_id} 融合内容时出错: {e}")
            return {
                'topic_id': topic_id,
                'success': False,
                'error': str(e),
                'full_content': '',
                'document_summaries': [],
                'processing_stats': {}
            }

    def get_topic_aggregated_content_for_fusion(self, topic_id: str, max_total_chars: int = 150000) -> Dict[str, Any]:
        """
        更好的融合方法：先集合所有txt内容，再整体筛选，最后LLM融合
        
        Args:
            topic_id: Topic ID
            max_total_chars: 最大总字符数限制
            
        Returns:
            包含聚合和筛选后内容的字典
        """
        # 加载所有原始文档
        raw_documents = self.load_topic_documents(topic_id)
        
        if not raw_documents:
            return {
                'topic_id': topic_id,
                'success': False,
                'error': 'No documents found',
                'aggregated_content': '',
                'processing_stats': {}
            }
        
        logger.info(f"开始聚合topic {topic_id} 的所有内容，共 {len(raw_documents)} 个文档")
        
        try:
            # 步骤1：聚合所有文档的原始内容
            all_content_parts = []
            total_raw_chars = 0
            
            for doc in raw_documents:
                content = doc.get('content', '').strip()
                if len(content) > 50:  # 只跳过极短的内容
                    all_content_parts.append(f"[Document {doc['doc_number']:03d}]")
                    all_content_parts.append(content)
                    all_content_parts.append("")  # 空行分隔
                    total_raw_chars += len(content)
            
            # 合并所有内容
            aggregated_raw_content = '\n'.join(all_content_parts)
            
            logger.info(f"聚合完成: {len(raw_documents)} 个文档 -> {total_raw_chars:,} 字符")
            
            # 步骤2：对整个聚合内容进行清洗
            logger.info("开始整体内容清洗...")
            cleaned_content = self.content_filter.clean_text(aggregated_raw_content)
            
            # 步骤3：提取有价值的句子（基于整体内容）
            logger.info("提取有价值的句子...")
            valuable_sentences = self.content_filter.extract_sentences(cleaned_content)
            
            # 步骤4：去重和优化（跨文档去重）
            logger.info("跨文档去重和优化...")
            unique_sentences = []
            seen_sentences = set()
            
            for sentence in valuable_sentences:
                # 简单的去重：基于句子的核心内容
                sentence_core = ' '.join(sentence.lower().split()[:10])  # 前10个词作为核心
                if sentence_core not in seen_sentences and len(sentence) >= 30:
                    unique_sentences.append(sentence)
                    seen_sentences.add(sentence_core)
            
            # 步骤5：按价值分数排序
            logger.info("按价值分数排序句子...")
            sentence_scores = []
            for sentence in unique_sentences:
                score = self.content_filter.calculate_content_value_score(sentence)
                sentence_scores.append((sentence, score))
            
            # 排序并选择最有价值的句子
            sentence_scores.sort(key=lambda x: x[1], reverse=True)
            
            # 步骤6：构建最终的聚合内容（控制在字符限制内）
            final_sentences = []
            current_chars = 0
            
            for sentence, score in sentence_scores:
                if current_chars + len(sentence) <= max_total_chars:
                    final_sentences.append(sentence)
                    current_chars += len(sentence)
                else:
                    break
            
            # 重新按逻辑顺序排列（而不是价值排序）
            final_content = '. '.join(final_sentences)
            
            # 步骤7：提取整体关键信息
            logger.info("提取整体关键信息...")
            overall_key_info = self.content_filter.extract_key_information(final_content)
            
            # 计算处理统计
            processing_stats = {
                'original_documents': len(raw_documents),
                'total_raw_chars': total_raw_chars,
                'cleaned_chars': len(cleaned_content),
                'valuable_sentences_extracted': len(valuable_sentences),
                'unique_sentences_after_dedup': len(unique_sentences),
                'final_sentences_selected': len(final_sentences),
                'final_content_chars': len(final_content),
                'content_compression_ratio': len(final_content) / total_raw_chars if total_raw_chars > 0 else 0,
                'deduplication_ratio': len(unique_sentences) / len(valuable_sentences) if valuable_sentences else 0,
                'avg_sentence_value_score': sum(score for _, score in sentence_scores[:len(final_sentences)]) / len(final_sentences) if final_sentences else 0
            }
            
            result = {
                'topic_id': topic_id,
                'success': True,
                'aggregated_content': final_content,
                'overall_key_information': overall_key_info,
                'processing_stats': processing_stats,
                'content_stats': {
                    'total_chars': len(final_content),
                    'total_words': len(final_content.split()),
                    'total_sentences': len(final_sentences),
                    'avg_sentence_length': len(final_content) / len(final_sentences) if final_sentences else 0
                }
            }
            
            logger.info(f"Topic {topic_id} 聚合内容处理完成:")
            logger.info(f"  原始文档: {len(raw_documents)} 个")
            logger.info(f"  原始字符: {total_raw_chars:,}")
            logger.info(f"  有价值句子: {len(valuable_sentences)}")
            logger.info(f"  去重后句子: {len(unique_sentences)}")
            logger.info(f"  最终句子: {len(final_sentences)}")
            logger.info(f"  最终字符: {len(final_content):,}")
            logger.info(f"  内容压缩率: {processing_stats['content_compression_ratio']:.3f}")
            logger.info(f"  去重率: {processing_stats['deduplication_ratio']:.3f}")
            logger.info(f"  平均句子价值分数: {processing_stats['avg_sentence_value_score']:.3f}")
            
            return result
            
        except Exception as e:
            logger.error(f"聚合处理topic {topic_id} 时出错: {e}")
            return {
                'topic_id': topic_id,
                'success': False,
                'error': str(e),
                'aggregated_content': '',
                'processing_stats': {}
            }

def main():
    """测试函数"""
    logging.basicConfig(level=logging.INFO)
    
    # 初始化加载器
    loader = TopicBasedDataLoader()
    
    # 获取可用topics
    topics = loader.get_available_topics()
    print(f"可用Topics: {topics[:5]}...")  # 显示前5个
    
    # 测试加载单个topic
    if topics:
        test_topic = topics[0]
        print(f"\n测试加载topic: {test_topic}")
        
        result = loader.filter_and_process_topic_documents(test_topic)
        if result['success']:
            print(f"成功! 原始文档: {result['document_count']['original']}, "
                  f"过滤后: {result['document_count']['filtered']}")
        else:
            print(f"失败: {result['error']}")

if __name__ == "__main__":
    main() 
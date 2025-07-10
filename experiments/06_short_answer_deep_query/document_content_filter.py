#!/usr/bin/env python3
"""
文档内容过滤和清洗模块
用于从原始ClueWeb22文档中提取有价值的学术内容
"""

import re
import logging
from typing import List, Dict, Set
from pathlib import Path

logger = logging.getLogger(__name__)

class DocumentContentFilter:
    """文档内容过滤器"""
    
    def __init__(self):
        # 定义无价值内容的模式
        self.noise_patterns = [
            # HTML标签和CSS
            r'<[^>]+>',
            r'\.css\{[^}]*\}',
            r'@media[^{]*\{[^}]*\}',
            r'font-family:[^;]*;',
            r'background-color:[^;]*;',
            r'margin:[^;]*;',
            r'padding:[^;]*;',
            
            # JavaScript
            r'<script[^>]*>.*?</script>',
            r'function\s+\w+\([^)]*\)\s*\{[^}]*\}',
            r'var\s+\w+\s*=\s*[^;]*;',
            r'document\.\w+',
            
            # 导航和菜单
            r'(navigation|menu|navbar|sidebar|header|footer)',
            r'(home|about|contact|search|login|register)',
            r'(privacy policy|terms of service|cookie policy)',
            
            # 广告和商业内容
            r'(advertisement|sponsored|affiliate|promotion)',
            r'(buy now|add to cart|purchase|order)',
            r'(discount|sale|offer|deal)',
            
            # 社交媒体
            r'(facebook|twitter|instagram|linkedin|youtube)',
            r'(share|like|follow|subscribe)',
            r'(comment|reply|post)',
            
            # 技术噪音
            r'(cookie|session|cache|database)',
            r'(404|error|not found|page not found)',
            r'(loading|please wait)',
            
            # 重复字符和无意义符号
            r'[^\w\s.!?,:;()-]{3,}',
            r'(.)\1{5,}',  # 连续重复字符
        ]
        
        # 编译正则表达式
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE | re.DOTALL) for pattern in self.noise_patterns]
        
        # 定义有价值内容的指标
        self.valuable_indicators = [
            # 学术研究词汇
            r'\b(research|study|experiment|analysis|methodology|findings|results|conclusion|data|statistical|significant|hypothesis|theory|model|framework|approach|technique|method|algorithm|procedure|investigation|evaluation|assessment|validation|verification|comparison|correlation|regression|classification|optimization|simulation|empirical|theoretical|quantitative|qualitative)\b',
            
            # 数字和度量
            r'\b\d+\.?\d*\s*(percent|percentage|%|degree|celsius|fahrenheit|meter|kilometer|gram|kilogram|second|minute|hour|day|year|sample|participant|subject|trial|iteration|epoch|accuracy|precision|recall|f1|score|rate|ratio|coefficient|p-value|confidence|interval|standard|deviation|mean|median|variance|correlation)\b',
            
            # 机构和出版
            r'\b(university|college|institute|laboratory|department|center|journal|conference|proceedings|publication|paper|article|thesis|dissertation|report|patent|standard|specification|guideline)\b',
            
            # 技术术语
            r'\b(machine learning|artificial intelligence|deep learning|neural network|natural language processing|computer vision|data mining|big data|cloud computing|internet of things|blockchain|cybersecurity|software engineering|database|algorithm|programming|development|technology|innovation|digital|electronic|computational|automated|intelligent|adaptive|predictive|analytics|optimization|performance|efficiency|scalability|reliability|security|privacy)\b',
        ]
        
        self.valuable_pattern = re.compile('|'.join(self.valuable_indicators), re.IGNORECASE)
    
    def clean_text(self, text: str) -> str:
        """清洗文本，移除噪音内容"""
        if not text:
            return ""
        
        # 移除HTML标签
        text = re.sub(r'<[^>]+>', ' ', text)
        
        # 移除多余的空白字符
        text = re.sub(r'\s+', ' ', text)
        
        # 移除噪音模式
        for pattern in self.compiled_patterns:
            text = pattern.sub(' ', text)
        
        # 再次清理空白字符
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def extract_sentences(self, text: str) -> List[str]:
        """提取有意义的句子"""
        if not text:
            return []
        
        # 按句号分割
        sentences = re.split(r'[.!?]+', text)
        
        valuable_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            
            # 过滤太短或太长的句子
            if len(sentence) < 20 or len(sentence) > 500:
                continue
            
            # 检查是否包含有价值的指标
            if self.valuable_pattern.search(sentence):
                valuable_sentences.append(sentence)
            
            # 检查是否包含数字信息
            elif re.search(r'\d+', sentence):
                valuable_sentences.append(sentence)
        
        return valuable_sentences
    
    def calculate_content_value_score(self, text: str) -> float:
        """计算内容价值分数 (0-1)"""
        if not text:
            return 0.0
        
        # 计算有价值指标的密度
        valuable_matches = len(self.valuable_pattern.findall(text))
        total_words = len(text.split())
        
        if total_words == 0:
            return 0.0
        
        # 计算密度分数
        density_score = min(valuable_matches / total_words * 10, 1.0)
        
        # 计算长度分数（适中长度更好）
        length_score = min(len(text) / 1000, 1.0) if len(text) < 2000 else max(1.0 - (len(text) - 2000) / 5000, 0.1)
        
        # 计算数字信息分数
        number_matches = len(re.findall(r'\d+\.?\d*', text))
        number_score = min(number_matches / total_words * 20, 0.3)
        
        # 综合分数
        final_score = (density_score * 0.6 + length_score * 0.3 + number_score * 0.1)
        
        return min(final_score, 1.0)
    
    def filter_document(self, document: Dict[str, str]) -> Dict[str, str]:
        """过滤单个文档"""
        content = document.get('content', '')
        
        # 清洗文本
        cleaned_content = self.clean_text(content)
        
        # 提取有价值的句子
        valuable_sentences = self.extract_sentences(cleaned_content)
        
        # 重新组合内容
        filtered_content = '. '.join(valuable_sentences)
        
        # 计算价值分数
        value_score = self.calculate_content_value_score(filtered_content)
        
        return {
            'doc_id': document.get('doc_id', ''),
            'source': document.get('source', ''),
            'content': filtered_content,
            'word_count': len(filtered_content.split()),
            'char_count': len(filtered_content),
            'value_score': value_score,
            'valuable_sentences_count': len(valuable_sentences),
            'original_length': len(content)
        }
    
    def extract_key_information(self, text: str) -> Dict[str, List[str]]:
        """提取关键信息类别"""
        key_info = {
            'numerical_data': [],
            'technical_terms': [],
            'institutions': [],
            'methodologies': [],
            'findings': []
        }
        
        # 提取数值数据
        numerical_patterns = [
            r'\b\d+\.?\d*\s*(?:percent|%|accuracy|precision|recall|f1|score)\b',
            r'\b\d+\.?\d*\s*(?:participants|samples|subjects|trials|epochs|iterations)\b',
            r'\bp\s*[<>=]\s*0\.\d+\b',  # p-values
            r'\b\d+\.?\d*\s*(?:years?|months?|days?|hours?|minutes?)\b'
        ]
        
        for pattern in numerical_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            key_info['numerical_data'].extend(matches)
        
        # 提取技术术语
        tech_terms = re.findall(r'\b(?:algorithm|model|framework|technique|method|approach|system|architecture|neural network|transformer|BERT|GPT|CNN|RNN|LSTM|SVM|random forest|clustering|classification|regression|optimization|deep learning|machine learning|AI|NLP|computer vision)\b', text, re.IGNORECASE)
        key_info['technical_terms'] = list(set(tech_terms))
        
        # 提取机构信息
        institutions = re.findall(r'\b(?:university|college|institute|laboratory|lab|research center|department|Google|Microsoft|OpenAI|Stanford|MIT|Harvard|Berkeley|CMU)\b', text, re.IGNORECASE)
        key_info['institutions'] = list(set(institutions))
        
        # 提取方法论
        methodologies = re.findall(r'\b(?:experiment|study|analysis|evaluation|assessment|validation|comparison|survey|review|investigation|simulation|training|testing|cross-validation|ablation study|hyperparameter tuning)\b', text, re.IGNORECASE)
        key_info['methodologies'] = list(set(methodologies))
        
        # 提取发现和结果
        findings = re.findall(r'\b(?:results?|findings?|conclusions?|outcomes?|achievements?|improvements?|performance|accuracy|effectiveness|efficiency|significant|outperform|state-of-the-art|breakthrough|novel|innovative)\b', text, re.IGNORECASE)
        key_info['findings'] = list(set(findings))
        
        return key_info

    def is_high_quality_content(self, content: str) -> bool:
        """判断内容是否为高质量"""
        if not content or len(content.strip()) < 100:
            return False
        
        # 计算价值分数
        value_score = self.calculate_content_value_score(content)
        
        # 检查基本质量指标
        word_count = len(content.split())
        has_valuable_indicators = bool(self.valuable_pattern.search(content))
        has_numbers = bool(re.search(r'\d+', content))
        
        # 综合判断
        is_quality = (
            value_score >= 0.05 and  # 基本价值分数
            word_count >= 50 and     # 最小字数
            (has_valuable_indicators or has_numbers)  # 包含有价值指标或数字
        )
        
        return is_quality
    
    def extract_clean_content(self, content: str) -> str:
        """提取清洁的内容"""
        cleaned = self.clean_text(content)
        sentences = self.extract_sentences(cleaned)
        return '. '.join(sentences)

    def filter_documents(self, documents: List[Dict[str, str]], min_value_score: float = 0.1, target_length: int = 50000) -> List[Dict[str, str]]:
        """过滤文档列表 - 增强版，智能选择最有价值的内容"""
        filtered_docs = []
        
        # 第一步：过滤和评分
        for doc in documents:
            filtered_doc = self.filter_document(doc)
            
            # 只保留有价值的文档
            if (filtered_doc['value_score'] >= min_value_score and 
                filtered_doc['word_count'] >= 20 and
                filtered_doc['valuable_sentences_count'] >= 2):
                
                # 添加关键信息提取
                key_info = self.extract_key_information(filtered_doc['content'])
                filtered_doc['key_information'] = key_info
                filtered_doc['info_density'] = sum(len(v) for v in key_info.values())
                
                filtered_docs.append(filtered_doc)
        
        # 第二步：按综合分数排序
        for doc in filtered_docs:
            # 综合分数 = 价值分数 * 0.6 + 信息密度分数 * 0.4
            info_score = min(doc['info_density'] / 20, 1.0)  # 归一化信息密度
            doc['combined_score'] = doc['value_score'] * 0.6 + info_score * 0.4
        
        filtered_docs.sort(key=lambda x: x['combined_score'], reverse=True)
        
        # 第三步：智能截取到目标长度
        if target_length > 0:
            selected_docs = []
            total_chars = 0
            
            for doc in filtered_docs:
                if total_chars + doc['char_count'] <= target_length:
                    selected_docs.append(doc)
                    total_chars += doc['char_count']
                elif total_chars < target_length * 0.8:  # 至少达到目标的80%
                    # 截取部分内容
                    remaining_chars = target_length - total_chars
                    if remaining_chars > 500:  # 至少留500字符
                        truncated_content = doc['content'][:remaining_chars]
                        # 确保在句子边界截取
                        last_period = truncated_content.rfind('.')
                        if last_period > remaining_chars * 0.8:
                            truncated_content = truncated_content[:last_period + 1]
                        
                        doc_copy = doc.copy()
                        doc_copy['content'] = truncated_content
                        doc_copy['char_count'] = len(truncated_content)
                        doc_copy['word_count'] = len(truncated_content.split())
                        doc_copy['truncated'] = True
                        selected_docs.append(doc_copy)
                    break
                else:
                    break
            
            return selected_docs
        
        return filtered_docs
    
    def get_filtering_stats(self, original_docs: List[Dict], filtered_docs: List[Dict]) -> Dict:
        """获取过滤统计信息"""
        return {
            'original_count': len(original_docs),
            'filtered_count': len(filtered_docs),
            'retention_rate': len(filtered_docs) / len(original_docs) if original_docs else 0,
            'original_total_chars': sum(len(doc.get('content', '')) for doc in original_docs),
            'filtered_total_chars': sum(doc['char_count'] for doc in filtered_docs),
            'content_compression_rate': sum(doc['char_count'] for doc in filtered_docs) / sum(len(doc.get('content', '')) for doc in original_docs) if original_docs else 0,
            'avg_value_score': sum(doc['value_score'] for doc in filtered_docs) / len(filtered_docs) if filtered_docs else 0
        }


def test_document_filter():
    """测试文档过滤器"""
    # 创建测试数据
    test_documents = [
        {
            'doc_id': 'test_1',
            'source': 'academic_paper.txt',
            'content': 'This research investigates machine learning algorithms for natural language processing. The study used a dataset of 10,000 samples and achieved 94.2% accuracy using transformer models. The experimental results show significant improvement over baseline methods.'
        },
        {
            'doc_id': 'test_2', 
            'source': 'noise_content.txt',
            'content': '<html><head><style>body{margin:0;padding:0;}</style></head><body><nav>Home About Contact</nav><div>Advertisement: Buy now! 50% discount!</div></body></html>'
        },
        {
            'doc_id': 'test_3',
            'source': 'mixed_content.txt',
            'content': 'Navigation: Home | Products | Contact. The university researchers conducted a controlled experiment with 500 participants. Results showed statistical significance (p<0.05). Footer: Copyright 2023.'
        }
    ]
    
    # 测试过滤器
    filter = DocumentContentFilter()
    
    print("🧪 测试文档内容过滤器")
    print("=" * 50)
    
    for doc in test_documents:
        print(f"\n原始文档 {doc['doc_id']}:")
        print(f"  内容: {doc['content'][:100]}...")
        print(f"  长度: {len(doc['content'])} 字符")
        
        filtered = filter.filter_document(doc)
        
        print(f"过滤后:")
        print(f"  内容: {filtered['content'][:100]}...")
        print(f"  长度: {filtered['char_count']} 字符")
        print(f"  价值分数: {filtered['value_score']:.3f}")
        print(f"  有价值句子数: {filtered['valuable_sentences_count']}")
    
    # 测试批量过滤
    print(f"\n📊 批量过滤结果:")
    filtered_docs = filter.filter_documents(test_documents)
    stats = filter.get_filtering_stats(test_documents, filtered_docs)
    
    print(f"  原始文档数: {stats['original_count']}")
    print(f"  过滤后文档数: {stats['filtered_count']}")
    print(f"  保留率: {stats['retention_rate']:.1%}")
    print(f"  内容压缩率: {stats['content_compression_rate']:.1%}")
    print(f"  平均价值分数: {stats['avg_value_score']:.3f}")


if __name__ == "__main__":
    test_document_filter() 
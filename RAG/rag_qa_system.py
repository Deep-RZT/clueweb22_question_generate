#!/usr/bin/env python3
"""
基于能源文献的RAG+问答系统
结合现有的600篇文章作为语料库，生成问答对
"""

import json
import random
import re
from typing import List, Dict, Tuple
from collections import defaultdict
import numpy as np

class EnergyRAGSystem:
    def __init__(self, papers_file: str):
        """初始化RAG系统"""
        self.papers = self.load_papers(papers_file)
        self.corpus = self.build_corpus()
        self.energy_topics = self.extract_energy_topics()
        
    def load_papers(self, papers_file: str) -> List[Dict]:
        """加载论文数据"""
        with open(papers_file, 'r', encoding='utf-8') as f:
            papers = json.load(f)
        
        # 只使用有摘要的论文
        valid_papers = [p for p in papers if p.get('abstract') and len(p['abstract']) > 50]
        print(f"加载了 {len(valid_papers)} 篇有效论文")
        return valid_papers
    
    def build_corpus(self) -> List[Dict]:
        """构建语料库"""
        corpus = []
        for paper in self.papers:
            doc = {
                'id': paper.get('id', ''),
                'title': paper.get('title', ''),
                'abstract': paper.get('abstract', ''),
                'authors': paper.get('authors', []),
                'published': paper.get('published', ''),
                'source': paper.get('source', ''),
                'keyword_matched': paper.get('keyword_matched', ''),
                'full_text': f"{paper.get('title', '')} {paper.get('abstract', '')}"
            }
            corpus.append(doc)
        return corpus
    
    def extract_energy_topics(self) -> Dict[str, List[str]]:
        """提取能源主题和相关文档"""
        topics = defaultdict(list)
        
        # 定义能源主题关键词
        topic_keywords = {
            'renewable_energy': ['renewable', 'solar', 'wind', 'photovoltaic', 'biomass', 'hydroelectric'],
            'energy_storage': ['storage', 'battery', 'batteries', 'capacitor', 'hydrogen storage'],
            'smart_grid': ['smart grid', 'grid', 'transmission', 'distribution', 'power system'],
            'energy_efficiency': ['efficiency', 'optimization', 'conservation', 'saving'],
            'fossil_fuels': ['natural gas', 'oil', 'coal', 'petroleum', 'fossil'],
            'nuclear_energy': ['nuclear', 'reactor', 'uranium', 'fusion', 'fission'],
            'energy_policy': ['policy', 'regulation', 'market', 'economics', 'planning'],
            'climate_change': ['climate', 'carbon', 'emission', 'greenhouse', 'decarbonization']
        }
        
        for doc in self.corpus:
            text = doc['full_text'].lower()
            for topic, keywords in topic_keywords.items():
                if any(keyword in text for keyword in keywords):
                    topics[topic].append(doc)
        
        return topics
    
    def simple_similarity(self, query: str, document: str) -> float:
        """简单的相似度计算（基于关键词重叠）"""
        query_words = set(query.lower().split())
        doc_words = set(document.lower().split())
        
        if not query_words or not doc_words:
            return 0.0
        
        intersection = query_words.intersection(doc_words)
        union = query_words.union(doc_words)
        
        return len(intersection) / len(union)
    
    def retrieve_relevant_docs(self, query: str, top_k: int = 3) -> List[Dict]:
        """检索相关文档"""
        scores = []
        
        for doc in self.corpus:
            score = self.simple_similarity(query, doc['full_text'])
            scores.append((score, doc))
        
        # 按相似度排序
        scores.sort(key=lambda x: x[0], reverse=True)
        
        return [doc for score, doc in scores[:top_k] if score > 0]
    
    def generate_question_templates(self) -> List[str]:
        """生成问题模板"""
        templates = [
            "What are the main challenges in {topic}?",
            "How does {technology} contribute to {goal}?",
            "What are the advantages of {technology} over traditional methods?",
            "What factors affect the efficiency of {system}?",
            "How can {technology} be optimized for better performance?",
            "What are the environmental impacts of {technology}?",
            "What are the economic considerations for {technology}?",
            "How does {technology} integrate with existing infrastructure?",
            "What are the future prospects for {technology}?",
            "What research gaps exist in {field}?",
            "How does {factor} influence {outcome}?",
            "What are the key components of {system}?",
            "How can {challenge} be addressed in {context}?",
            "What role does {technology} play in energy transition?",
            "What are the technical barriers to {implementation}?"
        ]
        return templates
    
    def extract_key_terms(self, text: str) -> List[str]:
        """从文本中提取关键术语"""
        # 简单的关键词提取
        energy_terms = [
            'solar energy', 'wind energy', 'renewable energy', 'energy storage',
            'smart grid', 'energy efficiency', 'natural gas', 'nuclear energy',
            'biomass', 'hydroelectric', 'geothermal', 'energy transition',
            'carbon emission', 'energy security', 'power system', 'grid integration',
            'energy planning', 'energy policy', 'energy market', 'sustainability'
        ]
        
        found_terms = []
        text_lower = text.lower()
        
        for term in energy_terms:
            if term in text_lower:
                found_terms.append(term)
        
        return found_terms
    
    def generate_qa_pair(self, doc: Dict, template: str) -> Tuple[str, str]:
        """基于文档和模板生成问答对"""
        title = doc['title']
        abstract = doc['abstract']
        
        # 提取关键术语
        key_terms = self.extract_key_terms(title + " " + abstract)
        
        if not key_terms:
            key_terms = ['energy systems']
        
        # 随机选择术语填充模板
        term = random.choice(key_terms)
        
        # 简单的模板填充
        question = template.replace('{technology}', term)
        question = question.replace('{topic}', term)
        question = question.replace('{system}', term)
        question = question.replace('{field}', term)
        question = question.replace('{goal}', 'energy efficiency')
        question = question.replace('{factor}', 'temperature')
        question = question.replace('{outcome}', 'performance')
        question = question.replace('{challenge}', 'integration challenges')
        question = question.replace('{context}', 'renewable energy systems')
        question = question.replace('{implementation}', 'widespread adoption')
        
        # 生成答案（基于摘要的关键信息）
        answer = self.generate_answer_from_abstract(abstract, question)
        
        return question, answer
    
    def generate_answer_from_abstract(self, abstract: str, question: str) -> str:
        """基于摘要生成答案"""
        # 简化的答案生成逻辑
        sentences = abstract.split('.')
        relevant_sentences = []
        
        question_words = set(question.lower().split())
        
        for sentence in sentences:
            sentence_words = set(sentence.lower().split())
            if len(question_words.intersection(sentence_words)) > 0:
                relevant_sentences.append(sentence.strip())
        
        if relevant_sentences:
            answer = '. '.join(relevant_sentences[:2])  # 取前两个相关句子
        else:
            answer = sentences[0].strip() if sentences else abstract[:200]
        
        return answer + "." if not answer.endswith('.') else answer
    
    def generate_qa_dataset(self, num_pairs: int = 200) -> List[Dict]:
        """生成问答数据集"""
        qa_pairs = []
        templates = self.generate_question_templates()
        
        print(f"开始生成 {num_pairs} 个问答对...")
        
        for i in range(num_pairs):
            # 随机选择文档和模板
            doc = random.choice(self.corpus)
            template = random.choice(templates)
            
            try:
                question, answer = self.generate_qa_pair(doc, template)
                
                qa_pair = {
                    'id': f"qa_{i+1:03d}",
                    'question': question,
                    'answer': answer,
                    'source_paper': {
                        'title': doc['title'],
                        'id': doc['id'],
                        'source': doc['source']
                    },
                    'topic': doc['keyword_matched']
                }
                
                qa_pairs.append(qa_pair)
                
                if (i + 1) % 50 == 0:
                    print(f"已生成 {i + 1} 个问答对")
                    
            except Exception as e:
                print(f"生成第 {i+1} 个问答对时出错: {e}")
                continue
        
        return qa_pairs
    
    def save_qa_dataset(self, qa_pairs: List[Dict], filename: str):
        """保存问答数据集"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(qa_pairs, f, ensure_ascii=False, indent=2)
        
        print(f"问答数据集已保存到: {filename}")
    
    def demonstrate_rag(self, query: str):
        """演示RAG检索和回答"""
        print(f"\n=== RAG演示 ===")
        print(f"查询: {query}")
        
        # 检索相关文档
        relevant_docs = self.retrieve_relevant_docs(query, top_k=3)
        
        print(f"\n检索到 {len(relevant_docs)} 个相关文档:")
        
        for i, doc in enumerate(relevant_docs, 1):
            print(f"\n{i}. {doc['title']}")
            print(f"   来源: {doc['source']}")
            print(f"   摘要: {doc['abstract'][:200]}...")
        
        # 基于检索结果生成答案
        if relevant_docs:
            combined_context = " ".join([doc['abstract'] for doc in relevant_docs])
            answer = self.generate_answer_from_abstract(combined_context, query)
            print(f"\n生成的答案: {answer}")
        else:
            print("\n未找到相关文档")

def main():
    """主函数"""
    print("=== 能源文献RAG+问答系统 ===\n")
    
    # 初始化RAG系统
    rag_system = EnergyRAGSystem('data/metadata/papers_20250526_182607.json')
    
    # 显示语料库统计
    print(f"语料库统计:")
    print(f"- 总文档数: {len(rag_system.corpus)}")
    print(f"- 主题分布:")
    for topic, docs in rag_system.energy_topics.items():
        print(f"  {topic}: {len(docs)} 篇")
    
    # 演示RAG检索
    demo_queries = [
        "renewable energy integration challenges",
        "energy storage technologies",
        "smart grid optimization"
    ]
    
    for query in demo_queries:
        rag_system.demonstrate_rag(query)
    
    # 生成问答数据集
    print(f"\n=== 生成问答数据集 ===")
    qa_pairs = rag_system.generate_qa_dataset(num_pairs=200)
    
    # 保存数据集
    rag_system.save_qa_dataset(qa_pairs, 'data/energy_qa_dataset.json')
    
    # 显示样本问答对
    print(f"\n=== 样本问答对 ===")
    for i, qa in enumerate(qa_pairs[:3], 1):
        print(f"\n{i}. 问题: {qa['question']}")
        print(f"   答案: {qa['answer']}")
        print(f"   来源: {qa['source_paper']['title']}")
    
    print(f"\n=== 总结 ===")
    print(f"✓ 成功构建基于 {len(rag_system.corpus)} 篇文献的RAG系统")
    print(f"✓ 生成了 {len(qa_pairs)} 个问答对")
    print(f"✓ 涵盖 {len(rag_system.energy_topics)} 个能源主题")
    print(f"✓ 数据集已保存，可用于后续训练和评估")

if __name__ == "__main__":
    main() 
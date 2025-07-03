#!/usr/bin/env python3
"""
RAG Effectiveness Validation System
系统性验证RAG融合的有效性和改进效果
"""

import json
import sys
import os
import time
import random
from pathlib import Path
from typing import List, Dict, Any, Tuple
from datetime import datetime
import requests
import pandas as pd
from collections import defaultdict
import re

# Add paths
sys.path.append('PROMPT')
sys.path.append('RAG')

class RAGEffectivenessValidator:
    """RAG有效性验证器"""
    
    def __init__(self, claude_api_key: str):
        self.claude_api_key = claude_api_key
        self.claude_api_url = "https://api.anthropic.com/v1/messages"
        self.headers = {
            "Content-Type": "application/json",
            "x-api-key": claude_api_key,
            "anthropic-version": "2023-06-01"
        }
        
        # 加载RAG系统
        from enhanced_generation_system import EnhancedEnergyGenerator
        self.rag_generator = EnhancedEnergyGenerator(claude_api_key)
        
        print(f"✅ RAG验证器初始化完成")
    
    def call_claude_api(self, messages: List[Dict], max_tokens: int = 2000) -> str:
        """调用Claude API"""
        payload = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": max_tokens,
            "messages": messages
        }
        
        try:
            response = requests.post(
                self.claude_api_url,
                headers=self.headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['content'][0]['text']
            else:
                print(f"❌ API Error {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ API Call failed: {e}")
            return None
    
    def generate_baseline_answer(self, question: str) -> str:
        """生成基线答案（无RAG支撑）"""
        messages = [
            {
                "role": "user",
                "content": f"""Please provide a comprehensive answer to the following energy domain question:

Question: {question}

Provide a detailed, research-grade analysis covering:
- Overview of the topic
- Key technical aspects
- Current challenges and opportunities
- Future directions

Answer length: 800-1200 words."""
            }
        ]
        
        return self.call_claude_api(messages, max_tokens=2000)
    
    def validate_literature_retrieval_accuracy(self, test_questions: List[str]) -> Dict[str, Any]:
        """验证文献检索准确性"""
        
        print("🔍 验证文献检索准确性...")
        
        retrieval_results = {
            'total_questions': len(test_questions),
            'successful_retrievals': 0,
            'average_relevance_score': 0.0,
            'coverage_by_subdomain': defaultdict(int),
            'detailed_results': []
        }
        
        total_relevance = 0
        
        for i, question in enumerate(test_questions, 1):
            print(f"  检索测试 {i}/{len(test_questions)}: {question[:50]}...")
            
            # 检索相关论文
            relevant_papers = self.rag_generator.retrieve_relevant_papers(question, top_k=5)
            
            if relevant_papers:
                retrieval_results['successful_retrievals'] += 1
                
                # 计算相关性分数（基于关键词重叠）
                question_words = set(question.lower().split())
                paper_relevance_scores = []
                
                for paper in relevant_papers:
                    paper_text = f"{paper['title']} {paper['abstract']}".lower()
                    paper_words = set(paper_text.split())
                    
                    # Jaccard相似度
                    intersection = question_words.intersection(paper_words)
                    union = question_words.union(paper_words)
                    relevance = len(intersection) / len(union) if union else 0
                    paper_relevance_scores.append(relevance)
                
                avg_relevance = sum(paper_relevance_scores) / len(paper_relevance_scores)
                total_relevance += avg_relevance
                
                # 记录详细结果
                retrieval_results['detailed_results'].append({
                    'question': question,
                    'papers_found': len(relevant_papers),
                    'average_relevance': avg_relevance,
                    'top_paper_title': relevant_papers[0]['title'] if relevant_papers else None
                })
                
                # 统计子领域覆盖
                for paper in relevant_papers:
                    for keyword in paper.get('keywords', []):
                        retrieval_results['coverage_by_subdomain'][keyword] += 1
        
        if retrieval_results['successful_retrievals'] > 0:
            retrieval_results['average_relevance_score'] = total_relevance / retrieval_results['successful_retrievals']
        
        retrieval_results['success_rate'] = retrieval_results['successful_retrievals'] / retrieval_results['total_questions']
        
        return retrieval_results
    
    def compare_answer_quality(self, test_questions: List[str]) -> Dict[str, Any]:
        """对比RAG答案与基线答案的质量"""
        
        print("📊 对比答案质量...")
        
        comparison_results = {
            'total_comparisons': len(test_questions),
            'rag_wins': 0,
            'baseline_wins': 0,
            'ties': 0,
            'quality_metrics': {
                'rag_avg_citations': 0,
                'baseline_avg_citations': 0,
                'rag_avg_word_count': 0,
                'baseline_avg_word_count': 0,
                'rag_factual_accuracy': 0,
                'baseline_factual_accuracy': 0
            },
            'detailed_comparisons': []
        }
        
        total_rag_citations = 0
        total_baseline_citations = 0
        total_rag_words = 0
        total_baseline_words = 0
        
        for i, question in enumerate(test_questions, 1):
            print(f"  质量对比 {i}/{len(test_questions)}: {question[:50]}...")
            
            # 生成RAG答案
            relevant_papers = self.rag_generator.retrieve_relevant_papers(question, top_k=5)
            rag_result = self.rag_generator.generate_rag_fused_answer(question, relevant_papers)
            rag_answer = rag_result['answer']
            
            # 生成基线答案
            baseline_answer = self.generate_baseline_answer(question)
            
            if rag_answer and baseline_answer:
                # 分析引用数量
                rag_citations = len(rag_result.get('sources', []))
                baseline_citations = self.count_citations(baseline_answer)
                
                total_rag_citations += rag_citations
                total_baseline_citations += baseline_citations
                
                # 分析词数
                rag_words = len(rag_answer.split())
                baseline_words = len(baseline_answer.split())
                
                total_rag_words += rag_words
                total_baseline_words += baseline_words
                
                # 使用Claude评估质量
                quality_comparison = self.evaluate_answer_quality(question, rag_answer, baseline_answer)
                
                if quality_comparison:
                    if 'rag' in quality_comparison.lower():
                        comparison_results['rag_wins'] += 1
                    elif 'baseline' in quality_comparison.lower():
                        comparison_results['baseline_wins'] += 1
                    else:
                        comparison_results['ties'] += 1
                
                # 记录详细对比
                comparison_results['detailed_comparisons'].append({
                    'question': question,
                    'rag_citations': rag_citations,
                    'baseline_citations': baseline_citations,
                    'rag_words': rag_words,
                    'baseline_words': baseline_words,
                    'quality_assessment': quality_comparison
                })
            
            # 限制API调用频率
            time.sleep(1)
        
        # 计算平均值
        if len(test_questions) > 0:
            comparison_results['quality_metrics']['rag_avg_citations'] = total_rag_citations / len(test_questions)
            comparison_results['quality_metrics']['baseline_avg_citations'] = total_baseline_citations / len(test_questions)
            comparison_results['quality_metrics']['rag_avg_word_count'] = total_rag_words / len(test_questions)
            comparison_results['quality_metrics']['baseline_avg_word_count'] = total_baseline_words / len(test_questions)
        
        return comparison_results
    
    def count_citations(self, text: str) -> int:
        """统计文本中的引用数量"""
        citation_patterns = [
            r'\([^)]*\d{4}[^)]*\)',  # (Author, 2024)
            r'\[[^\]]*\d+[^\]]*\]',  # [1], [Author 2024]
            r'et al\.',              # et al.
            r'doi:',                 # doi:
            r'http[s]?://',          # URLs
            r'www\.',                # www.
        ]
        
        total_citations = 0
        for pattern in citation_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            total_citations += len(matches)
        
        return total_citations
    
    def evaluate_answer_quality(self, question: str, rag_answer: str, baseline_answer: str) -> str:
        """使用Claude评估两个答案的质量"""
        
        messages = [
            {
                "role": "user",
                "content": f"""Please evaluate the quality of two answers to the same energy domain question. Consider factual accuracy, depth of analysis, use of evidence, and overall helpfulness.

Question: {question}

Answer A (RAG-based): {rag_answer[:1000]}...

Answer B (Baseline): {baseline_answer[:1000]}...

Which answer is better and why? Respond with either "Answer A (RAG)" or "Answer B (Baseline)" followed by a brief explanation focusing on:
1. Factual accuracy and evidence
2. Depth and comprehensiveness
3. Specific citations and sources
4. Overall research value

Keep your response concise (2-3 sentences)."""
            }
        ]
        
        return self.call_claude_api(messages, max_tokens=300)
    
    def validate_factual_accuracy(self, test_samples: List[Dict]) -> Dict[str, Any]:
        """验证事实准确性"""
        
        print("🔬 验证事实准确性...")
        
        accuracy_results = {
            'total_samples': len(test_samples),
            'rag_accurate_facts': 0,
            'baseline_accurate_facts': 0,
            'verifiable_claims': {
                'rag': 0,
                'baseline': 0
            },
            'detailed_analysis': []
        }
        
        for i, sample in enumerate(test_samples, 1):
            print(f"  事实验证 {i}/{len(test_samples)}")
            
            question = sample['question']
            rag_answer = sample['rag_answer']
            baseline_answer = sample['baseline_answer']
            
            # 使用Claude分析事实准确性
            fact_analysis = self.analyze_factual_claims(question, rag_answer, baseline_answer)
            
            if fact_analysis:
                accuracy_results['detailed_analysis'].append({
                    'question': question,
                    'analysis': fact_analysis
                })
            
            time.sleep(1)
        
        return accuracy_results
    
    def analyze_factual_claims(self, question: str, rag_answer: str, baseline_answer: str) -> str:
        """分析答案中的事实声明"""
        
        messages = [
            {
                "role": "user",
                "content": f"""Analyze the factual claims in these two answers to an energy domain question. Focus on verifiable facts, statistics, and technical details.

Question: {question}

Answer A (RAG-based): {rag_answer[:800]}...

Answer B (Baseline): {baseline_answer[:800]}...

For each answer, identify:
1. Number of specific factual claims
2. Presence of citations/sources
3. Technical accuracy (if verifiable)
4. Potential inaccuracies or unsupported claims

Provide a brief comparison focusing on factual reliability."""
            }
        ]
        
        return self.call_claude_api(messages, max_tokens=500)
    
    def measure_ground_truth_quality(self, sample_questions: List[str]) -> Dict[str, Any]:
        """测量ground truth质量"""
        
        print("📏 测量Ground Truth质量...")
        
        gt_quality = {
            'total_questions': len(sample_questions),
            'literature_supported': 0,
            'verifiable_claims': 0,
            'citation_quality': 0,
            'research_depth': 0,
            'quality_scores': []
        }
        
        for i, question in enumerate(sample_questions, 1):
            print(f"  质量测量 {i}/{len(sample_questions)}")
            
            # 生成RAG答案
            relevant_papers = self.rag_generator.retrieve_relevant_papers(question, top_k=5)
            rag_result = self.rag_generator.generate_rag_fused_answer(question, relevant_papers)
            
            if rag_result['answer']:
                # 评估质量指标
                quality_metrics = self.rag_generator.assess_answer_quality(
                    question, rag_result['answer'], rag_result['sources']
                )
                
                gt_quality['quality_scores'].append(quality_metrics['quality_scores']['overall'])
                
                if len(rag_result['sources']) > 0:
                    gt_quality['literature_supported'] += 1
                
                if quality_metrics['has_citations']:
                    gt_quality['verifiable_claims'] += 1
        
        # 计算平均质量分数
        if gt_quality['quality_scores']:
            gt_quality['average_quality'] = sum(gt_quality['quality_scores']) / len(gt_quality['quality_scores'])
            gt_quality['literature_support_rate'] = gt_quality['literature_supported'] / gt_quality['total_questions']
            gt_quality['verifiable_rate'] = gt_quality['verifiable_claims'] / gt_quality['total_questions']
        
        return gt_quality
    
    def run_comprehensive_validation(self, num_test_questions: int = 10) -> Dict[str, Any]:
        """运行综合验证"""
        
        print(f"🚀 开始RAG有效性综合验证")
        print("=" * 70)
        print(f"测试问题数量: {num_test_questions}")
        print("验证维度: 检索准确性、答案质量、事实准确性、Ground Truth质量")
        print("=" * 70)
        
        # 生成测试问题
        test_questions = self.generate_test_questions(num_test_questions)
        
        validation_results = {
            'test_metadata': {
                'num_questions': num_test_questions,
                'test_timestamp': datetime.now().isoformat(),
                'rag_corpus_size': len(self.rag_generator.rag_corpus)
            },
            'retrieval_accuracy': {},
            'answer_quality_comparison': {},
            'ground_truth_quality': {},
            'overall_assessment': {}
        }
        
        # 1. 验证检索准确性
        validation_results['retrieval_accuracy'] = self.validate_literature_retrieval_accuracy(test_questions)
        
        # 2. 对比答案质量
        validation_results['answer_quality_comparison'] = self.compare_answer_quality(test_questions[:5])  # 限制数量以节省时间
        
        # 3. 测量Ground Truth质量
        validation_results['ground_truth_quality'] = self.measure_ground_truth_quality(test_questions[:5])
        
        # 4. 生成总体评估
        validation_results['overall_assessment'] = self.generate_overall_assessment(validation_results)
        
        return validation_results
    
    def generate_test_questions(self, num_questions: int) -> List[str]:
        """生成测试问题"""
        
        test_questions = [
            "How do energy storage systems impact renewable energy integration?",
            "What are the economic challenges of nuclear power deployment?",
            "How does carbon pricing affect fossil fuel investment decisions?",
            "What role do smart grids play in energy transition?",
            "How do environmental policies influence renewable energy adoption?",
            "What are the technical barriers to offshore wind development?",
            "How does energy security relate to renewable energy deployment?",
            "What are the lifecycle impacts of solar photovoltaic systems?",
            "How do energy markets adapt to variable renewable generation?",
            "What policy frameworks support energy storage deployment?"
        ]
        
        return test_questions[:num_questions]
    
    def generate_overall_assessment(self, validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """生成总体评估"""
        
        retrieval = validation_results['retrieval_accuracy']
        quality = validation_results['answer_quality_comparison']
        gt_quality = validation_results['ground_truth_quality']
        
        assessment = {
            'rag_effectiveness_score': 0.0,
            'key_strengths': [],
            'areas_for_improvement': [],
            'recommendation': ""
        }
        
        # 计算综合效果分数
        retrieval_score = retrieval.get('success_rate', 0) * 0.3
        quality_score = (quality.get('rag_wins', 0) / max(quality.get('total_comparisons', 1), 1)) * 0.4
        gt_score = gt_quality.get('average_quality', 0) * 0.3
        
        assessment['rag_effectiveness_score'] = retrieval_score + quality_score + gt_score
        
        # 识别优势
        if retrieval.get('success_rate', 0) > 0.9:
            assessment['key_strengths'].append("高文献检索成功率")
        
        if quality.get('rag_wins', 0) > quality.get('baseline_wins', 0):
            assessment['key_strengths'].append("RAG答案质量优于基线")
        
        if gt_quality.get('literature_support_rate', 0) > 0.8:
            assessment['key_strengths'].append("强文献支撑的Ground Truth")
        
        # 生成建议
        if assessment['rag_effectiveness_score'] > 0.7:
            assessment['recommendation'] = "RAG系统表现优秀，建议用于生产环境"
        elif assessment['rag_effectiveness_score'] > 0.5:
            assessment['recommendation'] = "RAG系统表现良好，可考虑进一步优化"
        else:
            assessment['recommendation'] = "RAG系统需要显著改进"
        
        return assessment
    
    def save_validation_results(self, results: Dict[str, Any], output_dir: str = "validation_output") -> str:
        """保存验证结果"""
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = output_path / f"rag_validation_results_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 验证结果已保存: {filename}")
        return str(filename)
    
    def print_validation_summary(self, results: Dict[str, Any]):
        """打印验证摘要"""
        
        print(f"\n📊 RAG有效性验证结果摘要")
        print("=" * 70)
        
        # 检索准确性
        retrieval = results['retrieval_accuracy']
        print(f"🔍 文献检索准确性:")
        print(f"   成功率: {retrieval.get('success_rate', 0)*100:.1f}%")
        print(f"   平均相关性: {retrieval.get('average_relevance_score', 0):.3f}")
        
        # 答案质量对比
        quality = results['answer_quality_comparison']
        print(f"\n📊 答案质量对比:")
        print(f"   RAG胜出: {quality.get('rag_wins', 0)}")
        print(f"   基线胜出: {quality.get('baseline_wins', 0)}")
        print(f"   平局: {quality.get('ties', 0)}")
        
        # Ground Truth质量
        gt = results['ground_truth_quality']
        print(f"\n📏 Ground Truth质量:")
        print(f"   平均质量分: {gt.get('average_quality', 0):.3f}")
        print(f"   文献支撑率: {gt.get('literature_support_rate', 0)*100:.1f}%")
        
        # 总体评估
        overall = results['overall_assessment']
        print(f"\n🎯 总体评估:")
        print(f"   RAG有效性分数: {overall.get('rag_effectiveness_score', 0):.3f}")
        print(f"   建议: {overall.get('recommendation', 'N/A')}")
        
        print("=" * 70)

def main():
    """主函数"""
    
    print("🔬 RAG有效性验证系统")
    print("=" * 70)
    
    api_key = "xxxxx"
    
    try:
        validator = RAGEffectivenessValidator(api_key)
        
        # 运行验证
        results = validator.run_comprehensive_validation(num_test_questions=10)
        
        # 保存结果
        results_file = validator.save_validation_results(results)
        
        # 打印摘要
        validator.print_validation_summary(results)
        
        print(f"\n✅ RAG有效性验证完成!")
        print(f"详细结果: {results_file}")
        
    except Exception as e:
        print(f"❌ 验证过程出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 
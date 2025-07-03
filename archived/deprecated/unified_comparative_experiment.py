#!/usr/bin/env python3
"""
Unified Comparative Experiment
统一的LLM对比实验系统

支持OpenAI GPT-4o和Claude Sonnet 4的完整对比实验
自动处理API key无效的情况
"""

import os
import json
import time
import pandas as pd
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dynamic_llm_manager import DynamicLLMManager
from json_parser_utils import extract_questions_from_response

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UnifiedComparativeExperiment:
    """统一的对比实验系统"""
    
    def __init__(self):
        """初始化实验系统"""
        self.manager = DynamicLLMManager()
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = f"unified_comparative_experiment_{self.timestamp}"
        
        # 创建输出目录
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 实验配置
        self.config = {
            'clueweb22_topics': 9,      # ClueWeb22主题数量（实际可用）
            'random_topics': 5,         # 随机文档主题数量
            'questions_per_topic': 10,  # 每个主题生成的问题数
            'answers_per_topic': 5,     # 每个主题生成的答案数
            'documents_per_topic': 8,   # 每个主题使用的文档数
            'max_tokens_report': 3000,  # 报告最大token数
            'rest_time': 2              # API调用间隔时间(秒)
        }
        
        # 检查可用的LLM提供商
        self.available_providers = self._check_available_providers()
        
        logger.info(f"实验初始化完成")
        logger.info(f"可用的LLM提供商: {self.available_providers}")
        logger.info(f"输出目录: {self.output_dir}")
    
    def _check_available_providers(self) -> List[str]:
        """检查可用的LLM提供商"""
        available = []
        
        # 检查OpenAI
        try:
            test_response = self.manager.generate_text(
                "Test", provider="openai", max_tokens=10
            )
            if test_response.success:
                available.append("openai")
                logger.info("✅ OpenAI API 可用")
            else:
                logger.warning(f"❌ OpenAI API 不可用: {test_response.error}")
        except Exception as e:
            logger.warning(f"❌ OpenAI API 检查失败: {e}")
        
        # 检查Claude
        try:
            test_response = self.manager.generate_text(
                "Test", provider="claude", max_tokens=10
            )
            if test_response.success:
                available.append("claude")
                logger.info("✅ Claude API 可用")
            else:
                logger.warning(f"❌ Claude API 不可用: {test_response.error}")
        except Exception as e:
            logger.warning(f"❌ Claude API 检查失败: {e}")
        
        return available
    
    def load_clueweb22_data(self) -> Dict[str, List[Dict]]:
        """加载ClueWeb22数据"""
        topics_data = {}
        clueweb_path = "task_file/clueweb22_json_results"
        
        if not os.path.exists(clueweb_path):
            logger.error(f"ClueWeb22数据路径不存在: {clueweb_path}")
            return {}
        
        json_files = [f for f in os.listdir(clueweb_path) 
                     if f.endswith('.json') and not f.startswith('conversion_stats')]
        
        for i, filename in enumerate(json_files[:self.config['clueweb22_topics']]):
            file_path = os.path.join(clueweb_path, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                topic = data.get('topic', filename.replace('.json', ''))
                documents = data.get('results', [])[:self.config['documents_per_topic']]
                
                if documents:
                    topics_data[topic] = documents
                    
            except Exception as e:
                logger.error(f"加载ClueWeb22文件失败 {filename}: {e}")
        
        logger.info(f"加载了 {len(topics_data)} 个ClueWeb22主题")
        return topics_data
    
    def load_random_academic_data(self) -> Dict[str, List[Dict]]:
        """加载高质量随机学术文档数据"""
        topics_data = {}
        
        # 优先使用高质量文档
        high_quality_file = "task_file/random_academic_docs/high_quality_academic_documents.json"
        fallback_file = "task_file/random_academic_docs/academic_documents.json"
        
        docs_file = high_quality_file if os.path.exists(high_quality_file) else fallback_file
        
        if not os.path.exists(docs_file):
            logger.warning("未找到现有学术文档，将生成新的高质量文档...")
            try:
                from optimized_academic_crawler import OptimizedAcademicCrawler
                
                crawler = OptimizedAcademicCrawler(100)
                all_docs = crawler.generate_high_quality_documents()
                crawler.save_documents(all_docs)
                
                logger.info(f"✅ 生成了 {len(all_docs)} 篇高质量学术文档")
                
            except Exception as e:
                logger.error(f"生成高质量文档失败: {e}")
                return {}
        else:
            try:
                with open(docs_file, 'r', encoding='utf-8') as f:
                    all_docs = json.load(f)
                
                logger.info(f"加载了 {len(all_docs)} 篇学术文档")
                if docs_file == high_quality_file:
                    avg_words = sum(doc.get('word_count', 0) for doc in all_docs) / len(all_docs)
                    avg_quality = sum(doc.get('quality_score', 0) for doc in all_docs) / len(all_docs)
                    logger.info(f"📊 平均词数: {avg_words:.0f}, 平均质量分数: {avg_quality:.2f}")
                    
            except Exception as e:
                logger.error(f"加载学术文档失败: {e}")
                return {}
        
        # 按领域分组
        domain_groups = {}
        for doc in all_docs:
            domain = doc.get('domain', 'unknown')
            if domain not in domain_groups:
                domain_groups[domain] = []
            domain_groups[domain].append(doc)
        
        # 选择前N个领域，优先选择文档数量多的领域
        sorted_domains = sorted(domain_groups.items(), key=lambda x: len(x[1]), reverse=True)
        
        for i, (domain, docs) in enumerate(sorted_domains):
            if i >= self.config['random_topics']:
                break
            
            # 选择质量最高的文档
            if docs_file == high_quality_file:
                sorted_docs = sorted(docs, key=lambda x: x.get('quality_score', 0), reverse=True)
            else:
                sorted_docs = docs
            
            selected_docs = sorted_docs[:self.config['documents_per_topic']]
            topics_data[domain] = selected_docs
        
        logger.info(f"✅ 准备了 {len(topics_data)} 个高质量学术文档主题")
        return topics_data
    
    def process_single_topic(self, topic: str, documents: List[Dict], 
                           data_source: str, provider: str) -> Optional[Dict[str, Any]]:
        """处理单个主题"""
        
        logger.info(f"  处理主题: {topic} (使用 {provider})")
        start_time = time.time()
        
        result = {
            'topic': topic,
            'data_source': data_source,
            'provider': provider,
            'documents_count': len(documents),
            'success': False,
            'processing_time': 0,
            'steps': {},
            'qa_pairs': [],
            'statistics': {}
        }
        
        try:
            # 1. 生成报告
            logger.info(f"    1. 生成报告...")
            report_response = self.manager.generate_report(
                documents, topic, provider=provider, 
                max_tokens=self.config['max_tokens_report']
            )
            
            if not report_response.success:
                logger.error(f"    ❌ 报告生成失败: {report_response.error}")
                result['steps']['report'] = {'success': False, 'error': report_response.error}
                return result
            
            report_content = report_response.content
            result['steps']['report'] = {
                'success': True,
                'content': report_content,
                'length': len(report_content),
                'word_count': len(report_content.split()),
                'usage': report_response.usage
            }
            logger.info(f"    ✅ 报告生成成功 ({len(report_content)} 字符, {len(report_content.split())} 词)")
            
            # 2. 生成问题
            logger.info(f"    2. 生成问题...")
            questions_response = self.manager.generate_questions(
                report_content, topic, self.config['questions_per_topic'], provider=provider
            )
            
            if not questions_response.success:
                logger.error(f"    ❌ 问题生成失败: {questions_response.error}")
                result['steps']['questions'] = {'success': False, 'error': questions_response.error}
                return result
            
            questions_data = extract_questions_from_response(questions_response.content)
            
            if not questions_data:
                logger.error(f"    ❌ 问题解析失败")
                result['steps']['questions'] = {'success': False, 'error': 'JSON解析失败'}
                return result
            
            result['steps']['questions'] = {
                'success': True,
                'count': len(questions_data),
                'questions_data': questions_data,
                'usage': questions_response.usage
            }
            logger.info(f"    ✅ 问题生成成功 ({len(questions_data)} 个问题)")
            
            # 3. 生成答案
            logger.info(f"    3. 生成答案 (前{self.config['answers_per_topic']}个问题)...")
            qa_pairs = []
            
            for j, q_data in enumerate(questions_data[:self.config['answers_per_topic']]):
                question = q_data.get('question', '')
                difficulty = q_data.get('difficulty', 'Medium')
                question_type = q_data.get('type', 'unknown')
                reasoning = q_data.get('reasoning', '')
                
                if question:
                    logger.info(f"      生成答案 {j+1}/{self.config['answers_per_topic']}...")
                    answer_response = self.manager.generate_answer(
                        question, report_content, difficulty, provider=provider
                    )
                    
                    if answer_response.success:
                        qa_pairs.append({
                            'question_id': j + 1,
                            'question': question,
                            'answer': answer_response.content,
                            'difficulty': difficulty,
                            'type': question_type,
                            'reasoning': reasoning,
                            'answer_length': len(answer_response.content),
                            'answer_word_count': len(answer_response.content.split()),
                            'usage': answer_response.usage
                        })
                        logger.info(f"      ✅ 答案 {j+1} 完成 ({len(answer_response.content.split())} 词)")
                    else:
                        logger.warning(f"      ❌ 答案 {j+1} 失败: {answer_response.error}")
                    
                    # 短暂休息
                    time.sleep(1)
            
            result['qa_pairs'] = qa_pairs
            result['steps']['answers'] = {
                'success': True,
                'count': len(qa_pairs),
                'total_answer_length': sum(qa['answer_length'] for qa in qa_pairs)
            }
            logger.info(f"    ✅ 答案生成完成 ({len(qa_pairs)} 个答案)")
            
            # 4. 计算统计信息
            result['statistics'] = self._calculate_topic_statistics(qa_pairs)
            result['success'] = True
            
        except Exception as e:
            logger.error(f"    ❌ 处理失败: {e}")
            result['error'] = str(e)
        
        result['processing_time'] = time.time() - start_time
        logger.info(f"    ✅ 主题处理完成 (耗时: {result['processing_time']:.2f}秒)")
        
        return result
    
    def _calculate_topic_statistics(self, qa_pairs: List[Dict]) -> Dict[str, Any]:
        """计算主题统计信息"""
        
        if not qa_pairs:
            return {}
        
        # 难度分布
        difficulty_dist = {'Easy': 0, 'Medium': 0, 'Hard': 0}
        for qa in qa_pairs:
            difficulty = qa.get('difficulty', 'Medium')
            if difficulty in difficulty_dist:
                difficulty_dist[difficulty] += 1
        
        # 问题类型分布
        type_dist = {}
        for qa in qa_pairs:
            q_type = qa.get('type', 'unknown')
            type_dist[q_type] = type_dist.get(q_type, 0) + 1
        
        # 答案长度统计
        answer_lengths = [qa['answer_length'] for qa in qa_pairs]
        answer_word_counts = [qa['answer_word_count'] for qa in qa_pairs]
        
        return {
            'total_qa_pairs': len(qa_pairs),
            'difficulty_distribution': difficulty_dist,
            'difficulty_percentages': {
                k: (v / len(qa_pairs) * 100) if len(qa_pairs) > 0 else 0 
                for k, v in difficulty_dist.items()
            },
            'type_distribution': type_dist,
            'answer_length_stats': {
                'min': min(answer_lengths) if answer_lengths else 0,
                'max': max(answer_lengths) if answer_lengths else 0,
                'avg': sum(answer_lengths) / len(answer_lengths) if answer_lengths else 0
            },
            'answer_word_count_stats': {
                'min': min(answer_word_counts) if answer_word_counts else 0,
                'max': max(answer_word_counts) if answer_word_counts else 0,
                'avg': sum(answer_word_counts) / len(answer_word_counts) if answer_word_counts else 0
            }
        }
    
    def run_experiment_set(self, data_source: str, topics_data: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
        """运行一组实验（所有可用的LLM提供商）"""
        
        results = {}
        
        for provider in self.available_providers:
            logger.info(f"\n{'='*60}")
            logger.info(f"运行 {data_source} + {provider.upper()} 实验")
            logger.info(f"{'='*60}")
            
            provider_results = []
            
            for i, (topic, documents) in enumerate(topics_data.items()):
                logger.info(f"\n--- 处理主题 {i+1}/{len(topics_data)} ---")
                
                topic_result = self.process_single_topic(
                    topic, documents, data_source, provider
                )
                
                if topic_result and topic_result.get('success', False):
                    provider_results.append(topic_result)
                    
                    # 保存单个主题结果
                    safe_topic = topic.replace(' ', '_').replace('/', '_')[:50]
                    topic_file = os.path.join(
                        self.output_dir, 
                        f"{data_source}_{provider}_{i+1}_{safe_topic}.json"
                    )
                    with open(topic_file, 'w', encoding='utf-8') as f:
                        json.dump(topic_result, f, ensure_ascii=False, indent=2)
                
                # 休息避免API限制
                time.sleep(self.config['rest_time'])
            
            results[provider] = provider_results
            logger.info(f"{data_source} + {provider.upper()} 实验完成: {len(provider_results)} 个成功主题")
        
        return results
    
    def run_all_experiments(self) -> Dict[str, Any]:
        """运行所有实验"""
        
        if not self.available_providers:
            logger.error("没有可用的LLM提供商，无法运行实验")
            return {}
        
        logger.info("开始运行统一对比实验...")
        logger.info(f"实验配置: {self.config}")
        
        all_results = {
            'timestamp': self.timestamp,
            'config': self.config,
            'available_providers': self.available_providers,
            'experiments': {}
        }
        
        # 实验1: ClueWeb22数据
        logger.info(f"\n{'='*80}")
        logger.info("实验组1: ClueWeb22数据")
        logger.info(f"{'='*80}")
        
        clueweb_data = self.load_clueweb22_data()
        if clueweb_data:
            clueweb_results = self.run_experiment_set('clueweb22', clueweb_data)
            all_results['experiments']['clueweb22'] = clueweb_results
        else:
            logger.warning("ClueWeb22数据加载失败，跳过该实验组")
        
        # 实验2: 随机学术文档
        logger.info(f"\n{'='*80}")
        logger.info("实验组2: 随机学术文档")
        logger.info(f"{'='*80}")
        
        random_data = self.load_random_academic_data()
        if random_data:
            random_results = self.run_experiment_set('random_academic', random_data)
            all_results['experiments']['random_academic'] = random_results
        else:
            logger.warning("随机学术文档数据加载失败，跳过该实验组")
        
        # 生成汇总统计
        all_results['summary'] = self._generate_experiment_summary(all_results['experiments'])
        
        # 保存完整结果
        results_file = os.path.join(self.output_dir, "complete_experiment_results.json")
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        
        # 导出到Excel
        self._export_to_excel(all_results)
        
        logger.info(f"\n{'='*80}")
        logger.info("所有实验完成！")
        logger.info(f"{'='*80}")
        logger.info(f"结果保存到: {self.output_dir}")
        
        return all_results
    
    def _generate_experiment_summary(self, experiments: Dict[str, Any]) -> Dict[str, Any]:
        """生成实验汇总统计"""
        
        summary = {
            'total_experiments': 0,
            'successful_experiments': 0,
            'by_data_source': {},
            'by_provider': {},
            'comparison_matrix': {}
        }
        
        for data_source, provider_results in experiments.items():
            summary['by_data_source'][data_source] = {}
            
            for provider, results in provider_results.items():
                summary['total_experiments'] += 1
                
                if results:
                    summary['successful_experiments'] += 1
                    
                    # 按数据源统计
                    if provider not in summary['by_data_source'][data_source]:
                        summary['by_data_source'][data_source][provider] = {}
                    
                    # 按提供商统计
                    if provider not in summary['by_provider']:
                        summary['by_provider'][provider] = {}
                    
                    # 计算统计信息
                    stats = self._calculate_provider_stats(results)
                    summary['by_data_source'][data_source][provider] = stats
                    
                    if data_source not in summary['by_provider'][provider]:
                        summary['by_provider'][provider][data_source] = stats
        
        # 生成对比矩阵
        summary['comparison_matrix'] = self._generate_comparison_matrix(experiments)
        
        return summary
    
    def _calculate_provider_stats(self, results: List[Dict]) -> Dict[str, Any]:
        """计算提供商统计信息"""
        
        if not results:
            return {}
        
        total_qa_pairs = sum(len(r.get('qa_pairs', [])) for r in results)
        total_processing_time = sum(r.get('processing_time', 0) for r in results)
        
        # 汇总难度分布
        total_difficulty = {'Easy': 0, 'Medium': 0, 'Hard': 0}
        for result in results:
            stats = result.get('statistics', {})
            difficulty_dist = stats.get('difficulty_distribution', {})
            for difficulty, count in difficulty_dist.items():
                if difficulty in total_difficulty:
                    total_difficulty[difficulty] += count
        
        return {
            'topics_processed': len(results),
            'total_qa_pairs': total_qa_pairs,
            'avg_qa_pairs_per_topic': total_qa_pairs / len(results) if results else 0,
            'total_processing_time': total_processing_time,
            'avg_processing_time_per_topic': total_processing_time / len(results) if results else 0,
            'difficulty_distribution': total_difficulty,
            'difficulty_percentages': {
                k: (v / total_qa_pairs * 100) if total_qa_pairs > 0 else 0 
                for k, v in total_difficulty.items()
            }
        }
    
    def _generate_comparison_matrix(self, experiments: Dict[str, Any]) -> Dict[str, Any]:
        """生成对比矩阵"""
        
        matrix = {}
        
        for data_source, provider_results in experiments.items():
            for provider, results in provider_results.items():
                key = f"{data_source}_{provider}"
                
                if results:
                    stats = self._calculate_provider_stats(results)
                    matrix[key] = {
                        'data_source': data_source,
                        'provider': provider,
                        'success': True,
                        'topics': stats.get('topics_processed', 0),
                        'qa_pairs': stats.get('total_qa_pairs', 0),
                        'avg_processing_time': stats.get('avg_processing_time_per_topic', 0),
                        'difficulty_easy_pct': stats.get('difficulty_percentages', {}).get('Easy', 0),
                        'difficulty_medium_pct': stats.get('difficulty_percentages', {}).get('Medium', 0),
                        'difficulty_hard_pct': stats.get('difficulty_percentages', {}).get('Hard', 0)
                    }
                else:
                    matrix[key] = {
                        'data_source': data_source,
                        'provider': provider,
                        'success': False,
                        'topics': 0,
                        'qa_pairs': 0,
                        'avg_processing_time': 0,
                        'difficulty_easy_pct': 0,
                        'difficulty_medium_pct': 0,
                        'difficulty_hard_pct': 0
                    }
        
        return matrix
    
    def _export_to_excel(self, all_results: Dict[str, Any]):
        """导出结果到Excel"""
        
        try:
            excel_file = os.path.join(self.output_dir, "unified_comparative_experiment.xlsx")
            
            # 准备数据
            summary_data = []
            topics_data = []
            qa_pairs_data = []
            
            # 汇总数据
            for experiment_key, stats in all_results['summary']['comparison_matrix'].items():
                summary_data.append(stats)
            
            # 详细数据
            for data_source, provider_results in all_results['experiments'].items():
                for provider, results in provider_results.items():
                    for result in results:
                        # 主题数据
                        stats = result.get('statistics', {})
                        topic_data = {
                            'experiment': f"{data_source}_{provider}",
                            'data_source': data_source,
                            'provider': provider,
                            'topic': result.get('topic', ''),
                            'documents_count': result.get('documents_count', 0),
                            'qa_pairs_count': stats.get('total_qa_pairs', 0),
                            'processing_time': result.get('processing_time', 0),
                            'report_length': result.get('steps', {}).get('report', {}).get('length', 0),
                            'report_word_count': result.get('steps', {}).get('report', {}).get('word_count', 0),
                            'avg_answer_length': stats.get('answer_length_stats', {}).get('avg', 0),
                            'avg_answer_word_count': stats.get('answer_word_count_stats', {}).get('avg', 0),
                            'easy_questions': stats.get('difficulty_distribution', {}).get('Easy', 0),
                            'medium_questions': stats.get('difficulty_distribution', {}).get('Medium', 0),
                            'hard_questions': stats.get('difficulty_distribution', {}).get('Hard', 0)
                        }
                        topics_data.append(topic_data)
                        
                        # QA对数据
                        for qa in result.get('qa_pairs', []):
                            qa_data = {
                                'experiment': f"{data_source}_{provider}",
                                'data_source': data_source,
                                'provider': provider,
                                'topic': result.get('topic', ''),
                                'question_id': qa.get('question_id', 0),
                                'question': qa.get('question', ''),
                                'difficulty': qa.get('difficulty', ''),
                                'type': qa.get('type', ''),
                                'answer_length': qa.get('answer_length', 0),
                                'answer_word_count': qa.get('answer_word_count', 0),
                                'reasoning': qa.get('reasoning', '')
                            }
                            qa_pairs_data.append(qa_data)
            
            # 创建Excel文件
            with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
                if summary_data:
                    pd.DataFrame(summary_data).to_excel(writer, sheet_name='Experiment_Summary', index=False)
                if topics_data:
                    pd.DataFrame(topics_data).to_excel(writer, sheet_name='Topics_Detail', index=False)
                if qa_pairs_data:
                    pd.DataFrame(qa_pairs_data).to_excel(writer, sheet_name='QA_Pairs_Detail', index=False)
            
            logger.info(f"Excel文件已导出: {excel_file}")
            
        except Exception as e:
            logger.error(f"Excel导出失败: {e}")

def main():
    """主函数"""
    
    print("="*80)
    print("统一LLM对比实验系统")
    print("="*80)
    print("支持: OpenAI GPT-4o, Claude Sonnet 4")
    print("数据源: ClueWeb22, 随机学术文档")
    print("自动处理API key无效情况")
    print("="*80)
    
    # 创建实验实例
    experiment = UnifiedComparativeExperiment()
    
    if not experiment.available_providers:
        print("❌ 没有可用的LLM提供商，请检查API配置")
        return
    
    print(f"✅ 检测到可用的LLM提供商: {', '.join(experiment.available_providers)}")
    print(f"📁 结果将保存到: {experiment.output_dir}")
    
    # 运行所有实验
    results = experiment.run_all_experiments()
    
    # 打印最终摘要
    if results and 'summary' in results:
        summary = results['summary']
        print(f"\n{'='*80}")
        print("实验完成摘要")
        print(f"{'='*80}")
        print(f"总实验数: {summary['total_experiments']}")
        print(f"成功实验数: {summary['successful_experiments']}")
        print(f"成功率: {summary['successful_experiments']/summary['total_experiments']*100:.1f}%")
        
        for experiment_key, stats in summary['comparison_matrix'].items():
            if stats['success']:
                print(f"✅ {experiment_key}: {stats['topics']} 主题, {stats['qa_pairs']} QA对")
            else:
                print(f"❌ {experiment_key}: 失败")
        
        print(f"\n📊 详细结果: {experiment.output_dir}/unified_comparative_experiment.xlsx")

if __name__ == "__main__":
    main() 
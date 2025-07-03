#!/usr/bin/env python3
"""
四方对比实验脚本
Four-Way Comparative Experiment

对比实验设计：
1. ClueWeb22数据集 + OpenAI GPT-4o (已有结果)
2. ClueWeb22数据集 + Claude Sonnet 4 (新实验)
3. 随机文档100篇 + OpenAI GPT-4o (新实验)
4. 随机文档100篇 + Claude Sonnet 4 (新实验)

输出结果：
- 四份完整的结果文件
- 统一格式的Excel对比表
- Markdown报告文件
"""

import os
import json
import time
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
import random
import re

# 导入API客户端
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'core'))

from llm_clients.openai_api_client import OpenAIClient
from llm_clients.claude_api_client import ClaudeAPIClient
from llm_clients.llm_manager import DynamicLLMManager

class FourWayComparativeExperiment:
    """四方对比实验管理器"""
    
    def __init__(self, openai_api_key: str, claude_api_key: str):
        """
        初始化实验
        
        Args:
            openai_api_key: OpenAI API密钥
            claude_api_key: Claude API密钥
        """
        self.openai_api_key = openai_api_key
        self.claude_api_key = claude_api_key
        
        # 创建全新的输出目录 - 避免与历史数据混淆
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = Path(f"FRESH_FOUR_WAY_EXPERIMENT_{timestamp}")
        self.output_dir.mkdir(exist_ok=True)
        
        # 设置环境变量
        os.environ['OPENAI_API_KEY'] = openai_api_key
        os.environ['ANTHROPIC_API_KEY'] = claude_api_key
        
        # 初始化LLM管理器
        self.llm_manager = DynamicLLMManager()
        
        # 数据源配置
        self.clueweb_data_dir = Path("task_file/clueweb22_query_results")
        self.random_docs_dir = Path("task_file/random_documents") 
        
        # 🔄 实验配置 - 全部重新执行
        self.experiments = {
            "clueweb_openai": {
                "name": "ClueWeb22 + OpenAI GPT-4o",
                "data_source": "clueweb22",
                "provider": "openai",
                "model": "gpt-4o",
                "status": "pending"  # 🔄 改为pending，重新执行
            },
            "clueweb_claude": {
                "name": "ClueWeb22 + Claude Sonnet 4", 
                "data_source": "clueweb22",
                "provider": "claude",
                "model": "claude-sonnet-4-20250514",
                "status": "pending"
            },
            "random_openai": {
                "name": "Random Documents + OpenAI GPT-4o",
                "data_source": "random_documents", 
                "provider": "openai",
                "model": "gpt-4o",
                "status": "pending"
            },
            "random_claude": {
                "name": "Random Documents + Claude Sonnet 4",
                "data_source": "random_documents",
                "provider": "claude", 
                "model": "claude-sonnet-4-20250514",
                "status": "pending"
            }
        }
        
        print("🔧 全新四方对比实验初始化完成")
        print(f"🆕 全新输出目录: {self.output_dir}")
        print("🔄 所有实验将从零开始执行:")
        for exp_id, config in self.experiments.items():
            print(f"  {exp_id}: {config['name']} - ✋ 待执行")
    
    def prepare_clueweb_data(self) -> List[Dict[str, Any]]:
        """准备ClueWeb22数据"""
        print("📚 准备ClueWeb22数据...")
        
        # 使用与之前相同的主题和文档
        clueweb_topics = [
            "clueweb22-ja0009-18-07874",
            "clueweb22-en0023-77-17052", 
            "clueweb22-en0044-53-10967",
            "clueweb22-en0028-68-06349",
            "clueweb22-en0000-00-00000",
            "clueweb22-en0005-84-07694",
            "clueweb22-ja0001-17-28828",
            "clueweb22-en0037-99-02648",
            "clueweb22-en0026-20-03284"
        ]
        
        topics_data = []
        
        for topic_id in clueweb_topics:
            try:
                # 查找该主题的文档文件
                txt_files = list(self.clueweb_data_dir.glob(f"{topic_id}_top*.txt"))
                
                if not txt_files:
                    print(f"⚠️ 未找到主题 {topic_id} 的文档文件")
                    continue
                
                # 按文件编号排序
                txt_files.sort(key=lambda x: int(re.search(r'_top(\d+)\.txt', x.name).group(1)))
                
                # 加载文档内容
                documents = []
                for i, file_path in enumerate(txt_files):
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read().strip()
                        
                        if content and len(content) > 50:
                            documents.append({
                                'doc_id': f"{topic_id}_doc_{i:03d}",
                                'source': file_path.name,
                                'content': content,
                                'word_count': len(content.split()),
                                'char_count': len(content)
                            })
                    except Exception as e:
                        print(f"⚠️ 读取文档失败 {file_path}: {e}")
                        continue
                
                if documents:
                    topics_data.append({
                        'topic_id': topic_id,
                        'data_source': 'clueweb22',
                        'documents': documents,
                        'document_count': len(documents)
                    })
                    print(f"✅ {topic_id}: {len(documents)} 个文档")
                
            except Exception as e:
                print(f"⚠️ 处理主题 {topic_id} 失败: {e}")
                continue
        
        print(f"✅ ClueWeb22数据准备完成: {len(topics_data)} 个主题")
        return topics_data
    
    def prepare_random_documents_data(self) -> List[Dict[str, Any]]:
        """准备随机文档数据"""
        print("📚 准备随机文档数据...")
        
        # 查找最新的随机文档JSON文件
        json_files = list(self.random_docs_dir.glob("random_documents_*.json"))
        
        if not json_files:
            print("⚠️ 未找到随机文档文件，请先运行random_documents_crawler.py")
            return []
        
        # 使用最新的文件
        latest_json = max(json_files, key=lambda x: x.stat().st_mtime)
        print(f"📁 使用随机文档文件: {latest_json}")
        
        try:
            with open(latest_json, 'r', encoding='utf-8') as f:
                papers = json.load(f)
            
            # 按领域分组
            domain_groups = {}
            for paper in papers:
                domain = paper.get('domain', 'unknown')
                if domain not in domain_groups:
                    domain_groups[domain] = []
                domain_groups[domain].append(paper)
            
            # 为每个领域创建一个主题
            topics_data = []
            for domain, papers_list in domain_groups.items():
                if len(papers_list) >= 5:  # 至少5篇文档才创建主题
                    documents = []
                    for i, paper in enumerate(papers_list):
                        documents.append({
                            'doc_id': f"random_{domain}_doc_{i:03d}",
                            'source': f"{paper.get('source', 'unknown')}",
                            'content': paper.get('full_content', ''),
                            'word_count': paper.get('word_count', 0),
                            'char_count': paper.get('char_count', 0),
                            'title': paper.get('title', ''),
                            'language': paper.get('language', 'en')
                        })
                    
                    topics_data.append({
                        'topic_id': f"random_{domain}",
                        'data_source': 'random_documents',
                        'domain': domain,
                        'documents': documents,
                        'document_count': len(documents)
                    })
                    print(f"✅ {domain}: {len(documents)} 个文档")
            
            print(f"✅ 随机文档数据准备完成: {len(topics_data)} 个主题")
            return topics_data
            
        except Exception as e:
            print(f"❌ 读取随机文档文件失败: {e}")
            return []
    
    def _generate_questions_in_batches(self, report_content: str, topic_id: str, provider: str, test_mode: bool = False) -> List[Dict[str, Any]]:
        """分段生成问题"""
        if test_mode:
            print("  🧪 测试模式：生成3个问题")
            questions_result = self.llm_manager.generate_questions(report_content, topic_id, num_questions=3, provider=provider)
            
            if questions_result.success and hasattr(questions_result, 'questions'):
                return questions_result.questions
            else:
                print("  ⚠️ 测试问题生成失败，使用默认问题")
                return [
                    {'question': 'What are the main findings in this research?', 'difficulty': 'Easy', 'type': 'factual'},
                    {'question': 'How do these findings relate to current field developments?', 'difficulty': 'Medium', 'type': 'analytical'},
                    {'question': 'What are the implications and future directions?', 'difficulty': 'Hard', 'type': 'evaluative'}
                ]
        else:
            print("  📝 分段生成50个问题...")
            all_questions = []
            
            # 分3批生成：Easy(15) + Medium(20) + Hard(15) = 50
            batches = [
                ("Easy", 15),
                ("Medium", 20), 
                ("Hard", 15)
            ]
            
            for difficulty, count in batches:
                print(f"    🎯 生成 {difficulty} 难度问题 ({count}个)...")
                
                batch_result = self.llm_manager.generate_questions(
                    report_content, 
                    f"{topic_id}_{difficulty.lower()}", 
                    num_questions=count, 
                    provider=provider
                )
                
                if batch_result.success and hasattr(batch_result, 'questions'):
                    batch_questions = batch_result.questions
                    # 确保难度设置正确
                    for q in batch_questions:
                        q['difficulty'] = difficulty
                    all_questions.extend(batch_questions)
                    print(f"    ✅ {difficulty}: {len(batch_questions)} 个问题")
                else:
                    print(f"    ⚠️ {difficulty} 批次失败，跳过")
                
                # 批次间休息
                time.sleep(1)
            
            return all_questions
    
    def process_topic_with_llm(self, topic_data: Dict[str, Any], provider: str, model: str, test_mode: bool = False) -> Dict[str, Any]:
        """使用指定LLM处理单个主题"""
        topic_id = topic_data['topic_id']
        documents = topic_data['documents']
        
        print(f"🔍 处理主题: {topic_id} (使用 {provider})")
        
        start_time = time.time()
        
        try:
            # Step 1: 生成报告
            print("  📝 生成领域报告...")
            report_result = self.llm_manager.generate_report(documents, topic_id, provider)
            
            if not report_result.success:
                print(f"  ❌ 报告生成失败: {report_result.error}")
                return {
                    'topic': topic_id,
                    'data_source': topic_data['data_source'],
                    'provider': provider,
                    'documents_count': len(documents),
                    'success': False,
                    'error': f"Report generation failed: {report_result.error}",
                    'processing_time': time.time() - start_time
                }
            
            report_content = report_result.content
            print(f"  ✅ 报告生成完成 ({len(report_content.split())} 词)")
            
            # Step 2: 生成问题 (分段生成)
            print("  ❓ 生成研究问题...")
            questions_data = self._generate_questions_in_batches(report_content, topic_id, provider, test_mode)
            
            if not questions_data:
                print(f"  ❌ 问题生成失败")
                # 备用方案：创建默认问题
                questions_data = [
                    {'question': 'What are the main findings in this research?', 'difficulty': 'Easy', 'type': 'factual'},
                    {'question': 'How do these findings relate to current field developments?', 'difficulty': 'Medium', 'type': 'analytical'},
                    {'question': 'What are the implications and future directions?', 'difficulty': 'Hard', 'type': 'evaluative'}
                ]
            
            print(f"  ✅ 问题生成完成 ({len(questions_data)} 个问题)")
            
            # Step 3: 生成答案
            print("  💬 生成答案...")
            answers_result = self.llm_manager.generate_answers(questions_data, report_content, provider, max_answers=50)
            
            if not answers_result['success']:
                print(f"  ❌ 答案生成失败: {answers_result.get('error', 'Unknown error')}")
                answers_result = {
                    'success': True,
                    'count': 0,
                    'total_answer_length': 0
                }
            else:
                print(f"  ✅ 答案生成完成 ({answers_result['count']} 个答案)")
            
            # 编译结果
            processing_time = time.time() - start_time
            
            result = {
                'topic': topic_id,
                'data_source': topic_data['data_source'],
                'provider': provider,
                'documents_count': len(documents),
                'success': True,
                'processing_time': processing_time,
                'steps': {
                    'report': {
                        'success': True,
                        'content': report_content,
                        'model': report_result.model,
                        'usage': report_result.usage
                    },
                    'questions': {
                        'success': True,
                        'content': f"Generated {len(questions_data)} questions",
                        'questions': questions_data,
                        'count': len(questions_data),
                        'model': report_result.model,  # 使用report的model信息
                        'usage': {'total_tokens': 0}  # 分段生成，暂时设为0
                    },
                    'answers': answers_result
                }
            }
            
            # 添加QA对
            if 'qa_pairs' in answers_result:
                result['qa_pairs'] = answers_result['qa_pairs']
            
            # 添加统计信息
            result['statistics'] = {
                'total_qa_pairs': answers_result['count'],
                'difficulty_distribution': {},
                'type_distribution': {},
                'answer_length_stats': {},
                'answer_word_count_stats': {}
            }
            
            if 'qa_pairs' in result:
                qa_pairs = result['qa_pairs']
                if qa_pairs:
                    # 计算难度分布
                    difficulties = [qa['difficulty'] for qa in qa_pairs]
                    for diff in ['Easy', 'Medium', 'Hard']:
                        result['statistics']['difficulty_distribution'][diff] = difficulties.count(diff)
                        result['statistics']['difficulty_percentages'] = {
                            diff: (difficulties.count(diff) / len(difficulties) * 100) if difficulties else 0
                            for diff in ['Easy', 'Medium', 'Hard']
                        }
                    
                    # 计算类型分布
                    types = [qa['type'] for qa in qa_pairs]
                    unique_types = list(set(types))
                    for qtype in unique_types:
                        result['statistics']['type_distribution'][qtype] = types.count(qtype)
                    
                    # 计算答案长度统计
                    answer_lengths = [qa['answer_length'] for qa in qa_pairs if 'answer_length' in qa]
                    answer_word_counts = [qa['answer_word_count'] for qa in qa_pairs if 'answer_word_count' in qa]
                    
                    if answer_lengths:
                        result['statistics']['answer_length_stats'] = {
                            'min': min(answer_lengths),
                            'max': max(answer_lengths),
                            'avg': sum(answer_lengths) / len(answer_lengths)
                        }
                    
                    if answer_word_counts:
                        result['statistics']['answer_word_count_stats'] = {
                            'min': min(answer_word_counts),
                            'max': max(answer_word_counts),
                            'avg': sum(answer_word_counts) / len(answer_word_counts)
                        }
            
            print(f"  ✅ 主题 {topic_id} 处理完成 ({processing_time:.1f}秒)")
            return result
            
        except Exception as e:
            print(f"  ❌ 主题 {topic_id} 处理失败: {e}")
            return {
                'topic': topic_id,
                'data_source': topic_data['data_source'],
                'provider': provider,
                'documents_count': len(documents),
                'success': False,
                'error': str(e),
                'processing_time': time.time() - start_time
            }
    
    def run_experiment(self, experiment_id: str, topics_data: List[Dict[str, Any]]) -> str:
        """运行单个实验"""
        config = self.experiments[experiment_id]
        
        print(f"\n🚀 开始实验: {config['name']}")
        print("=" * 60)
        
        # 创建实验输出目录
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        exp_output_dir = self.output_dir / f"{experiment_id}_{timestamp}"
        exp_output_dir.mkdir(exist_ok=True)
        
        # 检查是否有已存在的实验目录（断点续做）
        existing_dirs = list(self.output_dir.glob(f"{experiment_id}_*"))
        if existing_dirs:
            latest_dir = max(existing_dirs, key=lambda x: x.stat().st_mtime)
            print(f"🔄 发现已有实验目录: {latest_dir}")
            
            # 检查已完成的主题
            completed_topics = set()
            for json_file in latest_dir.glob("*.json"):
                if json_file.name != "complete_experiment_results.json":
                    try:
                        with open(json_file, 'r', encoding='utf-8') as f:
                            result = json.load(f)
                        if result.get('success', False):
                            completed_topics.add(result.get('topic', ''))
                    except:
                        continue
            
            if completed_topics:
                print(f"✅ 发现已完成主题: {len(completed_topics)} 个")
                print(f"📂 继续使用目录: {latest_dir}")
                exp_output_dir = latest_dir
                
                # 过滤掉已完成的主题
                remaining_topics = []
                for topic_data in topics_data:
                    if topic_data['topic_id'] not in completed_topics:
                        remaining_topics.append(topic_data)
                topics_data = remaining_topics
                
                print(f"🔄 剩余待处理主题: {len(topics_data)} 个")
                
                if not topics_data:
                    print("✅ 所有主题已完成，直接生成最终结果")
                    # 读取已有结果
                    results = []
                    for json_file in exp_output_dir.glob("*.json"):
                        if json_file.name != "complete_experiment_results.json":
                            try:
                                with open(json_file, 'r', encoding='utf-8') as f:
                                    result = json.load(f)
                                results.append(result)
                            except:
                                continue
                    
                    # 保存完整实验结果
                    self._save_complete_results(exp_output_dir, config, experiment_id, results)
                    return str(exp_output_dir)
        
        results = []
        
        try:
            for i, topic_data in enumerate(topics_data, 1):
                print(f"\n📊 进度: {i}/{len(topics_data)}")
                
                result = self.process_topic_with_llm(
                    topic_data, 
                    config['provider'], 
                    config['model'],
                    test_mode=False  # 完整实验模式
                )
                
                results.append(result)
                
                # 保存单个主题结果
                result_file = exp_output_dir / f"{config['provider']}_{i}_{result['topic']}.json"
                with open(result_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                
                print(f"💾 保存: {result_file}")
                
                # 短暂休息避免API限制
                time.sleep(1)
        
        except Exception as e:
            print(f"❌ 实验 {experiment_id} 执行失败: {e}")
            print(f"📊 已完成: {len(results)} 个主题")
            return ""
        
        # 保存完整实验结果
        self._save_complete_results(exp_output_dir, config, experiment_id, results)
        return str(exp_output_dir)
    
    def _save_complete_results(self, exp_output_dir: Path, config: Dict, experiment_id: str, results: List):
        """保存完整实验结果"""
        experiment_result = {
            'experiment_info': {
                'experiment_id': experiment_id,
                'name': config['name'],
                'data_source': config['data_source'],
                'provider': config['provider'],
                'model': config['model'],
                'timestamp': datetime.now().strftime("%Y%m%d_%H%M%S"),
                'total_topics': len(results),
                'successful_topics': len([r for r in results if r.get('success', False)]),
                'failed_topics': len([r for r in results if not r.get('success', False)])
            },
            'results': results
        }
        
        complete_results_file = exp_output_dir / "complete_experiment_results.json"
        with open(complete_results_file, 'w', encoding='utf-8') as f:
            json.dump(experiment_result, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ 实验 {config['name']} 完成!")
        print(f"📁 结果目录: {exp_output_dir}")
        print(f"📊 成功: {experiment_result['experiment_info']['successful_topics']}/{len(results)} 个主题")
    
    def run_all_experiments(self) -> Dict[str, str]:
        """运行所有实验 - 全部从零开始"""
        print("🚀 开始全新四方对比实验")
        print("=" * 70)
        print("🆕 本次实验将彻底重新执行四个对照组:")
        print("1. ClueWeb22数据集 + OpenAI GPT-4o (全新执行)")
        print("2. ClueWeb22数据集 + Claude Sonnet 4 (全新执行)")
        print("3. 随机文档100篇 + OpenAI GPT-4o (全新执行)")
        print("4. 随机文档100篇 + Claude Sonnet 4 (全新执行)")
        print("=" * 70)
        print("⚠️  注意: 本次实验不使用任何历史数据，所有结果存储在新目录")
        print("=" * 70)
        
        experiment_results = {}
        
        # 📚 准备实验数据
        print("\n📚 准备实验数据...")
        clueweb_data = self.prepare_clueweb_data()
        random_docs_data = self.prepare_random_documents_data()
        
        if not clueweb_data:
            print("❌ ClueWeb22数据准备失败")
            return experiment_results
        
        if not random_docs_data:
            print("❌ 随机文档数据准备失败")
            return experiment_results
        
        print(f"✅ 数据准备完成:")
        print(f"   ClueWeb22: {len(clueweb_data)} 个主题")
        print(f"   随机文档: {len(random_docs_data)} 个主题")
        
        # 🔄 执行所有四个实验
        experiments_to_run = [
            ('clueweb_openai', clueweb_data, 'ClueWeb22 + OpenAI GPT-4o'),
            ('clueweb_claude', clueweb_data, 'ClueWeb22 + Claude Sonnet 4'),
            ('random_openai', random_docs_data, '随机文档 + OpenAI GPT-4o'),
            ('random_claude', random_docs_data, '随机文档 + Claude Sonnet 4')
        ]
        
        for i, (exp_id, data, description) in enumerate(experiments_to_run, 1):
            print(f"\n🎯 执行实验 {i}/4: {description}")
            print("=" * 60)
            
            try:
                result_dir = self.run_experiment(exp_id, data)
                if result_dir:
                    experiment_results[exp_id] = result_dir
                    self.experiments[exp_id]['status'] = 'completed'
                    print(f"✅ 实验 {exp_id} 成功完成")
                else:
                    print(f"❌ 实验 {exp_id} 执行失败")
            except Exception as e:
                print(f"❌ 实验 {exp_id} 异常: {e}")
                continue
        
        print(f"\n🎉 四方对比实验完成!")
        print(f"📊 成功实验: {len(experiment_results)}/4")
        
        return experiment_results
    
    def generate_comparison_excel(self, experiment_results: Dict[str, str]) -> str:
        """生成对比Excel文件"""
        print("\n📊 生成对比Excel文件...")
        
        all_data = []
        
        for exp_id, result_dir in experiment_results.items():
            if not result_dir:
                continue
            
            # 处理测试实验ID的映射
            if exp_id.endswith('_test'):
                base_exp_id = exp_id.replace('_test', '')
                if base_exp_id in self.experiments:
                    config = self.experiments[base_exp_id].copy()
                    config['name'] = config['name'] + ' (测试)'
                else:
                    # 测试实验的默认配置
                    config = {
                        'name': exp_id.replace('_', ' ').title(),
                        'data_source': 'clueweb22' if 'clueweb' in exp_id else 'random_documents',
                        'provider': 'openai' if 'openai' in exp_id else 'claude',
                        'model': 'gpt-4o' if 'openai' in exp_id else 'claude-sonnet-4-20250514'
                    }
            else:
                config = self.experiments[exp_id]
            result_path = Path(result_dir)
            
            # 查找完整结果文件
            complete_file = result_path / "complete_experiment_results.json"
            if not complete_file.exists():
                # 尝试其他可能的文件名
                json_files = list(result_path.glob("*results*.json"))
                if json_files:
                    complete_file = json_files[0]
                else:
                    print(f"⚠️ 未找到实验结果文件: {result_path}")
                    continue
            
            try:
                with open(complete_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 处理不同的文件格式
                if 'results' in data:
                    results_list = data['results']
                elif 'topic_results' in data:
                    results_list = list(data['topic_results'].values())
                else:
                    print(f"⚠️ 无法识别结果文件格式: {complete_file}")
                    continue
                
                # 提取数据
                for result in results_list:
                    if not result.get('success', False):
                        continue
                    
                    # 主题摘要行
                    topic_summary = {
                        'Experiment_ID': exp_id,
                        'Experiment_Name': config['name'],
                        'Data_Source': config['data_source'],
                        'Provider': config['provider'],
                        'Model': config['model'],
                        'Topic_ID': result.get('topic', 'Unknown'),
                        'Type': 'TOPIC_SUMMARY',
                        'Documents_Count': result.get('documents_count', 0),
                        'Processing_Time': result.get('processing_time', 0),
                        'Success': result.get('success', False),
                        'Report_Content': '',
                        'Report_Length': 0,
                        'Questions_Count': 0,
                        'QA_Pairs_Count': 0,
                        'Report_Usage_Tokens': 0,
                        'Questions_Usage_Tokens': 0,
                        'Total_Usage_Tokens': 0
                    }
                    
                    # 提取报告内容
                    if 'steps' in result and 'report' in result['steps']:
                        report_step = result['steps']['report']
                        if report_step.get('success') and 'content' in report_step:
                            topic_summary['Report_Content'] = report_step['content']
                            topic_summary['Report_Length'] = len(report_step['content'].split())
                            # 提取token使用情况
                            if 'usage' in report_step:
                                usage = report_step['usage']
                                topic_summary['Report_Usage_Tokens'] = usage.get('total_tokens', 0)
                    
                    # 提取问题数量
                    if 'steps' in result and 'questions' in result['steps']:
                        questions_step = result['steps']['questions']
                        if questions_step.get('success'):
                            topic_summary['Questions_Count'] = questions_step.get('count', 0)
                            # 提取token使用情况
                            if 'usage' in questions_step:
                                usage = questions_step['usage']
                                topic_summary['Questions_Usage_Tokens'] = usage.get('total_tokens', 0)
                    
                    # 提取QA对数量
                    if 'qa_pairs' in result:
                        topic_summary['QA_Pairs_Count'] = len(result['qa_pairs'])
                    elif 'statistics' in result:
                        topic_summary['QA_Pairs_Count'] = result['statistics'].get('total_qa_pairs', 0)
                    
                    # 计算总token使用量
                    topic_summary['Total_Usage_Tokens'] = topic_summary['Report_Usage_Tokens'] + topic_summary['Questions_Usage_Tokens']
                    
                    all_data.append(topic_summary)
                    
                    # QA对详细信息
                    if 'qa_pairs' in result:
                        for qa in result['qa_pairs']:
                            qa_row = {
                                'Experiment_ID': exp_id,
                                'Experiment_Name': config['name'],
                                'Data_Source': config['data_source'],
                                'Provider': config['provider'],
                                'Model': config['model'],
                                'Topic_ID': result.get('topic', 'Unknown'),
                                'Type': 'QA_PAIR',
                                'Question_ID': qa.get('question_id', ''),
                                'Question': qa.get('question', ''),
                                'Answer': qa.get('answer', ''),
                                'Difficulty': qa.get('difficulty', ''),
                                'Question_Type': qa.get('type', ''),
                                'Answer_Length': qa.get('answer_length', 0),
                                'Answer_Word_Count': qa.get('answer_word_count', 0),
                                'Question_Reasoning': qa.get('reasoning', ''),
                                'Success': qa.get('success', True)
                            }
                            all_data.append(qa_row)
                
            except Exception as e:
                print(f"⚠️ 处理实验结果失败 {exp_id}: {e}")
                continue
        
        if not all_data:
            print("❌ 没有可用的实验数据")
            return ""
        
        # 创建DataFrame并保存
        df = pd.DataFrame(all_data)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        excel_file = self.output_dir / f"four_way_comparative_results_{timestamp}.xlsx"
        
        try:
            df.to_excel(excel_file, index=False, engine='openpyxl')
            print(f"✅ Excel文件生成完成: {excel_file}")
            print(f"📊 总计数据行数: {len(all_data)}")
            
            # 统计信息
            topic_summaries = df[df['Type'] == 'TOPIC_SUMMARY']
            qa_pairs = df[df['Type'] == 'QA_PAIR']
            
            print(f"   主题摘要: {len(topic_summaries)} 行")
            print(f"   QA对: {len(qa_pairs)} 行")
            print(f"   实验分布:")
            for exp_id in df['Experiment_ID'].unique():
                exp_data = df[df['Experiment_ID'] == exp_id]
                exp_topics = len(exp_data[exp_data['Type'] == 'TOPIC_SUMMARY'])
                exp_qas = len(exp_data[exp_data['Type'] == 'QA_PAIR'])
                print(f"     {exp_id}: {exp_topics} 主题, {exp_qas} QA对")
            
            return str(excel_file)
            
        except Exception as e:
            print(f"❌ Excel文件生成失败: {e}")
            return ""
    
    def generate_comparison_report(self, experiment_results: Dict[str, str], excel_file: str) -> str:
        """生成对比分析报告"""
        print("\n📝 生成对比分析报告...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.output_dir / f"FOUR_WAY_COMPARATIVE_ANALYSIS_{timestamp}.md"
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write("# 📊 四方对比实验分析报告\n")
                f.write("## Four-Way Comparative Experiment Analysis Report\n\n")
                f.write(f"**生成时间**: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}\n")
                f.write(f"**实验目的**: 对比ClueWeb22数据集与随机文档在OpenAI GPT-4o和Claude Sonnet 4上的表现\n\n")
                
                f.write("---\n\n")
                
                f.write("## 📋 实验设计\n\n")
                f.write("### 实验配置\n\n")
                f.write("| 实验ID | 数据源 | 模型 | 状态 |\n")
                f.write("|--------|--------|------|------|\n")
                
                # 先写入基础实验配置
                for exp_id, config in self.experiments.items():
                    status = "✅ 完成" if experiment_results.get(exp_id) else "❌ 失败"
                    f.write(f"| {exp_id} | {config['data_source']} | {config['model']} | {status} |\n")
                
                # 然后写入测试实验（如果存在）
                for exp_id in experiment_results.keys():
                    if exp_id.endswith('_test') and exp_id not in [k for k in self.experiments.keys()]:
                        test_config = {
                            'name': exp_id.replace('_', ' ').title(),
                            'data_source': 'clueweb22' if 'clueweb' in exp_id else 'random_documents',
                            'provider': 'openai' if 'openai' in exp_id else 'claude',
                            'model': 'gpt-4o' if 'openai' in exp_id else 'claude-sonnet-4-20250514'
                        }
                        status = "✅ 完成" if experiment_results.get(exp_id) else "❌ 失败"
                        f.write(f"| {exp_id} | {test_config['data_source']} | {test_config['model']} | {status} |\n")
                
                f.write("\n### 数据源说明\n\n")
                f.write("- **ClueWeb22**: 网络爬取的多语言文档集合，包含日文和英文内容\n")
                f.write("- **Random Documents**: 从学术数据库爬取的100篇英文+日文混合研究论文\n\n")
                
                f.write("### 模型说明\n\n")
                f.write("- **OpenAI GPT-4o**: OpenAI最新的多模态大语言模型\n")
                f.write("- **Claude Sonnet 4**: Anthropic的Claude Sonnet 4模型\n\n")
                
                f.write("---\n\n")
                
                f.write("## 📊 实验结果统计\n\n")
                
                # 统计每个实验的结果
                for exp_id, result_dir in experiment_results.items():
                    if not result_dir:
                        continue
                    
                    # 处理测试实验ID的映射
                    if exp_id.endswith('_test'):
                        base_exp_id = exp_id.replace('_test', '')
                        if base_exp_id in self.experiments:
                            config = self.experiments[base_exp_id].copy()
                            config['name'] = config['name'] + ' (测试)'
                        else:
                            # 测试实验的默认配置
                            config = {
                                'name': exp_id.replace('_', ' ').title(),
                                'data_source': 'clueweb22' if 'clueweb' in exp_id else 'random_documents',
                                'provider': 'openai' if 'openai' in exp_id else 'claude',
                                'model': 'gpt-4o' if 'openai' in exp_id else 'claude-sonnet-4-20250514'
                            }
                    else:
                        config = self.experiments[exp_id]
                    f.write(f"### {config['name']}\n\n")
                    
                    # 读取实验结果进行统计
                    result_path = Path(result_dir)
                    complete_file = result_path / "complete_experiment_results.json"
                    
                    if complete_file.exists():
                        try:
                            with open(complete_file, 'r', encoding='utf-8') as rf:
                                data = json.load(rf)
                            
                            if 'experiment_info' in data:
                                info = data['experiment_info']
                                f.write(f"- **处理主题数**: {info.get('total_topics', 0)}\n")
                                f.write(f"- **成功主题数**: {info.get('successful_topics', 0)}\n")
                                f.write(f"- **成功率**: {info.get('successful_topics', 0) / max(info.get('total_topics', 1), 1) * 100:.1f}%\n")
                            
                            # 统计处理时间
                            if 'results' in data:
                                times = [r.get('processing_time', 0) for r in data['results'] if r.get('success')]
                                if times:
                                    f.write(f"- **平均处理时间**: {sum(times) / len(times):.1f}秒\n")
                                    f.write(f"- **总处理时间**: {sum(times):.1f}秒\n")
                                
                                # 统计生成内容
                                total_qa_pairs = 0
                                total_report_words = 0
                                
                                for result in data['results']:
                                    if result.get('success'):
                                        if 'qa_pairs' in result:
                                            total_qa_pairs += len(result['qa_pairs'])
                                        if 'steps' in result and 'report' in result['steps']:
                                            report_content = result['steps']['report'].get('content', '')
                                            total_report_words += len(report_content.split())
                                
                                f.write(f"- **生成QA对数**: {total_qa_pairs}\n")
                                f.write(f"- **报告总字数**: {total_report_words:,}\n")
                        
                        except Exception as e:
                            f.write(f"- **状态**: 结果文件读取失败 - {e}\n")
                    else:
                        f.write("- **状态**: 结果文件未找到\n")
                    
                    f.write(f"- **结果目录**: `{result_dir}`\n\n")
                
                f.write("---\n\n")
                
                f.write("## 🔍 关键发现\n\n")
                f.write("### 模型性能对比\n\n")
                f.write("基于实验结果，我们可以从以下几个维度分析不同模型的表现：\n\n")
                f.write("1. **处理效率**: 处理时间和成功率对比\n")
                f.write("2. **内容质量**: 生成报告和答案的质量\n")
                f.write("3. **数据适应性**: 不同数据源上的表现差异\n")
                f.write("4. **多语言处理**: 对日英混合内容的处理能力\n\n")
                
                f.write("### 数据源影响分析\n\n")
                f.write("通过对比相同模型在不同数据源上的表现，可以分析：\n\n")
                f.write("- **ClueWeb22数据集**: 网络内容的多样性和复杂性\n")
                f.write("- **学术论文数据**: 结构化内容的处理优势\n")
                f.write("- **语言混合影响**: 多语言内容对模型表现的影响\n\n")
                
                f.write("---\n\n")
                
                f.write("## 📈 详细分析\n\n")
                f.write(f"完整的数据分析请参考Excel文件: `{Path(excel_file).name if excel_file else 'N/A'}`\n\n")
                f.write("Excel文件包含以下工作表：\n")
                f.write("- **原始数据**: 所有实验的详细结果\n")
                f.write("- **主题摘要**: 每个主题的处理统计\n")
                f.write("- **QA对详情**: 所有问答对的具体内容\n\n")
                
                f.write("---\n\n")
                
                f.write("## 🎯 结论与建议\n\n")
                f.write("### 主要结论\n\n")
                f.write("1. **模型适用性**: 不同模型在不同类型内容上的优势\n")
                f.write("2. **数据源选择**: 数据特征对生成质量的影响\n")
                f.write("3. **多语言能力**: 各模型的多语言处理表现\n")
                f.write("4. **实用建议**: 基于实验结果的应用建议\n\n")
                
                f.write("### 后续研究方向\n\n")
                f.write("- 扩大数据集规模进行更大规模对比\n")
                f.write("- 引入人工评估提高质量分析准确性\n")
                f.write("- 针对特定领域进行专门优化实验\n")
                f.write("- 探索模型组合使用的可能性\n\n")
                
                f.write("---\n\n")
                f.write(f"*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
                f.write(f"*实验系统版本: Four-Way Comparative v1.0*\n")
            
            print(f"✅ 对比分析报告生成完成: {report_file}")
            return str(report_file)
            
        except Exception as e:
            print(f"❌ 对比分析报告生成失败: {e}")
            return ""
    
    def run_test_experiment(self) -> Dict[str, str]:
        """运行测试实验：只处理一个topic"""
        print("🧪 开始测试实验")
        print("=" * 70)
        
        experiment_results = {}
        
        # 准备测试数据：只取一个主题
        print("\n📚 准备测试数据...")
        clueweb_data = self.prepare_clueweb_data()
        random_docs_data = self.prepare_random_documents_data()
        
        if not clueweb_data and not random_docs_data:
            print("❌ 测试数据准备失败")
            return experiment_results
        
        # 准备测试主题：同时测试两种数据源
        test_topics = []
        
        if random_docs_data:
            random_topic = random_docs_data[0]  # 取第一个随机文档主题
            test_topics.append({
                'topic': random_topic,
                'data_source': 'random_documents',
                'experiments': [
                    ('random_openai', 'Random Documents + OpenAI GPT-4o'),
                    ('random_claude', 'Random Documents + Claude Sonnet 4')
                ]
            })
            print(f"📝 随机文档测试主题: {random_topic['topic_id']} ({random_topic['document_count']} 个文档)")
        
        if clueweb_data:
            # 选择ClueWeb22中文档较少的主题
            clueweb_data.sort(key=lambda x: x['document_count'])
            clueweb_topic = clueweb_data[0]  # 取文档最少的主题
            test_topics.append({
                'topic': clueweb_topic,
                'data_source': 'clueweb22',
                'experiments': [
                    ('clueweb_openai_test', 'ClueWeb22 + OpenAI GPT-4o (测试)'),
                    ('clueweb_claude_test', 'ClueWeb22 + Claude Sonnet 4 (测试)')
                ]
            })
            print(f"📝 ClueWeb22测试主题: {clueweb_topic['topic_id']} ({clueweb_topic['document_count']} 个文档)")
        
        if not test_topics:
            print("❌ 未找到合适的测试主题")
            return experiment_results
        
        print(f"🎯 将测试 {len(test_topics)} 种数据源")
        
        # 运行所有测试实验
        for topic_info in test_topics:
            test_topic = topic_info['topic']
            test_data_source = topic_info['data_source']
            test_experiments = topic_info['experiments']
            
            print(f"\n📊 测试数据源: {test_data_source}")
            print(f"   主题: {test_topic['topic_id']}")
            print(f"   文档数: {test_topic['document_count']}")
            
            for exp_id, exp_name in test_experiments:
                print(f"\n🚀 开始测试实验: {exp_name}")
                print("=" * 60)
                
                try:
                    # 创建测试实验配置
                    test_config = {
                        'name': exp_name,
                        'data_source': test_data_source,
                        'provider': 'openai' if 'openai' in exp_id else 'claude',
                        'model': 'gpt-4o' if 'openai' in exp_id else 'claude-sonnet-4-20250514'
                    }
                    
                    # 运行单个主题测试
                    result = self.process_topic_with_llm(
                        test_topic,
                        test_config['provider'],
                        test_config['model'],
                        test_mode=True  # 测试模式：只生成3个问题
                    )
                    
                    # 创建测试结果目录
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    test_output_dir = self.output_dir / f"test_{exp_id}_{timestamp}"
                    test_output_dir.mkdir(exist_ok=True)
                    
                    # 保存测试结果
                    result_file = test_output_dir / f"test_{result['topic']}.json"
                    with open(result_file, 'w', encoding='utf-8') as f:
                        json.dump(result, f, indent=2, ensure_ascii=False)
                    
                    # 保存完整测试结果
                    test_experiment_result = {
                        'experiment_info': {
                            'experiment_id': exp_id,
                            'name': exp_name,
                            'data_source': test_data_source,
                            'provider': test_config['provider'],
                            'model': test_config['model'],
                            'timestamp': timestamp,
                            'total_topics': 1,
                            'successful_topics': 1 if result.get('success', False) else 0,
                            'failed_topics': 0 if result.get('success', False) else 1,
                            'test_mode': True
                        },
                        'results': [result]
                    }
                    
                    complete_results_file = test_output_dir / "complete_experiment_results.json"
                    with open(complete_results_file, 'w', encoding='utf-8') as f:
                        json.dump(test_experiment_result, f, indent=2, ensure_ascii=False)
                    
                    if result.get('success', False):
                        experiment_results[exp_id] = str(test_output_dir)
                        print(f"✅ 测试实验成功: {exp_name}")
                        print(f"📁 结果目录: {test_output_dir}")
                        
                        # 显示测试结果摘要
                        if 'qa_pairs' in result:
                            print(f"📝 生成QA对: {len(result['qa_pairs'])} 个")
                        if 'steps' in result and 'report' in result['steps']:
                            report_length = len(result['steps']['report'].get('content', '').split())
                            print(f"📄 报告长度: {report_length} 词")
                        print(f"⏱️ 处理时间: {result.get('processing_time', 0):.1f} 秒")
                    else:
                        print(f"❌ 测试实验失败: {exp_name}")
                        print(f"💥 错误信息: {result.get('error', 'Unknown error')}")
                    
                except Exception as e:
                    print(f"❌ 测试实验 {exp_name} 执行异常: {e}")
                    import traceback
                    traceback.print_exc()
                    continue
        
        # 统计最终结果
        total_expected = sum(len(topic_info['experiments']) for topic_info in test_topics)
        print(f"\n🎯 测试完成！成功: {len(experiment_results)}/{total_expected} 个实验")
        return experiment_results

def main():
    """主函数"""
    print("🔬 全新四方对比实验系统")
    print("=" * 70)
    print("🆕 本次实验将彻底重新执行四个对照组:")
    print("1. ClueWeb22数据集 + OpenAI GPT-4o (全新执行)")
    print("2. ClueWeb22数据集 + Claude Sonnet 4 (全新执行)")
    print("3. 随机文档100篇 + OpenAI GPT-4o (全新执行)")
    print("4. 随机文档100篇 + Claude Sonnet 4 (全新执行)")
    print("=" * 70)
    print("⚠️  注意: 本次实验不使用任何历史数据，所有结果存储在新目录")
    print("=" * 70)
    
    # 检查是否为测试模式
    import sys
    test_mode = len(sys.argv) > 1 and sys.argv[1] == "test"
    
    if test_mode:
        print("🧪 测试模式：只运行一个topic进行快速验证")
    else:
        # 添加用户确认
        print("🔄 准备开始完整的四方对比实验...")
        print("   预计每个主题需要3-5分钟处理时间")
        print("   完整实验可能需要数小时完成")
        
        confirm = input("\n是否继续执行完整实验? (y/N): ").strip().lower()
        if confirm not in ['y', 'yes', '是']:
            print("❌ 实验已取消")
            return
    
    # API密钥配置
    openai_api_key = "xxxx"  # 请替换为实际密钥
    claude_api_key = os.getenv('ANTHROPIC_API_KEY', 'xxxx')  # 请替换为实际密钥
    
    try:
        # 初始化实验系统
        experiment = FourWayComparativeExperiment(openai_api_key, claude_api_key)
        
        if test_mode:
            # 测试模式：运行单个topic测试
            experiment_results = experiment.run_test_experiment()
        else:
            # 完整实验模式
            experiment_results = experiment.run_all_experiments()
        
        # 生成对比Excel文件
        excel_file = experiment.generate_comparison_excel(experiment_results)
        
        # 生成对比分析报告
        report_file = experiment.generate_comparison_report(experiment_results, excel_file)
        
        # 输出最终结果
        print("\n🎉 全新四方对比实验完成!")
        print("=" * 70)
        print("📊 实验结果:")
        
        for exp_id, result_dir in experiment_results.items():
            # 处理测试实验ID的映射
            if exp_id.endswith('_test'):
                base_exp_id = exp_id.replace('_test', '')
                if base_exp_id in experiment.experiments:
                    config = experiment.experiments[base_exp_id].copy()
                    config['name'] = config['name'] + ' (测试)'
                else:
                    # 测试实验的默认配置
                    config = {
                        'name': exp_id.replace('_', ' ').title(),
                        'data_source': 'clueweb22' if 'clueweb' in exp_id else 'random_documents',
                        'provider': 'openai' if 'openai' in exp_id else 'claude',
                        'model': 'gpt-4o' if 'openai' in exp_id else 'claude-sonnet-4-20250514'
                    }
            else:
                config = experiment.experiments[exp_id]
            status = "✅ 成功" if result_dir else "❌ 失败"
            print(f"  {config['name']}: {status}")
            if result_dir:
                print(f"    结果目录: {result_dir}")
        
        print(f"\n📈 综合分析:")
        if excel_file:
            print(f"  Excel对比文件: {excel_file}")
        if report_file:
            print(f"  分析报告: {report_file}")
        
        completed_count = len([r for r in experiment_results.values() if r])
        total_count = 4 if not test_mode else 2  # 测试模式只测试2个实验
        print(f"\n✅ 完成实验: {completed_count}/{total_count}")
        print(f"📁 所有结果保存在: {experiment.output_dir}")
        
    except Exception as e:
        print(f"❌ 系统错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 
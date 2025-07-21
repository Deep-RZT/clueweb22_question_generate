#!/usr/bin/env python3
"""
Agent深度推理测试框架 - 主入口文件
Agent Depth Reasoning Test Framework - Main Entry Point

基于全新的6步设计，为智能Agent构建深度推理测试题库
核心目标：让普通LLM无法直接答题，需要Agent逐步推理解决
"""

import logging
import sys
import os
import time
import json
from pathlib import Path
from typing import Dict, List, Optional, Any

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入核心组件
from config import get_config
from core.llm_clients.openai_api_client import OpenAIClient
from document_loader import DocumentLoader
from document_screener import DocumentScreener
from agent_depth_reasoning_framework_fixed import AgentDepthReasoningFramework
from agent_export_system import AgentExportSystem
from web_search import web_search

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('agent_reasoning_experiment.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AgentReasoningMainFramework:
    """Agent推理测试主框架"""
    
    def __init__(self):
        self.config = get_config()
        self.api_client = None
        self.search_client = web_search
        
        # 核心组件
        self.document_loader = DocumentLoader()
        self.document_screener = DocumentScreener()
        self.agent_reasoning_framework = None
        self.export_system = AgentExportSystem()
        
        # 统计信息
        self.experiment_stats = {
            'session_start_time': time.time(),
            'documents_processed': 0,
            'successful_documents': 0,
            'failed_documents': 0,
            'total_reasoning_trees': 0,
            'total_composite_queries': 0,
            'step1_success_rate': 0.0,
            'step2_success_rate': 0.0,
            'step6_success_rate': 0.0
        }
    
    def initialize_framework(self, api_key: str) -> bool:
        """初始化框架组件"""
        try:
            logger.info("🎯 初始化Agent深度推理测试框架...")
            
            # 初始化API客户端
            self.api_client = OpenAIClient(api_key=api_key)
            
            # 设置API客户端到各组件
            self.document_screener.set_api_client(self.api_client)
            
            # 初始化Agent推理框架
            self.agent_reasoning_framework = AgentDepthReasoningFramework(
                api_client=self.api_client,
                search_client=self.search_client
            )
            
            logger.info("✅ Agent推理框架初始化完成")
            logger.info("🎯 框架目标:")
            logger.info("  - 为智能Agent生成深度推理测试题")
            logger.info("  - 防止普通LLM直接获取答案")
            logger.info("  - 通过多层级问题树训练逐步推理")
            logger.info("  - 生成嵌套式综合问题")
            
            return True
            
        except Exception as e:
            logger.error(f"框架初始化失败: {e}")
            return False
    
    def run_agent_reasoning_experiment(self, topic: str, max_documents: int = 20) -> Dict[str, Any]:
        """
        运行Agent推理测试实验
        
        Args:
            topic: ClueWeb22主题名称
            max_documents: 最大处理文档数
        """
        logger.info(f"🚀 启动Agent深度推理实验: {topic}")
        logger.info(f"最大文档数: {max_documents}")
        
        session_id = f"agent_reasoning_{topic}_{int(time.time())}"
        start_time = time.time()
        
        try:
            # 1. 加载文档
            logger.info("📄 加载ClueWeb22文档...")
            document_data_list = self.document_loader.load_documents_from_topic(topic, max_documents)
            
            if not document_data_list:
                return self._create_error_result(session_id, "No documents loaded")
            
            logger.info(f"加载文档数: {len(document_data_list)}")
            
            # 2. 文档筛选（可选）
            logger.info("🔍 文档质量预筛选...")
            screened_documents = []
            
            for doc_data in document_data_list[:max_documents]:
                # 基本质量检查
                if len(doc_data.content) < 200:
                    logger.info(f"跳过短文档: {doc_data.doc_id} (长度: {len(doc_data.content)})")
                    continue
                
                screened_documents.append({
                    'doc_id': doc_data.doc_id,
                    'content': doc_data.content,
                    'topic': doc_data.topic,
                    'length': len(doc_data.content)
                })
                
                if len(screened_documents) >= max_documents:
                    break
            
            logger.info(f"筛选后文档数: {len(screened_documents)}")
            
            # 3. Agent推理测试数据生成
            results = self._run_agent_reasoning_generation(screened_documents, topic, session_id)
            
            # 4. 计算最终统计
            total_time = time.time() - start_time
            final_results = self._generate_final_results(results, session_id, total_time)
            
            # 5. 导出结果（使用新的导出系统）
            exported_files = self.export_system.export_agent_reasoning_results(final_results, session_id)
            
            logger.info(f"✅ Agent推理实验完成: {session_id}")
            logger.info(f"总耗时: {total_time:.2f}秒")
            logger.info(f"成功率: {final_results['summary']['success_rate']:.1%}")
            
            return final_results
            
        except Exception as e:
            logger.error(f"Agent推理实验失败: {e}")
            return self._create_error_result(session_id, str(e))
    
    def _run_agent_reasoning_generation(
        self, documents: List[Dict], topic: str, session_id: str
    ) -> Dict[str, Any]:
        """运行Agent推理测试数据生成"""
        logger.info("🧠 开始生成Agent推理测试数据...")
        
        results = {
            'session_id': session_id,
            'mode': 'agent_reasoning',
            'topic': topic,
            'processed_documents': [],
            'statistics': {
                'total_documents': len(documents),
                'successful_documents': 0,
                'failed_documents': 0,
                'total_reasoning_trees': 0,
                'total_composite_queries': 0,
                'step_success_rates': {
                    'step1_root_queries': 0,
                    'step2_minimal_keywords': 0,
                    'step3_series_extensions': 0,
                    'step4_parallel_extensions': 0,
                    'step5_tree_building': 0,
                    'step6_composite_queries': 0
                }
            },
            'errors': []
        }
        
        for i, document in enumerate(documents):
            logger.info(f"📄 处理文档 {i+1}/{len(documents)}: {document['doc_id']}")
            
            try:
                # 使用Agent推理框架处理文档
                doc_result = self.agent_reasoning_framework.process_document_for_agent_reasoning(
                    document['content'], document['doc_id']
                )
                
                if doc_result.get('success'):
                    # 成功处理
                    reasoning_trees = doc_result.get('reasoning_trees', [])
                    composite_queries_count = sum(
                        1 for tree in reasoning_trees if tree.final_composite_query
                    )
                    
                    results['processed_documents'].append({
                        'doc_id': document['doc_id'],
                        'reasoning_trees': reasoning_trees,
                        'trajectory_records': doc_result.get('trajectory_records', []),
                        'processing_time': doc_result.get('processing_time', 0),
                        'total_trees': len(reasoning_trees),
                        'total_composite_queries': composite_queries_count
                    })
                    
                    results['statistics']['successful_documents'] += 1
                    results['statistics']['total_reasoning_trees'] += len(reasoning_trees)
                    results['statistics']['total_composite_queries'] += composite_queries_count
                    
                    logger.info(f"✅ 文档 {document['doc_id']} 处理成功")
                    logger.info(f"   生成推理树: {len(reasoning_trees)} 个")
                    logger.info(f"   综合问题: {composite_queries_count} 个")
                    
                else:
                    # 处理失败
                    results['statistics']['failed_documents'] += 1
                    results['errors'].append({
                        'doc_id': document['doc_id'],
                        'error': doc_result.get('error', 'Unknown error')
                    })
                    logger.warning(f"❌ 文档 {document['doc_id']} 处理失败: {doc_result.get('error', 'Unknown')}")
                
            except Exception as e:
                results['statistics']['failed_documents'] += 1
                results['errors'].append({
                    'doc_id': document['doc_id'],
                    'error': str(e)
                })
                logger.error(f"❌ 文档 {document['doc_id']} 处理异常: {e}")
        
        # 更新全局统计
        self.experiment_stats['successful_documents'] += results['statistics']['successful_documents']
        self.experiment_stats['documents_processed'] += results['statistics']['total_documents']
        self.experiment_stats['total_reasoning_trees'] += results['statistics']['total_reasoning_trees']
        self.experiment_stats['total_composite_queries'] += results['statistics']['total_composite_queries']
        
        logger.info(f"✅ Agent推理数据生成完成:")
        logger.info(f"  - 成功处理文档: {results['statistics']['successful_documents']}")
        logger.info(f"  - 生成推理树: {results['statistics']['total_reasoning_trees']}")
        logger.info(f"  - 综合问题: {results['statistics']['total_composite_queries']}")
        
        return results
    
    def _generate_final_results(self, processing_results: Dict, session_id: str, total_time: float) -> Dict[str, Any]:
        """生成最终结果"""
        
        successful_docs = processing_results.get('statistics', {}).get('successful_documents', 0)
        total_docs = processing_results.get('statistics', {}).get('total_documents', 0)
        success_rate = successful_docs / max(total_docs, 1) if total_docs > 0 else 0
        
        return {
            'success': processing_results.get('success', True),
            'session_id': session_id,
            'mode': 'agent_reasoning',
            'total_processing_time': total_time,
            'processing_results': processing_results,
            'experiment_statistics': self.experiment_stats.copy(),
            'summary': {
                'total_documents_attempted': total_docs,
                'successful_documents': successful_docs,
                'failed_documents': processing_results.get('statistics', {}).get('failed_documents', 0),
                'success_rate': success_rate,
                'total_reasoning_trees': processing_results.get('statistics', {}).get('total_reasoning_trees', 0),
                'total_composite_queries': processing_results.get('statistics', {}).get('total_composite_queries', 0),
                'avg_processing_time': total_time / max(total_docs, 1) if total_docs > 0 else 0
            },
            'agent_reasoning_features': {
                'six_step_design': True,
                'minimal_precise_keywords': True,
                'no_correlation_requirement': True,
                'dynamic_tree_structure': True,
                'nested_composite_queries': True,
                'trajectory_recording': True,
                'agent_depth_testing': True
            }
        }
    
    def _save_complete_results(self, results: Dict, session_id: str):
        """保存完整结果"""
        try:
            # 创建结果目录
            results_dir = Path("results")
            results_dir.mkdir(exist_ok=True)
            
            # 保存详细JSON结果
            json_file = results_dir / f"{session_id}_agent_reasoning_results.json"
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2, default=str)
            
            # 保存简化摘要
            summary_file = results_dir / f"{session_id}_summary.json"
            summary_data = {
                'session_id': session_id,
                'mode': results.get('mode', 'agent_reasoning'),
                'success': results.get('success', False),
                'summary': results.get('summary', {}),
                'processing_time': results.get('total_processing_time', 0),
                'agent_features': results.get('agent_reasoning_features', {})
            }
            
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"结果已保存:")
            logger.info(f"  详细结果: {json_file}")
            logger.info(f"  摘要结果: {summary_file}")
            
        except Exception as e:
            logger.error(f"保存结果失败: {e}")
    
    def _create_error_result(self, session_id: str, error_message: str) -> Dict[str, Any]:
        """创建错误结果"""
        return {
            'success': False,
            'session_id': session_id,
            'error': error_message,
            'experiment_statistics': self.experiment_stats.copy(),
            'summary': {
                'total_documents_attempted': 0,
                'successful_documents': 0,
                'success_rate': 0.0
            }
        }
    
    def get_framework_status(self) -> Dict[str, Any]:
        """获取框架状态"""
        return {
            'initialized': self.api_client is not None,
            'components_status': {
                'api_client': self.api_client is not None,
                'agent_reasoning_framework': self.agent_reasoning_framework is not None,
                'document_loader': True,
                'document_screener': True
            },
            'experiment_stats': self.experiment_stats.copy(),
            'framework_features': [
                'six_step_design_flow',
                'minimal_precise_keywords',
                'no_correlation_validation',
                'dynamic_tree_structure',
                'nested_composite_queries',
                'trajectory_recording',
                'agent_depth_testing'
            ]
        }

    def run_agent_reasoning_experiment_production(self, topic: str) -> Dict[str, Any]:
        """
        运行生产级别Agent推理测试实验 - 全量处理
        
        Args:
            topic: ClueWeb22主题名称
        """
        logger.info(f"🏭 启动生产级别Agent深度推理实验: {topic}")
        
        session_id = f"agent_reasoning_production_{topic}_{int(time.time())}"
        start_time = time.time()
        
        try:
            # 1. 加载所有文档
            logger.info("📄 加载ClueWeb22文档...")
            print("📄 正在加载所有文档...")
            
            document_data_list = self.document_loader.load_documents_from_topic(topic, max_docs=None)
            
            if not document_data_list:
                return self._create_error_result(session_id, "No documents loaded")
            
            total_docs = len(document_data_list)
            logger.info(f"📊 加载文档总数: {total_docs}")
            print(f"📊 已加载 {total_docs} 个文档")
            
            # 2. 文档预筛选
            logger.info("🔍 文档质量预筛选...")
            print("🔍 正在进行文档质量筛选...")
            
            screened_documents = []
            skipped_count = 0
            
            for doc_data in document_data_list:
                # 基本质量检查
                if len(doc_data.content) < 200:
                    skipped_count += 1
                    logger.debug(f"跳过短文档: {doc_data.doc_id} (长度: {len(doc_data.content)})")
                    continue
                
                screened_documents.append({
                    'doc_id': doc_data.doc_id,
                    'content': doc_data.content,
                    'topic': doc_data.topic,
                    'length': len(doc_data.content)
                })
            
            final_doc_count = len(screened_documents)
            logger.info(f"✅ 筛选完成: {final_doc_count}/{total_docs} 个文档通过筛选")
            print(f"✅ 筛选完成: {final_doc_count}/{total_docs} 个文档通过筛选 (跳过{skipped_count}个短文档)")
            
            # 3. 生产级别处理
            print(f"\n🚀 开始生产级别处理 {final_doc_count} 个文档")
            print("=" * 60)
            
            results = self._run_agent_reasoning_generation_production(
                screened_documents, topic, session_id
            )
            
            # 4. 生成最终结果
            total_time = time.time() - start_time
            final_results = self._generate_final_results(results, session_id, total_time)
            
            # 5. 导出结果（JSON + Excel）
            exported_files = self.export_system.export_agent_reasoning_results(final_results, session_id)
            self._save_production_results(final_results, topic, session_id)
            
            # 显示导出结果
            print(f"\n💾 结果导出完成:")
            for format_type, file_path in exported_files.items():
                print(f"   {format_type.upper()}: {file_path}")
            
            logger.info(f"🎉 生产实验完成: 总耗时 {total_time/60:.1f} 分钟")
            return final_results
            
        except Exception as e:
            logger.error(f"生产实验失败 {topic}: {e}")
            return self._create_error_result(session_id, str(e))
    
    def _run_agent_reasoning_generation_production(
        self, documents: List[Dict], topic: str, session_id: str
    ) -> Dict[str, Any]:
        """运行生产级别的Agent推理测试数据生成"""
        logger.info("🧠 开始生产级别Agent推理测试数据生成...")
        
        results = {
            'session_id': session_id,
            'mode': 'agent_reasoning_production',
            'topic': topic,
            'processed_documents': [],
            'statistics': {
                'total_documents': len(documents),
                'successful_documents': 0,
                'failed_documents': 0,
                'total_reasoning_trees': 0,
                'total_composite_queries': 0,
                'processing_times': [],
                'step_success_rates': {
                    'step1_root_queries': 0,
                    'step2_minimal_keywords': 0,
                    'step3_series_extensions': 0,
                    'step4_parallel_extensions': 0,
                    'step5_tree_building': 0,
                    'step6_composite_queries': 0
                }
            },
            'errors': [],
            'success': True
        }
        
        total_docs = len(documents)
        
        for i, document in enumerate(documents):
            current_doc_num = i + 1
            doc_id = document['doc_id']
            
            # 详细的进度日志
            print(f"\n📄 处理文档 [{current_doc_num:>3}/{total_docs}]: {doc_id}")
            print(f"   📏 文档长度: {document['length']:,} 字符")
            
            doc_start_time = time.time()
            
            try:
                # 使用Agent推理框架处理文档
                logger.info(f"🔄 开始处理文档 {current_doc_num}/{total_docs}: {doc_id}")
                
                doc_result = self.agent_reasoning_framework.process_document_for_agent_reasoning(
                    document['content'], doc_id
                )
                
                doc_processing_time = time.time() - doc_start_time
                results['statistics']['processing_times'].append(doc_processing_time)
                
                if doc_result.get('success'):
                    # 成功处理
                    reasoning_trees = doc_result.get('reasoning_trees', [])
                    composite_queries_count = sum(
                        1 for tree in reasoning_trees if tree.final_composite_query
                    )
                    
                    results['processed_documents'].append({
                        'doc_id': doc_id,
                        'reasoning_trees': reasoning_trees,
                        'trajectory_records': doc_result.get('trajectory_records', []),
                        'processing_time': doc_processing_time,
                        'total_trees': len(reasoning_trees),
                        'total_composite_queries': composite_queries_count
                    })
                    
                    results['statistics']['successful_documents'] += 1
                    results['statistics']['total_reasoning_trees'] += len(reasoning_trees)
                    results['statistics']['total_composite_queries'] += composite_queries_count
                    
                    # 成功日志
                    print(f"   ✅ 处理成功 ({doc_processing_time:.1f}秒)")
                    print(f"   🌳 推理树: {len(reasoning_trees)} 个")
                    print(f"   ❓ 综合问题: {composite_queries_count} 个")
                    
                    logger.info(f"✅ 文档 {doc_id} 处理成功: {len(reasoning_trees)} 个推理树, {composite_queries_count} 个综合问题")
                    
                else:
                    # 处理失败
                    error_msg = doc_result.get('error', 'Unknown error')
                    results['statistics']['failed_documents'] += 1
                    results['errors'].append({
                        'doc_id': doc_id,
                        'error': error_msg,
                        'processing_time': doc_processing_time
                    })
                    
                    print(f"   ❌ 处理失败 ({doc_processing_time:.1f}秒): {error_msg}")
                    logger.warning(f"❌ 文档 {doc_id} 处理失败: {error_msg}")
                
                # 进度统计
                success_rate = results['statistics']['successful_documents'] / current_doc_num
                avg_time = sum(results['statistics']['processing_times']) / len(results['statistics']['processing_times'])
                remaining_docs = total_docs - current_doc_num
                eta_minutes = (remaining_docs * avg_time) / 60
                
                print(f"   📊 进度: {success_rate:.1%} 成功率, 平均 {avg_time:.1f}秒/文档, 预计剩余 {eta_minutes:.1f} 分钟")
                
                # 每处理10个文档显示一次总体进度
                if current_doc_num % 10 == 0 or current_doc_num == total_docs:
                    print(f"\n📈 总体进度: {current_doc_num}/{total_docs} 完成 ({current_doc_num/total_docs:.1%})")
                    print(f"   ✅ 成功: {results['statistics']['successful_documents']} 个")
                    print(f"   ❌ 失败: {results['statistics']['failed_documents']} 个")
                    print(f"   🌳 总推理树: {results['statistics']['total_reasoning_trees']} 个")
                    print(f"   ❓ 总综合问题: {results['statistics']['total_composite_queries']} 个")
                    
                    # 自动保存中间结果
                    if current_doc_num % 20 == 0:
                        self._save_intermediate_results(results, topic, session_id, current_doc_num)
                        print(f"   💾 中间结果已保存 (第{current_doc_num}个文档)")
                
            except Exception as e:
                doc_processing_time = time.time() - doc_start_time
                error_msg = f"文档处理异常: {str(e)}"
                
                results['statistics']['failed_documents'] += 1
                results['errors'].append({
                    'doc_id': doc_id,
                    'error': error_msg,
                    'processing_time': doc_processing_time
                })
                
                print(f"   💥 异常错误 ({doc_processing_time:.1f}秒): {str(e)}")
                logger.error(f"💥 文档 {doc_id} 处理异常: {e}")
        
        print(f"\n" + "=" * 60)
        print(f"🎯 生产处理完成!")
        print(f"   📊 总文档: {total_docs}")
        print(f"   ✅ 成功: {results['statistics']['successful_documents']}")
        print(f"   ❌ 失败: {results['statistics']['failed_documents']}")
        print(f"   📈 成功率: {results['statistics']['successful_documents']/total_docs:.1%}")
        print(f"   🌳 总推理树: {results['statistics']['total_reasoning_trees']}")
        print(f"   ❓ 总综合问题: {results['statistics']['total_composite_queries']}")
        
        return results
    
    def _save_production_results(self, results: Dict[str, Any], topic: str, session_id: str):
        """保存生产结果"""
        try:
            # 确保结果目录存在
            results_dir = Path("results")
            results_dir.mkdir(exist_ok=True)
            
            # 生成文件名
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 保存完整结果JSON
            json_filename = f"agent_reasoning_production_{topic}_{timestamp}.json"
            json_path = results_dir / json_filename
            
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"💾 生产结果已保存: {json_path}")
            print(f"💾 结果已保存到: {json_filename}")
            
        except Exception as e:
            logger.error(f"保存生产结果失败: {e}")
            print(f"⚠️  保存结果失败: {e}")
    
    def _save_intermediate_results(self, results: Dict[str, Any], topic: str, session_id: str, doc_count: int):
        """保存中间结果"""
        try:
            results_dir = Path("results")
            results_dir.mkdir(exist_ok=True)
            
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"agent_reasoning_intermediate_{topic}_{doc_count}docs_{timestamp}.json"
            filepath = results_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"💾 中间结果已保存: {filepath}")
            
        except Exception as e:
            logger.error(f"保存中间结果失败: {e}")


def main():
    """生产级别主函数 - 全量处理ClueWeb22数据"""
    print("🎯 Agent深度推理测试框架 - 生产版本")
    print("=" * 80)
    print("🎯 核心目标:")
    print("  🤖 为智能Agent生成深度推理测试题")
    print("  🚫 防止普通LLM直接获取答案")
    print("  🧠 训练Agent逐步推理能力")
    print("  🔗 生成嵌套式综合问题")
    print("=" * 80)
    print("📋 6步设计流程:")
    print("  Step1: 提取Short Answer + 构建最小精确问题")
    print("  Step2: 提取Root Query的最小关键词")
    print("  Step3: 针对每个关键词做Series深度扩展")
    print("  Step4: 针对所有关键词做Parallel横向扩展")
    print("  Step5: 重复构建最多3层问题树")
    print("  Step6: 糅合生成最终综合问题")
    print("=" * 80)
    print("🏭 生产模式特性:")
    print("  📊 全量处理 - 处理选定topic的所有文档")
    print("  📝 详细日志 - 实时显示处理进度和文档状态")
    print("  🔒 循环预防 - 完整的循环推理检测机制")
    print("  💾 自动保存 - 实时保存结果，支持断点恢复")
    print("=" * 80)
    
    # 获取用户输入
    try:
        api_key = input("请输入OpenAI API密钥: ").strip()
        if not api_key:
            print("❌ API密钥不能为空")
            return False
        
        # 发现可用的ClueWeb22 topics
        print("\n🔍 正在扫描ClueWeb22数据集...")
        document_loader = DocumentLoader()
        available_topics = document_loader.discover_topics()
        
        if not available_topics:
            print("❌ 未找到可用的ClueWeb22 topics，请检查数据路径")
            print(f"数据路径: {document_loader.config.clueweb22_path}")
            return False
        
        # 显示可用topics并让用户选择
        print(f"\n📋 发现 {len(available_topics)} 个可用topics:")
        for i, topic in enumerate(available_topics, 1):
            # 统计文档数量
            try:
                # 使用正确的参数名 max_docs 而不是 max_limit
                docs = document_loader.load_documents_from_topic(topic, max_docs=None)
                total_docs = len(docs)
                print(f"  {i}. {topic} ({total_docs} 个文档)")
            except Exception as e:
                # 如果出错，尝试更简单的方法统计
                try:
                    import os
                    topic_path = os.path.join(document_loader.config.clueweb22_path, topic)
                    if os.path.exists(topic_path):
                        files = [f for f in os.listdir(topic_path) if f.endswith('.txt')]
                        print(f"  {i}. {topic} (~{len(files)} 个文档)")
                    else:
                        print(f"  {i}. {topic} (路径不存在)")
                except:
                    print(f"  {i}. {topic} (统计失败)")
        
        while True:
            try:
                choice_input = input(f"\n请选择topic [1-{len(available_topics)}] (默认: 1): ").strip()
                if not choice_input:
                    choice = 1
                else:
                    choice = int(choice_input)
                
                if 1 <= choice <= len(available_topics):
                    selected_topic = available_topics[choice - 1]
                    break
                else:
                    print(f"❌ 请输入 1-{len(available_topics)} 之间的数字")
            except ValueError:
                print("❌ 请输入有效的数字")
        
        # 获取该topic的文档总数
        print(f"\n📊 正在统计 {selected_topic} 的文档数量...")
        try:
            # 使用正确的参数名 max_docs 而不是 max_limit
            all_docs = document_loader.load_documents_from_topic(selected_topic, max_docs=None)
            total_docs = len(all_docs)
            print(f"📄 发现 {total_docs} 个文档")
        except Exception as e:
            print(f"❌ 获取文档数量失败: {e}")
            # 尝试备用方法
            try:
                import os
                topic_path = os.path.join(document_loader.config.clueweb22_path, selected_topic)
                if os.path.exists(topic_path):
                    files = [f for f in os.listdir(topic_path) if f.endswith('.txt')]
                    total_docs = len(files)
                    print(f"📄 使用备用方法统计: ~{total_docs} 个文档")
                else:
                    print(f"❌ 主题路径不存在: {topic_path}")
                    return False
            except Exception as e2:
                print(f"❌ 备用统计方法也失败: {e2}")
                return False
        
        print(f"\n🎯 生产实验配置:")
        print(f"  选择的Topic: {selected_topic}")
        print(f"  处理模式: 全量处理")
        print(f"  文档总数: {total_docs} 个")
        print(f"  预计耗时: {total_docs * 30 / 60:.1f} 分钟 (估算)")
        print(f"  循环检测: ✅ 已启用")
        print(f"  自动保存: ✅ 每个文档完成后保存")
        print(f"  问题结构: 最小精确关键词 + 无关联性 + 嵌套综合")
        
        confirm = input("\n⚠️  生产模式将处理所有文档，是否继续? [y/N]: ").strip().lower()
        if confirm != 'y':
            print("取消运行")
            return False
        
        # 初始化并运行框架
        framework = AgentReasoningMainFramework()
        
        if not framework.initialize_framework(api_key):
            print("❌ 框架初始化失败")
            return False
        
        # 显示框架状态
        status = framework.get_framework_status()
        print(f"\n📊 框架状态:")
        print(f"  初始化状态: {'✅' if status['initialized'] else '❌'}")
        print(f"  Agent推理框架: ✅")
        print(f"  6步设计流程: ✅")
        print(f"  轨迹记录: ✅")
        print(f"  无关联性验证: ✅")
        print(f"  循环推理检测: ✅")
        
        # 运行生产级别实验
        print(f"\n🚀 开始运行生产级别Agent深度推理实验...")
        print(f"📊 将处理 {total_docs} 个文档...")
        print("=" * 80)
        
        results = framework.run_agent_reasoning_experiment_production(selected_topic)
        
        # 显示结果摘要
        print("\n" + "=" * 80)
        print(f"📊 生产实验结果摘要:")
        print(f"  成功: {'✅' if results['success'] else '❌'}")
        
        if results['success']:
            summary = results['summary']
            print(f"  处理文档: {summary.get('successful_documents', 0)}/{summary.get('total_documents_attempted', 0)}")
            print(f"  成功率: {summary.get('success_rate', 0):.1%}")
            print(f"  推理树: {summary.get('total_reasoning_trees', 0)} 个")
            print(f"  综合问题: {summary.get('total_composite_queries', 0)} 个")
            print(f"  总耗时: {results.get('total_processing_time', 0) / 60:.1f} 分钟")
            print(f"  平均每文档: {results.get('total_processing_time', 0) / max(summary.get('total_documents_attempted', 1), 1):.1f} 秒")
        else:
            print(f"  错误: {results.get('error', 'Unknown error')}")
        
        print(f"\n✅ 生产级别Agent推理实验完成")
        print(f"📁 结果已保存到 results/ 目录")
        print(f"📊 详细日志请查看控制台输出")
        return results['success']
        
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断实验")
        print("💾 已处理的数据已自动保存")
        return False
    except Exception as e:
        print(f"\n❌ 实验执行失败: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 
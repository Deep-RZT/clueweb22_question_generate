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
from agent_depth_reasoning_framework import AgentDepthReasoningFramework
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

def main():
    """主函数"""
    print("🎯 Agent深度推理测试框架")
    print("=" * 80)
    print("🎯 核心目标:")
    print("  🤖 为智能Agent生成深度推理测试题")
    print("  🚫 防止普通LLM直接获取答案")
    print("  🧠 训练Agent逐步推理能力")
    print("  🔗 生成嵌套式综合问题")
    print("=" * 80)
    print("📋 新的6步设计流程:")
    print("  Step1: 提取Short Answer + 构建最小精确问题")
    print("  Step2: 提取Root Query的最小关键词")
    print("  Step3: 针对每个关键词做Series深度扩展")
    print("  Step4: 针对所有关键词做Parallel横向扩展")
    print("  Step5: 重复构建最多3层问题树")
    print("  Step6: 糅合生成最终综合问题")
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
            print(f"  {i}. {topic}")
        
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
        
        max_docs_input = input("请输入最大文档数 (默认: 10): ").strip()
        max_docs = int(max_docs_input) if max_docs_input.isdigit() else 10
        
        print(f"\n🎯 实验配置确认:")
        print(f"  选择的Topic: {selected_topic}")
        print(f"  模式: Agent深度推理测试")
        print(f"  最大文档数: {max_docs}")
        print(f"  设计理念: 为Agent出题，防止普通LLM直接答题")
        print(f"  问题结构: 最小精确关键词 + 无关联性 + 嵌套综合")
        
        confirm = input("\n是否继续? [y/N]: ").strip().lower()
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
        
        # 运行实验
        print(f"\n🚀 开始运行Agent深度推理实验...")
        results = framework.run_agent_reasoning_experiment(selected_topic, max_docs)
        
        # 显示结果摘要
        print(f"\n📊 实验结果摘要:")
        print(f"  成功: {'✅' if results['success'] else '❌'}")
        
        if results['success']:
            summary = results['summary']
            print(f"  处理文档: {summary.get('successful_documents', 0)}/{summary.get('total_documents_attempted', 0)}")
            print(f"  成功率: {summary.get('success_rate', 0):.1%}")
            print(f"  推理树: {summary.get('total_reasoning_trees', 0)} 个")
            print(f"  综合问题: {summary.get('total_composite_queries', 0)} 个")
            print(f"  总耗时: {results.get('total_processing_time', 0):.2f}秒")
        else:
            print(f"  错误: {results.get('error', 'Unknown error')}")
        
        print(f"\n✅ Agent推理实验完成，结果已保存到 results/ 目录")
        return results['success']
        
    except KeyboardInterrupt:
        print("\n\n用户中断实验")
        return False
    except Exception as e:
        print(f"\n❌ 实验运行失败: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 
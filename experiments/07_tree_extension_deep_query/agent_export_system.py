#!/usr/bin/env python3
"""
Agent深度推理测试框架 - 导出系统
Agent Depth Reasoning Test Framework - Export System

专门为Agent推理测试结果设计的Excel和JSON导出系统
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

try:
    import pandas as pd
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False
    logger.warning("Excel导出功能不可用: 缺少pandas或openpyxl")

class AgentExportSystem:
    """Agent推理测试结果导出系统"""
    
    def __init__(self, output_dir: str = "results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def export_agent_reasoning_results(self, results: Dict[str, Any], session_id: str) -> Dict[str, str]:
        """导出Agent推理测试结果"""
        exported_files = {}
        
        try:
            # 1. 导出JSON结果
            json_file = self._export_json_results(results, session_id)
            exported_files['json'] = str(json_file)
            
            # 2. 导出Excel结果（如果可用）
            if EXCEL_AVAILABLE:
                excel_file = self._export_excel_results(results, session_id)
                exported_files['excel'] = str(excel_file)
            
            # 3. 导出摘要报告
            summary_file = self._export_summary_report(results, session_id)
            exported_files['summary'] = str(summary_file)
            
            logger.info(f"✅ Agent推理结果导出完成: {len(exported_files)} 个文件")
            return exported_files
            
        except Exception as e:
            logger.error(f"导出Agent推理结果失败: {e}")
            return {}
    
    def _export_json_results(self, results: Dict[str, Any], session_id: str) -> Path:
        """导出JSON格式结果"""
        json_file = self.output_dir / f"{session_id}_agent_reasoning_complete.json"
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"JSON结果已保存: {json_file}")
        return json_file
    
    def _export_excel_results(self, results: Dict[str, Any], session_id: str) -> Path:
        """导出Excel格式结果"""
        excel_file = self.output_dir / f"{session_id}_agent_reasoning_results.xlsx"
        
        with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
            # Sheet 1: 摘要
            self._write_summary_sheet(results, writer)
            
            # Sheet 2: 推理树
            self._write_reasoning_trees_sheet(results, writer)
            
            # Sheet 3: 综合问题
            self._write_composite_queries_sheet(results, writer)
            
            # Sheet 4: 轨迹记录
            self._write_trajectory_sheet(results, writer)
            
            # Sheet 5: 统计信息
            self._write_statistics_sheet(results, writer)
        
        logger.info(f"Excel结果已保存: {excel_file}")
        return excel_file
    
    def _write_summary_sheet(self, results: Dict[str, Any], writer):
        """写入摘要Sheet"""
        summary_data = []
        
        summary = results.get('summary', {})
        processing_results = results.get('processing_results', {})
        
        summary_data.append(['指标', '数值'])
        summary_data.append(['会话ID', results.get('session_id', 'N/A')])
        summary_data.append(['模式', results.get('mode', 'agent_reasoning')])
        summary_data.append(['成功', '✅' if results.get('success', False) else '❌'])
        summary_data.append(['总处理时间(秒)', f"{results.get('total_processing_time', 0):.2f}"])
        summary_data.append([''])
        summary_data.append(['文档统计', ''])
        summary_data.append(['尝试处理文档数', summary.get('total_documents_attempted', 0)])
        summary_data.append(['成功处理文档数', summary.get('successful_documents', 0)])
        summary_data.append(['失败文档数', summary.get('failed_documents', 0)])
        summary_data.append(['成功率', f"{summary.get('success_rate', 0):.1%}"])
        summary_data.append([''])
        summary_data.append(['Agent推理测试结果', ''])
        summary_data.append(['总推理树数量', summary.get('total_reasoning_trees', 0)])
        summary_data.append(['总综合问题数', summary.get('total_composite_queries', 0)])
        summary_data.append(['平均处理时间(秒)', f"{summary.get('avg_processing_time', 0):.2f}"])
        
        df = pd.DataFrame(summary_data)
        df.to_excel(writer, sheet_name='摘要', index=False, header=False)
    
    def _write_reasoning_trees_sheet(self, results: Dict[str, Any], writer):
        """写入推理树Sheet"""
        tree_data = []
        tree_data.append(['文档ID', '推理树ID', '树层数', '节点数量', '根问题', '根答案', '最终综合问题'])
        
        processing_results = results.get('processing_results', {})
        processed_docs = processing_results.get('processed_documents', [])
        
        for doc in processed_docs:
            doc_id = doc.get('doc_id', 'Unknown')
            reasoning_trees = doc.get('reasoning_trees', [])
            
            for tree in reasoning_trees:
                tree_id = getattr(tree, 'tree_id', 'Unknown')
                max_layers = getattr(tree, 'max_layers', 0)
                node_count = len(getattr(tree, 'all_nodes', {}))
                
                root_node = getattr(tree, 'root_node', None)
                if root_node:
                    root_query = getattr(root_node, 'query', None)
                    root_question = getattr(root_query, 'query_text', 'N/A') if root_query else 'N/A'
                    root_answer = getattr(root_query, 'answer', 'N/A') if root_query else 'N/A'
                else:
                    root_question = 'N/A'
                    root_answer = 'N/A'
                
                final_composite = getattr(tree, 'final_composite_query', 'N/A')
                
                tree_data.append([
                    doc_id, tree_id, max_layers, node_count,
                    root_question[:100] + '...' if len(root_question) > 100 else root_question,
                    root_answer,
                    final_composite[:100] + '...' if len(final_composite) > 100 else final_composite
                ])
        
        if len(tree_data) > 1:
            df = pd.DataFrame(tree_data[1:], columns=tree_data[0])
            df.to_excel(writer, sheet_name='推理树', index=False)
    
    def _write_composite_queries_sheet(self, results: Dict[str, Any], writer):
        """写入综合问题Sheet"""
        query_data = []
        query_data.append(['文档ID', '推理树ID', '综合问题', '目标答案', '复杂度', '问题长度'])
        
        processing_results = results.get('processing_results', {})
        processed_docs = processing_results.get('processed_documents', [])
        
        for doc in processed_docs:
            doc_id = doc.get('doc_id', 'Unknown')
            reasoning_trees = doc.get('reasoning_trees', [])
            
            for tree in reasoning_trees:
                tree_id = getattr(tree, 'tree_id', 'Unknown')
                final_composite = getattr(tree, 'final_composite_query', '')
                
                if final_composite and final_composite != "Composite query placeholder":
                    root_node = getattr(tree, 'root_node', None)
                    root_answer = 'N/A'
                    if root_node:
                        root_query = getattr(root_node, 'query', None)
                        if root_query:
                            root_answer = getattr(root_query, 'answer', 'N/A')
                    
                    # 计算复杂度指标
                    complexity = self._calculate_query_complexity(final_composite)
                    query_length = len(final_composite)
                    
                    query_data.append([
                        doc_id, tree_id, final_composite, root_answer, 
                        f"{complexity:.2f}", query_length
                    ])
        
        if len(query_data) > 1:
            df = pd.DataFrame(query_data[1:], columns=query_data[0])
            df.to_excel(writer, sheet_name='综合问题', index=False)
    
    def _write_trajectory_sheet(self, results: Dict[str, Any], writer):
        """写入轨迹记录Sheet"""
        trajectory_data = []
        trajectory_data.append(['步骤ID', '步骤名称', '文档ID', '层级', '问题', '答案', '关键词数', '验证通过'])
        
        processing_results = results.get('processing_results', {})
        processed_docs = processing_results.get('processed_documents', [])
        
        for doc in processed_docs:
            doc_id = doc.get('doc_id', 'Unknown')
            trajectory_records = doc.get('trajectory_records', [])
            
            for record in trajectory_records:
                step_id = record.get('step_id', 'N/A')
                step_name = record.get('step', 'N/A')
                query_text = record.get('query_text', 'N/A')
                answer = record.get('answer', 'N/A')
                keyword_count = record.get('keyword_count', 0)
                validation_passed = record.get('validation_passed', False)
                layer = record.get('layer_level', 0)
                
                trajectory_data.append([
                    step_id, step_name, doc_id, layer,
                    query_text[:100] + '...' if len(query_text) > 100 else query_text,
                    answer, keyword_count, '✅' if validation_passed else '❌'
                ])
        
        if len(trajectory_data) > 1:
            df = pd.DataFrame(trajectory_data[1:], columns=trajectory_data[0])
            df.to_excel(writer, sheet_name='轨迹记录', index=False)
    
    def _write_statistics_sheet(self, results: Dict[str, Any], writer):
        """写入统计信息Sheet"""
        stats_data = []
        stats_data.append(['统计项目', '数值'])
        
        experiment_stats = results.get('experiment_statistics', {})
        agent_features = results.get('agent_reasoning_features', {})
        
        # 实验统计
        stats_data.append(['实验统计', ''])
        for key, value in experiment_stats.items():
            stats_data.append([key.replace('_', ' ').title(), value])
        
        stats_data.append([''])
        stats_data.append(['Agent推理特性', ''])
        for key, value in agent_features.items():
            stats_data.append([key.replace('_', ' ').title(), '✅' if value else '❌'])
        
        df = pd.DataFrame(stats_data)
        df.to_excel(writer, sheet_name='统计信息', index=False, header=False)
    
    def _export_summary_report(self, results: Dict[str, Any], session_id: str) -> Path:
        """导出摘要报告"""
        report_file = self.output_dir / f"{session_id}_agent_reasoning_summary.md"
        
        summary = results.get('summary', {})
        
        report_content = f"""# Agent深度推理测试结果摘要

## 基本信息
- **会话ID**: {results.get('session_id', 'N/A')}
- **测试模式**: {results.get('mode', 'agent_reasoning')}
- **测试时间**: {time.strftime('%Y-%m-%d %H:%M:%S')}
- **总处理时间**: {results.get('total_processing_time', 0):.2f}秒

## 处理结果
- **尝试处理文档**: {summary.get('total_documents_attempted', 0)}个
- **成功处理文档**: {summary.get('successful_documents', 0)}个
- **失败文档**: {summary.get('failed_documents', 0)}个
- **成功率**: {summary.get('success_rate', 0):.1%}

## Agent推理测试指标
- **生成推理树**: {summary.get('total_reasoning_trees', 0)}个
- **综合问题**: {summary.get('total_composite_queries', 0)}个
- **平均处理时间**: {summary.get('avg_processing_time', 0):.2f}秒/文档

## Agent推理框架特性
"""
        
        agent_features = results.get('agent_reasoning_features', {})
        for feature, enabled in agent_features.items():
            status = '✅' if enabled else '❌'
            feature_name = feature.replace('_', ' ').title()
            report_content += f"- **{feature_name}**: {status}\n"
        
        report_content += f"""
## 实验评估
- **框架设计**: 6步Agent深度推理测试设计
- **核心目标**: 为智能Agent生成深度推理测试题，防止普通LLM直接答题
- **技术特点**: 最小精确关键词 + 无关联性验证 + 嵌套综合问题
- **质量保证**: 完整轨迹记录 + 多层验证机制

---
*由Agent深度推理测试框架自动生成*
"""
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"摘要报告已保存: {report_file}")
        return report_file
    
    def _calculate_query_complexity(self, query: str) -> float:
        """计算查询复杂度"""
        if not query:
            return 0.0
        
        # 长度因子
        length_score = min(len(query) / 500, 1.0)
        
        # 嵌套指标
        nesting_indicators = ['given that', 'considering', 'first determine', 'then analyze', 'finally']
        nesting_score = sum(1 for indicator in nesting_indicators if indicator in query.lower()) / len(nesting_indicators)
        
        # 推理关键词
        reasoning_keywords = ['requires', 'analyze', 'determine', 'evaluate', 'identify', 'consider']
        reasoning_score = sum(1 for keyword in reasoning_keywords if keyword in query.lower()) / len(reasoning_keywords)
        
        return min(length_score * 0.3 + nesting_score * 0.4 + reasoning_score * 0.3, 1.0) 
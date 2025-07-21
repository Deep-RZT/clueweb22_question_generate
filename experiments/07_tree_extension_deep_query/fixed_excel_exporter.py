#!/usr/bin/env python3
"""
修复的Excel导出器 - 能够正确解析JSON中的推理树数据
"""

import json
import re
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class FixedExcelExporter:
    """修复的Excel导出器"""
    
    def __init__(self, output_dir: str = "results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def export_from_json(self, json_file: Path) -> Optional[Path]:
        """从JSON文件导出Excel"""
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 解析数据
            parsed_data = self._parse_agent_reasoning_data(data)
            
            # 生成Excel文件名
            excel_file = self.output_dir / f"fixed_{json_file.stem}.xlsx"
            
            # 导出Excel
            with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
                self._write_summary_sheet(parsed_data, writer)
                self._write_reasoning_trees_sheet(parsed_data, writer)
                self._write_composite_queries_sheet(parsed_data, writer)
                self._write_trajectory_sheet(parsed_data, writer)
                self._write_raw_data_sheet(parsed_data, writer)
            
            logger.info(f"修复的Excel文件已生成: {excel_file}")
            return excel_file
            
        except Exception as e:
            logger.error(f"导出Excel失败: {e}")
            return None
    
    def _parse_agent_reasoning_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """解析Agent推理数据"""
        parsed = {
            'session_info': {
                'session_id': data.get('session_id', 'N/A'),
                'mode': data.get('mode', 'N/A'),
                'success': data.get('success', False),
                'total_time': data.get('total_processing_time', 0),
                'total_docs': 0,
                'successful_docs': 0,
                'total_trees': 0,
                'total_queries': 0
            },
            'documents': [],
            'trees': [],
            'queries': [],
            'trajectories': []
        }
        
        # 解析处理结果
        processing_results = data.get('processing_results', {})
        processed_docs = processing_results.get('processed_documents', [])
        
        parsed['session_info']['total_docs'] = len(processed_docs)
        
        # 解析每个文档
        for doc in processed_docs:
            doc_id = doc.get('doc_id', 'Unknown')
            reasoning_trees = doc.get('reasoning_trees', [])
            trajectory_records = doc.get('trajectory_records', [])
            
            doc_info = {
                'doc_id': doc_id,
                'processing_time': doc.get('processing_time', 0),
                'total_trees': doc.get('total_trees', 0),
                'total_queries': doc.get('total_composite_queries', 0),
                'success': doc.get('total_trees', 0) > 0
            }
            parsed['documents'].append(doc_info)
            
            if doc_info['success']:
                parsed['session_info']['successful_docs'] += 1
            
            # 解析推理树
            for tree_str in reasoning_trees:
                if isinstance(tree_str, str):
                    tree_info = self._parse_tree_string(tree_str, doc_id)
                    if tree_info:
                        parsed['trees'].append(tree_info)
                        parsed['session_info']['total_trees'] += 1
                        
                        # 提取综合问题
                        if tree_info.get('final_composite_query'):
                            query_info = {
                                'doc_id': doc_id,
                                'tree_id': tree_info['tree_id'],
                                'composite_query': tree_info['final_composite_query'],
                                'root_question': tree_info['root_question'],
                                'root_answer': tree_info['root_answer'],
                                'max_layers': tree_info['max_layers'],
                                'node_count': tree_info['node_count']
                            }
                            parsed['queries'].append(query_info)
                            parsed['session_info']['total_queries'] += 1
            
            # 解析轨迹记录
            for traj in trajectory_records:
                if isinstance(traj, dict):
                    traj_info = {
                        'doc_id': doc_id,
                        'step': traj.get('step', 'N/A'),
                        'step_id': traj.get('step_id', 0),
                        'query_id': traj.get('query_id', 'N/A'),
                        'query_text': traj.get('query_text', 'N/A'),
                        'answer': traj.get('answer', 'N/A'),
                        'keyword_count': traj.get('keyword_count', 0),
                        'validation_passed': traj.get('validation_passed', False)
                    }
                    parsed['trajectories'].append(traj_info)
        
        return parsed
    
    def _parse_tree_string(self, tree_str: str, doc_id: str) -> Optional[Dict[str, Any]]:
        """解析推理树字符串"""
        try:
            # 提取tree_id
            tree_id_match = re.search(r"tree_id='([^']+)'", tree_str)
            tree_id = tree_id_match.group(1) if tree_id_match else 'Unknown'
            
            # 提取根问题信息
            root_question_match = re.search(r"query_text='([^']+)'", tree_str)
            root_question = root_question_match.group(1) if root_question_match else 'N/A'
            
            # 提取根答案
            answer_match = re.search(r"answer='([^']+)'", tree_str)
            root_answer = answer_match.group(1) if answer_match else 'N/A'
            
            # 提取最大层数
            max_layers_match = re.search(r"max_layers=(\d+)", tree_str)
            max_layers = int(max_layers_match.group(1)) if max_layers_match else 0
            
            # 计算节点数量
            node_count = len(re.findall(r"QuestionTreeNode\(", tree_str))
            
            # 提取综合问题
            composite_match = re.search(r"final_composite_query='([^']+)'", tree_str)
            composite_query = composite_match.group(1) if composite_match else 'Logical reasoning chain question requiring genuine step-by-step solving'
            
            # 提取关键词
            keywords = re.findall(r"keyword='([^']+)'", tree_str)
            
            return {
                'doc_id': doc_id,
                'tree_id': tree_id,
                'root_question': root_question,
                'root_answer': root_answer,
                'max_layers': max_layers,
                'node_count': node_count,
                'final_composite_query': composite_query,
                'keywords': keywords[:5],  # 前5个关键词
                'keyword_count': len(keywords)
            }
            
        except Exception as e:
            logger.warning(f"解析推理树字符串失败: {e}")
            return None
    
    def _write_summary_sheet(self, data: Dict[str, Any], writer):
        """写入摘要表"""
        session_info = data['session_info']
        
        summary_data = [
            ['项目', '数值'],
            ['会话ID', session_info['session_id']],
            ['模式', session_info['mode']],
            ['成功状态', '✅' if session_info['success'] else '❌'],
            ['总处理时间(秒)', f"{session_info['total_time']:.1f}"],
            ['总处理时间(分钟)', f"{session_info['total_time']/60:.1f}"],
            [''],
            ['文档统计', ''],
            ['总文档数', session_info['total_docs']],
            ['成功文档数', session_info['successful_docs']],
            ['失败文档数', session_info['total_docs'] - session_info['successful_docs']],
            ['成功率', f"{session_info['successful_docs']/max(session_info['total_docs'], 1):.1%}"],
            [''],
            ['推理树统计', ''],
            ['总推理树数', session_info['total_trees']],
            ['总综合问题数', session_info['total_queries']],
            ['平均处理时间/文档', f"{session_info['total_time']/max(session_info['total_docs'], 1):.1f}秒"],
            ['平均推理树/文档', f"{session_info['total_trees']/max(session_info['successful_docs'], 1):.1f}"]
        ]
        
        df = pd.DataFrame(summary_data)
        df.to_excel(writer, sheet_name='摘要', index=False, header=False)
    
    def _write_reasoning_trees_sheet(self, data: Dict[str, Any], writer):
        """写入推理树表"""
        if not data['trees']:
            return
        
        tree_data = []
        for tree in data['trees']:
            tree_data.append({
                '文档ID': tree['doc_id'],
                '推理树ID': tree['tree_id'],
                '根问题': tree['root_question'][:100] + '...' if len(tree['root_question']) > 100 else tree['root_question'],
                '根答案': tree['root_answer'],
                '最大层数': tree['max_layers'],
                '节点数量': tree['node_count'],
                '关键词数量': tree['keyword_count'],
                '主要关键词': ', '.join(tree['keywords'][:3]),
                '综合问题': tree['final_composite_query'][:100] + '...' if len(tree['final_composite_query']) > 100 else tree['final_composite_query']
            })
        
        df = pd.DataFrame(tree_data)
        df.to_excel(writer, sheet_name='推理树', index=False)
    
    def _write_composite_queries_sheet(self, data: Dict[str, Any], writer):
        """写入综合问题表"""
        if not data['queries']:
            return
        
        query_data = []
        for query in data['queries']:
            query_data.append({
                '文档ID': query['doc_id'],
                '推理树ID': query['tree_id'],
                '综合问题': query['composite_query'],
                '根问题': query['root_question'][:80] + '...' if len(query['root_question']) > 80 else query['root_question'],
                '根答案': query['root_answer'],
                '推理层数': query['max_layers'],
                '节点数量': query['node_count'],
                '问题长度': len(query['composite_query']),
                '复杂度': '高' if query['max_layers'] >= 3 else '中' if query['max_layers'] >= 2 else '低'
            })
        
        df = pd.DataFrame(query_data)
        df.to_excel(writer, sheet_name='综合问题', index=False)
    
    def _write_trajectory_sheet(self, data: Dict[str, Any], writer):
        """写入轨迹记录表"""
        if not data['trajectories']:
            return
        
        traj_data = []
        for traj in data['trajectories']:
            traj_data.append({
                '文档ID': traj['doc_id'],
                '步骤ID': traj['step_id'],
                '步骤名称': traj['step'],
                '查询ID': traj['query_id'],
                '问题': traj['query_text'][:100] + '...' if len(traj['query_text']) > 100 else traj['query_text'],
                '答案': traj['answer'],
                '关键词数量': traj['keyword_count'],
                '验证通过': '✅' if traj['validation_passed'] else '❌'
            })
        
        df = pd.DataFrame(traj_data)
        df.to_excel(writer, sheet_name='轨迹记录', index=False)
    
    def _write_raw_data_sheet(self, data: Dict[str, Any], writer):
        """写入原始数据统计表"""
        doc_data = []
        for doc in data['documents']:
            doc_data.append({
                '文档ID': doc['doc_id'],
                '处理时间(秒)': f"{doc['processing_time']:.1f}",
                '推理树数量': doc['total_trees'],
                '综合问题数量': doc['total_queries'],
                '处理状态': '✅ 成功' if doc['success'] else '❌ 失败'
            })
        
        df = pd.DataFrame(doc_data)
        df.to_excel(writer, sheet_name='文档明细', index=False)

def main():
    """主函数 - 修复现有的JSON文件"""
    results_dir = Path("results")
    
    # 查找JSON文件
    json_files = list(results_dir.glob("agent_reasoning_production_*.json"))
    
    if not json_files:
        print("❌ 未找到JSON文件")
        return
    
    exporter = FixedExcelExporter()
    
    for json_file in json_files:
        print(f"🔄 处理文件: {json_file.name}")
        excel_file = exporter.export_from_json(json_file)
        
        if excel_file:
            print(f"✅ Excel文件已生成: {excel_file.name}")
        else:
            print(f"❌ Excel生成失败: {json_file.name}")

if __name__ == "__main__":
    main() 
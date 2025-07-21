#!/usr/bin/env python3
"""
简洁Excel导出器 - 只包含4个核心工作表
1. 糅合后的问答对结果
2. 过程中所有问答对（每层）
3. 轨迹数据
4. 效率数据
"""

import json
import re
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class CleanExcelExporter:
    """简洁Excel导出器 - 4个核心工作表"""
    
    def __init__(self, output_dir: str = "results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def export_clean_excel(self, json_file: Path) -> Optional[Path]:
        """生成简洁Excel文件"""
        try:
            print(f"🔄 读取JSON文件: {json_file.name}")
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"📊 解析数据...")
            # 解析数据
            parsed_data = self._parse_data(data)
            
            # 生成Excel文件名
            excel_file = self.output_dir / f"CLEAN_{json_file.stem}.xlsx"
            
            print(f"📋 生成4个核心工作表...")
            # 导出Excel - 只有4个工作表
            with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
                # 1. 糅合后的问答对结果
                self._write_final_composite_qa(parsed_data, writer)
                
                # 2. 过程中所有问答对（每层）
                self._write_all_process_qa(parsed_data, writer)
                
                # 3. 轨迹数据
                self._write_trajectory_data(parsed_data, writer)
                
                # 4. 效率数据
                self._write_efficiency_data(parsed_data, writer)
            
            print(f"✅ 简洁Excel已生成: {excel_file.name}")
            return excel_file
            
        except Exception as e:
            logger.error(f"简洁Excel导出失败: {e}")
            print(f"❌ 导出失败: {e}")
            return None
    
    def _parse_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """解析数据"""
        parsed = {
            'session_info': self._extract_session_info(data),
            'composite_qa': [],      # 糅合后的问答对
            'all_process_qa': [],    # 所有过程中的问答对
            'trajectories': [],      # 轨迹数据
            'efficiency_data': []    # 效率数据
        }
        
        processing_results = data.get('processing_results', {})
        processed_docs = processing_results.get('processed_documents', [])
        
        print(f"📋 解析处理结果...")
        
        for doc_idx, doc in enumerate(processed_docs):
            doc_id = doc.get('doc_id', f'Unknown_{doc_idx}')
            reasoning_trees = doc.get('reasoning_trees', [])
            trajectory_records = doc.get('trajectory_records', [])
            
            print(f"  📄 处理文档: {doc_id} ({len(reasoning_trees)} 推理树)")
            
            # 解析推理树
            for tree_idx, tree_str in enumerate(reasoning_trees):
                if isinstance(tree_str, str):
                    # 提取树ID
                    tree_id_match = re.search(r"tree_id='([^']+)'", tree_str)
                    tree_id = tree_id_match.group(1) if tree_id_match else f'{doc_id}_tree_{tree_idx}'
                    
                    # 提取final_composite_query（糅合后的问答对）
                    composite_match = re.search(r"final_composite_query='([^']*)'", tree_str)
                    final_composite = composite_match.group(1) if composite_match else 'N/A'
                    
                    if final_composite and final_composite != 'N/A' and len(final_composite) > 20:
                        # 找根答案
                        root_answer = self._extract_root_answer(tree_str)
                        
                        parsed['composite_qa'].append({
                            'doc_id': doc_id,
                            'tree_id': tree_id,
                            'composite_question': final_composite,
                            'target_answer': root_answer,
                            'question_length': len(final_composite),
                            'tree_index': tree_idx
                        })
                    
                    # 提取所有层级的问答对
                    process_qa = self._extract_all_qa_from_tree(tree_str, doc_id, tree_id, tree_idx)
                    parsed['all_process_qa'].extend(process_qa)
            
            # 解析轨迹记录
            for traj in trajectory_records:
                if isinstance(traj, dict):
                    traj_info = self._parse_trajectory(traj, doc_id)
                    if traj_info:
                        parsed['trajectories'].append(traj_info)
            
            # 生成文档级效率数据
            doc_efficiency = {
                'doc_id': doc_id,
                'processing_time': doc.get('processing_time', 0),
                'trees_generated': len(reasoning_trees),
                'composite_questions': sum(1 for tree in reasoning_trees if self._has_valid_composite(tree)),
                'success': len(reasoning_trees) > 0
            }
            parsed['efficiency_data'].append(doc_efficiency)
        
        print(f"📊 解析完成:")
        print(f"   糅合问答对: {len(parsed['composite_qa'])} 个")
        print(f"   过程问答对: {len(parsed['all_process_qa'])} 个")
        print(f"   轨迹记录: {len(parsed['trajectories'])} 条")
        
        return parsed
    
    def _extract_all_qa_from_tree(self, tree_str: str, doc_id: str, tree_id: str, tree_idx: int) -> List[Dict[str, Any]]:
        """提取推理树中所有层级的问答对"""
        qa_pairs = []
        
        # 查找所有节点ID
        node_ids = re.findall(r"'([^']+)': QuestionTreeNode\(", tree_str)
        
        for node_idx, node_id in enumerate(node_ids):
            try:
                # 定位节点
                node_start = tree_str.find(f"'{node_id}': QuestionTreeNode(")
                if node_start == -1:
                    continue
                
                # 直接取一个足够长的段落，包含完整的节点信息
                node_section = tree_str[node_start:node_start + 1500]
                
                # 提取问题和答案
                query_match = re.search(r"query_text='([^']+)'", node_section)
                answer_match = re.search(r"answer='([^']+)'", node_section)
                
                if query_match and answer_match:
                    query_text = query_match.group(1)
                    answer = answer_match.group(1)
                    
                    # 提取层级
                    layer_match = re.search(r"layer_level=(\d+)", node_section)
                    layer = int(layer_match.group(1)) if layer_match else 0
                    
                    # 提取验证状态
                    validation_match = re.search(r"validation_passed=(\w+)", node_section)
                    validation_passed = validation_match.group(1) == 'True' if validation_match else False
                    
                    # 确定分支类型
                    if 'root' in node_id:
                        branch_type = 'root'
                    elif 'series' in node_id:
                        branch_type = 'series'
                    elif 'parallel' in node_id:
                        branch_type = 'parallel'
                    else:
                        branch_type = 'unknown'
                    
                    qa_pairs.append({
                        'doc_id': doc_id,
                        'tree_id': tree_id,
                        'tree_index': tree_idx,
                        'node_id': node_id,
                        'layer': layer,
                        'branch_type': branch_type,
                        'question': query_text,
                        'answer': answer,
                        'validation_passed': validation_passed
                    })
                    
            except Exception as e:
                print(f"    ⚠️ 节点解析失败: {node_id} - {e}")
                continue
        
        # 按层级排序
        qa_pairs.sort(key=lambda x: (x['layer'], x['node_id']))
        print(f"    ✅ 提取了 {len(qa_pairs)} 个问答对")
        
        return qa_pairs
    
    def _extract_root_answer(self, tree_str: str) -> str:
        """提取根答案"""
        try:
            # 查找root节点
            root_match = re.search(r"_root.*?answer='([^']+)'", tree_str)
            if root_match:
                return root_match.group(1)
            return 'N/A'
        except:
            return 'N/A'
    
    def _has_valid_composite(self, tree_str: str) -> bool:
        """检查是否有有效的综合问题"""
        if isinstance(tree_str, str):
            composite_match = re.search(r"final_composite_query='([^']*)'", tree_str)
            if composite_match:
                composite = composite_match.group(1)
                return composite and composite != 'N/A' and len(composite) > 20
        return False
    
    def _parse_trajectory(self, traj: Dict[str, Any], doc_id: str) -> Dict[str, Any]:
        """解析轨迹记录"""
        return {
            'doc_id': doc_id,
            'step': traj.get('step', 'N/A'),
            'step_id': traj.get('step_id', 0),
            'query_text': traj.get('query_text', 'N/A'),
            'answer': traj.get('answer', 'N/A'),
            'validation_passed': traj.get('validation_passed', False),
            'keyword_count': traj.get('keyword_count', 0),
            'layer': traj.get('layer', 0),
            'tree_id': traj.get('tree_id', 'N/A'),
            'timestamp': traj.get('timestamp', 0)
        }
    
    def _extract_session_info(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """提取会话信息"""
        summary = data.get('summary', {})
        return {
            'session_id': data.get('session_id', 'N/A'),
            'total_docs': summary.get('total_documents_attempted', 0),
            'successful_docs': summary.get('successful_documents', 0),
            'total_trees': summary.get('total_reasoning_trees', 0),
            'success_rate': summary.get('success_rate', 0),
            'total_time': data.get('total_processing_time', 0)
        }
    
    # Excel工作表生成函数
    def _write_final_composite_qa(self, data: Dict[str, Any], writer):
        """1. 糅合后的问答对结果"""
        print(f"  📋 生成糅合后问答对工作表 ({len(data['composite_qa'])} 个)")
        
        if not data['composite_qa']:
            # 创建空表
            empty_data = [['文档ID', '推理树ID', '糅合后的综合问题', '目标答案', '问题长度', '树索引']]
            df = pd.DataFrame(empty_data[1:], columns=empty_data[0])
        else:
            composite_data = []
            for idx, comp in enumerate(data['composite_qa']):
                composite_data.append({
                    '序号': idx + 1,
                    '文档ID': comp['doc_id'],
                    '推理树ID': comp['tree_id'],
                    '糅合后的综合问题': comp['composite_question'],
                    '目标答案': comp['target_answer'],
                    '问题长度': comp['question_length'],
                    '树索引': comp['tree_index']
                })
            
            df = pd.DataFrame(composite_data)
        
        df.to_excel(writer, sheet_name='1-糅合后问答对', index=False)
    
    def _write_all_process_qa(self, data: Dict[str, Any], writer):
        """2. 过程中所有问答对（每层）"""
        print(f"  📋 生成过程问答对工作表 ({len(data['all_process_qa'])} 个)")
        
        if not data['all_process_qa']:
            # 创建空表
            empty_data = [['文档ID', '推理树ID', '节点ID', '层级', '分支类型', '问题', '答案', '验证状态']]
            df = pd.DataFrame(empty_data[1:], columns=empty_data[0])
        else:
            process_data = []
            for idx, qa in enumerate(data['all_process_qa']):
                process_data.append({
                    '序号': idx + 1,
                    '文档ID': qa['doc_id'],
                    '推理树ID': qa['tree_id'],
                    '树索引': qa['tree_index'],
                    '节点ID': qa['node_id'],
                    '层级': qa['layer'],
                    '分支类型': qa['branch_type'],
                    '问题': qa['question'],
                    '答案': qa['answer'],
                    '验证状态': '✅ 通过' if qa['validation_passed'] else '❌ 失败'
                })
            
            df = pd.DataFrame(process_data)
        
        df.to_excel(writer, sheet_name='2-过程中所有问答对', index=False)
    
    def _write_trajectory_data(self, data: Dict[str, Any], writer):
        """3. 轨迹数据"""
        print(f"  📋 生成轨迹数据工作表 ({len(data['trajectories'])} 条)")
        
        if not data['trajectories']:
            # 创建空表
            empty_data = [['文档ID', '步骤', '步骤ID', '层级', '问题', '答案', '验证状态', '关键词数量']]
            df = pd.DataFrame(empty_data[1:], columns=empty_data[0])
        else:
            traj_data = []
            for idx, traj in enumerate(data['trajectories']):
                traj_data.append({
                    '序号': idx + 1,
                    '文档ID': traj['doc_id'],
                    '步骤': traj['step'],
                    '步骤ID': traj['step_id'],
                    '层级': traj['layer'],
                    '问题': traj['query_text'],
                    '答案': traj['answer'],
                    '验证状态': '✅ 通过' if traj['validation_passed'] else '❌ 失败',
                    '关键词数量': traj['keyword_count'],
                    '推理树ID': traj['tree_id'],
                    '时间戳': traj['timestamp']
                })
            
            df = pd.DataFrame(traj_data)
        
        df.to_excel(writer, sheet_name='3-轨迹数据', index=False)
    
    def _write_efficiency_data(self, data: Dict[str, Any], writer):
        """4. 效率数据"""
        print(f"  📋 生成效率数据工作表")
        
        session_info = data['session_info']
        
        # 整体效率数据
        overall_data = [
            ['项目', '数值', '单位'],
            ['会话ID', session_info['session_id'], ''],
            ['总处理时间', f"{session_info['total_time']:.2f}", '秒'],
            ['处理文档数', session_info['total_docs'], '个'],
            ['成功文档数', session_info['successful_docs'], '个'],
            ['成功率', f"{session_info['success_rate']:.1%}", ''],
            ['生成推理树', session_info['total_trees'], '个'],
            ['糅合问答对', len(data['composite_qa']), '个'],
            ['过程问答对', len(data['all_process_qa']), '个'],
            ['轨迹记录', len(data['trajectories']), '条'],
            ['', '', ''],
            ['平均效率', '', ''],
            ['平均时间/文档', f"{session_info['total_time']/max(session_info['total_docs'], 1):.2f}", '秒/文档'],
            ['平均推理树/文档', f"{session_info['total_trees']/max(session_info['successful_docs'], 1):.1f}", '个/文档'],
            ['平均问答对/推理树', f"{len(data['all_process_qa'])/max(session_info['total_trees'], 1):.1f}", '个/树']
        ]
        
        # 文档级效率数据
        if data['efficiency_data']:
            overall_data.extend([
                ['', '', ''],
                ['文档级详细数据', '', '']
            ])
            
            for eff in data['efficiency_data']:
                overall_data.append([
                    eff['doc_id'],
                    f"{eff['processing_time']:.1f}秒",
                    f"{eff['trees_generated']}个推理树"
                ])
        
        df = pd.DataFrame(overall_data)
        df.to_excel(writer, sheet_name='4-效率数据', index=False, header=False)

def main():
    """主函数"""
    results_dir = Path("results")
    
    json_files = list(results_dir.glob("agent_reasoning_production_*.json"))
    
    if not json_files:
        print("❌ 未找到JSON文件")
        return
    
    exporter = CleanExcelExporter()
    
    for json_file in json_files:
        print(f"\n🚀 生成简洁Excel: {json_file.name}")
        excel_file = exporter.export_clean_excel(json_file)
        
        if excel_file:
            print(f"✅ 简洁Excel已生成: {excel_file.name}")
        else:
            print(f"❌ 生成失败: {json_file.name}")

if __name__ == "__main__":
    main() 
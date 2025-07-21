#!/usr/bin/env python3
"""
默认Excel导出器 - 包含所有修复
1. 正确的层级识别（只有root是0，其他都+1）
2. 正确的分支类型识别
3. 修复的糅合问题生成逻辑
4. 4个核心工作表
"""

import json
import re
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
import time

logger = logging.getLogger(__name__)

class DefaultExcelExporter:
    """默认Excel导出器 - 包含所有修复"""
    
    def __init__(self, output_dir: str = "results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def export_final_excel(self, json_file: Path) -> Optional[Path]:
        """生成最终整合版Excel文件"""
        try:
            print(f"🔄 读取JSON文件: {json_file.name}")
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"📊 解析数据...")
            # 解析数据
            parsed_data = self._parse_data(data)
            
            # 生成Excel文件名
            excel_file = self.output_dir / f"{json_file.stem}.xlsx"
            
            print(f"📋 生成4个最终整合工作表...")
            # 导出Excel - 只有4个工作表
            with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
                # 1. 糅合后的问答对结果
                self._write_composite_qa(parsed_data, writer)
                
                # 2. 过程中所有问答对（每层）- 修复层级
                self._write_all_process_qa(parsed_data, writer)
                
                # 3. 轨迹数据 - 修复层级
                self._write_trajectory_data(parsed_data, writer)
                
                # 4. 效率数据
                self._write_efficiency_data(parsed_data, writer)
            
            print(f"✅ 最终整合Excel已生成: {excel_file.name}")
            return excel_file
            
        except Exception as e:
            logger.error(f"最终整合Excel导出失败: {e}")
            print(f"❌ 导出失败: {e}")
            return None
    
    def _parse_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """解析数据 - 包含所有修复"""
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
                    
                    # 检查是否是占位符或无效内容
                    is_placeholder = (
                        not final_composite or 
                        final_composite == 'N/A' or 
                        final_composite == 'Logical reasoning chain question requiring genuine step-by-step solving' or
                        len(final_composite) < 30
                    )
                    
                    if not is_placeholder:
                        # 找根答案
                        root_answer = self._extract_root_answer(tree_str)
                        
                        parsed['composite_qa'].append({
                            'doc_id': doc_id,
                            'tree_id': tree_id,
                            'composite_question': final_composite,
                            'target_answer': root_answer,
                            'question_length': len(final_composite),
                            'tree_index': tree_idx,
                            'is_valid': True
                        })
                    else:
                        # 记录无效的糅合问题
                        root_answer = self._extract_root_answer(tree_str)
                        parsed['composite_qa'].append({
                            'doc_id': doc_id,
                            'tree_id': tree_id,
                            'composite_question': '❌ 未生成真正的综合问题（仅为占位符）',
                            'target_answer': root_answer,
                            'question_length': 0,
                            'tree_index': tree_idx,
                            'is_valid': False
                        })
                    
                    # 提取所有层级的问答对 - 修复层级识别
                    process_qa = self._extract_all_qa_from_tree_fixed(tree_str, doc_id, tree_id, tree_idx)
                    parsed['all_process_qa'].extend(process_qa)
            
            # 解析轨迹记录 - 修复层级
            for traj in trajectory_records:
                if isinstance(traj, dict):
                    traj_info = self._parse_trajectory_fixed(traj, doc_id)
                    if traj_info:
                        parsed['trajectories'].append(traj_info)
            
            # 生成文档级效率数据
            valid_composites = sum(1 for comp in parsed['composite_qa'] if comp['doc_id'] == doc_id and comp['is_valid'])
            doc_efficiency = {
                'doc_id': doc_id,
                'processing_time': doc.get('processing_time', 0),
                'trees_generated': len(reasoning_trees),
                'valid_composite_questions': valid_composites,
                'placeholder_composite_questions': len(reasoning_trees) - valid_composites,
                'success': len(reasoning_trees) > 0
            }
            parsed['efficiency_data'].append(doc_efficiency)
        
        valid_composites = sum(1 for comp in parsed['composite_qa'] if comp['is_valid'])
        total_composites = len(parsed['composite_qa'])
        
        print(f"📊 解析完成:")
        print(f"   糅合问答对: {total_composites} 个 (有效: {valid_composites}, 占位符: {total_composites - valid_composites})")
        print(f"   过程问答对: {len(parsed['all_process_qa'])} 个")
        print(f"   轨迹记录: {len(parsed['trajectories'])} 条")
        
        return parsed
    
    def _extract_all_qa_from_tree_fixed(self, tree_str: str, doc_id: str, tree_id: str, tree_idx: int) -> List[Dict[str, Any]]:
        """提取推理树中所有层级的问答对 - 修复层级和分支类型识别"""
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
                    
                    # 提取层级信息
                    layer_match = re.search(r"'layer': (\d+)", node_section)
                    corrected_layer = self._get_corrected_layer(node_id)
                    
                    # 验证状态
                    validation_passed = "'validation_passed': True" in node_section
                    
                    # 修复分支类型识别 - 按优先级匹配
                    branch_type = self._identify_branch_type_fixed(node_id)
                    
                    qa_pairs.append({
                        'doc_id': doc_id,
                        'tree_id': tree_id,
                        'tree_index': tree_idx,
                        'node_id': node_id,
                        'layer': corrected_layer,
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
    
    def _get_corrected_layer(self, node_id: str) -> int:
        """根据节点ID获取正确的层级"""
        # Root节点 - 层级0
        if '_root' in node_id and node_id.endswith('_root'):
            return 0
        
        # Series1和Parallel1 - 层级1 
        if ('_series1' in node_id and '_series2' not in node_id) or \
           ('_parallel1' in node_id and '_series2' not in node_id):
            return 1
        
        # Series2和含有series2的parallel - 层级2
        if '_series2' in node_id:
            return 2
        
        # 其他series和parallel - 层级1（默认）
        if '_series' in node_id or '_parallel' in node_id:
            return 1
        
        # 默认层级0
        return 0
    
    def _identify_branch_type_fixed(self, node_id: str) -> str:
        """正确识别分支类型 - 按优先级匹配"""
        # 按照最具体的特征优先匹配
        if '_parallel' in node_id:
            return 'parallel'
        elif '_series' in node_id:
            return 'series'
        elif '_root' in node_id or node_id.endswith('_root'):
            return 'root'
        else:
            return 'unknown'
    
    def _parse_trajectory_fixed(self, traj: Dict[str, Any], doc_id: str) -> Dict[str, Any]:
        """解析轨迹记录 - 修复层级"""
        original_layer = traj.get('layer', 0)
        
        # 根据step类型修复层级
        step = traj.get('step', 'N/A')
        if 'root' in step.lower():
            corrected_layer = 0
        elif 'series1' in step.lower() or 'parallel1' in step.lower():
            corrected_layer = 1
        elif 'series2' in step.lower():
            corrected_layer = 2
        else:
            corrected_layer = original_layer
        
        return {
            'doc_id': doc_id,
            'step': step,
            'step_id': traj.get('step_id', 0),
            'query_text': traj.get('query_text', 'N/A'),
            'answer': traj.get('answer', 'N/A'),
            'validation_passed': traj.get('validation_passed', False),
            'keyword_count': traj.get('keyword_count', 0),
            'layer': corrected_layer,
            'original_layer': original_layer,
            'tree_id': traj.get('tree_id', 'N/A'),
            'timestamp': traj.get('timestamp', 0)
        }
    
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
    
    def _extract_composite_qa_data(self, data: Dict[str, Any]) -> List[Dict]:
        """提取糅合后的问答对数据"""
        composite_data = []
        
        processed_docs = data.get('processing_results', {}).get('processed_documents', [])
        
        for doc_idx, doc in enumerate(processed_docs):
            doc_id = doc.get('doc_id', f'unknown_doc_{doc_idx}')
            reasoning_trees = doc.get('reasoning_trees', [])
            
            for tree_idx, tree_str in enumerate(reasoning_trees):
                if isinstance(tree_str, str):
                    # 提取糅合问题
                    composite_match = re.search(r"final_composite_query='([^']*)'", tree_str)
                    composite_question = composite_match.group(1) if composite_match else "未找到糅合问题"
                    
                    # 构建原始推理链 - 直接从树结构提取
                    original_reasoning_chain = self._build_original_reasoning_chain(tree_str)
                    
                    # 提取root答案
                    root_answer_match = re.search(r"_root[^}]*'answer': '([^']*)'", tree_str)
                    target_answer = root_answer_match.group(1) if root_answer_match else "未找到目标答案"
                    
                    # 检查是否为占位符
                    is_placeholder = any(keyword in composite_question for keyword in [
                        "follow this reasoning chain",
                        "To discover",
                        "To identify", 
                        "To determine",
                        "Logical reasoning chain question"
                    ])
                    
                    status = '❌ 占位符' if is_placeholder else '✅ 有效'
                    
                    # 生成唯一的推理树ID
                    tree_id = f"multi_{doc_id}_root_{tree_idx}_{hash(tree_str) % 10000000000}"
                    
                    composite_data.append({
                        'doc_id': doc_id,
                        'tree_id': tree_id,
                        'tree_index': tree_idx,
                        'composite_question': composite_question,
                        'original_reasoning_chain': original_reasoning_chain,
                        'target_answer': target_answer,
                        'is_valid': not is_placeholder,
                        'question_length': len(composite_question)
                    })
        
        return composite_data
    
    def _build_original_reasoning_chain(self, tree_str: str) -> str:
        """从推理树构建原始推理链"""
        try:
            # 提取所有节点的问题 - 使用更精确的模式
            nodes_by_layer = {}
            
            # 先找到所有的query_text
            query_texts = re.findall(r"query_text='([^']*)'", tree_str)
            
            # 然后找到节点ID模式来建立对应关系
            node_id_pattern = r"node_id='([^']*_(root|series\d+|parallel\d+)[^']*)'[^}]*query_text='([^']*)'"
            matches = re.findall(node_id_pattern, tree_str)
            
            for full_match in matches:
                node_id = full_match[0]
                node_type_suffix = full_match[1]
                question = full_match[2]
                
                # 确定层级
                if '_root' in node_id:
                    layer = 0
                elif '_series1' in node_id or '_parallel1' in node_id:
                    layer = 1
                elif '_series2' in node_id:
                    layer = 2
                else:
                    layer = 1
                
                # 确定节点类型
                if '_parallel' in node_id:
                    node_type = 'parallel'
                elif '_series' in node_id:
                    node_type = 'series'
                else:
                    node_type = 'root'
                
                if layer not in nodes_by_layer:
                    nodes_by_layer[layer] = []
                
                nodes_by_layer[layer].append({
                    'id': node_id,
                    'question': question,
                    'type': node_type,
                    'layer': layer
                })
            
            # 如果上面的方法失败，使用更简单的方法
            if not nodes_by_layer and query_texts:
                return "原始问题序列: " + " → ".join(query_texts[:5])  # 最多显示5个问题
            
            # 构建推理链：从最深层开始倒序拼接
            reasoning_steps = []
            max_layer = max(nodes_by_layer.keys()) if nodes_by_layer else 0
            
            for layer in range(max_layer, -1, -1):
                if layer not in nodes_by_layer:
                    continue
                    
                layer_nodes = nodes_by_layer[layer]
                
                # 按类型分组：先处理parallel，再处理series
                parallel_nodes = [n for n in layer_nodes if n['type'] == 'parallel']
                series_nodes = [n for n in layer_nodes if n['type'] == 'series']
                root_nodes = [n for n in layer_nodes if n['type'] == 'root']
                
                # 处理parallel节点（横向拼接）
                if parallel_nodes:
                    parallel_questions = [node['question'] for node in parallel_nodes]
                    step_text = "并行分析: " + "; ".join(parallel_questions)
                    reasoning_steps.append(step_text)
                
                # 处理series节点
                for node in series_nodes:
                    reasoning_steps.append(f"进一步分析: {node['question']}")
                
                # 处理root节点
                for node in root_nodes:
                    reasoning_steps.append(f"最终问题: {node['question']}")
            
            return " → ".join(reasoning_steps) if reasoning_steps else "无法构建推理链"
            
        except Exception as e:
            return f"推理链构建失败: {str(e)}"
    
    def _write_composite_qa(self, data: Dict[str, Any], writer):
        """1. 糅合后问答对 - 添加原始推理链列"""
        print("  📋 生成糅合后问答对工作表", end="")
        
        composite_data = self._extract_composite_qa_data(data)
        
        if not composite_data:
            # 如果没有新格式的数据，尝试旧格式
            composite_data = []
            for idx, comp in enumerate(data.get('composite_qa', [])):
                status = '✅ 有效' if comp.get('is_valid', True) else '❌ 占位符'
                composite_data.append({
                    '序号': idx + 1,
                    '文档ID': comp['doc_id'],
                    '推理树ID': comp['tree_id'],
                    '糅合后的综合问题': comp['composite_question'],
                    '原始推理链': comp.get('original_reasoning_chain', '未记录'),
                    '目标答案': comp['target_answer'],
                    '问题状态': status,
                    '问题长度': comp['question_length'],
                    '树索引': comp['tree_index']
                })
            
            df = pd.DataFrame(composite_data)
        else:
            # 新格式数据处理
            formatted_data = []
            valid_count = sum(1 for item in composite_data if item['is_valid'])
            placeholder_count = len(composite_data) - valid_count
            
            for idx, item in enumerate(composite_data):
                status = '✅ 有效' if item['is_valid'] else '❌ 占位符'
                formatted_data.append({
                    '序号': idx + 1,
                    '文档ID': item['doc_id'],
                    '推理树ID': item['tree_id'],
                    '糅合后的综合问题': item['composite_question'],
                    '原始推理链': item['original_reasoning_chain'],
                    '目标答案': item['target_answer'],
                    '问题状态': status,
                    '问题长度': item['question_length'],
                    '树索引': item['tree_index']
                })
            
            df = pd.DataFrame(formatted_data)
            print(f" (总数: {len(composite_data)}, 有效: {valid_count}, 占位符: {placeholder_count})")
        
        df.to_excel(writer, sheet_name='1-糅合后问答对', index=False)
    
    def _write_all_process_qa(self, data: Dict[str, Any], writer):
        """2. 过程中所有问答对（每层）- 修复层级显示"""
        print(f"  📋 生成过程问答对工作表 ({len(data['all_process_qa'])} 个)")
        
        # 统计分支类型和层级
        branch_stats = {}
        layer_stats = {}
        for qa in data['all_process_qa']:
            branch_type = qa['branch_type']
            layer = qa['layer']
            branch_stats[branch_type] = branch_stats.get(branch_type, 0) + 1
            layer_stats[layer] = layer_stats.get(layer, 0) + 1
        
        print(f"    分支类型统计: {branch_stats}")
        print(f"    层级统计: {layer_stats}")
        
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
                    '修正层级': qa['layer'],
                    '分支类型': qa['branch_type'],
                    '问题': qa['question'],
                    '答案': qa['answer'],
                    '验证状态': '✅ 通过' if qa['validation_passed'] else '❌ 失败'
                })
            
            df = pd.DataFrame(process_data)
        
        df.to_excel(writer, sheet_name='2-过程中所有问答对', index=False)
    
    def _write_trajectory_data(self, data: Dict[str, Any], writer):
        """3. 轨迹数据 - 修复层级显示"""
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
                    '修正层级': traj['layer'],
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
        """4. 效率数据 - 包含糅合问题质量统计"""
        print(f"  📋 生成效率数据工作表")
        
        session_info = data['session_info']
        valid_composites = sum(1 for comp in data['composite_qa'] if comp.get('is_valid', True))
        total_composites = len(data['composite_qa'])
        placeholder_composites = total_composites - valid_composites
        
        # 统计层级分布
        layer_stats = {}
        for qa in data['all_process_qa']:
            layer = qa['layer']
            layer_stats[layer] = layer_stats.get(layer, 0) + 1
        
        # 整体效率数据
        overall_data = [
            ['项目', '数值', '单位'],
            ['会话ID', session_info['session_id'], ''],
            ['总处理时间', f"{session_info['total_time']:.2f}", '秒'],
            ['处理文档数', session_info['total_docs'], '个'],
            ['成功文档数', session_info['successful_docs'], '个'],
            ['成功率', f"{session_info['success_rate']:.1%}", ''],
            ['生成推理树', session_info['total_trees'], '个'],
            ['', '', ''],
            ['糅合问题质量', '', ''],
            ['总糅合问答对', total_composites, '个'],
            ['有效糅合问题', valid_composites, '个'],
            ['占位符问题', placeholder_composites, '个'],
            ['糅合问题有效率', f"{(valid_composites/max(total_composites, 1))*100:.1f}", '%'],
            ['', '', ''],
            ['层级分布 (修正后)', '', ''],
            ['层级0 (Root)', layer_stats.get(0, 0), '个'],
            ['层级1 (Series1/Parallel1)', layer_stats.get(1, 0), '个'],
            ['层级2 (Series2)', layer_stats.get(2, 0), '个'],
            ['', '', ''],
            ['过程数据', '', ''],
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
                ['文档级详细数据', '', ''],
                ['文档ID', '处理时间', '推理树数量', '有效糅合问题', '占位符糅合问题']
            ])
            
            for eff in data['efficiency_data']:
                overall_data.append([
                    eff['doc_id'],
                    f"{eff['processing_time']:.1f}秒",
                    f"{eff['trees_generated']}个",
                    f"{eff['valid_composite_questions']}个",
                    f"{eff['placeholder_composite_questions']}个"
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
    
    exporter = DefaultExcelExporter()
    
    for json_file in json_files:
        # 跳过备份文件
        if '.backup.json' in json_file.name:
            continue
            
        print(f"\n🚀 生成最终整合Excel: {json_file.name}")
        excel_file = exporter.export_final_excel(json_file)
        
        if excel_file:
            print(f"✅ 最终整合Excel已生成: {excel_file.name}")
        else:
            print(f"❌ 生成失败: {json_file.name}")

if __name__ == "__main__":
    main() 
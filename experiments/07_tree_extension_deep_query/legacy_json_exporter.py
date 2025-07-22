#!/usr/bin/env python3
"""
旧格式JSON导出器 - 专门处理字符串格式的AgentReasoningTree数据
处理 agent_reasoning_production_en0028_20250722_122412.json 这类旧格式文件
"""

import json
import pandas as pd
import re
import openai
import os
from typing import Dict, List, Any, Optional
from pathlib import Path

class LegacyJsonExporter:
    """旧格式JSON导出器 - 处理字符串格式的推理树"""
    
    def __init__(self):
        self.data = {
            'documents_processed': 0,
            'total_reasoning_trees': 0,
            'total_processing_time': 0.0
        }
        
        # 初始化OpenAI客户端
        self.openai_client = None
        try:
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                self.openai_client = openai.OpenAI(api_key=api_key)
                print("✅ OpenAI客户端初始化成功，将调用GPT-4o生成自然语言整合问题")
            else:
                print("⚠️ 未找到OpenAI API key，请设置OPENAI_API_KEY环境变量")
        except Exception as e:
            print(f"⚠️ OpenAI客户端初始化失败: {e}")

    def export_to_excel(self, json_file_path: str, output_dir: str = "results") -> str:
        """导出旧格式JSON到Excel"""
        try:
            print(f"🔄 开始处理旧格式JSON文件: {json_file_path}")
            
            # 创建输出目录
            output_path = Path(output_dir)
            output_path.mkdir(exist_ok=True)
            
            # 读取JSON文件
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 解析旧格式数据
            parsed_data = self._parse_legacy_data(data)
            
            # 生成输出文件名
            input_filename = Path(json_file_path).stem
            excel_filename = f"legacy_export_{input_filename}.xlsx"
            excel_path = output_path / excel_filename
            
            # 写入Excel
            self._write_to_excel(parsed_data, str(excel_path))
            
            print(f"✅ Excel导出完成: {excel_path}")
            return str(excel_path)
            
        except Exception as e:
            print(f"❌ 导出失败: {e}")
            raise

    def _parse_legacy_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """解析旧格式的字符串JSON数据"""
        parsed = {
            'efficiency_data': [],   # 文档处理效率统计
            'composite_qa': [],      # 糅合后的问答对
            'all_process_qa': [],    # 所有过程中的问答对
            'trajectories': [],      # 轨迹数据
        }
        
        print(f"📊 解析数据结构: {list(data.keys())}")
        
        # 处理每个文档的结果
        if 'results' in data:
            for doc_result in data['results']:
                doc_id = doc_result.get('document_id', 'unknown')
                print(f"📄 处理文档: {doc_id}")
                
                # 处理推理树
                reasoning_trees = doc_result.get('reasoning_trees', [])
                for tree_idx, tree_str in enumerate(reasoning_trees):
                    if isinstance(tree_str, str):  # 字符串格式数据
                        print(f"🌳 解析推理树 {tree_idx + 1}: 字符串格式")
                        
                        # 提取问答对
                        qa_pairs = self._extract_all_qa_from_tree(tree_str, doc_id, tree_idx)
                        parsed['all_process_qa'].extend(qa_pairs)
                        
                        # 生成糅合问题和答案
                        root_answer = self._extract_root_answer(tree_str)
                        composite_qa = self._generate_composite_questions(qa_pairs, root_answer, doc_id, tree_idx)
                        
                        if composite_qa:
                            parsed['composite_qa'].append({
                                'doc_id': doc_id,
                                'tree_id': f"tree_{tree_idx}",
                                'tree_index': tree_idx,
                                'target_answer': root_answer,
                                'nested_question': composite_qa.get('nested_cumulative_question', '❌ 嵌套累积型问题生成失败'),
                                'natural_question': composite_qa.get('llm_integrated_question', '❌ LLM整合型问题生成失败'),
                                'nested_answer': composite_qa.get('nested_cumulative_answer', '❌ 嵌套累积型答案生成失败'),
                                'natural_answer': composite_qa.get('llm_integrated_answer', '❌ LLM整合型答案生成失败'),
                                'debug_info': composite_qa.get('debug_info', '')
                            })
                
                # 添加效率数据
                parsed['efficiency_data'].append({
                    'document_id': doc_id,
                    'processing_time': doc_result.get('processing_time', 0),
                    'reasoning_trees_count': len(reasoning_trees),
                    'nested_questions_count': sum(1 for qa in parsed['composite_qa'] if qa['doc_id'] == doc_id and '❌' not in qa['nested_question']),
                    'llm_questions_count': sum(1 for qa in parsed['composite_qa'] if qa['doc_id'] == doc_id and '❌' not in qa['natural_question']),
                    'total_valid_questions': sum(1 for qa in parsed['composite_qa'] if qa['doc_id'] == doc_id and '❌' not in qa['nested_question'] and '❌' not in qa['natural_question']),
                    'success': doc_result.get('success', True)
                })
                
                # 处理轨迹数据
                if 'trajectories' in doc_result:
                    parsed['trajectories'].extend(self._parse_trajectories(doc_result['trajectories'], doc_id))
        
        print(f"✅ 解析完成: {len(parsed['composite_qa'])} 个糅合问答, {len(parsed['all_process_qa'])} 个过程问答")
        return parsed

    def _extract_all_qa_from_tree(self, tree_str: str, doc_id: str, tree_idx: int) -> List[Dict[str, Any]]:
        """从字符串格式推理树中提取所有问答对"""
        qa_pairs = []
        
        try:
            # 使用正则表达式提取查询和答案
            # 匹配 PreciseQuery 结构
            query_pattern = r"PreciseQuery\(\s*query_id='([^']+)'.*?query_text='([^']+)'.*?answer='([^']+)'.*?\)"
            matches = re.findall(query_pattern, tree_str, re.DOTALL)
            
            for query_id, query_text, answer in matches:
                # 推断层级
                layer_level = self._infer_layer_from_node_id(query_id)
                
                # 确定分支类型
                branch_type = self._identify_branch_type(query_id)
                
                qa_pairs.append({
                    'document_id': doc_id,
                    'tree_id': f"tree_{tree_idx}",
                    'node_id': query_id,
                    'layer': layer_level,
                    'branch_type': branch_type,
                    'query_text': query_text,
                    'answer': answer,
                    'generation_method': 'extracted_from_tree',
                    'validation_passed': True  # 假设从树中提取的都是有效的
                })
                
            # 如果正则匹配失败，尝试其他方法
            if not qa_pairs:
                print(f"⚠️ 正则匹配失败，尝试简单文本提取 for tree_{tree_idx}")
                # 可以在这里添加更多的提取逻辑
                
        except Exception as e:
            print(f"❌ 提取问答对失败 for tree_{tree_idx}: {e}")
            
        return qa_pairs

    def _identify_branch_type(self, node_id: str) -> str:
        """识别分支类型"""
        if 'root' in node_id.lower():
            return 'root'
        elif 'series' in node_id.lower():
            return 'series'
        elif 'parallel' in node_id.lower():
            return 'parallel'
        else:
            return 'unknown'

    def _infer_layer_from_node_id(self, node_id: str) -> int:
        """从节点ID推断层级"""
        try:
            # 根据node_id模式推断层级
            if '_root' in node_id or node_id.endswith('_root'):
                return 0  # 根节点是第0层
            elif '_series1' in node_id or '_parallel1' in node_id:
                return 1  # 第一层扩展
            elif '_series2' in node_id or '_parallel2' in node_id:
                return 2  # 第二层扩展
            elif 'series' in node_id and not any(x in node_id for x in ['series1', 'series2']):
                return 1  # 默认series是第一层
            elif 'parallel' in node_id and not any(x in node_id for x in ['parallel1', 'parallel2']):
                return 1  # 默认parallel是第一层
            else:
                # 尝试从数字后缀推断
                parts = node_id.split('_')
                for part in reversed(parts):
                    if part.isdigit():
                        return min(int(part), 2)  # 最大层级是2
                return 0  # 默认返回0
        except Exception:
            return 0

    def _extract_root_answer(self, tree_str: str) -> str:
        """提取根答案"""
        try:
            # 查找根节点的答案
            root_pattern = r"root.*?answer='([^']+)'"
            match = re.search(root_pattern, tree_str, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1)
            
            # 如果找不到，尝试查找第一个答案
            first_answer_pattern = r"answer='([^']+)'"
            match = re.search(first_answer_pattern, tree_str)
            if match:
                return match.group(1)
                
            return "未找到根答案"
        except Exception as e:
            print(f"❌ 提取根答案失败: {e}")
            return "提取失败"

    def _generate_composite_questions(self, qa_pairs: List[Dict], root_answer: str, doc_id: str, tree_idx: int) -> Dict[str, str]:
        """生成双格式嵌套问题和答案"""
        if not qa_pairs:
            return self._fallback_generation(root_answer, "无问答对数据")
        
        try:
            # 按层级分组
            queries_by_layer = {}
            answers_by_layer = {}
            
            for qa in qa_pairs:
                layer = qa['layer']
                if layer not in queries_by_layer:
                    queries_by_layer[layer] = []
                    answers_by_layer[layer] = []
                queries_by_layer[layer].append(qa['query_text'])
                answers_by_layer[layer].append(qa['answer'])
            
            debug_info = f"提取到 {len(queries_by_layer)} 层数据: {list(queries_by_layer.keys())}"
            print(f"📊 {debug_info}")
            
            # 生成嵌套问题和答案
            if len(queries_by_layer) == 1:
                # 只有一层数据，使用简化生成
                layer = list(queries_by_layer.keys())[0]
                queries = queries_by_layer[layer]
                answers = answers_by_layer[layer]
                
                nested_question = f"({', '.join(queries)})" if len(queries) > 1 else queries[0]
                nested_answer = f"({', '.join(answers)})" if len(answers) > 1 else answers[0]
                
                llm_question = self._generate_single_layer_llm_question(queries)
                llm_answer = self._generate_single_layer_llm_answer(answers, root_answer)
                
                return {
                    'nested_cumulative_question': nested_question,
                    'nested_cumulative_answer': nested_answer,
                    'llm_integrated_question': llm_question,
                    'llm_integrated_answer': llm_answer,
                    'debug_info': debug_info + " (单层简化生成)"
                }
            else:
                # 多层数据，正常生成
                nested_question = self._generate_nested_cumulative_from_layers(queries_by_layer)
                nested_answer = self._generate_nested_cumulative_answer_from_layers(answers_by_layer)
                
                llm_question = self._generate_llm_integrated_question(queries_by_layer)
                llm_answer = self._generate_llm_integrated_answer(answers_by_layer, root_answer)
                
                return {
                    'nested_cumulative_question': nested_question,
                    'nested_cumulative_answer': nested_answer,
                    'llm_integrated_question': llm_question,
                    'llm_integrated_answer': llm_answer,
                    'debug_info': debug_info + " (多层正常生成)"
                }
                
        except Exception as e:
            print(f"❌ 生成糅合问题失败: {e}")
            return self._fallback_generation(root_answer, f"异常: {str(e)}")

    def _generate_single_layer_llm_question(self, queries: List[str]) -> str:
        """为单层数据生成LLM整合问题"""
        if not self.openai_client:
            return f"整合问题: {', '.join(queries)}"
        
        try:
            if len(queries) == 1:
                return queries[0]
            
            combined_queries = "; ".join(queries)
            prompt = f"""Create a natural reasoning question based on this sub-question to determine the answer.

Sub-questions: {combined_queries}

Create a single, clear question that logically combines these elements."""

            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You create clear reasoning questions."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=200,
                timeout=30
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"❌ LLM问题生成失败: {e}")
            return f"整合问题: {', '.join(queries)}"

    def _generate_single_layer_llm_answer(self, answers: List[str], root_answer: str) -> str:
        """为单层数据生成LLM整合答案"""
        if not self.openai_client:
            return f"整合答案: {', '.join(answers)} → {root_answer}"
        
        try:
            if len(answers) == 1:
                return answers[0]
            
            combined_answers = "; ".join(answers)
            prompt = f"""Create a natural reasoning answer that shows how the sub-answer leads to the final answer.

Sub-answers: {combined_answers}
Final answer: {root_answer}

Show the logical connection."""

            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You create clear logical explanations."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=200,
                timeout=30
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"❌ LLM答案生成失败: {e}")
            return f"整合答案: {', '.join(answers)} → {root_answer}"

    def _generate_nested_cumulative_from_layers(self, queries_by_layer: Dict[int, List[str]]) -> str:
        """生成嵌套累积型问题"""
        try:
            if not queries_by_layer:
                return "(空问题树)"
            
            # 获取所有层级，从深到浅排序
            layers = sorted(queries_by_layer.keys(), reverse=True)
            
            # 开始构建嵌套结构
            nested_parts = []
            
            for layer in layers:
                queries = queries_by_layer[layer]
                if queries:
                    if len(queries) == 1:
                        nested_parts.append(queries[0])
                    else:
                        # 多个查询用括号组合
                        combined = f"({', '.join(queries)})"
                        nested_parts.append(combined)
            
            if not nested_parts:
                return "(无有效问题)"
            
            # 构建最终的嵌套结构：从最深层到最浅层
            if len(nested_parts) == 1:
                return nested_parts[0]
            elif len(nested_parts) == 2:
                return f"({nested_parts[1]}, {nested_parts[0]})"
            else:
                # 3层或更多：(root, (middle, deepest))
                deepest = nested_parts[0]
                middle = nested_parts[1]
                root = nested_parts[2] if len(nested_parts) > 2 else ""
                
                if root:
                    return f"({root}, ({middle}, {deepest}))"
                else:
                    return f"({middle}, {deepest})"
                    
        except Exception as e:
            print(f"❌ 嵌套问题生成失败: {e}")
            return "(嵌套生成失败)"

    def _generate_nested_cumulative_answer_from_layers(self, answers_by_layer: Dict[int, List[str]]) -> str:
        """生成嵌套累积型答案"""
        try:
            # 获取所有层级，从深到浅排序
            layers = sorted(answers_by_layer.keys(), reverse=True)
            
            # 开始构建嵌套答案结构
            nested_parts = []
            
            for layer in layers:
                answers = answers_by_layer[layer]
                if answers:
                    if len(answers) == 1:
                        nested_parts.append(answers[0])
                    else:
                        # 多个答案用括号组合
                        combined = f"({', '.join(answers)})"
                        nested_parts.append(combined)
            
            if not nested_parts:
                return "(无有效答案)"
            
            # 构建最终的嵌套结构
            if len(nested_parts) == 1:
                return nested_parts[0]
            elif len(nested_parts) == 2:
                return f"({nested_parts[1]}, {nested_parts[0]})"
            else:
                # 3层或更多
                deepest = nested_parts[0]
                middle = nested_parts[1]
                root = nested_parts[2] if len(nested_parts) > 2 else ""
                
                if root:
                    return f"({root}, ({middle}, {deepest}))"
                else:
                    return f"({middle}, {deepest})"
                    
        except Exception as e:
            print(f"❌ 嵌套答案生成失败: {e}")
            return "(嵌套答案生成失败)"

    def _generate_llm_integrated_question(self, queries_by_layer: Dict[int, List[str]]) -> str:
        """生成LLM整合型问题"""
        if not self.openai_client:
            # 不使用LLM的备选方案
            all_queries = []
            for layer in sorted(queries_by_layer.keys()):
                all_queries.extend(queries_by_layer[layer])
            return f"整合问题: {'; '.join(all_queries)}"
        
        try:
            # 将所有层级的问题收集起来，按层级排列
            structured_queries = []
            for layer in sorted(queries_by_layer.keys()):
                queries = queries_by_layer[layer]
                if queries:
                    structured_queries.append(f"Layer {layer}: {'; '.join(queries)}")
            
            context = "\n".join(structured_queries)
            
            """调用OpenAI GPT-3.5生成自然语言整合问题"""
            integration_prompt = f"""**TASK: Create a natural language reasoning question that integrates multiple sub-questions while maintaining their logical order.**

Available sub-questions by layer:
{context}

**REQUIREMENTS:**
1. Create ONE comprehensive question that logically combines all sub-questions
2. Maintain the reasoning flow from different layers
3. Make it readable and coherent in natural language
4. Keep the logical dependency structure

**OUTPUT:** A single natural language question."""

            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert at creating natural language reasoning questions that integrate multiple sub-questions while maintaining logical flow."},
                    {"role": "user", "content": integration_prompt}
                ],
                temperature=0.4,
                max_tokens=300,
                timeout=30
            )
            
            generated_question = response.choices[0].message.content.strip()
            
            # 清理和验证生成的问题
            if generated_question and len(generated_question) > 10:
                return generated_question
            else:
                # 降级处理
                return self._generate_fallback_integrated_question(queries_by_layer)
                
        except Exception as e:
            print(f"❌ LLM整合问题生成失败: {e}")
            return self._generate_fallback_integrated_question(queries_by_layer)

    def _generate_llm_integrated_answer(self, answers_by_layer: Dict[int, List[str]], root_answer: str) -> str:
        """生成LLM整合型答案"""
        if not self.openai_client:
            # 不使用LLM的备选方案
            all_answers = []
            for layer in sorted(answers_by_layer.keys()):
                all_answers.extend(answers_by_layer[layer])
            return f"整合答案: {'; '.join(all_answers)} → {root_answer}"
        
        try:
            # 将所有层级的答案收集起来
            structured_answers = []
            for layer in sorted(answers_by_layer.keys()):
                answers = answers_by_layer[layer]
                if answers:
                    structured_answers.append(f"Layer {layer}: {'; '.join(answers)}")
            
            context = "\n".join(structured_answers)
            
            """调用OpenAI生成自然语言整合答案"""
            answer_prompt = f"""**TASK: Create a natural language integrated answer that shows the reasoning flow.**

Layer answers available:
{context}

Final target answer: {root_answer}

**REQUIREMENTS:**
1. Show how the answers from different layers lead to the final answer
2. Create a logical reasoning chain
3. Keep it concise but clear (under 200 words)
4. End with the final answer: {root_answer}

**OUTPUT:** A natural language answer showing the reasoning chain."""

            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert at creating clear, logical answer explanations."},
                    {"role": "user", "content": answer_prompt}
                ],
                temperature=0.4,
                max_tokens=300,
                timeout=30
            )
            
            generated_answer = response.choices[0].message.content.strip()
            
            if generated_answer and len(generated_answer) > 10:
                return generated_answer
            else:
                return self._generate_fallback_integrated_answer(answers_by_layer, root_answer)
                
        except Exception as e:
            print(f"❌ LLM整合答案生成失败: {e}")
            return self._generate_fallback_integrated_answer(answers_by_layer, root_answer)

    def _generate_fallback_integrated_question(self, queries_by_layer: Dict[int, List[str]]) -> str:
        """降级版本的整合问题生成"""
        all_queries = []
        for layer in sorted(queries_by_layer.keys()):
            all_queries.extend(queries_by_layer[layer])
        return f"Based on these interconnected questions: {'; '.join(all_queries)}, what is the comprehensive answer?"

    def _fallback_generation(self, root_answer: str, debug_info: str) -> Dict[str, str]:
        """降级生成方法"""
        return {
            'nested_cumulative_question': "(提取失败)",
            'nested_cumulative_answer': root_answer,
            'llm_integrated_question': "(提取失败)",
            'llm_integrated_answer': root_answer,
            'debug_info': debug_info + " (降级生成)"
        }

    def _parse_trajectories(self, trajectories: List[Dict], doc_id: str) -> List[Dict]:
        """解析轨迹记录"""
        parsed_trajectories = []
        for traj in trajectories:
            parsed_trajectories.append({
                'document_id': doc_id,
                'step': traj.get('step', ''),
                'query_id': traj.get('query_id', ''),
                'query_text': traj.get('query_text', ''),
                'answer': traj.get('answer', ''),
                'minimal_keywords': ', '.join(traj.get('minimal_keywords', [])),
                'generation_method': traj.get('generation_method', ''),
                'validation_passed': traj.get('validation_passed', True)
            })
        return parsed_trajectories

    def _write_to_excel(self, data: Dict[str, Any], excel_path: str):
        """写入Excel工作表"""
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            # Sheet1: 文档处理效率统计
            self._write_efficiency_stats(data['efficiency_data'], writer)
            
            # Sheet2: 所有过程中的问答对
            self._write_all_process_qa(data['all_process_qa'], writer)
            
            # Sheet3: 推理轨迹记录
            self._write_trajectories(data['trajectories'], writer)
            
            # Sheet4: 糅合后的综合问答（四列格式）
            self._write_final_composite_qa(data['composite_qa'], writer)

    def _write_efficiency_stats(self, efficiency_data: List[Dict], writer):
        """写入文档处理效率统计"""
        if not efficiency_data:
            return
        
        df = pd.DataFrame(efficiency_data)
        df.columns = ['文档ID', '处理时间(秒)', '生成推理树数', '有效嵌套问题数', '有效LLM问题数', '总有效问题数', '处理成功']
        
        df.to_excel(writer, sheet_name='Sheet1-文档处理效率统计', index=False)

    def _write_all_process_qa(self, all_process_qa: List[Dict], writer):
        """写入所有过程中的问答对"""
        if not all_process_qa:
            return
        
        df = pd.DataFrame(all_process_qa)
        df.columns = [
            '文档ID', '推理树ID', '节点ID', '层级', '分支类型',
            '问题', '答案', '生成方法', '验证通过'
        ]
        
        df.to_excel(writer, sheet_name='Sheet2-所有过程中的问答对', index=False)

    def _write_trajectories(self, trajectories: List[Dict], writer):
        """写入推理轨迹记录"""
        if not trajectories:
            return
        
        df = pd.DataFrame(trajectories)
        df.columns = [
            '文档ID', '步骤', '查询ID', '查询文本', '答案',
            '最小关键词', '生成方法', '验证通过'
        ]
        
        df.to_excel(writer, sheet_name='Sheet3-推理轨迹记录', index=False)

    def _write_final_composite_qa(self, composite_qa: List[Dict], writer):
        """写入糅合后的综合问答（四列格式）"""
        if not composite_qa:
            return
        
        # 准备数据
        export_data = []
        for idx, comp in enumerate(composite_qa):
            nested_status = "✅" if '❌' not in comp['nested_question'] else "❌"
            llm_status = "✅" if '❌' not in comp['natural_question'] else "❌"
            
            export_data.append({
                '序号': idx + 1,
                '文档ID': comp['doc_id'],
                '推理树ID': comp['tree_id'],
                '嵌套问题': comp['nested_question'],
                '自然问题': comp['natural_question'],
                '嵌套答案': comp['nested_answer'],
                '自然答案': comp['natural_answer'],
                '最终答案': comp['target_answer'],
                '嵌套状态': nested_status,
                '自然状态': llm_status,
                '调试信息': comp.get('debug_info', ''),
                '树索引': comp['tree_index']
            })
        
        df = pd.DataFrame(export_data)
        df.to_excel(writer, sheet_name='Sheet4-糅合后的综合问答', index=False)


def main():
    """主函数 - 处理指定的旧格式JSON文件"""
    exporter = LegacyJsonExporter()
    
    # 处理指定的JSON文件
    json_file = "agent_reasoning_production_en0028_20250722_122412.json"
    
    if Path(json_file).exists():
        excel_path = exporter.export_to_excel(json_file)
        print(f"🎉 处理完成，Excel文件已生成: {excel_path}")
    else:
        print(f"❌ 文件不存在: {json_file}")

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
"""
糅合问题生成修复器 - 修复占位符问题，生成真正的综合推理问题
"""

import json
import re
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import time

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CompositeQueryFixer:
    """修复糅合问题生成"""
    
    def __init__(self, api_client):
        self.api_client = api_client
        
    def fix_composite_queries_in_json(self, json_file: Path) -> bool:
        """修复JSON文件中的糅合问题"""
        try:
            print(f"🔄 读取并修复JSON文件: {json_file.name}")
            
            # 读取原始JSON
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 统计信息
            total_trees = 0
            fixed_queries = 0
            
            processing_results = data.get('processing_results', {})
            processed_docs = processing_results.get('processed_documents', [])
            
            print(f"📋 处理 {len(processed_docs)} 个文档...")
            
            for doc_idx, doc in enumerate(processed_docs):
                doc_id = doc.get('doc_id', f'Unknown_{doc_idx}')
                reasoning_trees = doc.get('reasoning_trees', [])
                
                print(f"  📄 处理文档: {doc_id} ({len(reasoning_trees)} 推理树)")
                
                for tree_idx, tree_str in enumerate(reasoning_trees):
                    if isinstance(tree_str, str):
                        total_trees += 1
                        
                        # 检查是否需要修复
                        composite_match = re.search(r"final_composite_query='([^']*)'", tree_str)
                        if composite_match:
                            current_composite = composite_match.group(1)
                            
                            # 检查是否是占位符
                            is_placeholder = (
                                not current_composite or 
                                current_composite == 'N/A' or
                                current_composite == 'Logical reasoning chain question requiring genuine step-by-step solving' or
                                len(current_composite) < 30
                            )
                            
                            if is_placeholder:
                                print(f"    🔧 修复推理树 {tree_idx}: 生成真正的综合问题...")
                                
                                # 提取推理树信息
                                tree_info = self._extract_tree_info(tree_str)
                                
                                if tree_info['queries_by_layer']:
                                    # 生成新的综合问题
                                    new_composite = self._generate_fixed_composite_query(tree_info)
                                    
                                    if new_composite and new_composite != current_composite:
                                        # 替换原文中的糅合问题
                                        new_tree_str = tree_str.replace(
                                            f"final_composite_query='{current_composite}'",
                                            f"final_composite_query='{new_composite}'"
                                        )
                                        
                                        # 更新数据
                                        reasoning_trees[tree_idx] = new_tree_str
                                        fixed_queries += 1
                                        
                                        print(f"    ✅ 修复成功: {new_composite[:80]}...")
                                    else:
                                        print(f"    ❌ 修复失败: 无法生成有效问题")
                                else:
                                    print(f"    ⚠️ 跳过: 无法提取推理树信息")
                            else:
                                print(f"    ✓ 已有效: {current_composite[:50]}...")
                        
                        # 防止API调用过于频繁
                        time.sleep(0.5)
            
            # 保存修复后的JSON
            if fixed_queries > 0:
                backup_file = json_file.with_suffix('.backup.json')
                # 备份原文件
                import shutil
                shutil.copy2(json_file, backup_file)
                print(f"📦 原文件已备份到: {backup_file.name}")
                
                # 保存修复后的文件
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                print(f"✅ 修复完成!")
                print(f"   总推理树: {total_trees}")
                print(f"   修复数量: {fixed_queries}")
                print(f"   修复率: {(fixed_queries/total_trees)*100:.1f}%")
                
                return True
            else:
                print(f"ℹ️  无需修复: 所有糅合问题都已正常")
                return False
                
        except Exception as e:
            logger.error(f"修复JSON文件失败: {e}")
            print(f"❌ 修复失败: {e}")
            return False
    
    def _extract_tree_info(self, tree_str: str) -> Dict[str, Any]:
        """从推理树字符串中提取信息"""
        info = {
            'tree_id': '',
            'root_answer': '',
            'queries_by_layer': {},
            'all_queries': []
        }
        
        try:
            # 提取树ID
            tree_id_match = re.search(r"tree_id='([^']+)'", tree_str)
            if tree_id_match:
                info['tree_id'] = tree_id_match.group(1)
            
            # 提取所有节点的问题和层级
            node_ids = re.findall(r"'([^']+)': QuestionTreeNode\(", tree_str)
            
            for node_id in node_ids:
                # 定位节点
                node_start = tree_str.find(f"'{node_id}': QuestionTreeNode(")
                if node_start == -1:
                    continue
                
                # 取节点段落
                node_section = tree_str[node_start:node_start + 1500]
                
                # 提取问题和层级
                query_match = re.search(r"query_text='([^']+)'", node_section)
                answer_match = re.search(r"answer='([^']+)'", node_section)
                layer_match = re.search(r"layer_level=(\d+)", node_section)
                
                if query_match and layer_match:
                    query_text = query_match.group(1)
                    layer = int(layer_match.group(1))
                    
                    if layer not in info['queries_by_layer']:
                        info['queries_by_layer'][layer] = []
                    
                    info['queries_by_layer'][layer].append(query_text)
                    info['all_queries'].append(query_text)
                    
                    # 如果是root节点，保存答案
                    if '_root' in node_id and answer_match:
                        info['root_answer'] = answer_match.group(1)
            
            print(f"      提取信息: {len(info['all_queries'])} 个问题, {len(info['queries_by_layer'])} 层")
            
        except Exception as e:
            logger.warning(f"提取推理树信息失败: {e}")
        
        return info
    
    def _generate_fixed_composite_query(self, tree_info: Dict[str, Any]) -> str:
        """生成修复的综合问题"""
        if not self.api_client or not tree_info['queries_by_layer']:
            return self._generate_fallback_query(tree_info)
        
        try:
            root_answer = tree_info.get('root_answer', 'the target answer')
            queries_by_layer = tree_info['queries_by_layer']
            all_queries = tree_info['all_queries']
            
            # 构建更简化、更稳定的prompt
            composite_prompt = f"""Create a logical reasoning chain question that requires step-by-step solving to reach the answer: {root_answer}

Available information from different reasoning layers:
{chr(10).join([f"Layer {layer}: {', '.join(queries[:2])}" for layer, queries in sorted(queries_by_layer.items())])}

Requirements:
1. Create ONE comprehensive question that connects multiple reasoning steps
2. Each step should build on the previous step's answer
3. The final step should lead to: {root_answer}
4. Agent must solve sequentially, cannot skip to the answer

Example pattern:
"To determine [FINAL_ANSWER], first identify [STEP1_INFO] by [STEP1_ACTION], then use that information to find [STEP2_INFO] through [STEP2_ACTION], and finally apply those results to discover [FINAL_ANSWER]."

Generate a single, coherent question (100-200 words) that requires this sequential reasoning to reach: {root_answer}

Response format: Just the question text, no JSON or extra formatting."""

            response = self.api_client.generate_response(
                prompt=composite_prompt,
                temperature=0.7,
                max_tokens=400
            )
            
            if response and len(response.strip()) > 50:
                # 清理响应
                cleaned_response = response.strip()
                # 移除可能的引号或格式标记
                cleaned_response = re.sub(r'^["\']|["\']$', '', cleaned_response)
                cleaned_response = re.sub(r'```.*?```', '', cleaned_response, flags=re.DOTALL)
                cleaned_response = cleaned_response.strip()
                
                if len(cleaned_response) > 30:
                    print(f"      🎯 API生成成功: {len(cleaned_response)} 字符")
                    return cleaned_response
            
            print(f"      ⚠️ API响应无效，使用后备方案")
            return self._generate_fallback_query(tree_info)
            
        except Exception as e:
            logger.warning(f"API生成综合问题失败: {e}")
            return self._generate_fallback_query(tree_info)
    
    def _generate_fallback_query(self, tree_info: Dict[str, Any]) -> str:
        """生成后备综合问题"""
        root_answer = tree_info.get('root_answer', 'the target answer')
        all_queries = tree_info.get('all_queries', [])
        
        if not all_queries:
            return f"Through multi-step reasoning and analysis, determine the answer: {root_answer}"
        
        # 选择最多3个关键问题
        selected_queries = all_queries[:3]
        
        if len(selected_queries) == 1:
            return f"To determine {root_answer}, analyze and solve: {selected_queries[0]}"
        elif len(selected_queries) == 2:
            return f"To identify {root_answer}, first address {selected_queries[0]}, then use that information to resolve {selected_queries[1]}"
        else:
            return f"To discover {root_answer}, follow this reasoning chain: first determine the answer to '{selected_queries[0]}', then apply that knowledge to solve '{selected_queries[1]}', and finally use both results to answer '{selected_queries[2]}' which will reveal the target answer."

def main():
    """主函数"""
    try:
        # 尝试导入和初始化API客户端
        api_client = None
        
        try:
            from core.llm_clients.claude_api_client import ClaudeAPIClient
            api_client = ClaudeAPIClient()
            print("✅ Claude API客户端初始化成功")
        except:
            try:
                from core.llm_clients.openai_api_client import OpenAIClient
                api_client = OpenAIClient()
                print("✅ OpenAI API客户端初始化成功")
            except Exception as e:
                print(f"❌ API客户端初始化失败: {e}")
                print("将使用后备方案生成问题")
        
        # 创建修复器
        fixer = CompositeQueryFixer(api_client)
        
        # 查找JSON文件
        results_dir = Path("results")
        json_files = list(results_dir.glob("agent_reasoning_production_*.json"))
        
        if not json_files:
            print("❌ 未找到需要修复的JSON文件")
            return
        
        # 修复每个文件
        for json_file in json_files:
            print(f"\n🚀 开始修复: {json_file.name}")
            success = fixer.fix_composite_queries_in_json(json_file)
            
            if success:
                print(f"✅ 修复完成: {json_file.name}")
            else:
                print(f"ℹ️  跳过: {json_file.name}")
        
        print(f"\n🎉 所有文件处理完成!")
        
    except Exception as e:
        logger.error(f"主程序执行失败: {e}")
        print(f"❌ 程序执行失败: {e}")

if __name__ == "__main__":
    main() 
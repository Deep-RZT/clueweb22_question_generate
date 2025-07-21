import json
import re
from typing import List, Dict, Any
from openai import OpenAI
import os

class ImprovedCompositeGenerator:
    def __init__(self):
        # 初始化OpenAI客户端
        from api_key_manager import APIKeyManager
        
        key_manager = APIKeyManager()
        api_key = key_manager.get_openai_key()
        if not api_key:
            raise ValueError("需要设置OpenAI API密钥")
        self.client = OpenAI(api_key=api_key)
    
    def extract_qa_nodes_by_layer(self, tree_str: str) -> Dict[int, List[Dict]]:
        """按层级提取问答节点"""
        nodes_by_layer = {}
        
        # 提取所有节点信息
        node_pattern = r"'([^']*_(?:root|series\d+|parallel\d+))': \{[^}]*'question': '([^']*)', 'answer': '([^']*)'[^}]*\}"
        matches = re.findall(node_pattern, tree_str)
        
        for node_id, question, answer in matches:
            # 确定层级
            if '_root' in node_id:
                layer = 0
            elif '_series1' in node_id or '_parallel1' in node_id:
                layer = 1
            elif '_series2' in node_id:
                layer = 2
            else:
                layer = 1  # 默认层级
            
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
                'answer': answer,
                'type': node_type,
                'layer': layer
            })
        
        return nodes_by_layer
    
    def build_reasoning_chain(self, nodes_by_layer: Dict[int, List[Dict]]) -> str:
        """构建推理链：从最深层开始倒序拼接"""
        reasoning_steps = []
        
        # 按层级从深到浅处理
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
        
        return " → ".join(reasoning_steps)
    
    def generate_natural_composite_question(self, reasoning_chain: str, root_question: str) -> tuple:
        """使用LLM生成自然的糅合问题，返回(生成的问题, 原始拼接串)"""
        # 记录原始拼接串
        original_chain = reasoning_chain
        
        try:
            prompt = f"""Based on the following reasoning chain, generate a natural and fluent composite question. Requirements:
1. Maintain the logical order of reasoning
2. Use natural language, avoid mechanical templates
3. Guide the agent to think step by step
4. Ultimately point to the root question

Reasoning chain: {reasoning_chain}

Final target question: {root_question}

Please generate a natural composite question (no more than 200 words):"""

            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a professional question designer who excels at creating logically clear composite reasoning questions."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.3
            )
            
            generated_question = response.choices[0].message.content.strip()
            
            # 简单验证生成的问题
            if len(generated_question) > 50 and not generated_question.startswith("follow this reasoning"):
                return generated_question, original_chain
            else:
                fallback_question = self.create_fallback_question(reasoning_chain, root_question)
                return fallback_question, original_chain
                
        except Exception as e:
            print(f"API调用失败: {e}")
            fallback_question = self.create_fallback_question(reasoning_chain, root_question)
            return fallback_question, original_chain
    
    def create_fallback_question(self, reasoning_chain: str, root_question: str) -> str:
        """创建更自然的后备问题"""
        return f"Analyze through the following reasoning process: {reasoning_chain}. Based on this analytical path, {root_question}"
    
    def fix_composite_question(self, tree_str: str) -> str:
        """修复单个推理树的糅合问题"""
        # 提取节点
        nodes_by_layer = self.extract_qa_nodes_by_layer(tree_str)
        
        if not nodes_by_layer:
            return tree_str
        
        # 找到root问题
        root_question = ""
        if 0 in nodes_by_layer:
            root_nodes = [n for n in nodes_by_layer[0] if n['type'] == 'root']
            if root_nodes:
                root_question = root_nodes[0]['question']
        
        if not root_question:
            return tree_str
        
        # 构建推理链
        reasoning_chain = self.build_reasoning_chain(nodes_by_layer)
        
        # 生成新的糅合问题和记录原始链
        new_composite_question, original_reasoning_chain = self.generate_natural_composite_question(reasoning_chain, root_question)
        
        # 替换原有的糅合问题，并添加原始推理链记录
        composite_pattern = r"final_composite_query='[^']*'"
        new_composite_str = f"final_composite_query='{new_composite_question}'"
        
        # 检查是否已经有original_reasoning_chain字段
        if 'original_reasoning_chain=' not in tree_str:
            # 添加原始推理链记录 - 在final_composite_query后面插入
            original_chain_str = f", original_reasoning_chain='{original_reasoning_chain}'"
            new_composite_str = new_composite_str + original_chain_str
        
        fixed_tree_str = re.sub(composite_pattern, new_composite_str, tree_str)
        
        return fixed_tree_str
    
    def process_json_file(self, json_file_path: str, output_file_path: str = None):
        """处理整个JSON文件，修复所有糅合问题"""
        if output_file_path is None:
            output_file_path = json_file_path.replace('.json', '_fixed_composite.json')
        
        print(f"正在处理文件: {json_file_path}")
        
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 备份原文件
        backup_path = json_file_path.replace('.json', '_backup_before_composite_fix.json')
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"已备份原文件到: {backup_path}")
        
        processed_count = 0
        fixed_count = 0
        
        processed_docs = data['processing_results']['processed_documents']
        
        for doc_idx, doc in enumerate(processed_docs):
            reasoning_trees = doc.get('reasoning_trees', [])
            
            for tree_idx, tree_str in enumerate(reasoning_trees):
                if isinstance(tree_str, str):
                    processed_count += 1
                    
                    # 检查是否需要修复
                    if ('follow this reasoning chain' in tree_str or 
                        'To discover' in tree_str or 
                        'To identify' in tree_str or
                        'To determine' in tree_str):
                        
                        print(f"修复文档{doc_idx+1}的推理树{tree_idx+1}...")
                        fixed_tree = self.fix_composite_question(tree_str)
                        reasoning_trees[tree_idx] = fixed_tree
                        fixed_count += 1
        
        # 保存修复后的文件
        with open(output_file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"处理完成!")
        print(f"总共处理了 {processed_count} 个推理树")
        print(f"修复了 {fixed_count} 个糅合问题")
        print(f"结果保存到: {output_file_path}")
        
        return output_file_path

def main():
    """主函数：修复糅合问题"""
    generator = ImprovedCompositeGenerator()
    
    # 处理最新的结果文件
    json_file = "results/agent_reasoning_production_en0023_20250721_133825.json"
    
    if os.path.exists(json_file):
        output_file = generator.process_json_file(json_file)
        print(f"\n糅合问题修复完成！")
        print(f"原文件: {json_file}")
        print(f"修复后文件: {output_file}")
    else:
        print(f"文件不存在: {json_file}")

if __name__ == "__main__":
    main() 
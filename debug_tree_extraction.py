#!/usr/bin/env python3
"""
Debug脚本：分析推理树的tree_id和问答对提取
"""

import json
import re
from pathlib import Path

def debug_tree_extraction():
    """Debug推理树提取"""
    json_file = Path('results/agent_reasoning_production_en0028_20250722_122412.json')
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    processing_results = data.get('processing_results', {})
    
    # 找到第一个有推理树的文档
    for doc_id, doc_data in processing_results.items():
        reasoning_trees = doc_data.get('reasoning_trees', [])
        
        if reasoning_trees:
            print(f"🔍 分析文档: {doc_id}")
            print(f"推理树数量: {len(reasoning_trees)}")
            
            # 分析第一个推理树
            first_tree = reasoning_trees[0]
            
            if isinstance(first_tree, str):
                print(f"\n📄 旧格式字符串数据分析:")
                
                # 提取tree_id
                tree_id_match = re.search(r"tree_id='([^']+)'", first_tree)
                tree_id = tree_id_match.group(1) if tree_id_match else 'NOT_FOUND'
                print(f"提取的tree_id: {tree_id}")
                
                # 提取所有节点ID
                node_ids = re.findall(r"'([^']+)': QuestionTreeNode\(", first_tree)
                print(f"节点ID列表: {node_ids}")
                
                # 分析每个节点的层级和问题
                print(f"\n📋 节点详细分析:")
                for node_id in node_ids[:5]:  # 只分析前5个节点
                    node_start = first_tree.find(f"'{node_id}': QuestionTreeNode(")
                    if node_start != -1:
                        node_section = first_tree[node_start:node_start + 800]
                        
                        # 提取信息
                        query_match = re.search(r"query_text='([^']+)'", node_section)
                        layer_match = re.search(r"layer_level=(\d+)", node_section)
                        
                        query_text = query_match.group(1) if query_match else "未找到"
                        layer = layer_match.group(1) if layer_match else "未找到"
                        
                        print(f"  节点: {node_id}")
                        print(f"    层级: {layer}")
                        print(f"    问题: {query_text[:100]}...")
                        print()
                
                # 测试按层级分组
                print(f"\n🎯 按层级分组测试:")
                queries_by_layer = {}
                
                for layer in [0, 1, 2]:
                    layer_pattern = rf"query_text='([^']+)'.*?layer_level={layer}"
                    layer_matches = re.findall(layer_pattern, first_tree, re.DOTALL)
                    if layer_matches:
                        queries_by_layer[layer] = layer_matches
                        print(f"Layer {layer}: {len(layer_matches)} 个问题")
                        for i, query in enumerate(layer_matches):
                            print(f"  {i+1}. {query[:80]}...")
                
                # 测试嵌套生成
                print(f"\n🏗️ 嵌套问题生成测试:")
                if queries_by_layer:
                    layers = sorted(queries_by_layer.keys(), reverse=True)
                    nested_query = ""
                    
                    for i, layer in enumerate(layers):
                        layer_queries = queries_by_layer[layer]
                        if not layer_queries:
                            continue
                        
                        current_query = layer_queries[0]
                        
                        if i == 0:
                            nested_query = f"({current_query})"
                        else:
                            nested_query = f"({current_query}, {nested_query})"
                    
                    print(f"生成的嵌套问题:")
                    print(nested_query)
                
            break

if __name__ == "__main__":
    debug_tree_extraction() 
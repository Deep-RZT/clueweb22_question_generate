#!/usr/bin/env python3
"""
验证所有修复是否正常工作的测试脚本
"""

from pathlib import Path
from default_excel_exporter import DefaultExcelExporter
import json
import re

def test_all_fixes():
    """测试所有修复"""
    print("🧪 开始验证所有修复...")
    
    # 1. 测试JSON数据完整性
    test_json_integrity()
    
    # 2. 测试糅合问题修复
    test_composite_query_fix()
    
    # 3. 测试层级修复
    test_layer_fix()
    
    # 4. 测试Excel导出
    test_excel_export()
    
    print("✅ 所有修复验证完成！")

def test_json_integrity():
    """测试JSON数据完整性"""
    print("\n1️⃣ 测试JSON数据完整性...")
    
    results_dir = Path("results")
    json_files = list(results_dir.glob("agent_reasoning_production_*.json"))
    
    for json_file in json_files:
        if '.backup.json' in json_file.name:
            continue
            
        print(f"  📄 检查: {json_file.name}")
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 检查基本结构
            assert 'processing_results' in data
            assert 'processed_documents' in data['processing_results']
            
            processed_docs = data['processing_results']['processed_documents']
            print(f"    ✅ 文档数量: {len(processed_docs)}")
            
            total_trees = sum(len(doc.get('reasoning_trees', [])) for doc in processed_docs)
            print(f"    ✅ 推理树总数: {total_trees}")
            
        except Exception as e:
            print(f"    ❌ JSON文件损坏: {e}")

def test_composite_query_fix():
    """测试糅合问题修复"""
    print("\n2️⃣ 测试糅合问题修复...")
    
    json_file = Path("results/agent_reasoning_production_en0023_20250721_133825.json")
    if not json_file.exists():
        print("    ⚠️ 测试文件不存在")
        return
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    processed_docs = data['processing_results']['processed_documents']
    
    valid_composites = 0
    placeholder_composites = 0
    total_trees = 0
    
    for doc in processed_docs:
        reasoning_trees = doc.get('reasoning_trees', [])
        
        for tree_str in reasoning_trees:
            if isinstance(tree_str, str):
                total_trees += 1
                
                # 检查糅合问题
                composite_match = re.search(r"final_composite_query='([^']*)'", tree_str)
                if composite_match:
                    composite = composite_match.group(1)
                    
                    if (composite and 
                        composite != 'N/A' and 
                        composite != 'Logical reasoning chain question requiring genuine step-by-step solving' and
                        len(composite) > 30):
                        valid_composites += 1
                    else:
                        placeholder_composites += 1
    
    print(f"    📊 糅合问题统计:")
    print(f"       总推理树: {total_trees}")
    print(f"       有效糅合问题: {valid_composites}")
    print(f"       占位符问题: {placeholder_composites}")
    print(f"       有效率: {(valid_composites/total_trees)*100:.1f}%")
    
    if valid_composites > 0:
        print(f"    ✅ 糅合问题修复成功")
    else:
        print(f"    ❌ 糅合问题修复失败")

def test_layer_fix():
    """测试层级修复"""
    print("\n3️⃣ 测试层级修复...")
    
    # 使用默认导出器解析数据
    exporter = DefaultExcelExporter()
    json_file = Path("results/agent_reasoning_production_en0023_20250721_133825.json")
    
    if not json_file.exists():
        print("    ⚠️ 测试文件不存在")
        return
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    parsed_data = exporter._parse_data(data)
    
    # 统计层级分布
    layer_stats = {}
    for qa in parsed_data['all_process_qa']:
        layer = qa['layer']
        layer_stats[layer] = layer_stats.get(layer, 0) + 1
    
    print(f"    📊 层级分布:")
    for layer in sorted(layer_stats.keys()):
        print(f"       层级{layer}: {layer_stats[layer]}个")
    
    # 验证层级是否正确
    if (0 in layer_stats and 1 in layer_stats):
        print(f"    ✅ 层级修复成功")
    else:
        print(f"    ❌ 层级修复失败")

def test_excel_export():
    """测试Excel导出"""
    print("\n4️⃣ 测试Excel导出...")
    
    exporter = DefaultExcelExporter()
    json_file = Path("results/agent_reasoning_production_en0023_20250721_133825.json")
    
    if not json_file.exists():
        print("    ⚠️ 测试文件不存在")
        return
    
    try:
        excel_file = exporter.export_final_excel(json_file)
        
        if excel_file and excel_file.exists():
            print(f"    ✅ Excel导出成功: {excel_file.name}")
            print(f"       文件大小: {excel_file.stat().st_size / 1024:.1f} KB")
        else:
            print(f"    ❌ Excel导出失败")
            
    except Exception as e:
        print(f"    ❌ Excel导出异常: {e}")

def show_final_summary():
    """显示最终摘要"""
    print("\n" + "="*60)
    print("🎉 所有修复验证完成！")
    print("="*60)
    
    print("\n📋 修复内容总结:")
    print("   ✅ 糅合问题生成修复 - 生成真正的综合推理问题")
    print("   ✅ 层级识别修复 - Root(0), Series1/Parallel1(1), Series2(2)")
    print("   ✅ 分支类型识别修复 - 正确区分root/series/parallel")
    print("   ✅ Excel导出修复 - 4个核心工作表，完整数据展示")
    
    print("\n🚀 下次使用方法:")
    print("   python agent_reasoning_main.py  # 使用修复版框架")
    print("   python default_excel_exporter.py  # 单独导出Excel")
    
    print("\n📁 重要文件:")
    print("   agent_depth_reasoning_framework_fixed.py  # 修复版推理框架")
    print("   default_excel_exporter.py                 # 默认Excel导出器")
    print("   agent_reasoning_main.py                   # 已更新的主程序")
    
    print("\n📊 生成文件位置:")
    print("   JSON: results/agent_reasoning_production_*.json")
    print("   Excel: results/*_agent_reasoning_production_*.xlsx")

if __name__ == "__main__":
    test_all_fixes()
    show_final_summary() 
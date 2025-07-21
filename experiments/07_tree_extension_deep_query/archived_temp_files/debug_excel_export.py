#!/usr/bin/env python3
"""
调试Excel导出中的原始推理链问题
"""

from default_excel_exporter import DefaultExcelExporter
import json
import pandas as pd
from pathlib import Path

def debug_excel_export():
    """调试Excel导出过程"""
    print("=== 调试Excel导出过程 ===\n")
    
    # 读取数据
    with open('results/agent_reasoning_production_en0023_20250721_133825_fixed_composite.json', 'r') as f:
        data = json.load(f)
    
    exporter = DefaultExcelExporter()
    
    # 步骤1: 测试数据提取
    print("📊 步骤1: 测试数据提取")
    composite_data = exporter._extract_composite_qa_data(data)
    print(f"提取了 {len(composite_data)} 个糅合问答对")
    
    if composite_data:
        sample = composite_data[0]
        print(f"样例数据: {sample['composite_question'][:50]}...")
        print(f"原始推理链: {sample['original_reasoning_chain'][:80]}...")
    
    # 步骤2: 模拟Excel写入过程
    print(f"\n📋 步骤2: 模拟Excel写入过程")
    
    if not composite_data:
        print("❌ 走旧格式路径")
        old_data = data.get('composite_qa', [])
        print(f"旧格式数据长度: {len(old_data)}")
    else:
        print("✅ 走新格式路径")
        
        # 格式化数据 - 直接复制_write_composite_qa中的逻辑
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
        
        print(f"格式化了 {len(formatted_data)} 行数据")
        print(f"有效: {valid_count}, 占位符: {placeholder_count}")
        
        # 检查前3行的原始推理链
        print(f"\n前3行的原始推理链:")
        for i, row in enumerate(formatted_data[:3]):
            chain = row['原始推理链']
            print(f"  {i+1}. {chain[:100]}...")
        
        # 创建DataFrame并写入测试Excel
        df = pd.DataFrame(formatted_data)
        test_excel = 'results/debug_test.xlsx'
        
        print(f"\n📄 步骤3: 写入测试Excel文件")
        with pd.ExcelWriter(test_excel, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='调试测试', index=False)
        
        print(f"✅ 测试Excel已生成: {test_excel}")
        
        # 读取并验证
        test_df = pd.read_excel(test_excel, sheet_name='调试测试')
        print(f"\n📊 步骤4: 验证测试Excel")
        print(f"读取了 {len(test_df)} 行数据")
        print(f"列名: {list(test_df.columns)}")
        
        print(f"前3行原始推理链验证:")
        for i, chain in enumerate(test_df['原始推理链'].head(3)):
            print(f"  {i+1}. {chain[:100]}...")

if __name__ == "__main__":
    debug_excel_export() 
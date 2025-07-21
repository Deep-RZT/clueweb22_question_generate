#!/usr/bin/env python3
"""
测试主生产流程的Excel导出功能
验证所有修复是否已正确集成
"""

import json
import os
from pathlib import Path
from default_excel_exporter import DefaultExcelExporter

def test_production_excel_export():
    """测试生产流程Excel导出"""
    print("=== 测试主生产流程Excel导出 ===\n")
    
    # 查找最新的生产结果文件
    results_dir = Path("results")
    json_files = list(results_dir.glob("agent_reasoning_production_*.json"))
    
    if not json_files:
        print("❌ 未找到生产结果文件")
        return False
    
    # 使用最新的文件
    latest_file = max(json_files, key=lambda f: f.stat().st_mtime)
    print(f"📄 使用文件: {latest_file.name}")
    
    # 测试Excel导出
    exporter = DefaultExcelExporter()
    
    try:
        print("\n🚀 开始Excel导出测试...")
        excel_file = exporter.export_final_excel(latest_file)
        
        if excel_file and excel_file.exists():
            print(f"✅ Excel导出成功: {excel_file.name}")
            
            # 验证Excel文件内容
            return verify_excel_content(excel_file)
        else:
            print("❌ Excel导出失败")
            return False
            
    except Exception as e:
        print(f"❌ Excel导出异常: {e}")
        return False

def verify_excel_content(excel_file: Path) -> bool:
    """验证Excel文件内容是否符合要求"""
    print(f"\n📊 验证Excel内容: {excel_file.name}")
    
    import pandas as pd
    
    try:
        # 读取Excel文件
        xls = pd.ExcelFile(excel_file)
        
        # 检查工作表数量和名称
        expected_sheets = ['1-糅合后问答对', '2-过程中所有问答对', '3-轨迹数据', '4-效率数据']
        actual_sheets = xls.sheet_names
        
        print(f"工作表检查:")
        print(f"  期望: {expected_sheets}")
        print(f"  实际: {actual_sheets}")
        
        if set(expected_sheets) != set(actual_sheets):
            print("❌ 工作表不匹配")
            return False
        print("✅ 工作表检查通过")
        
        # 检查每个工作表
        success = True
        
        # 1. 糅合后问答对
        df1 = pd.read_excel(excel_file, sheet_name='1-糅合后问答对')
        print(f"\n1. 糅合后问答对:")
        print(f"   行数: {len(df1)}")
        print(f"   列: {list(df1.columns)}")
        
        if '原始层级' in df1.columns:
            print("   ❌ 仍包含原始层级列")
            success = False
        else:
            print("   ✅ 已移除原始层级列")
        
        # 检查糅合问题质量
        if len(df1) > 0:
            valid_questions = df1[df1['问题状态'] == '✅ 有效']
            placeholder_questions = df1[df1['问题状态'] == '❌ 占位符']
            print(f"   有效问题: {len(valid_questions)}")
            print(f"   占位符问题: {len(placeholder_questions)}")
            
            # 显示部分糅合问题示例
            print("   问题示例:")
            for i, row in df1.head(3).iterrows():
                question = row['糅合后的综合问题'][:100]
                status = row['问题状态']
                print(f"     {i+1}. {question}... ({status})")
        
        # 2. 过程中所有问答对
        df2 = pd.read_excel(excel_file, sheet_name='2-过程中所有问答对')
        print(f"\n2. 过程中所有问答对:")
        print(f"   行数: {len(df2)}")
        print(f"   列: {list(df2.columns)}")
        
        if '原始层级' in df2.columns:
            print("   ❌ 仍包含原始层级列")
            success = False
        else:
            print("   ✅ 已移除原始层级列")
        
        # 检查层级和分支类型
        if '修正层级' in df2.columns and '分支类型' in df2.columns:
            layer_counts = df2['修正层级'].value_counts().sort_index()
            branch_counts = df2['分支类型'].value_counts()
            print(f"   层级分布: {dict(layer_counts)}")
            print(f"   分支类型分布: {dict(branch_counts)}")
            
            # 验证层级合理性
            if 0 in layer_counts.index and 1 in layer_counts.index:
                print("   ✅ 层级分布合理")
            else:
                print("   ❌ 层级分布异常")
                success = False
                
            # 验证分支类型
            expected_types = {'root', 'series', 'parallel'}
            actual_types = set(branch_counts.index)
            if expected_types.issubset(actual_types):
                print("   ✅ 分支类型完整")
            else:
                print("   ❌ 分支类型不完整")
                success = False
        
        # 3. 轨迹数据
        df3 = pd.read_excel(excel_file, sheet_name='3-轨迹数据')
        print(f"\n3. 轨迹数据:")
        print(f"   行数: {len(df3)}")
        print(f"   列: {list(df3.columns)}")
        
        if '原始层级' in df3.columns:
            print("   ❌ 仍包含原始层级列")
            success = False
        else:
            print("   ✅ 已移除原始层级列")
        
        # 4. 效率数据
        df4 = pd.read_excel(excel_file, sheet_name='4-效率数据')
        print(f"\n4. 效率数据:")
        print(f"   行数: {len(df4)}")
        print(f"   列: {list(df4.columns)}")
        
        if success:
            print(f"\n🎉 Excel内容验证全部通过!")
        else:
            print(f"\n❌ Excel内容验证发现问题")
        
        return success
        
    except Exception as e:
        print(f"❌ Excel验证异常: {e}")
        return False

def main():
    """主函数"""
    print("🧪 主生产流程Excel导出测试\n")
    
    success = test_production_excel_export()
    
    if success:
        print("\n🎉 所有测试通过! 主生产流程Excel导出正常")
        print("✅ 移除了原始层级列")
        print("✅ 层级和分支类型正确")
        print("✅ 4个工作表完整")
    else:
        print("\n❌ 测试失败，需要进一步修复")
    
    return success

if __name__ == "__main__":
    main() 
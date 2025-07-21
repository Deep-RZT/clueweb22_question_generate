#!/usr/bin/env python3
"""
整合所有修复的Agent推理主程序
包含：
1. 修复的糅合问题生成
2. 修复的层级识别 
3. 修复的分支类型识别
4. 完整的Excel导出
"""

import sys
from pathlib import Path
from agent_reasoning_main import AgentReasoningMainFramework
from default_excel_exporter import DefaultExcelExporter

def main():
    """主函数 - 使用所有修复"""
    print("🚀 启动整合修复版Agent推理系统...")
    
    # 初始化主框架（使用修复版）
    framework = AgentReasoningMainFramework()
    
    # 运行推理生成
    print("📋 开始运行推理生成...")
    results = framework.run_production_generation()
    
    if results:
        print(f"✅ 推理生成完成！")
        
        # 自动生成Excel报告
        print("📊 生成Excel报告...")
        exporter = DefaultExcelExporter()
        
        results_dir = Path("results")
        json_files = list(results_dir.glob("agent_reasoning_production_*.json"))
        
        for json_file in json_files:
            if '.backup.json' not in json_file.name:
                print(f"📋 导出: {json_file.name}")
                excel_file = exporter.export_final_excel(json_file)
                
                if excel_file:
                    print(f"✅ Excel已生成: {excel_file.name}")
                else:
                    print(f"❌ Excel生成失败: {json_file.name}")
        
        print("🎉 所有处理完成！")
        print(f"\n📁 结果位置:")
        print(f"   JSON: results/agent_reasoning_production_*.json")
        print(f"   Excel: results/agent_reasoning_production_*.xlsx")
        
    else:
        print("❌ 推理生成失败")

if __name__ == "__main__":
    main()

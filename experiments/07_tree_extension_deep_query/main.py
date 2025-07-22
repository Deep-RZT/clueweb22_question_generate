#!/usr/bin/env python3
"""
07 Tree Extension Deep Query - 主程序入口
基于推理树扩展的深度查询生成与Excel导出系统
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from default_excel_exporter import FixedCleanExcelExporter
from agent_reasoning_main import main as run_agent_reasoning

def main():
    """主程序入口"""
    print("🚀 07 Tree Extension Deep Query 系统")
    print("=" * 50)
    
    # 检查是否有现成的JSON文件
    results_dir = project_root / "results"
    json_files = list(results_dir.glob("agent_reasoning_production_*.json"))
    
    if json_files:
        print(f"📁 找到 {len(json_files)} 个已生成的JSON文件")
        
        # 使用最新的文件
        latest_json = max(json_files, key=lambda f: f.stat().st_mtime)
        print(f"📄 使用最新文件: {latest_json.name}")
        
        # 导出Excel
        print("\n🔄 开始Excel导出...")
        exporter = FixedCleanExcelExporter()
        output_file = exporter.export_clean_excel(latest_json)
        
        print(f"\n✅ 导出完成!")
        print(f"📊 Excel文件: {output_file}")
        print("\n📋 包含工作表:")
        print("  - Sheet1: 文档处理效率统计")
        print("  - Sheet2: 所有过程中的问答对 (完整层级结构)")
        print("  - Sheet3: 推理轨迹记录")
        print("  - Sheet4: 糅合后的综合问答 (双格式)")
        print("\n🎯 双格式综合问题和答案:")
        print("  - 嵌套累积型: (root问题, (中间层问题, 最深层问题))")
        print("  - LLM整合型: 自然语言流畅整合，使用OpenAI GPT-3.5")
                    
    else:
        print("❌ 未找到JSON文件")
        print("💡 请先运行 agent_reasoning_main.py 生成数据")
        
        user_input = input("\n是否现在运行推理生成? (y/n): ")
        if user_input.lower() == 'y':
            print("\n🔄 开始推理树生成...")
            run_agent_reasoning()
            
            # 重新检查并导出
            json_files = list(results_dir.glob("agent_reasoning_production_*.json"))
            if json_files:
                latest_json = max(json_files, key=lambda f: f.stat().st_mtime)
                exporter = FixedCleanExcelExporter()
                output_file = exporter.export_clean_excel(latest_json)
                print(f"\n✅ 完整流程完成! Excel文件: {output_file}")

if __name__ == "__main__":
    main() 
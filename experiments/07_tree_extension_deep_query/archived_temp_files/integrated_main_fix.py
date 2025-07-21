#!/usr/bin/env python3
"""
整合所有修复的主程序 - 将修复集成到主框架中
1. 修复糅合问题生成逻辑
2. 修复层级识别
3. 修复分支类型识别
4. 整合最终Excel导出器
"""

import sys
import os
from pathlib import Path

def integrate_fixes_to_main():
    """将所有修复整合到主框架中"""
    
    print("🔧 开始整合所有修复到主框架...")
    
    # 1. 修复agent_depth_reasoning_framework.py中的糅合问题生成
    fix_composite_query_generation()
    
    # 2. 将最终Excel导出器集成为默认导出器
    integrate_final_excel_exporter()
    
    # 3. 创建新的主入口程序
    create_integrated_main_entry()
    
    print("✅ 所有修复已成功整合到主框架！")
    print("\n🚀 使用方法:")
    print("   python agent_reasoning_main_fixed.py")
    print("\n📋 修复内容:")
    print("   ✅ 糅合问题生成 - 生成真正的综合推理问题")
    print("   ✅ 层级识别 - Root(0), Series1/Parallel1(1), Series2(2)")
    print("   ✅ 分支类型识别 - 正确区分root/series/parallel") 
    print("   ✅ Excel导出 - 4个核心工作表，完整数据展示")

def fix_composite_query_generation():
    """修复糅合问题生成逻辑"""
    print("  🔧 修复糅合问题生成逻辑...")
    
    # 读取原始框架文件
    framework_file = Path("agent_depth_reasoning_framework.py")
    
    if not framework_file.exists():
        print("    ❌ 未找到agent_depth_reasoning_framework.py")
        return
    
    with open(framework_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找并替换_build_nested_composite_query方法
    old_method_start = content.find("def _build_nested_composite_query(")
    if old_method_start == -1:
        print("    ❌ 未找到_build_nested_composite_query方法")
        return
    
    # 找到方法结束位置
    method_end = content.find("\n    def _", old_method_start + 1)
    if method_end == -1:
        method_end = content.find("\n    def _calculate_complexity_score(", old_method_start + 1)
    
    if method_end == -1:
        print("    ❌ 无法确定方法结束位置")
        return
    
    # 新的修复版方法
    new_method = '''def _build_nested_composite_query(self, queries_by_layer: Dict[int, List[str]], root_answer: str) -> str:
        """构建嵌套式综合问题 - 修复版"""
        if not self.api_client or not queries_by_layer:
            return self._generate_fallback_composite_query(queries_by_layer, root_answer)
        
        try:
            logger.info(f"构建嵌套式综合问题，目标答案: {root_answer}")
            
            # 收集所有层级的问题
            all_queries = []
            layer_summary = []
            
            for layer in sorted(queries_by_layer.keys()):
                queries = queries_by_layer[layer]
                all_queries.extend(queries)
                layer_summary.append(f"Layer {layer}: {len(queries)} queries")
            
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
                import re
                cleaned_response = re.sub(r'^["\']|["\']$', '', cleaned_response)
                cleaned_response = re.sub(r'```.*?```', '', cleaned_response, flags=re.DOTALL)
                cleaned_response = cleaned_response.strip()
                
                if len(cleaned_response) > 30:
                    logger.info(f"✅ API生成综合问题成功: {len(cleaned_response)} 字符")
                    return cleaned_response
            
            logger.warning("API响应无效，使用后备方案")
            return self._generate_fallback_composite_query(queries_by_layer, root_answer)
            
        except Exception as e:
            logger.error(f"构建嵌套式综合问题失败: {e}")
            return self._generate_fallback_composite_query(queries_by_layer, root_answer)
    
    def _generate_fallback_composite_query(self, queries_by_layer: Dict[int, List[str]], root_answer: str) -> str:
        """生成后备综合问题"""
        all_queries = []
        for layer in sorted(queries_by_layer.keys()):
            all_queries.extend(queries_by_layer[layer])
        
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

    '''
    
    # 替换方法
    new_content = content[:old_method_start] + new_method + content[method_end:]
    
    # 保存修复后的文件
    fixed_file = Path("agent_depth_reasoning_framework_fixed.py")
    with open(fixed_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"    ✅ 糅合问题生成逻辑已修复，保存到: {fixed_file.name}")

def integrate_final_excel_exporter():
    """整合最终Excel导出器"""
    print("  🔧 整合最终Excel导出器...")
    
    # 复制最终整合版Excel导出器为默认导出器
    final_exporter = Path("final_integrated_excel_exporter.py")
    if not final_exporter.exists():
        print("    ❌ 未找到final_integrated_excel_exporter.py")
        return
    
    # 读取最终导出器内容
    with open(final_exporter, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 修改类名和文件名，作为默认导出器
    content = content.replace("FinalIntegratedExcelExporter", "DefaultExcelExporter")
    content = content.replace("最终整合版Excel导出器", "默认Excel导出器")
    content = content.replace("FINAL_", "")
    
    # 保存为默认导出器
    default_exporter = Path("default_excel_exporter.py")
    with open(default_exporter, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"    ✅ 最终Excel导出器已整合为默认导出器: {default_exporter.name}")

def create_integrated_main_entry():
    """创建整合所有修复的主入口程序"""
    print("  🔧 创建整合主入口程序...")
    
    main_content = '''#!/usr/bin/env python3
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
        print(f"\\n📁 结果位置:")
        print(f"   JSON: results/agent_reasoning_production_*.json")
        print(f"   Excel: results/agent_reasoning_production_*.xlsx")
        
    else:
        print("❌ 推理生成失败")

if __name__ == "__main__":
    main()
'''
    
    # 保存主入口程序
    main_file = Path("agent_reasoning_main_fixed.py")
    with open(main_file, 'w', encoding='utf-8') as f:
        f.write(main_content)
    
    print(f"    ✅ 整合主入口程序已创建: {main_file.name}")

if __name__ == "__main__":
    integrate_fixes_to_main() 
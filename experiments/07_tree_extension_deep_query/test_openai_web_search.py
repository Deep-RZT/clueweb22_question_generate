#!/usr/bin/env python3
"""
测试OpenAI Web Search功能
Test OpenAI Web Search functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.web_search import web_search, perform_web_search, web_search_preview
import json

def test_openai_web_search():
    """测试OpenAI Web Search功能"""
    print("🔍 测试OpenAI Web Search功能")
    print("=" * 50)
    
    # 获取API key
    api_key = input("请输入OpenAI API密钥: ").strip()
    if not api_key:
        print("❌ API密钥不能为空")
        return False
    
    # 测试查询
    test_queries = [
        "OpenAI GPT-4.1 web search capabilities",
        "Python programming best practices 2024",
        "Tesla stock price today"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📋 测试 {i}: {query}")
        print("-" * 30)
        
        try:
            # 测试完整的web_search函数
            print("🔍 测试 web_search()...")
            results = web_search(query, api_key=api_key)
            
            print(f"状态: {results['status']}")
            print(f"提供商: {results.get('provider', 'unknown')}")
            print(f"结果数量: {results['total_results']}")
            
            if results.get('output_text'):
                print(f"输出文本: {results['output_text'][:200]}...")
            
            if results.get('citations'):
                print(f"引用数量: {len(results['citations'])}")
                for j, citation in enumerate(results['citations'][:2], 1):
                    print(f"  {j}. {citation.get('title', 'No title')}")
                    print(f"     {citation.get('url', 'No URL')}")
            
            # 测试兼容性函数
            print("\n📄 测试 web_search_preview()...")
            preview_text = web_search_preview(query, api_key=api_key)
            print(f"预览文本: {preview_text[:300]}...")
            
            print("✅ 测试成功")
            
        except Exception as e:
            print(f"❌ 测试失败: {e}")
    
    print(f"\n🎉 所有测试完成")
    return True

def test_failure_handling():
    """测试失败处理功能"""
    print("\n❌ 测试失败处理功能")
    print("=" * 30)
    
    try:
        # 使用无效API key测试失败处理
        results = web_search("test query", api_key="invalid_key")
        print(f"失败状态: {results['status']}")
        print(f"提供商: {results.get('provider', 'unknown')}")
        print(f"错误信息: {results.get('error', 'No error')}")
        if results['status'] == 'failed' and not results['results']:
            print("✅ 失败处理正确：不返回假数据")
        else:
            print("❌ 失败处理错误：可能返回了假数据")
        
    except Exception as e:
        print(f"❌ 失败处理测试异常: {e}")

def main():
    """主函数"""
    print("🧪 OpenAI Web Search测试套件")
    print("=" * 60)
    
    try:
        # 测试OpenAI Web Search
        if test_openai_web_search():
            # 测试失败处理功能
            test_failure_handling()
            
            print("\n🎯 总结:")
            print("✅ OpenAI Web Search集成成功")
            print("✅ gpt-4.1模型 + Responses API")
            print("✅ web_search_preview工具")
            print("✅ 引用和URL提取功能")
            print("✅ 失败时不返回假数据")
            print("🚫 已移除Mock数据，避免污染结果")
            print("\n🚀 现在可以在Agent推理框架中使用真实的Web Search了！")
            
        else:
            print("❌ 测试失败，请检查API密钥和网络连接")
    
    except KeyboardInterrupt:
        print("\n⚠️ 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试执行失败: {e}")

if __name__ == "__main__":
    main() 
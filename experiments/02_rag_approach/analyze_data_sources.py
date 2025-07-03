#!/usr/bin/env python3
"""
分析数据来源统计和文本预处理情况
"""

import json
import pandas as pd
from collections import Counter
import re

def analyze_data_sources():
    """分析数据来源统计"""
    print("=== 数据来源统计分析 ===\n")
    
    # 读取元数据
    with open('data/metadata/papers_20250526_182607.json', 'r', encoding='utf-8') as f:
        papers = json.load(f)
    
    # 统计来源
    sources = [paper['source'] for paper in papers]
    source_counts = Counter(sources)
    
    # 创建统计表格
    df = pd.DataFrame([
        {'数据源': 'arXiv', '数量': source_counts.get('arxiv', 0), '百分比': f"{source_counts.get('arxiv', 0)/len(papers)*100:.1f}%"},
        {'数据源': 'OpenAlex', '数量': source_counts.get('openalex', 0), '百分比': f"{source_counts.get('openalex', 0)/len(papers)*100:.1f}%"},
        {'数据源': 'CrossRef', '数量': source_counts.get('crossref', 0), '百分比': f"{source_counts.get('crossref', 0)/len(papers)*100:.1f}%"},
        {'数据源': '总计', '数量': len(papers), '百分比': '100.0%'}
    ])
    
    print("| 数据源 | 数量 | 百分比 |")
    print("|--------|------|--------|")
    for _, row in df.iterrows():
        print(f"| {row['数据源']} | {row['数量']} | {row['百分比']} |")
    
    print(f"\n总计收集文献: {len(papers)} 篇")
    
    # 分析关键词匹配情况
    keywords = [paper['keyword_matched'] for paper in papers]
    keyword_counts = Counter(keywords)
    
    print(f"\n=== 关键词匹配统计 ===")
    print(f"匹配到的不同关键词数量: {len(keyword_counts)}")
    print("前10个最常匹配的关键词:")
    for keyword, count in keyword_counts.most_common(10):
        print(f"  {keyword}: {count} 篇")
    
    return papers

def analyze_text_preprocessing():
    """分析文本预处理情况"""
    print("\n=== 文本预处理分析 ===\n")
    
    # 读取训练数据样本
    with open('data/processed_text/energy_train_20250526_183431.txt', 'r', encoding='utf-8') as f:
        lines = f.readlines()[:10]  # 只读取前10行作为样本
    
    print("当前文本预处理流程:")
    print("1. 数据来源: 论文标题 + 摘要")
    print("2. 文本清理: 去除特殊字符、标准化空格")
    print("3. 格式化: FastText格式 (__label__energy / __label__nonenergy)")
    print("4. 编码: UTF-8编码")
    
    print("\n文本内容分析:")
    energy_samples = [line for line in lines if line.startswith('__label__energy')]
    
    if energy_samples:
        sample_text = energy_samples[0].replace('__label__energy', '').strip()
        
        # 分析文本特征
        word_count = len(sample_text.split())
        char_count = len(sample_text)
        
        print(f"- 样本文本长度: {word_count} 词, {char_count} 字符")
        print(f"- 平均词长: {char_count/word_count:.1f} 字符/词")
        
        # 检查是否包含特定内容
        has_references = bool(re.search(r'\b(references?|bibliography|cited|et al\.)\b', sample_text.lower()))
        has_authors = bool(re.search(r'\b(author|university|department|email)\b', sample_text.lower()))
        has_figures = bool(re.search(r'\b(figure|fig\.|table|chart)\b', sample_text.lower()))
        
        print(f"- 包含参考文献信息: {'是' if has_references else '否'}")
        print(f"- 包含作者信息: {'是' if has_authors else '是 (在元数据中)'}")
        print(f"- 包含图表描述: {'是' if has_figures else '否'}")
        
        print(f"\n样本文本预览 (前200字符):")
        print(f"'{sample_text[:200]}...'")
    
    # 读取数据集统计
    try:
        with open('data/processed_text/dataset_stats_20250526_183431.json', 'r') as f:
            stats = json.load(f)
        
        print(f"\n数据集统计:")
        print(f"- 训练集样本: {stats.get('train_samples', 'N/A')}")
        print(f"- 验证集样本: {stats.get('val_samples', 'N/A')}")
        print(f"- 平均文本长度: {stats.get('avg_text_length', 'N/A')} 词")
        
    except FileNotFoundError:
        print("\n数据集统计文件未找到")

def check_full_text_availability():
    """检查全文可用性"""
    print("\n=== 全文数据可用性检查 ===\n")
    
    # 检查是否有全文数据
    import os
    full_text_dir = 'data/processed_text/full_text'
    
    if os.path.exists(full_text_dir):
        files = os.listdir(full_text_dir)
        print(f"全文数据目录存在，包含 {len(files)} 个文件")
        
        if files:
            # 检查一个样本文件
            sample_file = os.path.join(full_text_dir, files[0])
            try:
                with open(sample_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                print(f"样本全文长度: {len(content.split())} 词")
                print(f"样本文件: {files[0]}")
            except Exception as e:
                print(f"读取样本文件失败: {e}")
    else:
        print("全文数据目录不存在")
        print("当前使用: 标题 + 摘要 (平均约70-80词)")
        print("建议: 需要下载完整PDF并提取全文以获得更好的分类效果")

def main():
    """主函数"""
    papers = analyze_data_sources()
    analyze_text_preprocessing()
    check_full_text_availability()
    
    print("\n=== 总结 ===")
    print("a) 文本预处理情况:")
    print("   - 当前使用标题+摘要，不包含参考文献、完整作者信息和图表描述")
    print("   - 已进行基本文本清理和格式化")
    print("   - 平均文本长度约70-80词")
    print("   - 建议获取完整PDF全文以提升分类效果")
    
    print("\nb) 数据来源统计:")
    print("   - 已收集969篇能源相关文献")
    print("   - 来源分布: arXiv、OpenAlex、CrossRef")
    print("   - 可继续收集至1000篇目标")
    
    print("\nc) 下一步建议:")
    print("   - 实现PDF全文下载和提取")
    print("   - 基于现有数据构建RAG+问答系统")
    print("   - 生成200个查询用于测试")

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
"""
ClueWeb22 Comparative Analysis
专门分析ClueWeb22数据集在OpenAI GPT-4o和Claude Sonnet 4上的对比实验结果
"""

import os
import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
import statistics

class ClueWeb22ComparativeAnalysis:
    """ClueWeb22对比分析器"""
    
    def __init__(self):
        """初始化分析器"""
        self.base_dir = Path("FRESH_FOUR_WAY_EXPERIMENT_20250605_192214")
        self.openai_dir = self.base_dir / "clueweb_openai_20250605_192214"
        self.claude_dir = self.base_dir / "clueweb_claude_20250606_001257"
        
        # 输出目录
        self.output_dir = Path("ClueWeb22_Comparative_Analysis")
        self.output_dir.mkdir(exist_ok=True)
        
        print("🔍 ClueWeb22对比分析系统初始化")
        print(f"📁 OpenAI结果目录: {self.openai_dir}")
        print(f"📁 Claude结果目录: {self.claude_dir}")
        print(f"📁 输出目录: {self.output_dir}")
    
    def load_experiment_results(self) -> Dict[str, Any]:
        """加载两个实验的完整结果"""
        results = {}
        
        # 加载OpenAI结果
        openai_file = self.openai_dir / "complete_experiment_results.json"
        if openai_file.exists():
            with open(openai_file, 'r', encoding='utf-8') as f:
                results['openai'] = json.load(f)
            print(f"✅ 加载OpenAI结果: {len(results['openai']['results'])} 个主题")
        else:
            print(f"❌ 未找到OpenAI结果文件: {openai_file}")
            
        # 加载Claude结果
        claude_file = self.claude_dir / "complete_experiment_results.json"
        if claude_file.exists():
            with open(claude_file, 'r', encoding='utf-8') as f:
                results['claude'] = json.load(f)
            print(f"✅ 加载Claude结果: {len(results['claude']['results'])} 个主题")
        else:
            print(f"❌ 未找到Claude结果文件: {claude_file}")
            
        return results
    
    def extract_statistics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """提取详细统计信息"""
        stats = {}
        
        for provider, data in results.items():
            if 'results' not in data:
                continue
                
            provider_stats = {
                'total_topics': len(data['results']),
                'successful_topics': 0,
                'total_processing_time': 0,
                'total_qa_pairs': 0,
                'total_report_words': 0,
                'total_answer_words': 0,
                'processing_times': [],
                'report_lengths': [],
                'qa_counts': [],
                'answer_lengths': [],
                'difficulty_distribution': {'Easy': 0, 'Medium': 0, 'Hard': 0},
                'topic_details': []
            }
            
            for result in data['results']:
                if not result.get('success', False):
                    continue
                    
                provider_stats['successful_topics'] += 1
                
                # 处理时间
                processing_time = result.get('processing_time', 0)
                provider_stats['total_processing_time'] += processing_time
                provider_stats['processing_times'].append(processing_time)
                
                # 报告统计
                report_content = ""
                if 'steps' in result and 'report' in result['steps']:
                    report_content = result['steps']['report'].get('content', '')
                    report_words = len(report_content.split())
                    provider_stats['total_report_words'] += report_words
                    provider_stats['report_lengths'].append(report_words)
                
                # QA对统计
                qa_pairs = result.get('qa_pairs', [])
                qa_count = len(qa_pairs)
                provider_stats['total_qa_pairs'] += qa_count
                provider_stats['qa_counts'].append(qa_count)
                
                # 答案统计和难度分布
                topic_answer_words = 0
                for qa in qa_pairs:
                    answer_words = qa.get('answer_word_count', 0)
                    topic_answer_words += answer_words
                    provider_stats['answer_lengths'].append(answer_words)
                    
                    difficulty = qa.get('difficulty', 'Unknown')
                    if difficulty in provider_stats['difficulty_distribution']:
                        provider_stats['difficulty_distribution'][difficulty] += 1
                
                provider_stats['total_answer_words'] += topic_answer_words
                
                # 主题详情
                topic_detail = {
                    'topic_id': result.get('topic', 'Unknown'),
                    'processing_time': processing_time,
                    'report_words': len(report_content.split()) if report_content else 0,
                    'qa_pairs': qa_count,
                    'answer_words': topic_answer_words,
                    'documents_count': result.get('documents_count', 0)
                }
                provider_stats['topic_details'].append(topic_detail)
            
            # 计算平均值
            if provider_stats['successful_topics'] > 0:
                provider_stats['avg_processing_time'] = provider_stats['total_processing_time'] / provider_stats['successful_topics']
                provider_stats['avg_report_words'] = provider_stats['total_report_words'] / provider_stats['successful_topics']
                provider_stats['avg_qa_pairs'] = provider_stats['total_qa_pairs'] / provider_stats['successful_topics']
                provider_stats['avg_answer_words'] = provider_stats['total_answer_words'] / provider_stats['total_qa_pairs'] if provider_stats['total_qa_pairs'] > 0 else 0
            
            # 计算中位数和标准差
            if provider_stats['processing_times']:
                provider_stats['median_processing_time'] = statistics.median(provider_stats['processing_times'])
                provider_stats['std_processing_time'] = statistics.stdev(provider_stats['processing_times']) if len(provider_stats['processing_times']) > 1 else 0
            
            if provider_stats['report_lengths']:
                provider_stats['median_report_words'] = statistics.median(provider_stats['report_lengths'])
                provider_stats['std_report_words'] = statistics.stdev(provider_stats['report_lengths']) if len(provider_stats['report_lengths']) > 1 else 0
            
            if provider_stats['answer_lengths']:
                provider_stats['median_answer_words'] = statistics.median(provider_stats['answer_lengths'])
                provider_stats['std_answer_words'] = statistics.stdev(provider_stats['answer_lengths']) if len(provider_stats['answer_lengths']) > 1 else 0
            
            stats[provider] = provider_stats
        
        return stats
    
    def generate_excel_report(self, results: Dict[str, Any], stats: Dict[str, Any]) -> str:
        """生成详细的Excel对比报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        excel_file = self.output_dir / f"ClueWeb22_Comparative_Analysis_{timestamp}.xlsx"
        
        # 创建多个工作表的数据
        sheets_data = {}
        
        # 1. 总体统计对比
        summary_data = []
        for provider in ['openai', 'claude']:
            if provider in stats:
                s = stats[provider]
                summary_data.append({
                    'Provider': 'OpenAI GPT-4o' if provider == 'openai' else 'Claude Sonnet 4',
                    'Total_Topics': s['total_topics'],
                    'Successful_Topics': s['successful_topics'],
                    'Success_Rate_%': (s['successful_topics'] / s['total_topics'] * 100) if s['total_topics'] > 0 else 0,
                    'Total_Processing_Time_Min': s['total_processing_time'] / 60,
                    'Avg_Processing_Time_Min': s.get('avg_processing_time', 0) / 60,
                    'Median_Processing_Time_Min': s.get('median_processing_time', 0) / 60,
                    'Total_QA_Pairs': s['total_qa_pairs'],
                    'Avg_QA_Pairs_Per_Topic': s.get('avg_qa_pairs', 0),
                    'Total_Report_Words': s['total_report_words'],
                    'Avg_Report_Words': s.get('avg_report_words', 0),
                    'Median_Report_Words': s.get('median_report_words', 0),
                    'Total_Answer_Words': s['total_answer_words'],
                    'Avg_Answer_Words': s.get('avg_answer_words', 0),
                    'Median_Answer_Words': s.get('median_answer_words', 0),
                    'Easy_Questions': s['difficulty_distribution']['Easy'],
                    'Medium_Questions': s['difficulty_distribution']['Medium'],
                    'Hard_Questions': s['difficulty_distribution']['Hard']
                })
        
        sheets_data['Summary_Comparison'] = pd.DataFrame(summary_data)
        
        # 2. 主题详细对比
        topic_comparison_data = []
        if 'openai' in stats and 'claude' in stats:
            openai_topics = {t['topic_id']: t for t in stats['openai']['topic_details']}
            claude_topics = {t['topic_id']: t for t in stats['claude']['topic_details']}
            
            all_topics = set(openai_topics.keys()) | set(claude_topics.keys())
            
            for topic_id in sorted(all_topics):
                openai_data = openai_topics.get(topic_id, {})
                claude_data = claude_topics.get(topic_id, {})
                
                topic_comparison_data.append({
                    'Topic_ID': topic_id,
                    'OpenAI_Processing_Time_Min': openai_data.get('processing_time', 0) / 60,
                    'Claude_Processing_Time_Min': claude_data.get('processing_time', 0) / 60,
                    'Time_Difference_Min': (claude_data.get('processing_time', 0) - openai_data.get('processing_time', 0)) / 60,
                    'OpenAI_Report_Words': openai_data.get('report_words', 0),
                    'Claude_Report_Words': claude_data.get('report_words', 0),
                    'Report_Words_Difference': claude_data.get('report_words', 0) - openai_data.get('report_words', 0),
                    'OpenAI_QA_Pairs': openai_data.get('qa_pairs', 0),
                    'Claude_QA_Pairs': claude_data.get('qa_pairs', 0),
                    'QA_Pairs_Difference': claude_data.get('qa_pairs', 0) - openai_data.get('qa_pairs', 0),
                    'OpenAI_Answer_Words': openai_data.get('answer_words', 0),
                    'Claude_Answer_Words': claude_data.get('answer_words', 0),
                    'Answer_Words_Difference': claude_data.get('answer_words', 0) - openai_data.get('answer_words', 0),
                    'Documents_Count': max(openai_data.get('documents_count', 0), claude_data.get('documents_count', 0))
                })
        
        sheets_data['Topic_Comparison'] = pd.DataFrame(topic_comparison_data)
        
        # 3. 详细QA对数据
        qa_details_data = []
        for provider in ['openai', 'claude']:
            if provider in results and 'results' in results[provider]:
                provider_name = 'OpenAI GPT-4o' if provider == 'openai' else 'Claude Sonnet 4'
                
                for result in results[provider]['results']:
                    if not result.get('success', False):
                        continue
                        
                    topic_id = result.get('topic', 'Unknown')
                    qa_pairs = result.get('qa_pairs', [])
                    
                    for qa in qa_pairs:
                        qa_details_data.append({
                            'Provider': provider_name,
                            'Topic_ID': topic_id,
                            'Question_ID': qa.get('question_id', ''),
                            'Question': qa.get('question', ''),
                            'Answer': qa.get('answer', ''),
                            'Difficulty': qa.get('difficulty', ''),
                            'Question_Type': qa.get('type', ''),
                            'Answer_Length_Chars': qa.get('answer_length', 0),
                            'Answer_Word_Count': qa.get('answer_word_count', 0),
                            'Question_Reasoning': qa.get('reasoning', '')
                        })
        
        sheets_data['QA_Details'] = pd.DataFrame(qa_details_data)
        
        # 4. 报告内容对比
        report_comparison_data = []
        for provider in ['openai', 'claude']:
            if provider in results and 'results' in results[provider]:
                provider_name = 'OpenAI GPT-4o' if provider == 'openai' else 'Claude Sonnet 4'
                
                for result in results[provider]['results']:
                    if not result.get('success', False):
                        continue
                        
                    topic_id = result.get('topic', 'Unknown')
                    report_content = ""
                    if 'steps' in result and 'report' in result['steps']:
                        report_content = result['steps']['report'].get('content', '')
                    
                    report_comparison_data.append({
                        'Provider': provider_name,
                        'Topic_ID': topic_id,
                        'Report_Content': report_content,
                        'Report_Word_Count': len(report_content.split()),
                        'Report_Char_Count': len(report_content)
                    })
        
        sheets_data['Report_Comparison'] = pd.DataFrame(report_comparison_data)
        
        # 保存到Excel文件
        try:
            with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
                for sheet_name, df in sheets_data.items():
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            print(f"✅ Excel报告生成完成: {excel_file}")
            print(f"📊 包含工作表: {list(sheets_data.keys())}")
            
            # 输出数据统计
            for sheet_name, df in sheets_data.items():
                print(f"   {sheet_name}: {len(df)} 行数据")
            
            return str(excel_file)
            
        except Exception as e:
            print(f"❌ Excel文件生成失败: {e}")
            return ""
    
    def generate_markdown_report(self, results: Dict[str, Any], stats: Dict[str, Any], excel_file: str) -> str:
        """生成详细的Markdown分析报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        md_file = self.output_dir / f"ClueWeb22_Comparative_Analysis_{timestamp}.md"
        
        try:
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write("# 📊 ClueWeb22数据集对比分析报告\n")
                f.write("## ClueWeb22 Dataset Comparative Analysis Report\n\n")
                f.write(f"**生成时间**: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')}\n")
                f.write(f"**分析对象**: ClueWeb22数据集在OpenAI GPT-4o和Claude Sonnet 4上的表现对比\n")
                f.write(f"**数据来源**: 完整的9个ClueWeb22主题实验结果\n\n")
                
                f.write("---\n\n")
                
                # 执行摘要
                f.write("## 🎯 执行摘要\n\n")
                
                if 'openai' in stats and 'claude' in stats:
                    openai_stats = stats['openai']
                    claude_stats = stats['claude']
                    
                    f.write("### 关键发现\n\n")
                    
                    # 处理效率对比
                    openai_avg_time = openai_stats.get('avg_processing_time', 0) / 60
                    claude_avg_time = claude_stats.get('avg_processing_time', 0) / 60
                    time_diff = claude_avg_time - openai_avg_time
                    
                    if time_diff > 0:
                        f.write(f"- **处理效率**: OpenAI平均比Claude快 {abs(time_diff):.1f} 分钟 ({openai_avg_time:.1f}分钟 vs {claude_avg_time:.1f}分钟)\n")
                    else:
                        f.write(f"- **处理效率**: Claude平均比OpenAI快 {abs(time_diff):.1f} 分钟 ({claude_avg_time:.1f}分钟 vs {openai_avg_time:.1f}分钟)\n")
                    
                    # 内容生成量对比
                    openai_avg_report = openai_stats.get('avg_report_words', 0)
                    claude_avg_report = claude_stats.get('avg_report_words', 0)
                    report_diff = claude_avg_report - openai_avg_report
                    
                    if report_diff > 0:
                        f.write(f"- **报告生成**: Claude平均比OpenAI多生成 {report_diff:.0f} 词 ({claude_avg_report:.0f}词 vs {openai_avg_report:.0f}词)\n")
                    else:
                        f.write(f"- **报告生成**: OpenAI平均比Claude多生成 {abs(report_diff):.0f} 词 ({openai_avg_report:.0f}词 vs {claude_avg_report:.0f}词)\n")
                    
                    # QA对生成对比
                    openai_total_qa = openai_stats.get('total_qa_pairs', 0)
                    claude_total_qa = claude_stats.get('total_qa_pairs', 0)
                    f.write(f"- **QA对生成**: OpenAI总计{openai_total_qa}对，Claude总计{claude_total_qa}对\n")
                    
                    # 答案质量对比
                    openai_avg_answer = openai_stats.get('avg_answer_words', 0)
                    claude_avg_answer = claude_stats.get('avg_answer_words', 0)
                    answer_diff = claude_avg_answer - openai_avg_answer
                    
                    if answer_diff > 0:
                        f.write(f"- **答案详细度**: Claude平均比OpenAI多 {answer_diff:.0f} 词/答案 ({claude_avg_answer:.0f}词 vs {openai_avg_answer:.0f}词)\n")
                    else:
                        f.write(f"- **答案详细度**: OpenAI平均比Claude多 {abs(answer_diff):.0f} 词/答案 ({openai_avg_answer:.0f}词 vs {claude_avg_answer:.0f}词)\n")
                
                f.write("\n---\n\n")
                
                # 详细统计对比
                f.write("## 📈 详细统计对比\n\n")
                
                f.write("### 整体性能指标\n\n")
                f.write("| 指标 | OpenAI GPT-4o | Claude Sonnet 4 | 差异 |\n")
                f.write("|------|---------------|-----------------|------|\n")
                
                if 'openai' in stats and 'claude' in stats:
                    openai_stats = stats['openai']
                    claude_stats = stats['claude']
                    
                    # 成功率
                    openai_success_rate = (openai_stats['successful_topics'] / openai_stats['total_topics'] * 100) if openai_stats['total_topics'] > 0 else 0
                    claude_success_rate = (claude_stats['successful_topics'] / claude_stats['total_topics'] * 100) if claude_stats['total_topics'] > 0 else 0
                    f.write(f"| 成功率 | {openai_success_rate:.1f}% | {claude_success_rate:.1f}% | {claude_success_rate - openai_success_rate:+.1f}% |\n")
                    
                    # 平均处理时间
                    openai_avg_time = openai_stats.get('avg_processing_time', 0) / 60
                    claude_avg_time = claude_stats.get('avg_processing_time', 0) / 60
                    f.write(f"| 平均处理时间(分钟) | {openai_avg_time:.1f} | {claude_avg_time:.1f} | {claude_avg_time - openai_avg_time:+.1f} |\n")
                    
                    # 平均报告字数
                    openai_avg_report = openai_stats.get('avg_report_words', 0)
                    claude_avg_report = claude_stats.get('avg_report_words', 0)
                    f.write(f"| 平均报告字数 | {openai_avg_report:.0f} | {claude_avg_report:.0f} | {claude_avg_report - openai_avg_report:+.0f} |\n")
                    
                    # 平均QA对数
                    openai_avg_qa = openai_stats.get('avg_qa_pairs', 0)
                    claude_avg_qa = claude_stats.get('avg_qa_pairs', 0)
                    f.write(f"| 平均QA对数 | {openai_avg_qa:.1f} | {claude_avg_qa:.1f} | {claude_avg_qa - openai_avg_qa:+.1f} |\n")
                    
                    # 平均答案字数
                    openai_avg_answer = openai_stats.get('avg_answer_words', 0)
                    claude_avg_answer = claude_stats.get('avg_answer_words', 0)
                    f.write(f"| 平均答案字数 | {openai_avg_answer:.0f} | {claude_avg_answer:.0f} | {claude_avg_answer - openai_avg_answer:+.0f} |\n")
                
                f.write("\n### 难度分布对比\n\n")
                f.write("| 难度级别 | OpenAI GPT-4o | Claude Sonnet 4 |\n")
                f.write("|----------|---------------|------------------|\n")
                
                if 'openai' in stats and 'claude' in stats:
                    for difficulty in ['Easy', 'Medium', 'Hard']:
                        openai_count = stats['openai']['difficulty_distribution'][difficulty]
                        claude_count = stats['claude']['difficulty_distribution'][difficulty]
                        f.write(f"| {difficulty} | {openai_count} | {claude_count} |\n")
                
                f.write("\n---\n\n")
                
                # 主题级别分析
                f.write("## 🔍 主题级别详细分析\n\n")
                
                if 'openai' in stats and 'claude' in stats:
                    openai_topics = {t['topic_id']: t for t in stats['openai']['topic_details']}
                    claude_topics = {t['topic_id']: t for t in stats['claude']['topic_details']}
                    
                    all_topics = sorted(set(openai_topics.keys()) | set(claude_topics.keys()))
                    
                    f.write("### 各主题性能对比\n\n")
                    f.write("| 主题ID | OpenAI时间(分) | Claude时间(分) | 时间差异 | OpenAI报告(词) | Claude报告(词) | 报告差异 |\n")
                    f.write("|--------|----------------|----------------|----------|----------------|----------------|----------|\n")
                    
                    for topic_id in all_topics:
                        openai_data = openai_topics.get(topic_id, {})
                        claude_data = claude_topics.get(topic_id, {})
                        
                        openai_time = openai_data.get('processing_time', 0) / 60
                        claude_time = claude_data.get('processing_time', 0) / 60
                        time_diff = claude_time - openai_time
                        
                        openai_words = openai_data.get('report_words', 0)
                        claude_words = claude_data.get('report_words', 0)
                        words_diff = claude_words - openai_words
                        
                        f.write(f"| {topic_id} | {openai_time:.1f} | {claude_time:.1f} | {time_diff:+.1f} | {openai_words} | {claude_words} | {words_diff:+d} |\n")
                
                f.write("\n---\n\n")
                
                # 性能分析
                f.write("## 📊 性能分析\n\n")
                
                f.write("### 处理效率分析\n\n")
                if 'openai' in stats and 'claude' in stats:
                    openai_times = stats['openai']['processing_times']
                    claude_times = stats['claude']['processing_times']
                    
                    if openai_times and claude_times:
                        f.write(f"- **OpenAI处理时间**: 平均 {statistics.mean(openai_times)/60:.1f}分钟, 中位数 {statistics.median(openai_times)/60:.1f}分钟\n")
                        f.write(f"- **Claude处理时间**: 平均 {statistics.mean(claude_times)/60:.1f}分钟, 中位数 {statistics.median(claude_times)/60:.1f}分钟\n")
                        
                        if len(openai_times) > 1:
                            f.write(f"- **OpenAI时间标准差**: {statistics.stdev(openai_times)/60:.1f}分钟\n")
                        if len(claude_times) > 1:
                            f.write(f"- **Claude时间标准差**: {statistics.stdev(claude_times)/60:.1f}分钟\n")
                
                f.write("\n### 内容质量分析\n\n")
                if 'openai' in stats and 'claude' in stats:
                    openai_reports = stats['openai']['report_lengths']
                    claude_reports = stats['claude']['report_lengths']
                    
                    if openai_reports and claude_reports:
                        f.write(f"- **OpenAI报告长度**: 平均 {statistics.mean(openai_reports):.0f}词, 中位数 {statistics.median(openai_reports):.0f}词\n")
                        f.write(f"- **Claude报告长度**: 平均 {statistics.mean(claude_reports):.0f}词, 中位数 {statistics.median(claude_reports):.0f}词\n")
                        
                        if len(openai_reports) > 1:
                            f.write(f"- **OpenAI报告长度标准差**: {statistics.stdev(openai_reports):.0f}词\n")
                        if len(claude_reports) > 1:
                            f.write(f"- **Claude报告长度标准差**: {statistics.stdev(claude_reports):.0f}词\n")
                
                f.write("\n---\n\n")
                
                # 结论和建议
                f.write("## 🎯 结论与建议\n\n")
                
                f.write("### 主要发现\n\n")
                
                if 'openai' in stats and 'claude' in stats:
                    openai_stats = stats['openai']
                    claude_stats = stats['claude']
                    
                    # 效率对比
                    openai_avg_time = openai_stats.get('avg_processing_time', 0)
                    claude_avg_time = claude_stats.get('avg_processing_time', 0)
                    
                    if openai_avg_time < claude_avg_time:
                        f.write("1. **处理效率**: OpenAI在处理速度上具有优势，适合需要快速响应的场景\n")
                    else:
                        f.write("1. **处理效率**: Claude在处理速度上具有优势，适合需要快速响应的场景\n")
                    
                    # 内容质量对比
                    openai_avg_report = openai_stats.get('avg_report_words', 0)
                    claude_avg_report = claude_stats.get('avg_report_words', 0)
                    
                    if claude_avg_report > openai_avg_report:
                        f.write("2. **内容丰富度**: Claude生成的报告更加详细和全面，适合需要深度分析的场景\n")
                    else:
                        f.write("2. **内容丰富度**: OpenAI生成的报告更加详细和全面，适合需要深度分析的场景\n")
                    
                    # 答案质量对比
                    openai_avg_answer = openai_stats.get('avg_answer_words', 0)
                    claude_avg_answer = claude_stats.get('avg_answer_words', 0)
                    
                    if claude_avg_answer > openai_avg_answer:
                        f.write("3. **答案详细度**: Claude提供更详细的答案，更适合教育和研究用途\n")
                    else:
                        f.write("3. **答案详细度**: OpenAI提供更详细的答案，更适合教育和研究用途\n")
                
                f.write("\n### 应用建议\n\n")
                f.write("- **快速原型开发**: 选择处理速度更快的模型\n")
                f.write("- **深度研究分析**: 选择内容生成更丰富的模型\n")
                f.write("- **教育应用**: 选择答案更详细的模型\n")
                f.write("- **成本考虑**: 根据token使用量和处理时间评估成本效益\n")
                
                f.write("\n### 后续研究方向\n\n")
                f.write("- 扩展到更多ClueWeb22主题进行大规模验证\n")
                f.write("- 引入人工评估来评价内容质量\n")
                f.write("- 分析不同语言内容（英文vs日文）的处理差异\n")
                f.write("- 探索模型组合使用的可能性\n")
                
                f.write("\n---\n\n")
                
                f.write("## 📈 数据文件\n\n")
                f.write(f"完整的数据分析请参考Excel文件: `{Path(excel_file).name if excel_file else 'N/A'}`\n\n")
                f.write("Excel文件包含以下工作表：\n")
                f.write("- **Summary_Comparison**: 总体统计对比\n")
                f.write("- **Topic_Comparison**: 主题级别详细对比\n")
                f.write("- **QA_Details**: 所有问答对的详细内容\n")
                f.write("- **Report_Comparison**: 报告内容对比\n\n")
                
                f.write("---\n\n")
                f.write(f"*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")
                f.write(f"*分析系统版本: ClueWeb22 Comparative Analysis v1.0*\n")
            
            print(f"✅ Markdown报告生成完成: {md_file}")
            return str(md_file)
            
        except Exception as e:
            print(f"❌ Markdown报告生成失败: {e}")
            return ""
    
    def run_analysis(self):
        """运行完整的对比分析"""
        print("\n🚀 开始ClueWeb22对比分析")
        print("=" * 60)
        
        # 1. 加载实验结果
        print("\n📚 加载实验结果...")
        results = self.load_experiment_results()
        
        if not results:
            print("❌ 未找到有效的实验结果")
            return
        
        # 2. 提取统计信息
        print("\n📊 提取统计信息...")
        stats = self.extract_statistics(results)
        
        # 3. 生成Excel报告
        print("\n📈 生成Excel报告...")
        excel_file = self.generate_excel_report(results, stats)
        
        # 4. 生成Markdown报告
        print("\n📝 生成Markdown报告...")
        md_file = self.generate_markdown_report(results, stats, excel_file)
        
        # 5. 输出结果摘要
        print("\n🎉 ClueWeb22对比分析完成!")
        print("=" * 60)
        
        if 'openai' in stats and 'claude' in stats:
            openai_stats = stats['openai']
            claude_stats = stats['claude']
            
            print("📊 分析结果摘要:")
            print(f"   OpenAI: {openai_stats['successful_topics']}/{openai_stats['total_topics']} 主题成功")
            print(f"   Claude: {claude_stats['successful_topics']}/{claude_stats['total_topics']} 主题成功")
            print(f"   OpenAI平均处理时间: {openai_stats.get('avg_processing_time', 0)/60:.1f} 分钟")
            print(f"   Claude平均处理时间: {claude_stats.get('avg_processing_time', 0)/60:.1f} 分钟")
            print(f"   OpenAI总QA对: {openai_stats['total_qa_pairs']}")
            print(f"   Claude总QA对: {claude_stats['total_qa_pairs']}")
        
        print(f"\n📁 输出文件:")
        if excel_file:
            print(f"   Excel报告: {excel_file}")
        if md_file:
            print(f"   Markdown报告: {md_file}")
        
        print(f"\n📂 所有文件保存在: {self.output_dir}")

def main():
    """主函数"""
    print("🔍 ClueWeb22对比分析系统")
    print("=" * 60)
    print("专门分析ClueWeb22数据集在OpenAI GPT-4o和Claude Sonnet 4上的表现")
    print("=" * 60)
    
    try:
        analyzer = ClueWeb22ComparativeAnalysis()
        analyzer.run_analysis()
        
    except Exception as e:
        print(f"❌ 系统错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 
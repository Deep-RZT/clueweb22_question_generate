#!/usr/bin/env python3
"""
Export Test Results to Excel
Converts the existing test_qa_benchmark JSON to a comprehensive Excel file
"""

import json
import pandas as pd
from pathlib import Path
from datetime import datetime

def export_json_to_excel(json_file_path: str, output_excel_path: str = None):
    """
    Export test results JSON to comprehensive Excel file with complete data - NO TRUNCATION
    
    Args:
        json_file_path: Path to the test results JSON file
        output_excel_path: Optional output Excel file path
    """
    
    # Load the JSON data
    with open(json_file_path, 'r', encoding='utf-8') as f:
        qa_dataset = json.load(f)
    
    # Generate output path if not provided
    if not output_excel_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_excel_path = f"test_benchmark_complete_{timestamp}.xlsx"
    
    print(f"🔄 Exporting JSON to Excel: {output_excel_path}")
    
    # Create comprehensive Excel file
    with pd.ExcelWriter(output_excel_path, engine='openpyxl') as writer:
        
        # Sheet 1: Dataset Summary
        summary_data = {
            'Dataset_Name': [qa_dataset['dataset_metadata']['dataset_name']],
            'Version': [qa_dataset['dataset_metadata']['version']],
            'Creation_Timestamp': [qa_dataset['dataset_metadata']['creation_timestamp']],
            'Total_Topics': [qa_dataset['dataset_metadata']['total_topics']],
            'Total_QA_Pairs': [qa_dataset['dataset_metadata']['total_qa_pairs']],
            'Success_Rate_%': [qa_dataset['dataset_metadata']['success_rate']],
            'Description': [qa_dataset['dataset_metadata']['description']]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Dataset_Summary', index=False)
        
        # Sheet 2: Topic Overview
        topics_data = []
        for topic_id, topic_data in qa_dataset['topics'].items():
            questions = topic_data.get('questions', [])
            successful_answers = sum(1 for q in questions 
                                   if q.get('answer', {}).get('status') == 'success')
            
            topics_data.append({
                'Topic_ID': topic_id,
                'Domain': topic_data.get('topic_info', {}).get('domain', 'Unknown'),
                'Language': topic_data.get('topic_info', {}).get('language', 'Unknown'),
                'Document_Count': topic_data.get('topic_info', {}).get('document_count', 0),
                'Question_Count': len(questions),
                'Successful_Answers': successful_answers,
                'Success_Rate_%': (successful_answers / len(questions) * 100) if questions else 0,
                'Easy_Questions': sum(1 for q in questions if q.get('difficulty') == 'Easy'),
                'Medium_Questions': sum(1 for q in questions if q.get('difficulty') == 'Medium'),
                'Hard_Questions': sum(1 for q in questions if q.get('difficulty') == 'Hard'),
                'Answer_Generation_Status': topic_data.get('answer_generation_status', 'Unknown'),
                'Answer_Generation_Timestamp': topic_data.get('answer_generation_timestamp', '')
            })
        
        topics_df = pd.DataFrame(topics_data)
        topics_df.to_excel(writer, sheet_name='Topics_Overview', index=False)
        
        # Sheet 3: Complete QA Data - FULL CONTENT, NO TRUNCATION
        qa_data = []
        for topic_id, topic_data in qa_dataset['topics'].items():
            topic_info = topic_data.get('topic_info', {})
            domain = topic_info.get('domain', 'Unknown')
            
            for question in topic_data.get('questions', []):
                answer = question.get('answer', {})
                quality_metrics = answer.get('quality_metrics', {})
                structural_analysis = answer.get('structural_analysis', {})
                
                qa_row = {
                    'Topic_ID': topic_id,
                    'Domain': domain,
                    'Question_ID': question.get('question_id', ''),
                    'Question_Text': question.get('question_text', ''),  # COMPLETE question text
                    'Difficulty': question.get('difficulty', ''),
                    'Question_Type': question.get('question_type', ''),
                    'Question_Rationale': question.get('rationale', ''),
                    'Answer_Text': answer.get('text', ''),  # COMPLETE answer, no truncation
                    'Answer_Status': answer.get('status', ''),
                    'Answer_Word_Count': quality_metrics.get('word_count', 0),
                    'Answer_Char_Count': quality_metrics.get('char_count', 0),
                    'Answer_Quality_Level': quality_metrics.get('quality_level', ''),
                    'Answer_Quality_Score': quality_metrics.get('quality_score', 0),
                    'Has_Sections': quality_metrics.get('has_sections', False),
                    'Has_Citations': quality_metrics.get('has_citations', False),
                    'Meets_Length_Requirement': quality_metrics.get('meets_length_requirement', False),
                    'Expected_Word_Range': quality_metrics.get('expected_word_range', ''),
                    'Difficulty_Level': quality_metrics.get('difficulty_level', ''),
                    'Citation_Count': structural_analysis.get('citation_count', 0),
                    'Sections_Detected': ', '.join(structural_analysis.get('sections_detected', [])),
                    'Conclusion_Present': structural_analysis.get('conclusion_present', False),
                    'Generation_Timestamp': answer.get('generation_timestamp', '')
                }
                qa_data.append(qa_row)
        
        qa_df = pd.DataFrame(qa_data)
        qa_df.to_excel(writer, sheet_name='Complete_QA_Data', index=False)
        
        # Sheet 4: Domain Reports - COMPLETE REPORTS, NO TRUNCATION
        reports_data = []
        for topic_id, topic_data in qa_dataset['topics'].items():
            domain_report = topic_data.get('domain_report', 'Domain report not available')
            topic_info = topic_data.get('topic_info', {})
            
            report_row = {
                'Topic_ID': topic_id,
                'Domain': topic_info.get('domain', 'Unknown'),
                'Language': topic_info.get('language', 'Unknown'),
                'Document_Count': topic_info.get('document_count', 0),
                'Domain_Report': domain_report,  # COMPLETE report, no truncation
                'Report_Word_Count': len(domain_report.split()) if domain_report else 0,
                'Generation_Status': topic_data.get('generation_status', 'unknown'),
                'Generation_Timestamp': topic_data.get('generation_timestamp', '')
            }
            reports_data.append(report_row)
        
        reports_df = pd.DataFrame(reports_data)
        reports_df.to_excel(writer, sheet_name='Domain_Reports', index=False)
        
        # Sheet 5: Quality Analysis
        quality_data = []
        for topic_id, topic_data in qa_dataset['topics'].items():
            for question in topic_data.get('questions', []):
                answer = question.get('answer', {})
                if answer.get('status') == 'success':
                    quality_metrics = answer.get('quality_metrics', {})
                    structural_analysis = answer.get('structural_analysis', {})
                    
                    quality_row = {
                        'Topic_ID': topic_id,
                        'Question_ID': question.get('question_id', ''),
                        'Difficulty': question.get('difficulty', ''),
                        'Word_Count': quality_metrics.get('word_count', 0),
                        'Char_Count': quality_metrics.get('char_count', 0),
                        'Quality_Score': quality_metrics.get('quality_score', 0),
                        'Quality_Level': quality_metrics.get('quality_level', ''),
                        'Has_Sections': quality_metrics.get('has_sections', False),
                        'Has_Citations': quality_metrics.get('has_citations', False),
                        'Meets_Length_Requirement': quality_metrics.get('meets_length_requirement', False),
                        'Citation_Count': structural_analysis.get('citation_count', 0),
                        'Conclusion_Present': structural_analysis.get('conclusion_present', False),
                        'Expected_Word_Range': quality_metrics.get('expected_word_range', ''),
                        'Difficulty_Level': quality_metrics.get('difficulty_level', '')
                    }
                    quality_data.append(quality_row)
        
        quality_df = pd.DataFrame(quality_data)
        quality_df.to_excel(writer, sheet_name='Quality_Analysis', index=False)
        
        # Sheet 6: Quality Summary
        quality_summary = qa_dataset.get('quality_summary', {})
        if quality_summary:
            summary_rows = []
            
            # Overall metrics
            summary_rows.append({
                'Metric': 'Total Questions',
                'Value': quality_summary.get('total_questions', 0),
                'Category': 'Overall'
            })
            
            # Difficulty distribution
            difficulty_dist = quality_summary.get('difficulty_distribution', {})
            for difficulty, count in difficulty_dist.items():
                summary_rows.append({
                    'Metric': f'{difficulty} Questions',
                    'Value': count,
                    'Category': 'Difficulty Distribution'
                })
            
            # Quality distribution
            quality_dist = quality_summary.get('quality_distribution', {})
            for quality_level, count in quality_dist.items():
                summary_rows.append({
                    'Metric': f'{quality_level.title()} Quality Answers',
                    'Value': count,
                    'Category': 'Quality Distribution'
                })
            
            # Average word counts
            avg_words = quality_summary.get('average_word_count_by_difficulty', {})
            for difficulty, avg_count in avg_words.items():
                summary_rows.append({
                    'Metric': f'{difficulty} Avg Word Count',
                    'Value': round(avg_count, 1),
                    'Category': 'Word Count Analysis'
                })
            
            # Quality percentages
            quality_pct = quality_summary.get('quality_percentage', {})
            for quality_level, percentage in quality_pct.items():
                summary_rows.append({
                    'Metric': f'{quality_level.title()} Quality %',
                    'Value': f"{percentage:.1f}%",
                    'Category': 'Quality Percentage'
                })
            
            quality_summary_df = pd.DataFrame(summary_rows)
            quality_summary_df.to_excel(writer, sheet_name='Quality_Summary', index=False)
    
    print(f"✅ Excel export completed successfully!")
    print(f"📊 Complete Excel file saved with 6 sheets:")
    print(f"   - Dataset_Summary: Overall dataset information")
    print(f"   - Topics_Overview: Topic-level statistics")
    print(f"   - Complete_QA_Data: Full Q&A pairs (NO truncation)")
    print(f"   - Domain_Reports: Complete domain reports (NO truncation)")
    print(f"   - Quality_Analysis: Answer quality metrics")
    print(f"   - Quality_Summary: Quality statistics summary")
    print(f"📁 Output file: {output_excel_path}")
    
    return output_excel_path

def main():
    """Main function for standalone execution"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python export_to_excel.py <json_file_path> [output_excel_path]")
        print("Example: python export_to_excel.py test_output/test_qa_benchmark_20250604_140404.json")
        return
    
    json_file_path = sys.argv[1]
    output_excel_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Check if JSON file exists
    if not Path(json_file_path).exists():
        print(f"❌ Error: JSON file not found: {json_file_path}")
        return
    
    # Export to Excel
    try:
        output_file = export_json_to_excel(json_file_path, output_excel_path)
        print(f"\n🎉 Export completed successfully!")
        print(f"📊 Excel file ready: {output_file}")
    except Exception as e:
        print(f"❌ Export failed: {e}")

if __name__ == "__main__":
    main() 
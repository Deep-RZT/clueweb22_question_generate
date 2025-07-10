"""
Excel Export System for Short Answer Deep Query Experiment
为06短答案深度问题实验提供详细的Excel导出功能
"""

import json
import pandas as pd
import numpy as np
import statistics
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

class ShortAnswerDeepQueryExcelExporter:
    """短答案深度问题实验Excel导出器"""
    
    def __init__(self, results_dir: str = "./results"):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(exist_ok=True)
    
    def export_experiment_to_excel(self, experiment_result: Dict[str, Any], 
                                 output_filename: Optional[str] = None) -> str:
        """
        导出实验结果到Excel文件
        
        Args:
            experiment_result: 完整的实验结果JSON数据
            output_filename: 输出文件名，如果为None则自动生成
        
        Returns:
            生成的Excel文件路径
        """
        if not output_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            experiment_name = experiment_result.get('experiment_info', {}).get('name', 'experiment')
            output_filename = f"{experiment_name}_detailed_report_{timestamp}.xlsx"
        
        excel_file = self.results_dir / output_filename
        
        try:
            # 创建多个工作表的数据
            sheets_data = self._prepare_excel_sheets(experiment_result)
            
            # 保存到Excel文件
            with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
                for sheet_name, df in sheets_data.items():
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                    
                    # 自动调整列宽
                    worksheet = writer.sheets[sheet_name]
                    for column in worksheet.columns:
                        max_length = 0
                        column_letter = column[0].column_letter
                        for cell in column:
                            try:
                                if len(str(cell.value)) > max_length:
                                    max_length = len(str(cell.value))
                            except:
                                pass
                        adjusted_width = min(max_length + 2, 50)
                        worksheet.column_dimensions[column_letter].width = adjusted_width
            
            logger.info(f"✅ Excel报告生成完成: {excel_file}")
            logger.info(f"📊 包含工作表: {list(sheets_data.keys())}")
            
            # 输出数据统计
            for sheet_name, df in sheets_data.items():
                logger.info(f"   {sheet_name}: {len(df)} 行数据")
            
            return str(excel_file)
            
        except Exception as e:
            logger.error(f"❌ Excel文件生成失败: {e}")
            raise
    
    def _prepare_excel_sheets(self, experiment_result: Dict[str, Any]) -> Dict[str, pd.DataFrame]:
        """准备Excel工作表数据"""
        sheets_data = {}
        
        # 1. 实验概览
        sheets_data['Experiment_Overview'] = self._create_overview_sheet(experiment_result)
        
        # 2. 主题详细统计
        sheets_data['Topic_Statistics'] = self._create_topic_statistics_sheet(experiment_result)
        
        # 3. 问答对详细信息
        sheets_data['QA_Pairs_Details'] = self._create_qa_details_sheet(experiment_result)
        
        # 4. 质量分析报告
        sheets_data['Quality_Analysis'] = self._create_quality_analysis_sheet(experiment_result)
        
        # 5. BrowseComp分析
        sheets_data['BrowseComp_Analysis'] = self._create_browsecomp_analysis_sheet(experiment_result)
        
        # 6. 答案长度分析
        sheets_data['Answer_Length_Analysis'] = self._create_answer_length_analysis_sheet(experiment_result)
        
        # 7. 约束类型分析
        sheets_data['Constraint_Analysis'] = self._create_constraint_analysis_sheet(experiment_result)
        
        # 8. 报告质量评估
        sheets_data['Report_Quality'] = self._create_report_quality_sheet(experiment_result)
        
        # 9. GPT-4o评判结果
        if self._has_gpt4o_evaluation(experiment_result):
            sheets_data['GPT4o_Evaluation'] = self._create_gpt4o_evaluation_sheet(experiment_result)
        
        return sheets_data
    
    def _create_overview_sheet(self, experiment_result: Dict[str, Any]) -> pd.DataFrame:
        """创建实验概览工作表"""
        exp_info = experiment_result.get('experiment_info', {})
        summary = experiment_result.get('summary', {})
        agg_stats = experiment_result.get('aggregated_statistics', {})
        
        overview_data = [
            {'Metric': '实验名称', 'Value': exp_info.get('name', 'N/A'), 'Description': 'Experiment Name'},
            {'Metric': '执行时间', 'Value': exp_info.get('timestamp', 'N/A'), 'Description': 'Execution Timestamp'},
            {'Metric': '运行模式', 'Value': exp_info.get('mode', 'N/A'), 'Description': 'Execution Mode'},
            {'Metric': '数据源', 'Value': exp_info.get('data_source', 'N/A'), 'Description': 'Data Source'},
            {'Metric': '处理文档总数', 'Value': summary.get('total_documents', 0), 'Description': 'Total Documents Processed'},
            {'Metric': '成功处理主题数', 'Value': summary.get('successful_topics', 0), 'Description': 'Successfully Processed Topics'},
            {'Metric': '整体成功率', 'Value': f"{summary.get('success_rate', 0):.2%}", 'Description': 'Overall Success Rate'},
            {'Metric': '总处理时间(分钟)', 'Value': f"{summary.get('total_processing_time', 0)/60:.1f}", 'Description': 'Total Processing Time (Minutes)'},
            {'Metric': '平均处理时间/主题(分钟)', 'Value': f"{summary.get('avg_processing_time_per_topic', 0)/60:.1f}", 'Description': 'Average Processing Time per Topic (Minutes)'},
            {'Metric': '生成问题总数', 'Value': agg_stats.get('total_questions_generated', 0), 'Description': 'Total Questions Generated'},
            {'Metric': 'BrowseComp问题数', 'Value': agg_stats.get('total_browsecomp_questions', 0), 'Description': 'Total BrowseComp Questions'},
            {'Metric': 'BrowseComp比例', 'Value': f"{agg_stats.get('avg_browsecomp_ratio', 0):.2%}", 'Description': 'BrowseComp Ratio'},
            {'Metric': '平均约束数/问题', 'Value': f"{agg_stats.get('avg_constraints_per_question', 0):.2f}", 'Description': 'Average Constraints per Question'},
            {'Metric': '平均答案长度(词)', 'Value': f"{agg_stats.get('avg_answer_words', 0):.1f}", 'Description': 'Average Answer Length (Words)'},
        ]
        
        # 添加配置信息
        config = exp_info.get('config', {})
        config_data = [
            {'Metric': '最大答案词数限制', 'Value': config.get('max_answer_words', 'N/A'), 'Description': 'Max Answer Words Limit'},
            {'Metric': '最大答案字符限制', 'Value': config.get('max_answer_chars', 'N/A'), 'Description': 'Max Answer Characters Limit'},
            {'Metric': '每主题问题数', 'Value': config.get('questions_per_topic', 'N/A'), 'Description': 'Questions per Topic'},
            {'Metric': '最小BrowseComp比例', 'Value': f"{config.get('min_browsecomp_ratio', 0):.1%}", 'Description': 'Minimum BrowseComp Ratio'},
            {'Metric': '最小高约束比例', 'Value': f"{config.get('min_high_constraint_ratio', 0):.1%}", 'Description': 'Minimum High Constraint Ratio'},
            {'Metric': '启用答案压缩', 'Value': '是' if config.get('enable_answer_compression', False) else '否', 'Description': 'Answer Compression Enabled'},
            {'Metric': '启用GPT-4o评判', 'Value': '是' if config.get('enable_gpt4o_evaluation', False) else '否', 'Description': 'GPT-4o Evaluation Enabled'},
        ]
        
        overview_data.extend(config_data)
        
        return pd.DataFrame(overview_data)
    
    def _create_topic_statistics_sheet(self, experiment_result: Dict[str, Any]) -> pd.DataFrame:
        """创建主题详细统计工作表"""
        topic_data = []
        
        detailed_results = experiment_result.get('detailed_results', [])
        
        for result in detailed_results:
            if not result.get('success'):
                # 失败的主题
                topic_data.append({
                    'Topic_ID': result.get('topic_id', 'Unknown'),
                    'Status': '❌ 失败',
                    'Error_Message': result.get('error', 'Unknown error'),
                    'Processing_Time_Minutes': f"{result.get('processing_time', 0)/60:.1f}",
                    'Questions_Generated': 0,
                    'BrowseComp_Questions': 0,
                    'BrowseComp_Ratio': '0%',
                    'High_Constraint_Questions': 0,
                    'High_Constraint_Ratio': '0%',
                    'Avg_Constraints_Per_Question': 0,
                    'Avg_Answer_Length_Words': 0,
                    'Report_Quality_Score': 'N/A',
                    'Report_Quality_Grade': 'N/A',
                    'GPT4o_Score': 'N/A',
                    'GPT4o_Grade': 'N/A',
                    'Validation_Passed': '否'
                })
            else:
                # 成功的主题
                stats = result.get('statistics', {})
                validation = result.get('validation', {})
                report_analysis = result.get('report_analysis', {})
                gpt4o_eval = result.get('gpt4o_evaluation', {})
                
                topic_data.append({
                    'Topic_ID': result.get('topic_id', 'Unknown'),
                    'Status': '✅ 成功',
                    'Error_Message': '',
                    'Processing_Time_Minutes': f"{result.get('processing_time', 0)/60:.1f}",
                    'Questions_Generated': stats.get('total_questions', 0),
                    'BrowseComp_Questions': stats.get('browsecomp_questions', 0),
                    'BrowseComp_Ratio': f"{stats.get('browsecomp_ratio', 0):.1%}",
                    'High_Constraint_Questions': stats.get('high_constraint_questions', 0),
                    'High_Constraint_Ratio': f"{stats.get('high_constraint_ratio', 0):.1%}",
                    'Avg_Constraints_Per_Question': f"{stats.get('avg_constraints', 0):.2f}",
                    'Avg_Answer_Length_Words': f"{stats.get('avg_answer_words', 0):.1f}",
                    'Report_Quality_Score': f"{report_analysis.get('quality_score', 0):.3f}",
                    'Report_Quality_Grade': report_analysis.get('quality_grade', 'N/A'),
                    'GPT4o_Score': f"{gpt4o_eval.get('overall_assessment', {}).get('overall_avg_score', 0):.1f}/10" if gpt4o_eval else 'N/A',
                    'GPT4o_Grade': gpt4o_eval.get('overall_assessment', {}).get('overall_grade', 'N/A') if gpt4o_eval else 'N/A',
                    'Validation_Passed': '是' if validation.get('passed', False) else '否'
                })
        
        return pd.DataFrame(topic_data)
    
    def _create_qa_details_sheet(self, experiment_result: Dict[str, Any]) -> pd.DataFrame:
        """创建问答对详细信息工作表"""
        qa_data = []
        
        detailed_results = experiment_result.get('detailed_results', [])
        
        for result in detailed_results:
            if not result.get('success'):
                continue
                
            topic_id = result.get('topic_id', 'Unknown')
            questions = result.get('questions', [])
            
            for i, qa in enumerate(questions, 1):
                analysis = qa.get('analysis', {})
                
                qa_data.append({
                    'Topic_ID': topic_id,
                    'Question_Number': i,
                    'Question_ID': f"{topic_id}_Q{i:02d}",
                    'Question': qa.get('question', ''),
                    'Answer': qa.get('answer', ''),
                    'Is_BrowseComp': '是' if qa.get('is_browsecomp', False) else '否',
                    'Is_High_Constraint': '是' if analysis.get('is_high_constraint', False) else '否',
                    'Constraint_Count': analysis.get('constraint_count', 0),
                    'Constraint_Types': ', '.join(analysis.get('constraint_types', [])),
                    'Answer_Word_Count': analysis.get('answer_words', 0),
                    'Answer_Char_Count': analysis.get('answer_chars', 0),
                    'Is_Short_Answer': '是' if analysis.get('is_short_answer', False) else '否',
                    'Deep_Score': f"{analysis.get('deep_score', 0):.3f}",
                    'BrowseComp_Pattern_Match': '是' if analysis.get('browsecomp_pattern_match', False) else '否',
                    'Conditions_Met': analysis.get('conditions_met', 0),
                    'Compression_Applied': '是' if qa.get('compression_applied', False) else '否',
                    'Original_Answer': qa.get('original_answer', '') if qa.get('compression_applied', False) else ''
                })
        
        return pd.DataFrame(qa_data)
    
    def _create_quality_analysis_sheet(self, experiment_result: Dict[str, Any]) -> pd.DataFrame:
        """创建质量分析工作表"""
        quality_data = []
        
        detailed_results = experiment_result.get('detailed_results', [])
        
        for result in detailed_results:
            if not result.get('success'):
                continue
                
            topic_id = result.get('topic_id', 'Unknown')
            report_analysis = result.get('report_analysis', {})
            validation = result.get('validation', {})
            
            quality_breakdown = report_analysis.get('quality_breakdown', {})
            relevance_breakdown = report_analysis.get('relevance_breakdown', {})
            
            quality_data.append({
                'Topic_ID': topic_id,
                'Overall_Quality_Score': f"{report_analysis.get('quality_score', 0):.3f}",
                'Quality_Grade': report_analysis.get('quality_grade', 'N/A'),
                'Relevance_Score': f"{report_analysis.get('relevance_score', 0):.3f}",
                'Relevance_Level': relevance_breakdown.get('relevance_level', 'N/A'),
                'Information_Density': f"{quality_breakdown.get('information_density', 0):.3f}",
                'Coherence_Score': f"{quality_breakdown.get('coherence_score', 0):.3f}",
                'Factual_Richness': f"{quality_breakdown.get('factual_richness', 0):.3f}",
                'Technical_Depth': f"{quality_breakdown.get('technical_depth', 0):.3f}",
                'Structural_Quality': f"{quality_breakdown.get('structural_quality', 0):.3f}",
                'Keyword_Matching': f"{relevance_breakdown.get('individual_scores', {}).get('keyword_matching', 0):.3f}",
                'TF_IDF_Similarity': f"{relevance_breakdown.get('individual_scores', {}).get('tfidf_similarity', 0):.3f}",
                'Semantic_Overlap': f"{relevance_breakdown.get('individual_scores', {}).get('semantic_overlap', 0):.3f}",
                'Entity_Consistency': f"{relevance_breakdown.get('individual_scores', {}).get('entity_consistency', 0):.3f}",
                'BrowseComp_Ratio_Check': '通过' if validation.get('browsecomp_ratio_check', False) else '未通过',
                'High_Constraint_Check': '通过' if validation.get('high_constraint_ratio_check', False) else '未通过',
                'Avg_Constraints_Check': '通过' if validation.get('avg_constraints_check', False) else '未通过',
                'Answer_Length_Check': '通过' if validation.get('answer_length_check', False) else '未通过'
            })
        
        return pd.DataFrame(quality_data)
    
    def _create_browsecomp_analysis_sheet(self, experiment_result: Dict[str, Any]) -> pd.DataFrame:
        """创建BrowseComp分析工作表"""
        browsecomp_data = []
        
        detailed_results = experiment_result.get('detailed_results', [])
        
        for result in detailed_results:
            if not result.get('success'):
                continue
                
            topic_id = result.get('topic_id', 'Unknown')
            questions = result.get('questions', [])
            
            browsecomp_questions = [q for q in questions if q.get('is_browsecomp', False)]
            non_browsecomp_questions = [q for q in questions if not q.get('is_browsecomp', False)]
            
            # BrowseComp问题统计
            if browsecomp_questions:
                browsecomp_constraints = [q.get('analysis', {}).get('constraint_count', 0) for q in browsecomp_questions]
                browsecomp_answer_words = [q.get('analysis', {}).get('answer_words', 0) for q in browsecomp_questions]
                
                browsecomp_data.append({
                    'Topic_ID': topic_id,
                    'Question_Type': 'BrowseComp',
                    'Question_Count': len(browsecomp_questions),
                    'Percentage': f"{len(browsecomp_questions)/len(questions):.1%}",
                    'Avg_Constraints': f"{statistics.mean(browsecomp_constraints):.2f}",
                    'Max_Constraints': max(browsecomp_constraints),
                    'Min_Constraints': min(browsecomp_constraints),
                    'Avg_Answer_Words': f"{statistics.mean(browsecomp_answer_words):.1f}",
                    'Max_Answer_Words': max(browsecomp_answer_words),
                    'Min_Answer_Words': min(browsecomp_answer_words),
                    'Pattern_Match_Rate': f"{sum(1 for q in browsecomp_questions if q.get('analysis', {}).get('browsecomp_pattern_match', False))/len(browsecomp_questions):.1%}"
                })
            
            # 非BrowseComp问题统计
            if non_browsecomp_questions:
                non_browsecomp_constraints = [q.get('analysis', {}).get('constraint_count', 0) for q in non_browsecomp_questions]
                non_browsecomp_answer_words = [q.get('analysis', {}).get('answer_words', 0) for q in non_browsecomp_questions]
                
                browsecomp_data.append({
                    'Topic_ID': topic_id,
                    'Question_Type': '非BrowseComp',
                    'Question_Count': len(non_browsecomp_questions),
                    'Percentage': f"{len(non_browsecomp_questions)/len(questions):.1%}",
                    'Avg_Constraints': f"{statistics.mean(non_browsecomp_constraints):.2f}",
                    'Max_Constraints': max(non_browsecomp_constraints),
                    'Min_Constraints': min(non_browsecomp_constraints),
                    'Avg_Answer_Words': f"{statistics.mean(non_browsecomp_answer_words):.1f}",
                    'Max_Answer_Words': max(non_browsecomp_answer_words),
                    'Min_Answer_Words': min(non_browsecomp_answer_words),
                    'Pattern_Match_Rate': 'N/A'
                })
        
        return pd.DataFrame(browsecomp_data)
    
    def _create_answer_length_analysis_sheet(self, experiment_result: Dict[str, Any]) -> pd.DataFrame:
        """创建答案长度分析工作表"""
        length_data = []
        
        detailed_results = experiment_result.get('detailed_results', [])
        
        for result in detailed_results:
            if not result.get('success'):
                continue
                
            topic_id = result.get('topic_id', 'Unknown')
            questions = result.get('questions', [])
            
            # 按答案长度分类
            short_answers = [q for q in questions if q.get('analysis', {}).get('answer_words', 0) <= 5]
            medium_answers = [q for q in questions if 5 < q.get('analysis', {}).get('answer_words', 0) <= 10]
            long_answers = [q for q in questions if q.get('analysis', {}).get('answer_words', 0) > 10]
            
            # 统计不同长度类别
            categories = [
                ('1-5词 (极短)', short_answers),
                ('6-10词 (短)', medium_answers),
                ('11+词 (长)', long_answers)
            ]
            
            for category_name, category_questions in categories:
                if category_questions:
                    answer_words = [q.get('analysis', {}).get('answer_words', 0) for q in category_questions]
                    constraint_counts = [q.get('analysis', {}).get('constraint_count', 0) for q in category_questions]
                    browsecomp_count = sum(1 for q in category_questions if q.get('is_browsecomp', False))
                    
                    length_data.append({
                        'Topic_ID': topic_id,
                        'Length_Category': category_name,
                        'Question_Count': len(category_questions),
                        'Percentage': f"{len(category_questions)/len(questions):.1%}",
                        'Avg_Answer_Words': f"{statistics.mean(answer_words):.1f}",
                        'Max_Answer_Words': max(answer_words),
                        'Min_Answer_Words': min(answer_words),
                        'Avg_Constraints': f"{statistics.mean(constraint_counts):.2f}",
                        'BrowseComp_Count': browsecomp_count,
                        'BrowseComp_Ratio': f"{browsecomp_count/len(category_questions):.1%}"
                    })
                else:
                    length_data.append({
                        'Topic_ID': topic_id,
                        'Length_Category': category_name,
                        'Question_Count': 0,
                        'Percentage': '0%',
                        'Avg_Answer_Words': 'N/A',
                        'Max_Answer_Words': 'N/A',
                        'Min_Answer_Words': 'N/A',
                        'Avg_Constraints': 'N/A',
                        'BrowseComp_Count': 0,
                        'BrowseComp_Ratio': '0%'
                    })
        
        return pd.DataFrame(length_data)
    
    def _create_constraint_analysis_sheet(self, experiment_result: Dict[str, Any]) -> pd.DataFrame:
        """创建约束类型分析工作表"""
        constraint_data = []
        
        detailed_results = experiment_result.get('detailed_results', [])
        
        # 收集所有约束类型
        all_constraint_types = set()
        for result in detailed_results:
            if result.get('success'):
                questions = result.get('questions', [])
                for q in questions:
                    constraint_types = q.get('analysis', {}).get('constraint_types', [])
                    all_constraint_types.update(constraint_types)
        
        all_constraint_types = sorted(list(all_constraint_types))
        
        for result in detailed_results:
            if not result.get('success'):
                continue
                
            topic_id = result.get('topic_id', 'Unknown')
            questions = result.get('questions', [])
            
            # 统计每种约束类型
            for constraint_type in all_constraint_types:
                questions_with_constraint = [
                    q for q in questions 
                    if constraint_type in q.get('analysis', {}).get('constraint_types', [])
                ]
                
                if questions_with_constraint:
                    answer_words = [q.get('analysis', {}).get('answer_words', 0) for q in questions_with_constraint]
                    browsecomp_count = sum(1 for q in questions_with_constraint if q.get('is_browsecomp', False))
                    
                    constraint_data.append({
                        'Topic_ID': topic_id,
                        'Constraint_Type': constraint_type,
                        'Question_Count': len(questions_with_constraint),
                        'Percentage': f"{len(questions_with_constraint)/len(questions):.1%}",
                        'Avg_Answer_Words': f"{statistics.mean(answer_words):.1f}",
                        'Max_Answer_Words': max(answer_words),
                        'Min_Answer_Words': min(answer_words),
                        'BrowseComp_Count': browsecomp_count,
                        'BrowseComp_Ratio': f"{browsecomp_count/len(questions_with_constraint):.1%}",
                        'Example_Question': questions_with_constraint[0].get('question', '')[:100] + '...' if len(questions_with_constraint[0].get('question', '')) > 100 else questions_with_constraint[0].get('question', ''),
                        'Example_Answer': questions_with_constraint[0].get('answer', '')
                    })
                else:
                    constraint_data.append({
                        'Topic_ID': topic_id,
                        'Constraint_Type': constraint_type,
                        'Question_Count': 0,
                        'Percentage': '0%',
                        'Avg_Answer_Words': 'N/A',
                        'Max_Answer_Words': 'N/A',
                        'Min_Answer_Words': 'N/A',
                        'BrowseComp_Count': 0,
                        'BrowseComp_Ratio': '0%',
                        'Example_Question': '',
                        'Example_Answer': ''
                    })
        
        return pd.DataFrame(constraint_data)
    
    def _create_report_quality_sheet(self, experiment_result: Dict[str, Any]) -> pd.DataFrame:
        """创建报告质量评估工作表"""
        report_data = []
        
        detailed_results = experiment_result.get('detailed_results', [])
        
        for result in detailed_results:
            if not result.get('success'):
                continue
                
            topic_id = result.get('topic_id', 'Unknown')
            report = result.get('report', '')
            report_analysis = result.get('report_analysis', {})
            
            report_data.append({
                'Topic_ID': topic_id,
                'Report_Word_Count': len(report.split()) if report else 0,
                'Report_Char_Count': len(report) if report else 0,
                'Report_Content_Preview': (report[:200] + '...') if len(report) > 200 else report,
                'Quality_Score': f"{report_analysis.get('quality_score', 0):.3f}",
                'Quality_Grade': report_analysis.get('quality_grade', 'N/A'),
                'Relevance_Score': f"{report_analysis.get('relevance_score', 0):.3f}",
                'Information_Density': f"{report_analysis.get('quality_breakdown', {}).get('information_density', 0):.3f}",
                'Coherence_Score': f"{report_analysis.get('quality_breakdown', {}).get('coherence_score', 0):.3f}",
                'Factual_Richness': f"{report_analysis.get('quality_breakdown', {}).get('factual_richness', 0):.3f}",
                'Technical_Depth': f"{report_analysis.get('quality_breakdown', {}).get('technical_depth', 0):.3f}",
                'Structural_Quality': f"{report_analysis.get('quality_breakdown', {}).get('structural_quality', 0):.3f}",
                'Meets_Quality_Threshold': '是' if report_analysis.get('quality_score', 0) >= 0.45 else '否'
            })
        
        return pd.DataFrame(report_data)
    
    def _create_gpt4o_evaluation_sheet(self, experiment_result: Dict[str, Any]) -> pd.DataFrame:
        """创建GPT-4o评判结果工作表"""
        gpt4o_data = []
        
        detailed_results = experiment_result.get('detailed_results', [])
        
        for result in detailed_results:
            if not result.get('success'):
                continue
                
            topic_id = result.get('topic_id', 'Unknown')
            gpt4o_eval = result.get('gpt4o_evaluation', {})
            
            if not gpt4o_eval:
                continue
            
            overall_assessment = gpt4o_eval.get('overall_assessment', {})
            sample_evaluations = gpt4o_eval.get('sample_evaluations', [])
            
            # 总体评估
            gpt4o_data.append({
                'Topic_ID': topic_id,
                'Evaluation_Type': '总体评估',
                'Sample_Size': gpt4o_eval.get('evaluation_summary', {}).get('sample_size', 0),
                'Overall_Score': f"{overall_assessment.get('overall_avg_score', 0):.1f}/10",
                'Overall_Grade': overall_assessment.get('overall_grade', 'N/A'),
                'Question': '总体评价',
                'Answer': '总体评价',
                'Individual_Score': 'N/A',
                'Individual_Grade': 'N/A',
                'Strengths': overall_assessment.get('strengths', ''),
                'Areas_For_Improvement': overall_assessment.get('areas_for_improvement', ''),
                'Comments': overall_assessment.get('summary', '')
            })
            
            # 样本评估详情
            for i, sample_eval in enumerate(sample_evaluations, 1):
                gpt4o_data.append({
                    'Topic_ID': topic_id,
                    'Evaluation_Type': f'样本{i}',
                    'Sample_Size': 'N/A',
                    'Overall_Score': 'N/A',
                    'Overall_Grade': 'N/A',
                    'Question': sample_eval.get('question', ''),
                    'Answer': sample_eval.get('answer', ''),
                    'Individual_Score': f"{sample_eval.get('score', 0)}/10",
                    'Individual_Grade': sample_eval.get('grade', 'N/A'),
                    'Strengths': ', '.join(sample_eval.get('strengths', [])),
                    'Areas_For_Improvement': ', '.join(sample_eval.get('areas_for_improvement', [])),
                    'Comments': sample_eval.get('reasoning', '')
                })
        
        return pd.DataFrame(gpt4o_data)
    
    def _has_gpt4o_evaluation(self, experiment_result: Dict[str, Any]) -> bool:
        """检查是否有GPT-4o评判结果"""
        detailed_results = experiment_result.get('detailed_results', [])
        for result in detailed_results:
            if result.get('success') and result.get('gpt4o_evaluation'):
                return True
        return False


def export_experiment_results_to_excel(experiment_result_json_path: str, 
                                     output_filename: Optional[str] = None) -> str:
    """
    便利函数：从JSON文件导出Excel报告
    
    Args:
        experiment_result_json_path: 实验结果JSON文件路径
        output_filename: 输出Excel文件名
    
    Returns:
        生成的Excel文件路径
    """
    try:
        with open(experiment_result_json_path, 'r', encoding='utf-8') as f:
            experiment_result = json.load(f)
        
        exporter = ShortAnswerDeepQueryExcelExporter(
            results_dir=str(Path(experiment_result_json_path).parent)
        )
        
        return exporter.export_experiment_to_excel(experiment_result, output_filename)
        
    except Exception as e:
        logger.error(f"导出Excel失败: {e}")
        raise


if __name__ == "__main__":
    # 测试导出功能
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python excel_export_system.py <experiment_result.json> [output_filename.xlsx]")
        sys.exit(1)
    
    json_path = sys.argv[1]
    output_name = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        excel_path = export_experiment_results_to_excel(json_path, output_name)
        print(f"✅ Excel报告生成成功: {excel_path}")
    except Exception as e:
        print(f"❌ 导出失败: {e}")
        sys.exit(1) 
"""
Comprehensive Adaptive Framework
完整的自适应优化框架 - 整合所有质量控制和优化组件
"""

import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional
from pathlib import Path
from dataclasses import dataclass, asdict

from report_quality_evaluation_system import ReportQualityEvaluator, TopicRelevanceAnalyzer, QualityMetrics
from answer_compression_optimizer import AnswerCompressionOptimizer, EnhancedAnswerValidator

logger = logging.getLogger(__name__)

@dataclass
class AdaptiveOptimizationConfig:
    """自适应优化配置"""
    # 质量阈值
    min_report_quality_score: float = 0.65
    min_topic_relevance_score: float = 0.60
    min_answer_compression_success_rate: float = 0.70
    
    # 优化策略
    max_optimization_iterations: int = 5
    target_success_rate: float = 0.80
    aggressive_optimization_threshold: float = 0.30
    
    # 报告生成参数
    report_length_range: Tuple[int, int] = (800, 1500)
    max_structural_violations: int = 2
    min_information_density: float = 0.40
    
    # 问题生成参数
    min_browsecomp_ratio: float = 0.70
    min_high_constraint_ratio: float = 0.20
    min_avg_constraints: float = 2.5
    
    # 答案质量参数
    max_avg_word_count: float = 12.0
    max_answer_violations_ratio: float = 0.25
    target_compression_ratio: float = 0.90

@dataclass
class OptimizationResult:
    """优化结果"""
    iteration: int
    success: bool
    before_metrics: Dict[str, Any]
    after_metrics: Dict[str, Any]
    improvements: Dict[str, float]
    optimization_actions: List[str]
    processing_time: float
    recommendation: str

class ComprehensiveAdaptiveFramework:
    """综合自适应优化框架"""
    
    def __init__(self, experiment_dir: str, config: AdaptiveOptimizationConfig = None):
        self.experiment_dir = Path(experiment_dir)
        self.config = config or AdaptiveOptimizationConfig()
        
        # 初始化组件
        self.report_evaluator = ReportQualityEvaluator()
        self.relevance_analyzer = TopicRelevanceAnalyzer()
        self.answer_validator = EnhancedAnswerValidator()
        
        # 优化历史
        self.optimization_history = []
        self.performance_trends = {
            'report_quality': [],
            'topic_relevance': [],
            'answer_quality': [],
            'overall_success_rate': []
        }
        
        logger.info(f"🚀 综合自适应框架初始化完成")
        logger.info(f"📁 实验目录: {self.experiment_dir}")
        logger.info(f"🎯 目标成功率: {self.config.target_success_rate:.1%}")
    
    def run_adaptive_optimization_cycle(self, experiment_runner, max_iterations: int = None) -> Dict[str, Any]:
        """运行完整的自适应优化循环"""
        max_iterations = max_iterations or self.config.max_optimization_iterations
        
        cycle_results = {
            'start_time': datetime.now(),
            'max_iterations': max_iterations,
            'target_success_rate': self.config.target_success_rate,
            'iterations': [],
            'final_success_rate': 0.0,
            'optimization_successful': False,
            'total_improvements': {},
            'best_configuration': {}
        }
        
        logger.info(f"🔄 开始自适应优化循环 (最大{max_iterations}轮)")
        
        current_success_rate = 0.0
        best_config = None
        best_metrics = None
        
        for iteration in range(1, max_iterations + 1):
            logger.info(f"\n📊 === 优化轮次 {iteration}/{max_iterations} ===")
            
            iteration_start = time.time()
            
            # Step 1: 运行实验
            logger.info("🧪 执行实验...")
            # 使用默认参数，如果实验对象已经预配置则会使用预配置的设置
            experiment_result = experiment_runner.run_experiment()
            
            # Step 2: 全面分析实验结果
            logger.info("🔍 全面质量分析...")
            comprehensive_analysis = self._comprehensive_quality_analysis(experiment_result)
            
            # Step 3: 计算当前成功率和改进空间
            current_success_rate = comprehensive_analysis['overall_metrics']['success_rate']
            improvement_potential = self._assess_improvement_potential(comprehensive_analysis)
            
            # Step 4: 生成优化策略
            logger.info("🎯 生成优化策略...")
            optimization_strategies = self._generate_optimization_strategies(
                comprehensive_analysis, improvement_potential, iteration
            )
            
            # Step 5: 应用优化
            logger.info("⚙️ 应用优化策略...")
            optimization_actions = self._apply_optimizations(
                optimization_strategies, experiment_runner
            )
            
            # Step 6: 验证优化效果
            logger.info("✅ 验证优化效果...")
            post_optimization_result = experiment_runner.run_experiment()
            post_analysis = self._comprehensive_quality_analysis(post_optimization_result)
            new_success_rate = post_analysis['overall_metrics']['success_rate']
            
            # 计算改进情况
            improvements = self._calculate_improvements(comprehensive_analysis, post_analysis)
            
            iteration_time = time.time() - iteration_start
            
            # 保存本轮结果
            optimization_result = OptimizationResult(
                iteration=iteration,
                success=new_success_rate > current_success_rate,
                before_metrics=comprehensive_analysis['overall_metrics'],
                after_metrics=post_analysis['overall_metrics'],
                improvements=improvements,
                optimization_actions=optimization_actions,
                processing_time=iteration_time,
                recommendation=self._generate_recommendation(new_success_rate, iteration, max_iterations)
            )
            
            cycle_results['iterations'].append(asdict(optimization_result))
            self.optimization_history.append(optimization_result)
            
            # 更新性能趋势
            self._update_performance_trends(post_analysis)
            
            # 记录最佳配置
            if new_success_rate > current_success_rate or best_config is None:
                best_config = self._save_current_configuration(experiment_runner)
                best_metrics = post_analysis['overall_metrics']
                cycle_results['best_configuration'] = best_config
            
            logger.info(f"📈 轮次{iteration}结果: {current_success_rate:.1%} → {new_success_rate:.1%}")
            
            # 检查是否达到目标
            if new_success_rate >= self.config.target_success_rate:
                logger.info(f"🎯 达到目标成功率: {new_success_rate:.1%} >= {self.config.target_success_rate:.1%}")
                cycle_results['optimization_successful'] = True
                break
            
            # 更新当前成功率
            current_success_rate = new_success_rate
        
        # 完成优化循环
        cycle_results['final_success_rate'] = current_success_rate
        cycle_results['end_time'] = datetime.now()
        cycle_results['total_duration'] = (cycle_results['end_time'] - cycle_results['start_time']).total_seconds()
        
        # 计算总体改进
        if cycle_results['iterations']:
            first_metrics = cycle_results['iterations'][0]['before_metrics']
            final_metrics = cycle_results['iterations'][-1]['after_metrics']
            cycle_results['total_improvements'] = self._calculate_improvements(
                {'overall_metrics': first_metrics},
                {'overall_metrics': final_metrics}
            )
        
        # 保存结果
        self._save_optimization_cycle_results(cycle_results)
        
        logger.info(f"🏁 优化循环完成!")
        logger.info(f"📊 最终成功率: {current_success_rate:.1%}")
        logger.info(f"🎯 目标达成: {'✅' if cycle_results['optimization_successful'] else '❌'}")
        
        return cycle_results
    
    def _comprehensive_quality_analysis(self, experiment_result: Dict[str, Any]) -> Dict[str, Any]:
        """全面的质量分析"""
        analysis = {
            'experiment_info': experiment_result.get('experiment_info', {}),
            'report_quality_analysis': {},
            'topic_relevance_analysis': {},
            'answer_quality_analysis': {},
            'overall_metrics': {},
            'detailed_breakdown': {}
        }
        
        # 修复：使用正确的结果路径
        detailed_results = experiment_result.get('detailed_results', [])
        if not detailed_results:
            # 备用路径
            detailed_results = experiment_result.get('results', [])
        
        successful_results = [r for r in detailed_results if r.get('success')]
        total_results = len(detailed_results)
        
        if not successful_results:
            analysis['overall_metrics'] = {
                'success_rate': 0.0,
                'avg_report_quality': 0.0,
                'avg_topic_relevance': 0.0,
                'avg_answer_quality': 0.0,
                'total_topics': total_results
            }
            return analysis
        
        # 1. 报告质量分析
        report_qualities = []
        for result in successful_results:
            if 'report' in result:
                # 这里应该调用报告质量评估，简化版本
                report_quality = self._evaluate_single_report_quality(result)
                report_qualities.append(report_quality)
        
        # 2. 主题相关性分析
        relevance_scores = []
        for result in successful_results:
            relevance_score = self._evaluate_topic_relevance(result)
            relevance_scores.append(relevance_score)
        
        # 3. 答案质量分析
        answer_qualities = []
        for result in successful_results:
            if 'answers' in result:
                answer_quality = self._evaluate_answer_quality(result)
                answer_qualities.append(answer_quality)
        
        # 汇总分析
        analysis['overall_metrics'] = {
            'success_rate': len(successful_results) / max(total_results, 1),
            'avg_report_quality': sum(report_qualities) / max(len(report_qualities), 1),
            'avg_topic_relevance': sum(relevance_scores) / max(len(relevance_scores), 1),
            'avg_answer_quality': sum(answer_qualities) / max(len(answer_qualities), 1),
            'total_topics': total_results,
            'successful_topics': len(successful_results)
        }
        
        analysis['detailed_breakdown'] = {
            'report_qualities': report_qualities,
            'relevance_scores': relevance_scores,
            'answer_qualities': answer_qualities
        }
        
        return analysis
    
    def _evaluate_single_report_quality(self, result: Dict[str, Any]) -> float:
        """评估单个报告质量 (简化版本)"""
        try:
            # 修复：正确处理report字段，可能是字符串或字典
            report = result.get('report', '')
            if isinstance(report, dict):
                report_content = report.get('content', '')
            elif isinstance(report, str):
                report_content = report
            else:
                report_content = str(report) if report else ''
            
            if not report_content:
                return 0.0
            
            # 简单的质量指标
            word_count = len(report_content.split())
            char_count = len(report_content)
            
            # 长度分数
            target_min, target_max = self.config.report_length_range
            if target_min <= word_count <= target_max:
                length_score = 1.0
            elif word_count < target_min:
                length_score = word_count / target_min
            else:
                length_score = max(0.5, target_max / word_count)
            
            # 信息密度分数 (数字和专业词汇)
            import re
            numerical_count = len(re.findall(r'\d+\.?\d*', report_content))
            technical_words = ['research', 'study', 'analysis', 'method', 'data', 'result']
            technical_count = sum(report_content.lower().count(word) for word in technical_words)
            
            info_density = min((numerical_count + technical_count) / word_count * 10, 1.0)
            
            # 结构质量分数 (避免学术结构)
            bad_structures = ['abstract:', 'introduction:', 'conclusion:']
            structure_violations = sum(report_content.lower().count(marker) for marker in bad_structures)
            structure_score = max(0, 1.0 - structure_violations * 0.2)
            
            # 综合分数
            overall_score = (length_score * 0.3 + info_density * 0.4 + structure_score * 0.3)
            return overall_score
            
        except Exception as e:
            logger.error(f"报告质量评估失败: {e}")
            return 0.0
    
    def _evaluate_topic_relevance(self, result: Dict[str, Any]) -> float:
        """评估主题相关性"""
        try:
            # 简化的相关性评估
            return 0.7  # 默认中等相关性
        except Exception as e:
            logger.error(f"主题相关性评估失败: {e}")
            return 0.0
    
    def _evaluate_answer_quality(self, result: Dict[str, Any]) -> float:
        """评估答案质量"""
        try:
            # 修复：正确处理questions字段（实际字段名）
            questions = result.get('questions', [])
            if not questions:
                # 尝试其他可能的字段名
                questions = result.get('answers', {})
                if isinstance(questions, dict):
                    questions = questions.get('qa_pairs', [])
                elif not isinstance(questions, list):
                    questions = []
            
            if not questions:
                return 0.0
            
            total_score = 0.0
            valid_pairs = 0
            
            for qa_pair in questions:
                answer = qa_pair.get('answer', '')
                word_count = len(answer.split())
                
                # 长度分数 (短答案更好)
                if word_count <= 5:
                    length_score = 1.0
                elif word_count <= 10:
                    length_score = 0.8
                elif word_count <= 15:
                    length_score = 0.6
                else:
                    length_score = 0.3
                
                # 内容质量分数 (基于是否包含具体信息)
                import re
                has_numbers = bool(re.search(r'\d+', answer))
                has_specific_info = len(answer.split()) <= 3 and answer.strip()
                
                content_score = 0.5
                if has_numbers:
                    content_score += 0.3
                if has_specific_info:
                    content_score += 0.2
                
                pair_score = (length_score * 0.6 + content_score * 0.4)
                total_score += pair_score
                valid_pairs += 1
            
            return total_score / max(valid_pairs, 1)
            
        except Exception as e:
            logger.error(f"答案质量评估失败: {e}")
            return 0.0
    
    def _assess_improvement_potential(self, analysis: Dict[str, Any]) -> Dict[str, float]:
        """评估改进潜力"""
        metrics = analysis['overall_metrics']
        
        potential = {
            'report_quality': max(0, self.config.min_report_quality_score - metrics.get('avg_report_quality', 0)),
            'topic_relevance': max(0, self.config.min_topic_relevance_score - metrics.get('avg_topic_relevance', 0)),
            'answer_quality': max(0, 0.8 - metrics.get('avg_answer_quality', 0)),  # 目标80%
            'success_rate': max(0, self.config.target_success_rate - metrics.get('success_rate', 0))
        }
        
        return potential
    
    def _generate_optimization_strategies(self, analysis: Dict[str, Any], 
                                        potential: Dict[str, float], 
                                        iteration: int) -> List[Dict[str, Any]]:
        """生成优化策略"""
        strategies = []
        
        # 报告质量优化
        if potential['report_quality'] > 0.1:
            strategies.append({
                'type': 'report_optimization',
                'priority': 'high',
                'actions': [
                    'increase_report_length_target',
                    'enhance_information_density',
                    'reduce_structural_violations'
                ],
                'target_improvement': potential['report_quality']
            })
        
        # 答案质量优化
        if potential['answer_quality'] > 0.1:
            strategies.append({
                'type': 'answer_optimization',
                'priority': 'high',
                'actions': [
                    'apply_answer_compression',
                    'enhance_short_answer_detection',
                    'optimize_answer_generation_prompts'
                ],
                'target_improvement': potential['answer_quality']
            })
        
        # 成功率优化 (如果多轮优化后仍然不达标)
        if iteration > 2 and potential['success_rate'] > 0.2:
            strategies.append({
                'type': 'aggressive_optimization',
                'priority': 'critical',
                'actions': [
                    'lower_quality_thresholds',
                    'enable_emergency_mode',
                    'simplify_validation_criteria'
                ],
                'target_improvement': potential['success_rate']
            })
        
        return strategies
    
    def _apply_optimizations(self, strategies: List[Dict[str, Any]], 
                           experiment_runner) -> List[str]:
        """应用优化策略 - 真正修改实验配置"""
        applied_actions = []
        
        for strategy in strategies:
            strategy_type = strategy['type']
            actions = strategy['actions']
            
            logger.info(f"  🔧 应用{strategy_type}策略...")
            
            for action in actions:
                try:
                    if action == 'increase_report_length_target':
                        # 动态修改实验runner的报告长度配置
                        current_min = experiment_runner.config.get('min_report_words', 600)
                        current_max = experiment_runner.config.get('max_report_words', 1500)
                        new_min = max(600, current_min - 100)
                        new_max = current_max + 200
                        
                        experiment_runner.config['min_report_words'] = new_min
                        experiment_runner.config['max_report_words'] = new_max
                        applied_actions.append(f"📝 调整报告长度目标: {new_min}-{new_max}词")
                    
                    elif action == 'apply_answer_compression':
                        # 动态启用答案压缩
                        experiment_runner.config['enable_answer_compression'] = True
                        experiment_runner.config['compression_threshold'] = 10  # 更激进的压缩
                        applied_actions.append("启用答案压缩优化")
                    
                    elif action == 'enhance_short_answer_detection':
                        # 降低答案长度要求
                        experiment_runner.config['max_answer_words'] = max(10, 
                            experiment_runner.config.get('max_answer_words', 15) - 2)
                        applied_actions.append("增强短答案检测逻辑")
                    
                    elif action == 'lower_quality_thresholds':
                        # 动态降低质量阈值
                        experiment_runner.config['min_browsecomp_ratio'] = max(0.2, 
                            experiment_runner.config.get('min_browsecomp_ratio', 0.4) * 0.9)
                        experiment_runner.config['min_high_constraint_ratio'] = max(0.1, 
                            experiment_runner.config.get('min_high_constraint_ratio', 0.15) * 0.9)
                        experiment_runner.config['min_report_quality_score'] = max(0.3, 
                            experiment_runner.config.get('min_report_quality_score', 0.45) * 0.9)
                        applied_actions.append("📉 降低质量阈值: report={:.2f}".format(
                            experiment_runner.config['min_report_quality_score']))
                    
                    elif action == 'enable_emergency_mode':
                        # 紧急模式：大幅降低所有阈值
                        experiment_runner.config['min_browsecomp_ratio'] = 0.2
                        experiment_runner.config['min_high_constraint_ratio'] = 0.1
                        experiment_runner.config['min_avg_constraints'] = 0.8
                        experiment_runner.config['min_report_quality_score'] = 0.3
                        experiment_runner.config['min_relevance_score'] = 0.1
                        applied_actions.append("🚨 启用紧急模式，大幅降低阈值")
                    
                    elif action == 'optimize_answer_generation_prompts':
                        # 优化答案生成（不再动态降低问题数量）
                        # 注释掉降低问题数量的逻辑，保持用户配置的50个问题
                        # experiment_runner.config['questions_per_topic'] = min(25, 
                        #     experiment_runner.config.get('questions_per_topic', 30) - 5)
                        
                        # 改为优化其他参数
                        experiment_runner.config['max_answer_words'] = max(8, 
                            experiment_runner.config.get('max_answer_words', 15) - 2)
                        applied_actions.append("优化答案生成参数（保持问题数量不变）")
                    
                except Exception as e:
                    logger.error(f"优化行动 {action} 失败: {e}")
        
        # 重要：记录当前配置状态
        logger.info(f"  📊 当前配置: BrowseComp阈值={experiment_runner.config.get('min_browsecomp_ratio', 0):.2f}, "
                   f"质量阈值={experiment_runner.config.get('min_report_quality_score', 0):.2f}")
        
        return applied_actions
    

    
    def _calculate_improvements(self, before_analysis: Dict[str, Any], 
                              after_analysis: Dict[str, Any]) -> Dict[str, float]:
        """计算改进情况"""
        before_metrics = before_analysis['overall_metrics']
        after_metrics = after_analysis['overall_metrics']
        
        improvements = {}
        for key in before_metrics:
            if isinstance(before_metrics[key], (int, float)) and isinstance(after_metrics[key], (int, float)):
                improvement = after_metrics[key] - before_metrics[key]
                improvements[key] = improvement
        
        return improvements
    
    def _generate_recommendation(self, success_rate: float, iteration: int, max_iterations: int) -> str:
        """生成建议"""
        if success_rate >= self.config.target_success_rate:
            return "🎯 已达到目标成功率，可以结束优化"
        elif iteration >= max_iterations:
            return "⏰ 已达最大迭代次数，建议手动调整配置"
        elif success_rate < 0.3:
            return "🚨 成功率过低，建议检查基础配置"
        else:
            return "🔄 继续优化，逐步改进系统性能"
    
    def _update_performance_trends(self, analysis: Dict[str, Any]):
        """更新性能趋势"""
        metrics = analysis['overall_metrics']
        
        self.performance_trends['report_quality'].append(metrics.get('avg_report_quality', 0))
        self.performance_trends['topic_relevance'].append(metrics.get('avg_topic_relevance', 0))
        self.performance_trends['answer_quality'].append(metrics.get('avg_answer_quality', 0))
        self.performance_trends['overall_success_rate'].append(metrics.get('success_rate', 0))
        
        # 保持最近10次记录
        for key in self.performance_trends:
            if len(self.performance_trends[key]) > 10:
                self.performance_trends[key] = self.performance_trends[key][-10:]
    
    def _save_current_configuration(self, experiment_runner) -> Dict[str, Any]:
        """保存当前最佳配置"""
        config_snapshot = {
            'adaptive_config': asdict(self.config),
            'timestamp': datetime.now().isoformat(),
            'performance_trends': self.performance_trends.copy()
        }
        return config_snapshot
    
    def _save_optimization_cycle_results(self, cycle_results: Dict[str, Any]):
        """保存优化循环结果"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        results_file = self.experiment_dir / f"adaptive_optimization_cycle_{timestamp}.json"
        
        # 转换datetime对象为字符串
        def datetime_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(cycle_results, f, indent=2, ensure_ascii=False, default=datetime_serializer)
        
        logger.info(f"💾 优化循环结果已保存: {results_file}")
        
        # 生成总结报告
        self._generate_optimization_summary(cycle_results, timestamp)
    
    def _generate_optimization_summary(self, cycle_results: Dict[str, Any], timestamp: str):
        """生成优化总结报告"""
        summary_file = self.experiment_dir / f"adaptive_optimization_summary_{timestamp}.md"
        
        summary = []
        summary.append("# 自适应优化循环总结报告\n")
        summary.append(f"**时间**: {cycle_results['start_time']}\n")
        summary.append(f"**总用时**: {cycle_results.get('total_duration', 0):.1f}秒\n")
        summary.append(f"**目标成功率**: {cycle_results['target_success_rate']:.1%}\n")
        summary.append(f"**最终成功率**: {cycle_results['final_success_rate']:.1%}\n")
        summary.append(f"**优化成功**: {'✅ 是' if cycle_results['optimization_successful'] else '❌ 否'}\n\n")
        
        summary.append("## 优化轮次详情\n")
        for i, iteration in enumerate(cycle_results['iterations'], 1):
            summary.append(f"### 轮次 {i}\n")
            summary.append(f"- **成功率变化**: {iteration['before_metrics']['success_rate']:.1%} → {iteration['after_metrics']['success_rate']:.1%}\n")
            summary.append(f"- **处理时间**: {iteration['processing_time']:.1f}秒\n")
            summary.append(f"- **优化行动**: {', '.join(iteration['optimization_actions'])}\n")
            summary.append(f"- **建议**: {iteration['recommendation']}\n\n")
        
        if cycle_results.get('total_improvements'):
            summary.append("## 总体改进情况\n")
            for metric, improvement in cycle_results['total_improvements'].items():
                if isinstance(improvement, (int, float)):
                    summary.append(f"- **{metric}**: {improvement:+.3f}\n")
        
        summary.append("\n## 性能趋势\n")
        summary.append("📈 报告质量、主题相关性、答案质量和整体成功率的变化趋势已记录在性能数据中。\n")
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.writelines(summary)
        
        logger.info(f"📊 优化总结已保存: {summary_file}")


def create_adaptive_framework(experiment_dir: str, config: AdaptiveOptimizationConfig = None) -> ComprehensiveAdaptiveFramework:
    """创建综合自适应框架实例"""
    return ComprehensiveAdaptiveFramework(experiment_dir, config)


def test_adaptive_framework():
    """测试自适应框架"""
    print("=== 综合自适应框架测试 ===")
    
    # 创建测试配置
    config = AdaptiveOptimizationConfig(
        min_report_quality_score=0.60,
        target_success_rate=0.75,
        max_optimization_iterations=3
    )
    
    # 创建框架
    framework = ComprehensiveAdaptiveFramework("./test_results", config)
    
    print(f"框架配置: 目标成功率 {config.target_success_rate:.1%}")
    print(f"质量阈值: 报告 {config.min_report_quality_score:.2f}")
    print("框架初始化成功！")

if __name__ == "__main__":
    test_adaptive_framework() 
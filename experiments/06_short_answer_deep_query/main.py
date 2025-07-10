#!/usr/bin/env python3
"""
Short Answer Deep Query 统一入口脚本
====================================

集成Answer-to-Query + LLM深度设计系统的统一入口，提供交互式菜单选择。

核心创新：
- Answer-to-Query反向生成方法：先提取多样化答案，再设计深度问题
- LLM双重智能设计：事实筛选 + 问题精心设计
- 内置质量保证：多层次验证确保Short Answer Deep Query标准
- Report融合方式：保持多文档融合生成报告的优势

功能包括：
- Answer-to-Query问题生成（推荐）
- 传统模式实验
- 数据源选择
- 配置查看和修改

作者: Assistant
日期: 2025-01-09
版本: v3.0 Answer-to-Query Enhanced
"""

import sys
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional

# 导入核心组件
from final_optimized_experiment import FinalOptimizedExperiment

class UnifiedExperimentRunner:
    """统一实验运行器 - Answer-to-Query Enhanced"""
    
    def __init__(self):
        self.results_dir = "./results"
        self.current_config = None
        self.api_keys_configured = False
        
    def print_banner(self):
        """打印欢迎横幅"""
        print("\n" + "="*70)
        print("🚀 Short Answer Deep Query - Answer-to-Query Enhanced")
        print("="*70)
        print("🎯 创新方法: 先提取答案 → LLM智能筛选 → 精心设计深度问题")
        print("✨ 内置优化: 事实多样性 + 深度级别分层 + BrowseComp质量保证")
        print("🔬 核心思想: Short Answer Deep Query + BrowseComp + Report融合")
        print("="*70)
        print()
    
    def show_main_menu(self):
        """显示主菜单"""
        # 检查API密钥状态
        api_status = "✅ 已配置" if self.api_keys_configured else "❌ 未配置"
        print(f"🔑 API密钥状态: {api_status}")
        print()
        
        print("📋 请选择实验模式:")
        print()
        print("  1️⃣  Answer-to-Query实验 (推荐) - 创新的反向生成方法")
        print("      🔹 智能事实提取 → LLM筛选增强 → 深度问题设计")
        print("      🔹 内置多样性保证，解决同质化问题")
        print("      🔹 保持Short Answer Deep Query核心思想")
        print()
        print("  2️⃣  完整生产运行    - 处理所有文档，生产环境使用")
        print()
        print("  3️⃣  查看配置        - 显示当前配置参数")
        print("  4️⃣  修改配置        - 自定义实验参数")
        print("  5️⃣  配置API密钥     - 设置OpenAI或Claude API密钥")
        print()
        print("  6️⃣  帮助文档        - 查看使用说明")
        print("  0️⃣  退出程序")
        print()
        
    def show_data_source_menu(self):
        """显示数据源选择菜单"""
        print("📊 请选择数据源:")
        print()
        print("  1️⃣  ClueWeb22数据集  - 网页文档数据")
        print("  2️⃣  学术论文数据集    - 高质量学术文档")
        print()
        
    def show_scale_menu(self):
        """显示实验规模选择菜单"""
        print("📏 请选择实验规模:")
        print()
        print("  1️⃣  小规模测试   - 3个主题 (快速验证，约5-10分钟)")
        print("  2️⃣  中等规模测试 - 9个主题 (性能评估，约15-30分钟)")
        print("  3️⃣  大规模测试   - 20个主题 (完整评估，约40-60分钟)")
        print("  4️⃣  自定义规模   - 手动指定主题数量")
        print()
        
    def get_user_choice(self, prompt: str, valid_choices: list, default: str = None) -> str:
        """获取用户选择"""
        while True:
            if default:
                choice = input(f"{prompt} [默认: {default}]: ").strip()
                if not choice:
                    choice = default
            else:
                choice = input(f"{prompt}: ").strip()
                
            if choice in valid_choices:
                return choice
            else:
                print(f"❌ 无效选择，请输入: {', '.join(valid_choices)}")
                
    def show_current_config(self):
        """显示当前配置"""
        print("\n⚙️ 当前实验配置:")
        print("-" * 50)
        
        experiment = FinalOptimizedExperiment(self.results_dir)
        config = experiment.config
        
        print("🎯 Answer-to-Query配置:")
        print(f"  • 每主题问题数: {config['questions_per_topic']}")
        print(f"  • 事实提取倍数: 2x (确保充足选择)")
        print(f"  • LLM双重设计: 事实筛选 + 问题设计")
        print(f"  • 深度级别: surface/medium/deep 自动分层")
        print()
        
        print("📝 报告生成配置:")
        print(f"  • 最小报告字数: {config['min_report_words']}")
        print(f"  • 最大报告字数: {config['max_report_words']}")
        print(f"  • 多文档融合: Topic级智能融合")
        print()
        
        print("🔍 BrowseComp质量控制:")
        print(f"  • 最小BrowseComp比例: {config['min_browsecomp_ratio']:.0%}")
        print(f"  • 最大答案字数: {config['max_answer_words']}")
        print(f"  • 内置质量检测: 自动BrowseComp验证")
        print()
        
        print("✨ 新系统特性:")
        print("  • 7种事实类型提取: 数字、日期、人名、地点、方法、术语、比较")
        print("  • 智能去重机制: 答案指纹 + 相似度检测") 
        print("  • 深度问题设计: 基于推理复杂度分层设计")
        print("  • 内置多样性: 无需外部优化框架")
        print()
        
    def show_help(self):
        """显示帮助信息"""
        print("\n📚 Answer-to-Query Enhanced 使用帮助")
        print("="*60)
        print()
        print("🎯 Answer-to-Query方法论:")
        print("  ✨ 创新思路: 传统方法容易产生同质化问题")
        print("     → Answer-to-Query先提取多样化答案，再反向设计问题")
        print("  🔍 三层设计:")
        print("     1. 智能事实提取: 7种类型确保覆盖面")
        print("     2. LLM筛选增强: 选择最有价值的事实，分配深度级别")
        print("     3. 精心问题设计: 基于深度级别设计分析性问题")
        print()
        
        print("🔬 核心优势:")
        print("  • 多样性保证: 不同答案自动产生不同问题")
        print("  • 质量控制: LLM双重设计确保深度和准确性")
        print("  • 无需调优: 内置优化机制，自动平衡质量和多样性")
        print("  • 兼容性强: 保持Short Answer Deep Query和BrowseComp思想")
        print()
        
        print("📊 实验规模建议:")
        print("  • 小规模(3个主题): 验证方法有效性")
        print("  • 中等规模(9个主题): 评估系统性能")
        print("  • 大规模(20个主题): 完整评估和生产使用")
        print()
        
        print("🔧 技术要求:")
        print("  • API密钥: OpenAI GPT-4 或 Anthropic Claude")
        print("  • 数据: ClueWeb22数据集 (每topic含100个txt文档)")
        print("  • 时间: 约2-3分钟/topic (包含LLM双重设计)")
        print()
        
    def run_answer_to_query_experiment(self, data_source: str, num_topics: int, custom_config: Optional[Dict] = None):
        """运行Answer-to-Query增强实验 - 核心功能"""
        print(f"\n🚀 启动Answer-to-Query增强实验")
        print(f"📊 数据源: {data_source}")
        print(f"📏 主题数量: {num_topics}")
        print(f"🔬 方法: 事实提取 → LLM筛选 → 深度问题设计")
        print("-" * 60)
        
        try:
            # 创建实验实例
            experiment = FinalOptimizedExperiment(self.results_dir)
            
            # 应用自定义配置
            if custom_config:
                experiment.config.update(custom_config)
                print("⚙️ 应用自定义配置")
            
            # 限制主题数量
            original_load_documents = experiment.load_documents
            def limited_load_documents(data_source_param=data_source):
                topics = original_load_documents(data_source_param)
                return topics[:num_topics]
            experiment.load_documents = limited_load_documents
            
            print("💡 Answer-to-Query处理流程:")
            print("  1️⃣ Topic多文档融合 → 生成统一报告")
            print("  2️⃣ 智能事实提取 → 7种类型 × 2倍数量")
            print("  3️⃣ LLM筛选增强 → 选择最有价值事实 + 深度分级")
            print("  4️⃣ 精心问题设计 → 基于深度级别定制问题")
            print("  5️⃣ BrowseComp验证 → 确保符合标准")
            print()
            
            print("📋 实验配置:")
            print(f"  • 每主题问题数: {experiment.config['questions_per_topic']}")
            print(f"  • 事实提取类型: 数字、日期、人名、地点、方法、术语、比较")
            print(f"  • LLM深度设计: surface/medium/deep分层")
            print(f"  • 质量保证: BrowseComp自动验证")
            print(f"  • 最大答案长度: {experiment.config['max_answer_words']} 词")
            print()
            
            # 运行实验
            print("🔄 开始实验...")
            result = experiment.run_experiment("test", data_source)
            
            # 显示结果
            print("\n" + "="*60)
            print("🎉 Answer-to-Query实验完成!")
            print("="*60)
            
            # 基础统计
            stats = result['aggregated_statistics']
            summary = result['summary']
            
            print(f"📈 成功率: {summary['success_rate']:.2%}")
            print(f"📊 总问题数: {stats['total_questions_generated']}")
            print(f"🎯 BrowseComp问题: {stats['total_browsecomp_questions']} ({stats.get('avg_browsecomp_ratio', 0):.2%})")
            print(f"🔗 平均约束数: {stats['avg_constraints_per_question']:.2f}")
            print(f"📝 平均答案长度: {stats['avg_answer_words']:.1f} 词")
            print(f"⏱️ 总处理时间: {summary['total_processing_time']:.1f} 秒")
            print(f"⚡ 平均处理速度: {summary['total_processing_time']/num_topics:.1f} 秒/topic")
            
            # Answer-to-Query特有统计
            if 'detailed_results' in result:
                answer_types = {}
                depth_levels = {}
                
                for topic_result in result['detailed_results']:
                    if topic_result.get('success') and 'questions' in topic_result:
                        for q in topic_result['questions']:
                            # 统计答案类型
                            answer_type = q.get('answer_type', 'unknown')
                            answer_types[answer_type] = answer_types.get(answer_type, 0) + 1
                            
                            # 统计深度级别
                            depth_level = q.get('depth_level', 'unknown')
                            depth_levels[depth_level] = depth_levels.get(depth_level, 0) + 1
                
                if answer_types:
                    print(f"\n🔍 答案类型分布:")
                    for answer_type, count in sorted(answer_types.items(), key=lambda x: x[1], reverse=True):
                        print(f"  • {answer_type}: {count} 个问题")
                
                if depth_levels:
                    print(f"\n🎯 深度级别分布:")
                    for depth, count in sorted(depth_levels.items()):
                        print(f"  • {depth}: {count} 个问题")
            
            print(f"\n💾 详细结果保存: {experiment.experiment_dir}")
            print(f"📋 生成方法: Answer-to-Query + LLM深度设计")
            print("="*60)
            
            return True
            
        except Exception as e:
            print(f"\n❌ Answer-to-Query实验失败: {e}")
            print("\n🔧 可能的解决方案:")
            print("  1. 检查API密钥配置和网络连接")
            print("  2. 确认数据目录存在ClueWeb22数据")
            print("  3. 降低主题数量或问题数量")
            print("  4. 查看详细错误日志")
            return False
    
    def run_standard_experiment(self, mode: str, data_source: str, custom_config: Optional[Dict] = None):
        """运行标准实验 - 用于完整生产运行"""
        print(f"\n🚀 启动{mode}模式实验 (Answer-to-Query Enhanced)")
        print(f"📊 数据源: {data_source}")
        print("-" * 50)
        
        try:
            # 创建实验实例
            experiment = FinalOptimizedExperiment(self.results_dir)
            
            # 应用自定义配置
            if custom_config:
                experiment.config.update(custom_config)
                print("⚙️ 应用自定义配置")
            
            # 显示配置摘要
            print("📋 实验配置摘要:")
            print(f"  • 问题生成方法: Answer-to-Query + LLM深度设计")
            print(f"  • 问题数/主题: {experiment.config['questions_per_topic']}")
            print(f"  • BrowseComp目标: {experiment.config['min_browsecomp_ratio']:.0%}")
            print(f"  • 最大答案长度: {experiment.config['max_answer_words']} 词")
            print(f"  • 事实提取类型: 7种 (数字、日期、人名、地点、方法、术语、比较)")
            print()
            
            # 运行实验
            result = experiment.run_experiment(mode, data_source)
            
            # 显示结果摘要
            print("\n" + "="*60)
            print("🎉 Answer-to-Query标准实验完成!")
            print("="*60)
            
            stats = result['aggregated_statistics']
            summary = result['summary']
            
            print(f"📈 成功率: {summary['success_rate']:.2%}")
            print(f"📊 总问题数: {stats['total_questions_generated']}")
            print(f"🎯 BrowseComp问题: {stats['total_browsecomp_questions']} ({stats.get('avg_browsecomp_ratio', 0):.2%})")
            print(f"🔗 平均约束数: {stats['avg_constraints_per_question']:.2f}")
            print(f"📝 平均答案长度: {stats['avg_answer_words']:.1f} 词")
            print(f"⏱️ 总处理时间: {summary['total_processing_time']:.1f} 秒")
            print(f"📊 处理主题数: {summary.get('successful_topics', 0)}")
            print(f"💾 结果保存: {experiment.experiment_dir}")
            print(f"📋 生成方法: Answer-to-Query Enhanced")
            print("="*60)
            
            return True
            
        except Exception as e:
            print(f"\n❌ 标准实验运行失败: {e}")
            print("\n🔧 可能的解决方案:")
            print("  1. 检查API密钥配置")
            print("  2. 验证数据文件存在")
            print("  3. 检查网络连接")
            print("  4. 降低质量要求或问题数量")
            return False
    
    def run_adaptive_optimization(self, custom_config: Optional[Dict] = None):
        """运行自适应优化"""
        print("\n🔄 启动自适应优化模式")
        print("-" * 40)
        
        try:
            # 配置自适应优化参数
            config = AdaptiveOptimizationConfig(
                min_report_quality_score=0.65,
                target_success_rate=0.80,
                max_optimization_iterations=5,
                aggressive_optimization_threshold=0.30
            )
            
            # 应用自定义配置
            if custom_config:
                if 'min_report_quality_score' in custom_config:
                    config.min_report_quality_score = custom_config['min_report_quality_score']
                if 'target_success_rate' in custom_config:
                    config.target_success_rate = custom_config.get('target_success_rate', 0.80)
            
            print("⚙️ 自适应优化配置:")
            print(f"  • 目标成功率: {config.target_success_rate:.0%}")
            print(f"  • 最小质量分数: {config.min_report_quality_score}")
            print(f"  • 最大优化轮次: {config.max_optimization_iterations}")
            print(f"  • 激进优化阈值: {config.aggressive_optimization_threshold:.0%}")
            print()
            
            # 创建框架和实验
            framework = ComprehensiveAdaptiveFramework(self.results_dir, config)
            experiment = FinalOptimizedExperiment(self.results_dir)
            
            # 应用自定义实验配置
            if custom_config:
                experiment.config.update({k: v for k, v in custom_config.items() 
                                        if k not in ['min_report_quality_score', 'target_success_rate']})
            
            print("🔄 开始自适应优化循环...")
            print()
            
            # 运行优化
            cycle_results = framework.run_adaptive_optimization_cycle(experiment)
            
            print("\n" + "="*50)
            print("✅ 自适应优化完成!")
            print("="*50)
            print(f"🔄 优化轮次: {len(cycle_results.get('optimization_history', []))}")
            print(f"📈 最终成功率: {cycle_results.get('final_success_rate', 0):.2%}")
            print(f"🎯 性能提升: {cycle_results.get('performance_improvement', 0):.2%}")
            print(f"💾 结果保存: {framework.experiment_dir}")
            print("="*50)
            
            return True
            
        except Exception as e:
            print(f"\n❌ 自适应优化失败: {e}")
            print("\n🔧 可能的解决方案:")
            print("  1. 降低目标成功率")
            print("  2. 增加优化轮次限制")
            print("  3. 检查系统资源")
            return False
    
    def modify_config(self):
        """修改配置"""
        print("\n🔧 Answer-to-Query配置修改")
        print("-" * 40)
        print("(按回车保持当前值)")
        print()
        
        experiment = FinalOptimizedExperiment(self.results_dir)
        config = experiment.config.copy()
        
        # 核心配置项修改
        try:
            # 问题数量
            questions_input = input(f"每主题问题数 [{config['questions_per_topic']}]: ").strip()
            if questions_input:
                config['questions_per_topic'] = int(questions_input)
            
            # BrowseComp比例
            browsecomp_input = input(f"最小BrowseComp比例 0-1 [{config['min_browsecomp_ratio']}]: ").strip()
            if browsecomp_input:
                config['min_browsecomp_ratio'] = float(browsecomp_input)
            
            # 答案长度
            words_input = input(f"最大答案字数 [{config['max_answer_words']}]: ").strip()
            if words_input:
                config['max_answer_words'] = int(words_input)
            
            self.current_config = config
            print("\n✅ 配置更新成功！")
            print("💡 Answer-to-Query系统会自动应用新配置")
            
        except ValueError as e:
            print(f"❌ 配置格式错误: {e}")
            print("配置未更改")
            
    def configure_api_keys(self):
        """配置API密钥"""
        print("\n🔑 API密钥配置")
        print("-" * 30)
        print("支持的API提供商:")
        print("  1. OpenAI (GPT-4) - 推荐")
        print("  2. Anthropic (Claude)")
        print()
        
        try:
            choice = self.get_user_choice("请选择API提供商", ["1", "2"], "1")
            
            if choice == "1":
                print("\n🔧 配置OpenAI API密钥")
                print("请前往 https://platform.openai.com/api-keys 获取API密钥")
                api_key = input("请输入OpenAI API密钥: ").strip()
                
                if api_key:
                    os.environ['OPENAI_API_KEY'] = api_key
                    print("✅ OpenAI API密钥配置成功！")
                    self.api_keys_configured = True
                else:
                    print("❌ API密钥为空，配置失败")
                    
            elif choice == "2":
                print("\n🔧 配置Anthropic Claude API密钥")
                print("请前往 https://console.anthropic.com/ 获取API密钥")
                api_key = input("请输入Anthropic API密钥: ").strip()
                
                if api_key:
                    os.environ['ANTHROPIC_API_KEY'] = api_key
                    print("✅ Anthropic API密钥配置成功！")
                    self.api_keys_configured = True
                else:
                    print("❌ API密钥为空，配置失败")
            
            # 验证配置
            if self.api_keys_configured:
                print("\n🧪 验证API配置...")
                try:
                    from final_optimized_experiment import FinalOptimizedExperiment
                    experiment = FinalOptimizedExperiment(self.results_dir)
                    print("✅ API配置验证成功！")
                except Exception as e:
                    print(f"⚠️ API配置可能有问题: {e}")
                    
        except Exception as e:
            print(f"❌ 配置过程中发生错误: {e}")
    
    def check_api_keys(self):
        """检查API密钥是否已配置"""
        openai_key = os.getenv('OPENAI_API_KEY')
        claude_key = os.getenv('ANTHROPIC_API_KEY')
        
        self.api_keys_configured = bool(openai_key or claude_key)
        return self.api_keys_configured
    
    def run(self):
        """主运行循环"""
        self.print_banner()
        
        # 初始检查API密钥
        self.check_api_keys()
        
        while True:
            try:
                self.show_main_menu()
                choice = self.get_user_choice("请选择", ["1", "2", "3", "4", "5", "6", "0"])
                
                if choice == "0":
                    print("\n👋 感谢使用！再见！")
                    break
                    
                elif choice == "1":  # Answer-to-Query实验
                    # 检查API密钥
                    if not self.api_keys_configured:
                        print("\n⚠️ 需要先配置API密钥才能运行实验")
                        api_choice = self.get_user_choice("是否现在配置API密钥? (y/n)", ["y", "n"], "y")
                        if api_choice == "y":
                            self.configure_api_keys()
                        if not self.api_keys_configured:
                            continue
                    
                    print()
                    # 选择数据源
                    self.show_data_source_menu()
                    data_choice = self.get_user_choice("请选择数据源", ["1", "2"], "1")
                    data_source = "clueweb" if data_choice == "1" else "academic"
                    
                    print()
                    # 选择实验规模
                    self.show_scale_menu()
                    scale_choice = self.get_user_choice("请选择实验规模", ["1", "2", "3", "4"], "1")
                    
                    if scale_choice == "1":
                        num_topics = 3  # 小规模
                    elif scale_choice == "2":  
                        num_topics = 9  # 中等规模
                    elif scale_choice == "3":
                        num_topics = 20 # 大规模
                    elif scale_choice == "4":
                        try:
                            num_topics = int(input("请输入主题数量 (1-100): ").strip())
                            if num_topics < 1 or num_topics > 100:
                                print("❌ 主题数量必须在1-100之间")
                                continue
                        except ValueError:
                            print("❌ 请输入有效的数字")
                            continue
                    
                    print(f"\n🎯 将运行Answer-to-Query增强实验: {num_topics}个主题")
                    confirm = self.get_user_choice("确认开始? (y/n)", ["y", "n"], "y")
                    if confirm == "y":
                        self.run_answer_to_query_experiment(data_source, num_topics, self.current_config)
                    
                elif choice == "2":  # 完整生产运行
                    # 检查API密钥
                    if not self.api_keys_configured:
                        print("\n⚠️ 需要先配置API密钥才能运行生产模式")
                        api_choice = self.get_user_choice("是否现在配置API密钥? (y/n)", ["y", "n"], "y")
                        if api_choice == "y":
                            self.configure_api_keys()
                        if not self.api_keys_configured:
                            continue
                    
                    print()
                    self.show_data_source_menu()
                    data_choice = self.get_user_choice("请选择数据源", ["1", "2"], "1")
                    data_source = "clueweb" if data_choice == "1" else "academic"
                    
                    print("\n⚠️ 完整生产运行将处理所有文档，可能需要数小时")
                    confirm = self.get_user_choice("确认开始完整运行? (y/n)", ["y", "n"], "n")
                    if confirm == "y":
                        self.run_standard_experiment("full", data_source, self.current_config)
                    
                elif choice == "3":  # 查看配置
                    self.show_current_config()
                    
                elif choice == "4":  # 修改配置
                    self.modify_config()
                    
                elif choice == "5":  # 配置API密钥
                    self.configure_api_keys()
                    
                elif choice == "6":  # 帮助
                    self.show_help()
                
                # 等待用户确认继续
                if choice != "0":
                    input("\n按回车键继续...")
                    
            except KeyboardInterrupt:
                print("\n\n⚠️ 用户中断，程序退出")
                break
            except Exception as e:
                print(f"\n❌ 发生错误: {e}")
                input("按回车键继续...")

def main():
    """主函数"""
    runner = UnifiedExperimentRunner()
    runner.run()

if __name__ == "__main__":
    main() 
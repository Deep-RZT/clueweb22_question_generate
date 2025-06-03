#!/usr/bin/env python3
"""
Complete 200-Question Enhanced Energy Dataset Generation
基于新Claude API和RAG融合的完整数据集生成
"""

from enhanced_generation_system import EnhancedEnergyGenerator
import sys

def main():
    """生成完整的200问题数据集"""
    
    print("🔋 完整能源领域数据集生成系统")
    print("=" * 70)
    print("目标: 生成200个高质量能源问题 + RAG融合ground truth答案")
    print("特点: 新Claude API + 588篇文献支撑 + 多维度质量评估")
    print("=" * 70)
    
    # 确认用户准备
    print("\n⚠️  注意事项:")
    print("  • 预计生成时间: 约30-40分钟")
    print("  • API调用次数: 约400次 (200问题 + 200答案)")
    print("  • 输出文件: JSON + Excel格式")
    print("  • 文献支撑: 基于588篇真实研究论文")
    
    user_input = input("\n是否继续生成完整数据集? (y/N): ").strip().lower()
    
    if user_input not in ['y', 'yes']:
        print("❌ 用户取消生成")
        return
    
    # 初始化生成器
    api_key = "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"
    
    try:
        print("\n🔧 初始化增强生成系统...")
        generator = EnhancedEnergyGenerator(api_key)
        
        print("\n🚀 开始生成200问题完整数据集...")
        results = generator.generate_enhanced_dataset(num_questions=200)
        
        if results:
            print(f"\n💾 保存结果...")
            json_file, excel_file = generator.save_enhanced_dataset(results)
            
            # 生成最终统计
            stats = generator.calculate_dataset_statistics(results)
            
            print(f"\n📊 最终数据集统计:")
            print(f"   总问题数: {stats['total_questions']}")
            print(f"   平均质量分: {stats['quality_metrics']['average_quality_score']:.3f}")
            print(f"   平均词数: {stats['quality_metrics']['average_word_count']:.0f}")
            print(f"   文献覆盖率: {stats['literature_coverage']['coverage_percentage']:.1f}%")
            
            print(f"\n🎯 数据集生成完成!")
            print(f"   JSON文件: {json_file}")
            if excel_file:
                print(f"   Excel文件: {excel_file}")
            
            print(f"\n✅ 可用于FastText训练的高质量ground truth数据集已生成!")
            
            # 显示难度和子领域分布
            print(f"\n📈 数据分布:")
            print(f"   难度分布: {stats['difficulty_distribution']}")
            print(f"   子领域分布: {stats['subdomain_distribution']}")
            print(f"   答案方法: {stats['answer_methods']}")
        
        else:
            print("❌ 数据集生成失败")
    
    except KeyboardInterrupt:
        print("\n⚠️ 用户中断生成过程")
        print("   部分结果可能已保存在临时文件中")
    except Exception as e:
        print(f"❌ 系统错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 
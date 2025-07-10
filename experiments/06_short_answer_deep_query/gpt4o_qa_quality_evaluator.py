#!/usr/bin/env python3
"""
GPT-4o Question-Answer Quality Evaluator
=========================================

使用GPT-4o评判自己生成的问答对质量的系统。
虽然存在"自己评价自己"的主观性，但可以作为质量检查的参考维度。

作者: Assistant
日期: 2025-01-08
版本: v1.0
"""

import json
import logging
import time
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class QAQualityMetrics:
    """问答质量评分数据类"""
    question_clarity: float        # 问题清晰度 (0-1)
    question_specificity: float    # 问题具体性 (0-1)
    answer_accuracy: float         # 答案准确性 (0-1)
    answer_completeness: float     # 答案完整性 (0-1)
    browsecomp_adherence: float    # BrowseComp方法论符合度 (0-1)
    overall_score: float           # 综合评分 (0-1)
    grade: str                     # 等级评定 (A/B/C/D/F)
    detailed_feedback: str         # 详细反馈

class GPT4oQAQualityEvaluator:
    """GPT-4o问答质量评判器"""
    
    def __init__(self, llm_manager):
        """初始化评判器"""
        self.llm_manager = llm_manager
        self.evaluation_template = self._create_evaluation_template()
        
    def _create_evaluation_template(self) -> str:
        """创建评判提示词模板"""
        return """你是一位专业的问答质量评判专家。请客观评价以下基于报告内容生成的问答对质量。

**评判标准**：

1. **问题清晰度** (0-10分)：问题表述是否清晰明确，无歧义
2. **问题具体性** (0-10分)：是否符合BrowseComp"高约束、多限定"要求
3. **答案准确性** (0-10分)：答案是否准确回答了问题，基于报告内容
4. **答案完整性** (0-10分)：答案是否完整但简洁，符合短答案要求
5. **BrowseComp符合度** (0-10分)：是否符合"难以找到但容易验证"的原则

**参考报告**：
{report}

**待评判的问答对**：
{qa_pairs}

请按以下JSON格式输出评判结果：
{{
    "evaluations": [
        {{
            "question_index": 1,
            "question_clarity": 8.5,
            "question_specificity": 9.0,
            "answer_accuracy": 7.5,
            "answer_completeness": 8.0,
            "browsecomp_adherence": 8.5,
            "overall_score": 8.3,
            "grade": "B",
            "strengths": ["问题表述清晰", "约束明确"],
            "weaknesses": ["答案可以更精确"],
            "suggestions": ["建议缩短答案长度"]
        }}
    ],
    "overall_assessment": {{
        "avg_question_clarity": 8.2,
        "avg_question_specificity": 8.7,
        "avg_answer_accuracy": 7.8,
        "avg_answer_completeness": 8.1,
        "avg_browsecomp_adherence": 8.4,
        "overall_avg_score": 8.2,
        "overall_grade": "B",
        "general_feedback": "整体质量良好，建议进一步优化答案精确度"
    }}
}}

注意：
- 分数范围0-10，对应等级：A(9-10), B(7-9), C(5-7), D(3-5), F(0-3)
- 重点评判是否符合"短答案深度查询"的要求
- 考虑BrowseComp方法论的"倒置问题"特征
"""

    def evaluate_qa_pairs(self, report: str, qa_pairs: List[Dict[str, Any]], 
                         sample_size: int = 10) -> Dict[str, Any]:
        """评判问答对质量"""
        
        logger.info(f"🤖 开始GPT-4o质量评判，样本数量: {min(sample_size, len(qa_pairs))}")
        
        # 采样评判（避免过长输入）
        sample_pairs = qa_pairs[:sample_size] if len(qa_pairs) > sample_size else qa_pairs
        
        # 格式化问答对
        formatted_pairs = []
        for i, qa in enumerate(sample_pairs, 1):
            formatted_pairs.append(f"""
{i}. 问题: {qa['question']}
   答案: {qa['answer']}
""")
        
        qa_text = "\n".join(formatted_pairs)
        
        # 构建评判提示
        prompt = self.evaluation_template.format(
            report=report[:2000],  # 限制报告长度
            qa_pairs=qa_text
        )
        
        try:
            start_time = time.time()
            api_response = self.llm_manager.generate_text(prompt)
            evaluation_time = time.time() - start_time
            
            if not api_response.success:
                raise Exception(f"LLM调用失败: {api_response.error}")
            
            response = api_response.content
            
            # 解析评判结果
            evaluation_data = self._parse_evaluation_response(response)
            
            # 添加元数据
            evaluation_data['meta'] = {
                'sample_size': len(sample_pairs),
                'total_qa_pairs': len(qa_pairs),
                'evaluation_time': evaluation_time,
                'evaluator': 'GPT-4o-self'
            }
            
            logger.info(f"✅ GPT-4o评判完成，整体评分: {evaluation_data.get('overall_assessment', {}).get('overall_avg_score', 0):.1f}/10")
            
            return evaluation_data
            
        except Exception as e:
            logger.error(f"❌ GPT-4o质量评判失败: {e}")
            return self._create_fallback_evaluation(sample_pairs)
    
    def _parse_evaluation_response(self, response: str) -> Dict[str, Any]:
        """解析GPT-4o的评判响应"""
        try:
            # 提取JSON部分
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0].strip()
            else:
                json_str = response.strip()
            
            # 清理格式问题
            json_str = json_str.replace('\n', ' ').replace('\r', '')
            json_str = json_str.replace(',}', '}').replace(',]', ']')
            
            evaluation_data = json.loads(json_str)
            
            # 验证数据结构
            if 'evaluations' not in evaluation_data or 'overall_assessment' not in evaluation_data:
                raise ValueError("评判响应格式不正确")
            
            return evaluation_data
            
        except Exception as e:
            logger.warning(f"解析GPT-4o评判响应失败: {e}")
            return self._extract_evaluation_fallback(response)
    
    def _extract_evaluation_fallback(self, response: str) -> Dict[str, Any]:
        """备用评判结果提取"""
        # 简单的文本分析备用方案
        lines = response.lower().split('\n')
        
        # 尝试提取分数
        scores = []
        for line in lines:
            if any(keyword in line for keyword in ['分数', 'score', '评分', '分']):
                # 提取数字
                import re
                numbers = re.findall(r'(\d+\.?\d*)', line)
                for num in numbers:
                    try:
                        score = float(num)
                        if 0 <= score <= 10:
                            scores.append(score)
                    except:
                        continue
        
        avg_score = sum(scores) / len(scores) if scores else 6.0
        grade = self._score_to_grade(avg_score)
        
        return {
            'evaluations': [],
            'overall_assessment': {
                'avg_question_clarity': avg_score,
                'avg_question_specificity': avg_score,
                'avg_answer_accuracy': avg_score,
                'avg_answer_completeness': avg_score,
                'avg_browsecomp_adherence': avg_score,
                'overall_avg_score': avg_score,
                'overall_grade': grade,
                'general_feedback': f"基于文本分析的估算评分: {avg_score:.1f}/10"
            }
        }
    
    def _create_fallback_evaluation(self, qa_pairs: List[Dict]) -> Dict[str, Any]:
        """创建备用评判结果"""
        return {
            'evaluations': [],
            'overall_assessment': {
                'avg_question_clarity': 6.0,
                'avg_question_specificity': 6.0,
                'avg_answer_accuracy': 6.0,
                'avg_answer_completeness': 6.0,
                'avg_browsecomp_adherence': 6.0,
                'overall_avg_score': 6.0,
                'overall_grade': 'C',
                'general_feedback': '评判系统暂时不可用，使用默认中等评分'
            },
            'meta': {
                'sample_size': len(qa_pairs),
                'total_qa_pairs': len(qa_pairs),
                'evaluation_time': 0,
                'evaluator': 'fallback'
            }
        }
    
    def _score_to_grade(self, score: float) -> str:
        """分数转换为等级"""
        if score >= 9:
            return 'A'
        elif score >= 7:
            return 'B'
        elif score >= 5:
            return 'C'
        elif score >= 3:
            return 'D'
        else:
            return 'F'
    
    def generate_quality_report(self, evaluation_data: Dict[str, Any]) -> str:
        """生成质量评判报告"""
        
        overall = evaluation_data.get('overall_assessment', {})
        meta = evaluation_data.get('meta', {})
        
        report = f"""
# GPT-4o问答质量评判报告

## 📊 总体评分

**整体评级**: {overall.get('overall_grade', 'N/A')} ({overall.get('overall_avg_score', 0):.1f}/10)

### 分项评分
- 🎯 问题清晰度: {overall.get('avg_question_clarity', 0):.1f}/10
- 🔍 问题具体性: {overall.get('avg_question_specificity', 0):.1f}/10  
- ✅ 答案准确性: {overall.get('avg_answer_accuracy', 0):.1f}/10
- 📝 答案完整性: {overall.get('avg_answer_completeness', 0):.1f}/10
- 🎪 BrowseComp符合度: {overall.get('avg_browsecomp_adherence', 0):.1f}/10

## 💭 总体反馈

{overall.get('general_feedback', '暂无反馈')}

## 📈 评判元数据

- 评判样本: {meta.get('sample_size', 0)}/{meta.get('total_qa_pairs', 0)} 个问答对
- 评判时间: {meta.get('evaluation_time', 0):.1f} 秒
- 评判器: {meta.get('evaluator', 'Unknown')}

## 🤔 自我评判的局限性

1. **主观性**: GPT-4o评判自己生成的内容可能存在偏见
2. **一致性**: 同一个模型的自我评判可能过于宽松或严格
3. **参考意义**: 应结合算法评估和人工抽查使用

## 💡 建议

- 将此评判作为质量参考，不作为唯一标准
- 结合算法指标(BrowseComp比例、约束检测等)综合判断
- 定期进行人工抽查验证评判准确性
"""
        
        return report


def test_gpt4o_evaluator():
    """测试GPT-4o评判器"""
    # 模拟LLM管理器
    class MockLLMManager:
        def generate_text(self, prompt):
            class MockResponse:
                success = True
                content = '''```json
{
    "evaluations": [
        {
            "question_index": 1,
            "question_clarity": 8.5,
            "question_specificity": 9.0,
            "answer_accuracy": 7.5,
            "answer_completeness": 8.0,
            "browsecomp_adherence": 8.5,
            "overall_score": 8.3,
            "grade": "B",
            "strengths": ["问题表述清晰", "约束明确"],
            "weaknesses": ["答案可以更精确"],
            "suggestions": ["建议缩短答案长度"]
        }
    ],
    "overall_assessment": {
        "avg_question_clarity": 8.5,
        "avg_question_specificity": 9.0,
        "avg_answer_accuracy": 7.5,
        "avg_answer_completeness": 8.0,
        "avg_browsecomp_adherence": 8.5,
        "overall_avg_score": 8.3,
        "overall_grade": "B",
        "general_feedback": "整体质量良好，问题具体性强，建议优化答案精确度"
    }
}
```'''
            return MockResponse()
    
    # 测试数据
    test_report = "这是一份关于人工智能技术发展的研究报告。报告显示，2023年AI技术在多个领域取得突破..."
    test_qa_pairs = [
        {
            "question": "According to the report, what percentage of AI breakthroughs occurred in 2023?",
            "answer": "75%"
        },
        {
            "question": "Which specific technology was mentioned as the most promising?",
            "answer": "Large Language Models"
        }
    ]
    
    # 运行测试
    evaluator = GPT4oQAQualityEvaluator(MockLLMManager())
    result = evaluator.evaluate_qa_pairs(test_report, test_qa_pairs)
    
    print("=== GPT-4o质量评判测试结果 ===")
    print(f"整体评分: {result['overall_assessment']['overall_avg_score']}")
    print(f"整体等级: {result['overall_assessment']['overall_grade']}")
    print(f"反馈: {result['overall_assessment']['general_feedback']}")
    
    # 生成报告
    report = evaluator.generate_quality_report(result)
    print("\n=== 质量报告 ===")
    print(report)


if __name__ == "__main__":
    test_gpt4o_evaluator() 
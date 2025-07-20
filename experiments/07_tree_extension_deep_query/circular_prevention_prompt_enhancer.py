#!/usr/bin/env python3
"""
循环预防提示词增强器
在问题生成阶段就预防循环提问，而不是依赖后期检测

核心思想：通过提示词设计，在源头上避免循环问题的产生
"""

import logging
from typing import List, Dict, Set, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class HistoricalContext:
    """历史问题上下文"""
    questions: List[str]
    answers: List[str]
    question_types: List[str]  # what, when, where, who, which
    answer_types: List[str]    # name, date, location, etc.
    key_patterns: Set[str]     # 关键模式

class CircularPreventionPromptEnhancer:
    """循环预防提示词增强器"""
    
    def __init__(self):
        self.circular_patterns = self._initialize_circular_patterns()
        self.prevention_strategies = self._initialize_prevention_strategies()
    
    def _initialize_circular_patterns(self) -> Dict[str, List[str]]:
        """初始化已知的循环模式"""
        return {
            'temporal_circular': [
                "A事件发生于B年 vs A事件发生于哪一年",
                "X在Y时间做了什么 vs X什么时候做了这件事",
                "A在B年发布 vs A什么时候发布"
            ],
            'entity_property_circular': [
                "A的属性是B vs A具有什么属性",
                "A由B公司开发 vs A是由哪家公司开发的",
                "A的特征是B vs A有什么特征"
            ],
            'reverse_relationship': [
                "A导致了B vs 什么导致了B",
                "A包含B vs B属于什么",
                "A影响了B vs B受到什么影响"
            ],
            'synonym_repetition': [
                "A的创始人是B vs A的建立者是谁",
                "A的发明者是B vs A是谁发明的",
                "A的制造商是B vs A是谁制造的"
            ]
        }
    
    def _initialize_prevention_strategies(self) -> Dict[str, str]:
        """初始化预防策略"""
        return {
            'aspect_diversification': "Focus on different aspects (technical, historical, impact, context)",
            'granularity_variation': "Vary question granularity (specific details vs broader context)",
            'perspective_shift': "Change perspective (who, what, when, where, why)",
            'relationship_exploration': "Explore different relationships (causal, temporal, spatial, hierarchical)",
            'domain_extension': "Extend to related domains or parallel concepts"
        }
    
    def enhance_root_question_prompt(self, base_prompt: str, document_content: str, 
                                   short_answer: str, answer_type: str) -> str:
        """增强根问题生成提示词，预防循环"""
        
        # 分析答案类型，预测可能的循环模式
        potential_circles = self._predict_circular_risks(short_answer, answer_type, document_content)
        
        # 生成预防指导
        prevention_guidance = self._generate_prevention_guidance(potential_circles, "root")
        
        enhanced_prompt = f"""{base_prompt}

🔄 CIRCULAR QUESTION PREVENTION GUIDANCE:
Based on the answer type "{answer_type}" and content "{short_answer}", be aware of these potential circular patterns:

{prevention_guidance}

CRITICAL PREVENTION RULES:
1. AVOID TEMPORAL CIRCULARITY: Don't create time-based questions if the answer contains temporal information
   ❌ BAD: If answer is "2021" → Don't ask "When was X launched?"
   ✅ GOOD: If answer is "2021" → Ask "What milestone occurred in the year of cryptocurrency boom?"

2. AVOID ENTITY-PROPERTY CIRCULARITY: Don't ask for properties when the answer IS the property
   ❌ BAD: If answer is "SpaceX" → Don't ask "Which company launched X?"
   ✅ GOOD: If answer is "SpaceX" → Ask "What aerospace firm pioneered reusable rocket technology?"

3. AVOID REVERSE RELATIONSHIP CIRCULARITY: Don't create inverse question-answer pairs
   ❌ BAD: If you have "A developed B" → Don't ask "Who developed B?"
   ✅ GOOD: If you have "A developed B" → Ask "What innovation emerged from A's research?"

4. USE ABSTRACTION AND INDIRECTION: Make questions more indirect and abstract
   ✅ STRATEGY: Use descriptive phrases instead of direct terms
   ✅ STRATEGY: Reference context, impact, or relationships rather than direct attributes

GENERATION STRATEGY FOR THIS SPECIFIC CASE:
- Answer: "{short_answer}"
- Type: "{answer_type}"
- Prevention Focus: {self._get_primary_prevention_focus(answer_type)}

Remember: Create a question that requires knowledge and reasoning, not just recall of stated facts."""

        return enhanced_prompt
    
    def enhance_child_question_prompt(self, base_prompt: str, parent_question: str,
                                    parent_answer: str, target_keyword: str,
                                    historical_context: HistoricalContext) -> str:
        """增强子问题生成提示词，预防循环"""
        
        # 分析历史上下文，识别已有模式
        existing_patterns = self._analyze_existing_patterns(historical_context)
        
        # 预测与父问题的潜在循环
        parent_circular_risks = self._predict_parent_child_circular_risks(
            parent_question, parent_answer, target_keyword
        )
        
        # 预测与历史问题的潜在循环
        historical_circular_risks = self._predict_historical_circular_risks(
            target_keyword, existing_patterns
        )
        
        # 生成综合预防指导
        prevention_guidance = self._generate_comprehensive_prevention_guidance(
            parent_circular_risks, historical_circular_risks, existing_patterns
        )
        
        enhanced_prompt = f"""{base_prompt}

🔄 ADVANCED CIRCULAR PREVENTION FOR CHILD QUESTIONS:

PARENT CONTEXT ANALYSIS:
- Parent Question: {parent_question}
- Parent Answer: {parent_answer}
- Target Keyword: {target_keyword}

HISTORICAL PATTERN ANALYSIS:
{self._format_historical_patterns(existing_patterns)}

CIRCULAR RISK ASSESSMENT:
{prevention_guidance}

SPECIFIC PREVENTION STRATEGIES FOR THIS CASE:

1. PARENT-CHILD CIRCULAR PREVENTION:
   {self._format_parent_child_prevention(parent_circular_risks)}

2. HISTORICAL PATTERN AVOIDANCE:
   {self._format_historical_prevention(historical_circular_risks)}

3. DIVERSIFICATION REQUIREMENTS:
   - Use different question type than: {', '.join(historical_context.question_types[-3:])}
   - Avoid answer types similar to: {', '.join(historical_context.answer_types[-3:])}
   - Explore aspects NOT covered in previous questions

MANDATORY CHECKS BEFORE GENERATING:
✓ Does my question avoid repeating parent question patterns?
✓ Does my question explore a genuinely different aspect?
✓ Would someone familiar with previous questions find this fresh and non-repetitive?
✓ Am I using sufficiently abstract/indirect language to avoid obvious patterns?

CREATIVE REDIRECTION STRATEGIES:
{self._generate_creative_strategies(target_keyword, existing_patterns)}

Generate a question that someone reviewing all previous questions would consider genuinely novel and non-circular."""

        return enhanced_prompt
    
    def _predict_circular_risks(self, answer: str, answer_type: str, context: str) -> List[str]:
        """预测潜在的循环风险"""
        risks = []
        
        answer_lower = answer.lower()
        
        # 时间相关风险
        if answer_type in ['date', 'year', 'time'] or any(term in answer_lower for term in ['year', 'month', 'day', '20', '19']):
            risks.append("temporal_circular")
        
        # 实体相关风险
        if answer_type in ['name', 'company', 'person', 'organization']:
            risks.append("entity_property_circular")
        
        # 数值相关风险
        if answer_type in ['number', 'quantity', 'measurement']:
            risks.append("measurement_circular")
        
        # 位置相关风险
        if answer_type in ['location', 'place', 'country', 'city']:
            risks.append("location_circular")
        
        return risks
    
    def _generate_prevention_guidance(self, risks: List[str], question_level: str) -> str:
        """生成预防指导"""
        guidance_lines = []
        
        for risk in risks:
            if risk == "temporal_circular":
                guidance_lines.append(
                    "⚠️ TEMPORAL RISK: Avoid direct time-based questions. Use contextual descriptions instead."
                )
            elif risk == "entity_property_circular":
                guidance_lines.append(
                    "⚠️ ENTITY RISK: Avoid asking for entity properties. Focus on context, impact, or relationships."
                )
            elif risk == "measurement_circular":
                guidance_lines.append(
                    "⚠️ MEASUREMENT RISK: Avoid direct quantity questions. Ask about significance or comparison."
                )
            elif risk == "location_circular":
                guidance_lines.append(
                    "⚠️ LOCATION RISK: Avoid direct location questions. Focus on events, significance, or characteristics."
                )
        
        return '\n'.join(guidance_lines) if guidance_lines else "No specific circular risks detected."
    
    def _get_primary_prevention_focus(self, answer_type: str) -> str:
        """获取主要预防焦点"""
        focus_map = {
            'date': "Use descriptive phrases for time periods instead of direct temporal questions",
            'name': "Focus on contributions, context, or relationships rather than identity",
            'company': "Emphasize innovations, impact, or industry role rather than ownership",
            'location': "Highlight significance, events, or characteristics rather than geography",
            'number': "Ask about implications, comparisons, or context rather than quantities"
        }
        return focus_map.get(answer_type, "Use abstract and contextual approaches")
    
    def _analyze_existing_patterns(self, historical_context: HistoricalContext) -> Dict[str, any]:
        """分析已有的问题模式"""
        patterns = {
            'question_types_used': set(historical_context.question_types),
            'answer_types_used': set(historical_context.answer_types),
            'common_keywords': self._extract_common_keywords(historical_context.questions),
            'pattern_frequency': self._calculate_pattern_frequency(historical_context)
        }
        return patterns
    
    def _predict_parent_child_circular_risks(self, parent_question: str, parent_answer: str, target_keyword: str) -> List[str]:
        """预测父子问题循环风险"""
        risks = []
        
        parent_lower = parent_question.lower()
        target_lower = target_keyword.lower()
        
        # 检查是否存在反向关系风险
        if target_lower in parent_lower:
            risks.append("reverse_inclusion")
        
        # 检查时间循环风险 - 更精确的检测
        if any(char.isdigit() for char in target_keyword):
            # 如果父问题是关于时间的，而目标关键词是时间相关的
            if any(time_word in parent_lower for time_word in ['when', 'year', 'time', 'date']) or any(year in target_keyword for year in ['19', '20']):
                risks.append("temporal_reverse")
        
        # 检查实体属性循环风险 - 更精确的检测
        if target_keyword.istitle() or any(c.isupper() for c in target_keyword):  # 可能是专有名词
            if any(entity_word in parent_lower for entity_word in ['who', 'which', 'what']):
                # 检查是否是公司、人名等实体
                if any(entity_type in parent_lower for entity_type in ['company', 'organization', 'person', 'inventor', 'founder']):
                    risks.append("entity_reverse")
        
        return risks
    
    def _predict_historical_circular_risks(self, target_keyword: str, existing_patterns: Dict) -> List[str]:
        """预测与历史问题的循环风险"""
        risks = []
        
        # 检查关键词重复
        target_lower = target_keyword.lower()
        common_keywords = existing_patterns.get('common_keywords', set())
        
        if target_lower in common_keywords:
            risks.append("keyword_repetition")
        
        # 检查模式重复
        pattern_freq = existing_patterns.get('pattern_frequency', {})
        if pattern_freq.get('what_questions', 0) > 2:
            risks.append("what_question_overuse")
        if pattern_freq.get('when_questions', 0) > 1:
            risks.append("when_question_overuse")
        
        return risks
    
    def _generate_comprehensive_prevention_guidance(self, parent_risks: List[str], 
                                                  historical_risks: List[str], 
                                                  patterns: Dict) -> str:
        """生成综合预防指导"""
        guidance = []
        
        if parent_risks:
            guidance.append("PARENT-CHILD RISKS:")
            for risk in parent_risks:
                guidance.append(f"  - {risk}: {self._get_risk_explanation(risk)}")
        
        if historical_risks:
            guidance.append("HISTORICAL PATTERN RISKS:")
            for risk in historical_risks:
                guidance.append(f"  - {risk}: {self._get_risk_explanation(risk)}")
        
        return '\n'.join(guidance) if guidance else "No specific risks identified."
    
    def _get_risk_explanation(self, risk: str) -> str:
        """获取风险解释"""
        explanations = {
            "reverse_inclusion": "Target keyword appears in parent question - avoid simple reversal",
            "temporal_reverse": "Risk of time-based circular question - use context instead",
            "entity_reverse": "Risk of entity-focused circular question - focus on relationships",
            "keyword_repetition": "Target keyword used before - ensure different perspective",
            "what_question_overuse": "Too many 'what' questions - try 'which', 'who', or 'where'",
            "when_question_overuse": "Too many temporal questions - explore other aspects"
        }
        return explanations.get(risk, "Unknown risk pattern")
    
    def _format_historical_patterns(self, patterns: Dict) -> str:
        """格式化历史模式"""
        lines = []
        lines.append(f"Question types used: {', '.join(patterns.get('question_types_used', set()))}")
        lines.append(f"Answer types covered: {', '.join(patterns.get('answer_types_used', set()))}")
        lines.append(f"Common keywords: {', '.join(list(patterns.get('common_keywords', set()))[:5])}")
        return '\n'.join(lines)
    
    def _format_parent_child_prevention(self, risks: List[str]) -> str:
        """格式化父子预防策略"""
        if not risks:
            return "No specific parent-child circular risks detected."
        
        strategies = []
        for risk in risks:
            if risk == "reverse_inclusion":
                strategies.append("AVOID: Simply reversing the parent question structure")
            elif risk == "temporal_reverse":
                strategies.append("AVOID: Creating time-based questions when parent involves time")
            elif risk == "entity_reverse":
                strategies.append("AVOID: Asking 'who/what is X' when parent already involves entity questions")
        
        return '\n   '.join(strategies)
    
    def _format_historical_prevention(self, risks: List[str]) -> str:
        """格式化历史预防策略"""
        if not risks:
            return "No historical pattern conflicts detected."
        
        strategies = []
        for risk in risks:
            if risk == "keyword_repetition":
                strategies.append("REQUIREMENT: Use different angle/context for repeated keyword")
            elif risk.endswith("_overuse"):
                question_type = risk.split('_')[0]
                strategies.append(f"REQUIREMENT: Avoid '{question_type}' questions - use alternative question types")
        
        return '\n   '.join(strategies)
    
    def _generate_creative_strategies(self, target_keyword: str, patterns: Dict) -> str:
        """生成创意策略"""
        strategies = []
        
        # 基于关键词类型的策略
        if target_keyword.isdigit() or any(char.isdigit() for char in target_keyword):
            strategies.append("• For numbers: Focus on significance, comparisons, or what the number represents")
        
        if target_keyword[0].isupper():  # 可能是专有名词
            strategies.append("• For proper nouns: Explore context, relationships, or indirect descriptions")
        
        # 基于历史模式的策略
        used_types = patterns.get('question_types_used', set())
        if 'what' not in used_types:
            strategies.append("• Consider 'what' questions for variety")
        if 'which' not in used_types:
            strategies.append("• Consider 'which' questions for specificity")
        if 'who' not in used_types:
            strategies.append("• Consider 'who' questions for human elements")
        
        return '\n'.join(strategies) if strategies else "• Use creative, indirect approaches to avoid repetition"
    
    def _extract_common_keywords(self, questions: List[str]) -> Set[str]:
        """提取常见关键词"""
        # 简单的关键词提取
        all_words = []
        for question in questions:
            words = question.lower().split()
            # 过滤停用词
            meaningful_words = [w for w in words if len(w) > 3 and w not in ['what', 'when', 'where', 'which', 'who', 'how', 'why', 'the', 'and', 'or', 'but', 'for', 'with']]
            all_words.extend(meaningful_words)
        
        # 找出出现频率 >= 2 的词
        from collections import Counter
        word_counts = Counter(all_words)
        return {word for word, count in word_counts.items() if count >= 2}
    
    def _calculate_pattern_frequency(self, historical_context: HistoricalContext) -> Dict[str, int]:
        """计算模式频率"""
        frequency = {}
        
        for q_type in historical_context.question_types:
            key = f"{q_type}_questions"
            frequency[key] = frequency.get(key, 0) + 1
        
        return frequency
    
    def create_historical_context(self, questions: List[str], answers: List[str]) -> HistoricalContext:
        """创建历史上下文"""
        question_types = []
        answer_types = []
        
        for question in questions:
            q_lower = question.lower().strip()
            if q_lower.startswith('what'):
                question_types.append('what')
            elif q_lower.startswith('when'):
                question_types.append('when')
            elif q_lower.startswith('where'):
                question_types.append('where')
            elif q_lower.startswith('who'):
                question_types.append('who')
            elif q_lower.startswith('which'):
                question_types.append('which')
            else:
                question_types.append('other')
        
        for answer in answers:
            # 简单的答案类型判断
            if any(char.isdigit() for char in answer):
                if any(year in answer for year in ['19', '20']) and len(answer) == 4:
                    answer_types.append('year')
                else:
                    answer_types.append('number')
            elif answer[0].isupper() and ' ' not in answer:
                answer_types.append('name')
            elif answer[0].isupper():
                answer_types.append('entity')
            else:
                answer_types.append('other')
        
        return HistoricalContext(
            questions=questions,
            answers=answers,
            question_types=question_types,
            answer_types=answer_types,
            key_patterns=set()
        ) 
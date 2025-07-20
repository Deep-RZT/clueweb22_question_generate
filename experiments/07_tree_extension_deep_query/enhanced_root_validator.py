"""
Enhanced Root Validator for Tree Extension Deep Query Framework
Implements dual-model validation for root questions ensuring specificity, uniqueness, and verifiability.
"""

import logging
import json
import re
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

from config import get_config

# Setup logging
logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Validation result structure"""
    passed: bool
    validity_score: float  # 0.0 - 1.0
    uniqueness_score: float  # 0.0 - 1.0
    specificity_score: float  # 0.0 - 1.0
    overall_score: float  # 0.0 - 1.0
    issues: List[str]
    reasoning: str

class EnhancedRootValidator:
    """Enhanced validator for root questions following strict workflow requirements"""
    
    def __init__(self, api_client=None):
        self.config = get_config()
        self.api_client = api_client
        self.validation_cache = {}
        
    def set_api_client(self, api_client):
        """Set the API client for LLM calls"""
        self.api_client = api_client
        
    def validate_root_question(self, question: str, answer: str, document_content: str) -> ValidationResult:
        """
        Comprehensive root question validation following workflow requirements
        
        Requirements:
        1. Answer must be highly specific (proper nouns, numbers, technical terms)
        2. Answer must be distinctive and not too broad or ambiguous
        3. Answer must be unique and not repeated
        4. Question must have only one correct answer
        5. Question must be solvable and based on document
        """
        logger.info(f"Validating root question: {question[:60]}...")
        
        # Initialize result
        result = ValidationResult(
            passed=False,
            validity_score=0.0,
            uniqueness_score=0.0,
            specificity_score=0.0,
            overall_score=0.0,
            issues=[],
            reasoning=""
        )
        
        try:
            # 1. Answer Specificity Check (关键要求a)
            specificity_check = self._check_answer_specificity(answer)
            result.specificity_score = specificity_check['score']
            if not specificity_check['passed']:
                result.issues.extend(specificity_check['issues'])
            
            # 2. Question Validity Check (双模型验证)
            validity_check = self._dual_model_validity_check(question, answer, document_content)
            result.validity_score = validity_check['score']
            if not validity_check['passed']:
                result.issues.extend(validity_check['issues'])
            
            # 3. Answer Uniqueness Check (双模型验证)
            uniqueness_check = self._dual_model_uniqueness_check(question, answer, document_content)
            result.uniqueness_score = uniqueness_check['score']
            if not uniqueness_check['passed']:
                result.issues.extend(uniqueness_check['issues'])
            
            # 4. Calculate overall score
            result.overall_score = (
                result.specificity_score * 0.4 +
                result.validity_score * 0.3 + 
                result.uniqueness_score * 0.3
            )
            
            # 5. Final pass/fail decision (优化阈值)
            # 生产环境适度降低阈值以提高通过率
            validity_threshold = max(0.6, getattr(self.config, 'validity_threshold', 0.7))
            uniqueness_threshold = max(0.6, getattr(self.config, 'uniqueness_threshold', 0.7))
            overall_threshold = 0.65  # 总体阈值
            
            result.passed = (
                result.specificity_score >= 0.6 and  # 特异性阈值
                result.validity_score >= validity_threshold and
                result.uniqueness_score >= uniqueness_threshold and
                result.overall_score >= overall_threshold
            )
            
            # 6. Generate reasoning
            result.reasoning = self._generate_validation_reasoning(result)
            
            logger.info(f"Validation result: {'PASS' if result.passed else 'FAIL'} (score: {result.overall_score:.2f})")
            
            return result
            
        except Exception as e:
            logger.error(f"Error during validation: {e}")
            result.issues.append(f"Validation error: {str(e)}")
            return result
    
    def _check_answer_specificity(self, answer: str) -> Dict[str, Any]:
        """
        Check if answer meets specificity requirements:
        - Highly specific (proper nouns, numbers, technical terms)
        - Distinctive and not too broad or ambiguous
        - Not repeated/generic
        """
        issues = []
        score = 0.0
        
        # Clean answer
        answer_clean = answer.strip().lower()
        
        # 1. Length check (优化评分分配)
        if len(answer) < 3:
            issues.append("Answer too short (< 3 characters)")
        elif len(answer) < 8:
            score += 0.15  # 提高短答案的基础分
        else:
            score += 0.25  # 提高长答案的基础分
        
        # 2. Check for highly specific types (优先级顺序按workflow)
        specificity_patterns = {
            'proper_nouns': {
                'patterns': [r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'],
                'score': 0.5,  # 提高专有名词分数，因为人名是高特异性的
                'examples': ['James Webb telescope', 'Stanford University', 'Isaac Newton']
            },
            'numbers': {
                'patterns': [r'\d+\.?\d*', r'\$\d+', r'\d+%', r'\d+\s*(million|billion|thousand)'],
                'score': 0.4,  # 数字也是高特异性的
                'examples': ['2023', '$10bn', '94.2%', '500 participants']
            },
            'technical_terms': {
                'patterns': [r'\b[A-Za-z]+(?:-[A-Za-z]+)+\b', r'\b[A-Z]{2,}\b'],
                'score': 0.2,
                'examples': ['machine-learning', 'CNN', 'API']
            },
            'dates': {
                'patterns': [r'\b\d{4}\b', r'\b\d{1,2}/\d{1,2}/\d{4}\b', r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b'],
                'score': 0.4,  # 日期也是高特异性的
                'examples': ['2023', '12/03/2013', 'March 15, 2023']
            },
            'locations': {
                'patterns': [r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+(?:University|College|Institute|Laboratory|Center))\b', r'\b[A-Z][a-z]+,\s*[A-Z][a-z]+\b'],
                'score': 0.25,
                'examples': ['Stanford University', 'New York, NY']
            }
        }
        
        found_specific_type = False
        for type_name, type_data in specificity_patterns.items():
            for pattern in type_data['patterns']:
                if re.search(pattern, answer):
                    score += type_data['score']
                    found_specific_type = True
                    break
            if found_specific_type:
                break
        
        if not found_specific_type:
            issues.append("Answer lacks highly specific elements (proper nouns, numbers, technical terms)")
        
        # 3. Check for problematic generic answers
        generic_answers = [
            'telescope', 'method', 'process', 'system', 'technology', 'approach',
            'technique', 'strategy', 'way', 'manner', 'procedure', 'algorithm',
            'model', 'framework', 'platform', 'tool', 'device', 'instrument'
        ]
        
        if any(generic in answer_clean for generic in generic_answers):
            issues.append("Answer is too generic/broad")
            score -= 0.2
        
        # 4. Check for context-less names (特别针对问题b)
        if len(answer.split()) <= 2:
            # Check if it's just a name without context
            name_patterns = [r'^[A-Z][a-z]+\s+[A-Z][a-z]+$', r'^[A-Z][a-z]+$']
            if any(re.match(pattern, answer) for pattern in name_patterns):
                # Additional check: does it provide meaningful context?
                if not any(keyword in answer.lower() for keyword in ['university', 'institute', 'company', 'corporation', 'laboratory', 'center']):
                    # 对于在科学/技术文档中出现的人名，应该被认为是具体的
                    # 只对明显无意义的通用名字进行惩罚
                    common_generic_names = ['john', 'smith', 'james', 'michael', 'david', 'robert', 'mary', 'patricia', 'jennifer', 'linda']
                    is_generic_name = any(part.lower() in common_generic_names for part in answer.split())
                    
                    if is_generic_name:
                        issues.append("Name appears to be too generic/common")
                        score -= 0.1  # 减少惩罚程度
                    # 对于科学家、专业人士等名字，不进行惩罚
        
        # 5. Ensure score is in valid range
        score = max(0.0, min(1.0, score))
        
        return {
            'passed': score >= 0.6 and len(issues) == 0,  # 降低特异性阈值，因为人名应该被认为是具体的
            'score': score,
            'issues': issues
        }
    
    def _dual_model_validity_check(self, question: str, answer: str, document_content: str) -> Dict[str, Any]:
        """
        Dual-model validity check: question must have only one correct answer and be solvable
        """
        if not self.api_client:
            return {'passed': False, 'score': 0.0, 'issues': ['No API client available']}
        
        # 首先检查问题是否包含答案（严重错误）
        answer_words = set(answer.lower().split())
        question_words = set(question.lower().split())
        overlap = answer_words.intersection(question_words)
        
        # 排除常见停用词
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'was', 'are', 'were'}
        meaningful_overlap = overlap - stop_words
        
        if meaningful_overlap:
            return {
                'passed': False, 
                'score': 0.0, 
                'issues': [f'Question contains answer words: {meaningful_overlap}'],
                'model1_result': {'reasoning': 'Question leaks answer'},
                'model2_result': {'reasoning': 'Question leaks answer'}
            }
        
        try:
            # Model 1: Validity Check (优化提示词)
            validity_prompt = f"""You are Model 1 in a dual-model validation system. Your task is to verify if this question has a valid, unambiguous answer.

QUESTION: {question}
PROPOSED ANSWER: {answer}
DOCUMENT CONTEXT: {document_content[:1500]}

CRITICAL VALIDATION CRITERIA:
1. SINGLE CORRECT ANSWER: Does this question have exactly one correct answer?
   ✅ GOOD: "What telescope was launched in 2021?" → "James Webb Space Telescope"
   ❌ BAD: "What technologies are important?" → Multiple possible answers

2. SOLVABLE: Can this question be answered using the provided document?
   ✅ GOOD: Information clearly stated or inferable from document
   ❌ BAD: Requires outside knowledge not in document

3. UNAMBIGUOUS: Is the question clear and well-formed?
   ✅ GOOD: "Which company developed GPT-4?" → Clear target
   ❌ BAD: "What is the best approach?" → Subjective/vague

4. VERIFIABLE: Can the answer be independently verified?
   ✅ GOOD: Names, dates, numbers, technical terms
   ❌ BAD: Opinions, subjective assessments

5. NO ANSWER LEAKAGE: Does the question avoid revealing the answer directly?
   ✅ GOOD: Question doesn't contain answer words
   ❌ BAD: "Which James Webb telescope was launched?" → Contains "James Webb"

SCORING GUIDE:
- 0.9-1.0: Excellent quality, meets all criteria strongly
- 0.7-0.8: Good quality, meets most criteria well
- 0.5-0.6: Acceptable quality, meets basic requirements
- 0.3-0.4: Poor quality, significant issues
- 0.0-0.2: Very poor quality, fails most criteria

Please respond in JSON format:
{{
    "has_single_answer": true/false,
    "is_solvable": true/false,
    "is_unambiguous": true/false,
    "is_verifiable": true/false,
    "no_answer_leakage": true/false,
    "validity_score": 0.0-1.0,
    "reasoning": "Detailed explanation of your assessment with specific examples"
}}"""

            model1_response = self.api_client.generate_response(
                prompt=validity_prompt,
                temperature=0.2,
                max_tokens=400
            )
            
            # Parse Model 1 response
            model1_result = self._parse_validation_response(model1_response)
            
            # Model 2: Independent Validity Check (优化提示词)
            validity_prompt2 = f"""You are Model 2 in an independent dual-model validation system. Assess this question-answer pair without seeing the first model's response.

QUESTION: {question}
PROPOSED ANSWER: {answer}
DOCUMENT CONTEXT: {document_content[:1500]}

ASSESSMENT REQUIREMENTS:
1. Is this question answerable with a single, definitive response?
   ✅ GOOD: "When was X founded?" → One specific date
   ❌ BAD: "What are the benefits of X?" → Multiple possible answers

2. Does the question require document-based knowledge (not common sense)?
   ✅ GOOD: Specific facts, names, dates from the document
   ❌ BAD: General knowledge everyone knows

3. Is the proposed answer factually correct based on the document?
   ✅ GOOD: Answer directly stated or clearly inferable
   ❌ BAD: Answer contradicts or is not supported by document

4. Would different people consistently arrive at the same answer?
   ✅ GOOD: Objective facts with clear evidence
   ❌ BAD: Subjective interpretations or ambiguous information

QUALITY BENCHMARKS:
- EXCELLENT (0.8-1.0): Clear, specific, well-documented facts
- GOOD (0.6-0.7): Generally reliable with minor ambiguities
- ACCEPTABLE (0.5-0.6): Basic requirements met but not ideal
- POOR (0.0-0.4): Significant issues with clarity or factual basis

Respond in JSON format:
{{
    "single_definitive_answer": true/false,
    "requires_document": true/false,
    "factually_correct": true/false,
    "consistent_answer": true/false,
    "validity_score": 0.0-1.0,
    "reasoning": "Your independent assessment with specific rationale"
}}"""

            model2_response = self.api_client.generate_response(
                prompt=validity_prompt2,
                temperature=0.2,
                max_tokens=400
            )
            
            # Parse Model 2 response
            model2_result = self._parse_validation_response(model2_response, model2=True)
            
            # Combine results (优化组合逻辑)
            combined_score = (model1_result['score'] + model2_result['score']) / 2
            
            # 优化阈值和容错机制
            threshold = 0.6  # 降低阈值
            issues = []
            
            # 允许一定的容错：如果一个模型很好(>=0.75)，另一个稍差也可以接受
            model1_good = model1_result['score'] >= 0.75
            model2_good = model2_result['score'] >= 0.75
            both_acceptable = model1_result['score'] >= 0.5 and model2_result['score'] >= 0.5
            
            if model1_result['score'] < threshold:
                issues.append("Model 1: " + model1_result.get('reasoning', 'Failed validity check'))
            if model2_result['score'] < threshold:
                issues.append("Model 2: " + model2_result.get('reasoning', 'Failed validity check'))
            
            # 通过条件：
            # 1. 组合分数足够高
            # 2. 或者一个模型很好且另一个可接受
            # 3. 或者两个模型都可接受且组合分数不太低
            passed = (
                combined_score >= 0.7 or  # 高组合分数
                (model1_good and model2_result['score'] >= 0.5) or  # M1好，M2可接受
                (model2_good and model1_result['score'] >= 0.5) or  # M2好，M1可接受
                (both_acceptable and combined_score >= 0.55)  # 都可接受且总分不太低
            )
            
            return {
                'passed': passed,
                'score': combined_score,
                'issues': issues,
                'model1_result': model1_result,
                'model2_result': model2_result
            }
            
        except Exception as e:
            logger.error(f"Dual-model validity check failed: {e}")
            return {'passed': False, 'score': 0.0, 'issues': [f'Validation error: {str(e)}']}
    
    def _dual_model_uniqueness_check(self, question: str, answer: str, document_content: str) -> Dict[str, Any]:
        """
        Dual-model uniqueness check: answer must be unique and not ambiguous
        """
        if not self.api_client:
            return {'passed': False, 'score': 0.0, 'issues': ['No API client available']}
        
        try:
            # Model 1: Uniqueness Check
            uniqueness_prompt = f"""You are Model 1 in a dual-model uniqueness validation system. Assess if this answer is unique and unambiguous.

QUESTION: {question}
PROPOSED ANSWER: {answer}
DOCUMENT CONTEXT: {document_content[:1500]}

UNIQUENESS CRITERIA:
1. DISTINCTIVE: Is this answer distinctive and not too broad?
2. NON-AMBIGUOUS: Does this answer refer to a specific, identifiable entity/fact?
3. NOT REPEATED: Is this answer unique within the document context?
4. PRECISE: Is the answer precise enough to distinguish from similar entities?

Respond in JSON format:
{{
    "is_distinctive": true/false,
    "is_non_ambiguous": true/false,
    "is_not_repeated": true/false,
    "is_precise": true/false,
    "uniqueness_score": 0.0-1.0,
    "reasoning": "Detailed assessment of uniqueness"
}}"""

            model1_response = self.api_client.generate_response(
                prompt=uniqueness_prompt,
                temperature=0.2,
                max_tokens=400
            )
            
            model1_result = self._parse_uniqueness_response(model1_response)
            
            # Model 2: Independent Uniqueness Check
            uniqueness_prompt2 = f"""You are Model 2 providing independent uniqueness assessment. Evaluate this answer's uniqueness without seeing other model results.

QUESTION: {question}
PROPOSED ANSWER: {answer}
DOCUMENT CONTEXT: {document_content[:1500]}

INDEPENDENT ASSESSMENT:
1. Could this answer refer to multiple different things?
2. Is this answer sufficiently specific to identify exactly one entity?
3. Are there other possible answers that could be confused with this one?
4. Is this answer clear enough for objective verification?

Respond in JSON format:
{{
    "multiple_referents": true/false,
    "sufficiently_specific": true/false,
    "potential_confusion": true/false,
    "objectively_verifiable": true/false,
    "uniqueness_score": 0.0-1.0,
    "reasoning": "Independent uniqueness evaluation"
}}"""

            model2_response = self.api_client.generate_response(
                prompt=uniqueness_prompt2,
                temperature=0.2,
                max_tokens=400
            )
            
            model2_result = self._parse_uniqueness_response(model2_response, model2=True)
            
            # Combine results
            combined_score = (model1_result['score'] + model2_result['score']) / 2
            
            issues = []
            if model1_result['score'] < 0.7:
                issues.append("Model 1: " + model1_result.get('reasoning', 'Failed uniqueness check'))
            if model2_result['score'] < 0.7:
                issues.append("Model 2: " + model2_result.get('reasoning', 'Failed uniqueness check'))
            
            return {
                'passed': combined_score >= 0.7 and len(issues) == 0,
                'score': combined_score,
                'issues': issues,
                'model1_result': model1_result,
                'model2_result': model2_result
            }
            
        except Exception as e:
            logger.error(f"Dual-model uniqueness check failed: {e}")
            return {'passed': False, 'score': 0.0, 'issues': [f'Uniqueness check error: {str(e)}']}
    
    def _parse_validation_response(self, response: str, model2: bool = False) -> Dict[str, Any]:
        """Parse validation response from LLM"""
        try:
            # Extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_text = response[json_start:json_end]
                data = json.loads(json_text)
                
                if model2:
                    # Model 2 format
                    score = (
                        data.get('single_definitive_answer', False) * 0.2 +
                        data.get('requires_document', False) * 0.2 +
                        data.get('factually_correct', False) * 0.2 +
                        data.get('consistent_answer', False) * 0.2 +
                        data.get('no_answer_leakage', False) * 0.2
                    )
                else:
                    # Model 1 format
                    score = (
                        data.get('has_single_answer', False) * 0.2 +
                        data.get('is_solvable', False) * 0.2 +
                        data.get('is_unambiguous', False) * 0.2 +
                        data.get('is_verifiable', False) * 0.2 +
                        data.get('no_answer_leakage', False) * 0.2
                    )
                
                return {
                    'score': min(1.0, max(0.0, score)),
                    'reasoning': data.get('reasoning', ''),
                    'raw_data': data
                }
            
        except Exception as e:
            logger.warning(f"Failed to parse validation response: {e}")
        
        return {'score': 0.0, 'reasoning': 'Failed to parse response'}
    
    def _parse_uniqueness_response(self, response: str, model2: bool = False) -> Dict[str, Any]:
        """Parse uniqueness response from LLM"""
        try:
            # Extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_text = response[json_start:json_end]
                data = json.loads(json_text)
                
                if model2:
                    # Model 2 format (reverse scoring for negative indicators)
                    score = (
                        (not data.get('multiple_referents', True)) * 0.25 +
                        data.get('sufficiently_specific', False) * 0.25 +
                        (not data.get('potential_confusion', True)) * 0.25 +
                        data.get('objectively_verifiable', False) * 0.25
                    )
                else:
                    # Model 1 format
                    score = (
                        data.get('is_distinctive', False) * 0.25 +
                        data.get('is_non_ambiguous', False) * 0.25 +
                        data.get('is_not_repeated', False) * 0.25 +
                        data.get('is_precise', False) * 0.25
                    )
                
                return {
                    'score': min(1.0, max(0.0, score)),
                    'reasoning': data.get('reasoning', ''),
                    'raw_data': data
                }
            
        except Exception as e:
            logger.warning(f"Failed to parse uniqueness response: {e}")
        
        return {'score': 0.0, 'reasoning': 'Failed to parse response'}
    
    def _generate_validation_reasoning(self, result: ValidationResult) -> str:
        """Generate comprehensive reasoning for validation result"""
        reasoning_parts = []
        
        # Overall assessment
        if result.passed:
            reasoning_parts.append("✅ VALIDATION PASSED - All criteria met")
        else:
            reasoning_parts.append("❌ VALIDATION FAILED - Some criteria not met")
        
        # Detailed scores
        reasoning_parts.append(f"Specificity: {result.specificity_score:.2f}")
        reasoning_parts.append(f"Validity: {result.validity_score:.2f}")
        reasoning_parts.append(f"Uniqueness: {result.uniqueness_score:.2f}")
        reasoning_parts.append(f"Overall: {result.overall_score:.2f}")
        
        # Issues
        if result.issues:
            reasoning_parts.append("Issues found:")
            for issue in result.issues:
                reasoning_parts.append(f"- {issue}")
        
        return "; ".join(reasoning_parts)

    def validate_answer_extraction_quality(self, answer: str, document_content: str) -> Tuple[bool, str]:
        """
        Quick validation for answer extraction quality
        """
        issues = []
        
        # 1. Answer exists in document
        if answer not in document_content:
            issues.append("Answer not found in document")
        
        # 2. Answer is not just punctuation or whitespace
        if not answer.strip() or answer.strip() in '.,;:!?':
            issues.append("Answer is empty or just punctuation")
        
        # 3. Answer is not too long (likely extracted wrong)
        if len(answer) > 200:
            issues.append("Answer suspiciously long")
        
        # 4. Answer is not just a common word
        common_words = ['the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
        if answer.lower().strip() in common_words:
            issues.append("Answer is just a common word")
        
        is_valid = len(issues) == 0
        return is_valid, "; ".join(issues) if issues else "Valid" 
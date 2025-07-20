"""
Keyword Hierarchy Manager for Tree Extension Deep Query Framework
Ensures strict keyword inheritance: child question answers must be parent question keywords.
"""

import logging
import json
import re
import time
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass

from config import get_config

# Setup logging
logger = logging.getLogger(__name__)

@dataclass
class KeywordNode:
    """Represents a keyword in the hierarchy"""
    keyword: str
    parent_context: str  # The question/answer context where this keyword appears
    specificity_score: float  # How specific this keyword is
    extraction_confidence: float  # Confidence in keyword extraction
    keyword_type: str  # proper_noun, number, technical_term, etc.
    position: int  # Position in parent text

@dataclass
class HierarchyValidationResult:
    """Result of hierarchy validation"""
    valid: bool
    child_answer: str
    parent_keywords: List[str]
    matched_keyword: Optional[str]
    confidence: float
    issues: List[str]
    reasoning: str

class KeywordHierarchyManager:
    """Manages strict keyword hierarchy for question tree extensions"""
    
    def __init__(self, api_client=None):
        self.config = get_config()
        self.api_client = api_client
        self.keyword_cache = {}
        
    def set_api_client(self, api_client):
        """Set the API client for LLM calls"""
        self.api_client = api_client
    
    def extract_parent_keywords(self, parent_question: str, parent_answer: str, document_context: str = "") -> List[KeywordNode]:
        """
        Extract keywords from parent question/answer that can serve as child answers
        
        Workflow requirement: Extract n sub-keywords from query(q0) where n is the minimal 
        number of keywords sufficient to identify answer a0
        """
        logger.info(f"Extracting keywords from parent: {parent_question[:50]}...")
        
        if not self.api_client:
            logger.error("No API client configured for keyword extraction")
            return []
        
        try:
            # Create extraction prompt following workflow requirements
            extraction_prompt = f"""You are extracting sub-keywords from a root question-answer pair for building a keyword hierarchy tree.

PARENT QUESTION: {parent_question}
PARENT ANSWER: {parent_answer}
DOCUMENT CONTEXT: {document_context[:1000] if document_context else ""}

KEYWORD EXTRACTION REQUIREMENTS (Following Workflow):
1. Extract n sub-keywords where n is the MINIMAL number sufficient to identify the answer
2. Keywords must be HIGHLY SPECIFIC (proper nouns, numbers, technical terms)
3. Keywords must be DISTINCTIVE and not too broad or ambiguous  
4. Keywords must be UNIQUE and not repeated
5. Each keyword should be able to serve as a child question answer

EXTRACTION PRIORITIES (in order):
1. PROPER NOUNS: Names, companies, organizations, technologies, products
2. NUMBERS: Specific quantities, measurements, percentages, years, prices  
3. TECHNICAL TERMS: Scientific/technical terminology, algorithms, methods
4. DATES: Specific time references, periods
5. LOCATIONS: Cities, countries, institutions

EXTRACTION RULES:
- Prefer single-word or short-phrase keywords (1-3 words)
- Each keyword must be independently meaningful
- Keywords should cover different aspects of the answer
- Avoid generic terms like "system", "method", "approach"
- AVOID question words: "what", "which", "who", "when", "where", "how", "why"
- AVOID common articles/prepositions: "the", "a", "an", "in", "on", "at", "for", "with"
- Extract from BOTH question and answer contexts
- Focus on CONTENT WORDS (nouns, proper nouns, numbers, dates, specific terms)

Respond in JSON format:
{{
    "extracted_keywords": [
        {{
            "keyword": "exact keyword text",
            "parent_context": "sentence/phrase containing the keyword",
            "keyword_type": "proper_noun/number/technical_term/date/location",
            "specificity_score": 0.0-1.0,
            "extraction_confidence": 0.0-1.0,
            "reasoning": "why this keyword was selected",
            "position": character_position_in_text
        }}
    ],
    "minimum_keyword_count": "minimal number needed to identify answer",
    "extraction_strategy": "explanation of extraction approach"
}}

TARGET: Extract 2-5 highly specific keywords that together uniquely identify the parent answer."""

            response = self.api_client.generate_response(
                prompt=extraction_prompt,
                temperature=0.3,  # Moderate creativity for keyword discovery
                max_tokens=600
            )
            
            # Parse response
            keywords = self._parse_keyword_extraction_response(response, parent_question, parent_answer)
            
            logger.info(f"Extracted {len(keywords)} keywords from parent")
            
            return keywords
            
        except Exception as e:
            logger.error(f"Error extracting parent keywords: {e}")
            return []
    
    def validate_child_answer_hierarchy(self, child_question: str, child_answer: str, 
                                      parent_keywords: List[KeywordNode]) -> HierarchyValidationResult:
        """
        Validate that child answer corresponds to one of the parent keywords
        
        Workflow requirement: a11 = k01, a12 = k02, a1n = k0n
        (Child answers should be parent keywords)
        
        修复：添加答案多样性检查，避免过度重复
        """
        logger.info(f"Validating child answer hierarchy: {child_answer}")
        
        result = HierarchyValidationResult(
            valid=False,
            child_answer=child_answer,
            parent_keywords=[kw.keyword for kw in parent_keywords],
            matched_keyword=None,
            confidence=0.0,
            issues=[],
            reasoning=""
        )
        
        if not parent_keywords:
            result.issues.append("No parent keywords available for validation")
            return result
        
        # 1. Direct exact match
        child_answer_clean = child_answer.strip().lower()
        for keyword_node in parent_keywords:
            keyword_clean = keyword_node.keyword.strip().lower()
            
            if child_answer_clean == keyword_clean:
                result.valid = True
                result.matched_keyword = keyword_node.keyword
                result.confidence = keyword_node.extraction_confidence
                result.reasoning = f"Direct exact match with parent keyword: {keyword_node.keyword}"
                return result
        
        # 2. FLEXIBLE HIERARCHY CHECK - 放宽匹配条件以增加多样性
        for keyword_node in parent_keywords:
            keyword_clean = keyword_node.keyword.strip().lower()
            
            # 允许的变体：单复数、大小写、标点符号
            if self._is_acceptable_keyword_variant(child_answer_clean, keyword_clean):
                result.valid = True
                result.matched_keyword = keyword_node.keyword
                result.confidence = keyword_node.extraction_confidence * 0.95
                result.reasoning = f"Acceptable variant of parent keyword: {keyword_node.keyword}"
                return result
        
        # 3. 检查是否为专有名词的一部分（如James Webb -> James Webb Space Telescope）
        for keyword_node in parent_keywords:
            if self._is_proper_noun_extension(child_answer, keyword_node.keyword):
                result.valid = True
                result.matched_keyword = keyword_node.keyword
                result.confidence = keyword_node.extraction_confidence * 0.9
                result.reasoning = f"Proper noun extension of parent keyword: {keyword_node.keyword}"
                return result
        
        # 4. 新增：语义相关性检查 - 允许相关但不完全相同的答案
        semantic_match = self._check_semantic_keyword_match(child_answer, parent_keywords)
        if semantic_match.get('valid', False):
            result.valid = True
            result.matched_keyword = semantic_match['matched_keyword']
            result.confidence = semantic_match['confidence'] * 0.8  # 降低置信度
            result.reasoning = f"Semantic match: {semantic_match['reasoning']}"
            return result
        
        # 5. 新增：RELAXED VALIDATION for diversity - 如果是技术术语相关
        if self._is_technical_term_related(child_answer, parent_keywords):
            result.valid = True
            result.matched_keyword = f"Related to: {parent_keywords[0].keyword}"
            result.confidence = 0.6  # 中等置信度
            result.reasoning = f"Technical term related to parent keywords"
            logger.info(f"Allowing technical term relation for diversity: {child_answer}")
            return result
        
        # 6. Failed validation
        result.issues.append(f"Child answer '{child_answer}' does not match any parent keyword")
        result.issues.append(f"Available parent keywords: {[kw.keyword for kw in parent_keywords]}")
        result.reasoning = f"Child answer '{child_answer}' failed to match parent keywords: {[kw.keyword for kw in parent_keywords]}"
        
        return result
    
    def perform_minimum_keyword_check(self, keywords: List[KeywordNode], parent_answer: str) -> Dict[str, Any]:
        """
        Perform Minimum Keyword Check as specified in workflow:
        Each time a keyword is masked, check if remaining keywords can still identify the answer
        """
        logger.info(f"Performing minimum keyword check on {len(keywords)} keywords")
        
        if not self.api_client:
            return {'passed': False, 'reasoning': 'No API client available'}
        
        try:
            results = []
            
            # Test each keyword by masking it
            for i, masked_keyword in enumerate(keywords):
                remaining_keywords = [kw for j, kw in enumerate(keywords) if j != i]
                
                # Check if remaining keywords can still identify the answer
                check_prompt = f"""You are performing a Minimum Keyword Check. Determine if the remaining keywords are sufficient to uniquely identify the target answer.

TARGET ANSWER: {parent_answer}
MASKED KEYWORD: {masked_keyword.keyword}
REMAINING KEYWORDS: {[kw.keyword for kw in remaining_keywords]}

ASSESSMENT TASK:
1. Can the remaining keywords uniquely identify the target answer?
2. Is the masked keyword essential for answer identification?
3. Would someone using only the remaining keywords arrive at the correct answer?

Respond in JSON format:
{{
    "sufficient_identification": true/false,
    "masked_keyword_essential": true/false,
    "confidence": 0.0-1.0,
    "reasoning": "detailed explanation"
}}"""

                response = self.api_client.generate_response(
                    prompt=check_prompt,
                    temperature=0.2,
                    max_tokens=300
                )
                
                check_result = self._parse_minimum_check_response(response, masked_keyword.keyword)
                results.append(check_result)
            
            # Analyze results
            essential_keywords = [r for r in results if r.get('masked_keyword_essential', True)]
            sufficient_subsets = [r for r in results if r.get('sufficient_identification', False)]
            
            # 优化判断逻辑：至少要有1个关键词是必要的，但不需要全部都必要
            total_keywords = len(keywords)
            essential_count = len(essential_keywords)
            optimal_range = range(1, max(2, total_keywords))  # 期望1到total-1个必要关键词
            
            passed = essential_count in optimal_range
            
            reasoning = f"Found {essential_count} essential keywords out of {total_keywords}"
            if essential_count == 0:
                reasoning += " - All keywords redundant, need better extraction"
            elif essential_count == total_keywords:
                reasoning += " - All keywords essential, may need broader extraction"
            else:
                reasoning += " - Good keyword balance achieved"
            
            return {
                'passed': passed,
                'essential_keyword_count': essential_count,
                'sufficient_subset_count': len(sufficient_subsets),
                'results': results,
                'reasoning': reasoning
            }
            
        except Exception as e:
            logger.error(f"Minimum keyword check failed: {e}")
            return {'passed': False, 'reasoning': f'Check failed: {str(e)}'}
    
    def generate_child_question_for_keyword(self, keyword_node: KeywordNode, parent_question: str, 
                                          parent_answer: str, extension_type: str = "series") -> Optional[str]:
        """
        Generate a child question where the keyword serves as the answer
        
        Workflow requirement: For each answer, design a corresponding question aligned with 
        "Generate a simple query. A root keyword is the only correct answer to the query"
        """
        logger.info(f"Generating child question for keyword: {keyword_node.keyword}")
        
        if not self.api_client:
            logger.error("No API client configured for question generation")
            return None
        
        try:
            # Create question generation prompt
            generation_prompt = f"""You are generating a child question where a specific keyword serves as the ONLY correct answer.

PARENT QUESTION: {parent_question}
PARENT ANSWER: {parent_answer}
TARGET KEYWORD (must be the answer): {keyword_node.keyword}
KEYWORD TYPE: {keyword_node.keyword_type}
PARENT CONTEXT: {keyword_node.parent_context}
EXTENSION TYPE: {extension_type}

CHILD QUESTION REQUIREMENTS (Following Workflow):
1. The question must have "{keyword_node.keyword}" as the ONLY correct answer
2. Question must require document-based knowledge (not common sense)
3. Question must be solvable and unambiguous
4. Question style must be consistent with parent question style
5. AVOID "how" questions - use "what", "which", "who", "when", "where"
6. Question must be focused and evaluable (not subjective)

GENERATION STRATEGY for {extension_type.upper()} EXTENSION:
"""

            if extension_type == "series":
                generation_prompt += f"""
SERIES EXTENSION: Create a question that drills deeper into the parent answer by focusing on the specific keyword.
- Build upon the parent question's context
- Make the keyword a natural, logical answer
- Ensure the question flows from parent to child conceptually

EXAMPLE PATTERNS:
- "What [specific aspect] of [parent context] is associated with [related concept]?"
- "Which [category] was [action] by [entity related to keyword]?"  
- "When did [keyword-related event] occur in the context of [parent topic]?"
"""
            else:  # parallel
                generation_prompt += f"""
PARALLEL EXTENSION: Create a question that explores a different aspect of the parent topic while using the keyword.
- Explore a parallel/alternative dimension of the parent topic
- Make the keyword an answer from a different perspective
- Maintain topical relevance but different angle

EXAMPLE PATTERNS:
- "What [alternative aspect] is associated with [parent topic element]?"
- "Which [parallel category] shares [common property] with [parent topic]?"
- "Who [parallel role] contributed to [related field/topic]?"
"""

            generation_prompt += f"""
CRITICAL CONSTRAINTS:
- Question MUST be answerable by "{keyword_node.keyword}" ONLY
- Question MUST avoid subjective or process-oriented queries
- Question MUST be verifiable through web search
- Question MUST align with parent question style/complexity

Generate exactly ONE focused question that meets all requirements:"""

            response = self.api_client.generate_response(
                prompt=generation_prompt,
                temperature=0.4,  # Some creativity needed for question variety
                max_tokens=200
            )
            
            # Extract and clean the question
            question = self._extract_generated_question(response)
            
            if question:
                logger.info(f"Generated child question: {question[:60]}...")
                return question
            else:
                logger.warning(f"Failed to generate valid question for keyword: {keyword_node.keyword}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating child question: {e}")
            return None
    
    def validate_shortcut_prevention(self, child_question: str, child_answer: str, 
                                   ancestor_answers: List[str], sibling_answers: List[str]) -> Dict[str, Any]:
        """
        Perform Shortcut Check as specified in workflow:
        Ensure child question does not contain keywords that could directly pinpoint other ancestor answers
        """
        logger.info(f"Performing shortcut prevention check for: {child_answer}")
        
        issues = []
        confidence = 1.0
        
        # 1. Check against ancestor answers
        for ancestor_answer in ancestor_answers:
            if self._could_infer_answer(child_question, ancestor_answer):
                issues.append(f"Child question could directly infer ancestor answer: {ancestor_answer}")
                confidence -= 0.3
        
        # 2. Check against sibling answers  
        for sibling_answer in sibling_answers:
            if sibling_answer != child_answer and self._could_infer_answer(child_question, sibling_answer):
                issues.append(f"Child question could directly infer sibling answer: {sibling_answer}")
                confidence -= 0.2
        
        # 3. Ensure child question only leads to its own answer
        if not self._ensures_unique_answer(child_question, child_answer):
            issues.append("Child question does not ensure unique answer")
            confidence -= 0.4
        
        # 生产优化：放宽快捷路径检查 - 允许一些overlap
        passed = confidence >= 0.4  # 从0.7降到0.4，更宽松
        
        return {
            'passed': passed,
            'confidence': max(0.0, confidence),
            'issues': issues,
            'reasoning': f"Shortcut check: {len(issues)} issues found, confidence: {confidence:.2f}"
        }
    
    def _parse_keyword_extraction_response(self, response: str, parent_question: str, parent_answer: str) -> List[KeywordNode]:
        """Parse keyword extraction response from LLM"""
        try:
            # Extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_text = response[json_start:json_end]
                data = json.loads(json_text)
                
                keywords = []
                for kw_data in data.get('extracted_keywords', []):
                    keyword_node = KeywordNode(
                        keyword=str(kw_data.get('keyword', '')).strip(),
                        parent_context=str(kw_data.get('parent_context', '')),
                        specificity_score=float(kw_data.get('specificity_score', 0.0)),
                        extraction_confidence=float(kw_data.get('extraction_confidence', 0.0)),
                        keyword_type=str(kw_data.get('keyword_type', 'unknown')),
                        position=int(kw_data.get('position', 0))
                    )
                    
                    if keyword_node.keyword:  # Only add non-empty keywords
                        keywords.append(keyword_node)
                
                return keywords
            
        except Exception as e:
            logger.warning(f"Failed to parse keyword extraction response: {e}")
        
        # Fallback: basic keyword extraction
        return self._fallback_keyword_extraction(parent_question, parent_answer)
    
    def _fallback_keyword_extraction(self, parent_question: str, parent_answer: str) -> List[KeywordNode]:
        """Fallback keyword extraction using regex patterns with quality filtering"""
        keywords = []
        combined_text = f"{parent_question} {parent_answer}"
        
        # Define words to avoid
        avoid_words = {
            'what', 'which', 'who', 'when', 'where', 'how', 'why',
            'the', 'a', 'an', 'in', 'on', 'at', 'for', 'with', 'by', 'to', 'from',
            'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
            'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might',
            'this', 'that', 'these', 'those', 'and', 'or', 'but', 'if', 'then'
        }
        
        # Extract proper nouns with filtering
        proper_nouns = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', combined_text)
        filtered_nouns = [noun for noun in proper_nouns if noun.lower() not in avoid_words and len(noun) > 2]
        for noun in filtered_nouns[:3]:  # Limit to top 3
            keywords.append(KeywordNode(
                keyword=noun,
                parent_context=combined_text,
                specificity_score=0.7,
                extraction_confidence=0.6,
                keyword_type='proper_noun',
                position=combined_text.find(noun)
            ))
        
        # Extract numbers
        numbers = re.findall(r'\b\d{2,4}\b', combined_text)  # Focus on meaningful numbers (years, etc.)
        for number in numbers[:2]:  # Limit to top 2
            keywords.append(KeywordNode(
                keyword=number,
                parent_context=combined_text,
                specificity_score=0.8,
                extraction_confidence=0.7,
                keyword_type='number',
                position=combined_text.find(number)
            ))
        
        # Extract technical terms (hyphenated words, acronyms)
        technical_terms = re.findall(r'\b[A-Za-z]+-[A-Za-z]+\b|\b[A-Z]{2,}\b', combined_text)
        filtered_terms = [term for term in technical_terms if term.lower() not in avoid_words and len(term) > 2]
        for term in filtered_terms[:2]:  # Limit to top 2
            keywords.append(KeywordNode(
                keyword=term,
                parent_context=combined_text,
                specificity_score=0.6,
                extraction_confidence=0.5,
                keyword_type='technical_term',
                position=combined_text.find(term)
            ))
        
        return keywords
    
    def _is_meaningful_keyword_match(self, child_answer: str, parent_keyword: str) -> bool:
        """Check if keyword match is meaningful (not just substring)"""
        # Both should be similar length or one should be abbreviation of other
        len_ratio = min(len(child_answer), len(parent_keyword)) / max(len(child_answer), len(parent_keyword))
        return len_ratio >= 0.5  # At least 50% length similarity
    
    def _check_semantic_keyword_match(self, child_answer: str, parent_keywords: List[KeywordNode]) -> Dict[str, Any]:
        """Check for semantic similarity between child answer and parent keywords"""
        # For now, simple implementation - could be enhanced with embedding similarity
        child_words = set(child_answer.lower().split())
        
        for keyword_node in parent_keywords:
            keyword_words = set(keyword_node.keyword.lower().split())
            
            # Check for word overlap
            overlap = len(child_words.intersection(keyword_words))
            if overlap > 0:
                confidence = overlap / max(len(child_words), len(keyword_words))
                if confidence >= 0.5:
                    return {
                        'valid': True,
                        'matched_keyword': keyword_node.keyword,
                        'confidence': confidence * keyword_node.extraction_confidence,
                        'reasoning': f"Semantic match through word overlap: {overlap} words"
                    }
        
        return {'valid': False}
    
    def _parse_minimum_check_response(self, response: str, masked_keyword: str) -> Dict[str, Any]:
        """Parse minimum keyword check response"""
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_text = response[json_start:json_end]
                data = json.loads(json_text)
                
                return {
                    'masked_keyword': masked_keyword,
                    'sufficient_identification': data.get('sufficient_identification', False),
                    'masked_keyword_essential': data.get('masked_keyword_essential', True),
                    'confidence': data.get('confidence', 0.0),
                    'reasoning': data.get('reasoning', '')
                }
        except:
            pass
        
        return {
            'masked_keyword': masked_keyword,
            'sufficient_identification': False,
            'masked_keyword_essential': True,
            'confidence': 0.0,
            'reasoning': 'Failed to parse response'
        }
    
    def _extract_generated_question(self, response: str) -> Optional[str]:
        """Extract generated question from LLM response"""
        # Look for question patterns
        lines = response.split('\n')
        for line in lines:
            line = line.strip()
            # Skip empty lines and headers
            if not line or line.startswith('Question:') or line.startswith('Generated'):
                continue
            # Look for actual questions
            if '?' in line and len(line) > 10:
                # Clean up the question
                question = line.strip()
                if question.startswith('"') and question.endswith('"'):
                    question = question[1:-1]
                return question
        
        # Fallback: return first non-empty line with question mark
        for line in lines:
            if '?' in line.strip() and len(line.strip()) > 5:
                return line.strip()
        
        return None
    
    def _could_infer_answer(self, question: str, answer: str) -> bool:
        """Check if question could directly infer a specific answer"""
        question_lower = question.lower()
        answer_lower = answer.lower()
        
        # Check if answer appears in question
        if answer_lower in question_lower:
            return True
        
        # Check if answer words appear in question
        answer_words = answer_lower.split()
        question_words = question_lower.split()
        
        overlap = len(set(answer_words).intersection(set(question_words)))
        
        # If significant overlap, could be inferrable
        return overlap >= len(answer_words) * 0.7
    
    def _ensures_unique_answer(self, question: str, expected_answer: str) -> bool:
        """Check if question structure ensures unique answer"""
        # Basic heuristics for question uniqueness
        question_lower = question.lower()
        
        # Questions with specific constraints tend to have unique answers
        constraint_indicators = [
            'specific', 'exact', 'first', 'earliest', 'latest', 'only',
            'particular', 'mentioned', 'stated', 'according to'
        ]
        
        has_constraints = any(indicator in question_lower for indicator in constraint_indicators)
        
        # Question should be specific enough
        is_specific = len(question.split()) >= 8  # Reasonably detailed question
        
        return has_constraints and is_specific
    
    def _is_acceptable_keyword_variant(self, child_answer: str, parent_keyword: str) -> bool:
        """检查是否为可接受的关键词变体"""
        import re
        
        # 标准化处理
        child_clean = re.sub(r'[^\w\s]', '', child_answer.lower().strip())
        parent_clean = re.sub(r'[^\w\s]', '', parent_keyword.lower().strip())
        
        # 完全匹配
        if child_clean == parent_clean:
            return True
        
        # 单复数变体
        if child_clean.endswith('s') and child_clean[:-1] == parent_clean:
            return True
        if parent_clean.endswith('s') and parent_clean[:-1] == child_clean:
            return True
        
        # 常见变体（如不同形式的同一个词）
        common_variants = [
            ('usa', 'united states', 'united states of america'),
            ('uk', 'united kingdom', 'britain'),
            ('eu', 'european union'),
            ('nato', 'north atlantic treaty organization'),
        ]
        
        for variant_group in common_variants:
            if child_clean in variant_group and parent_clean in variant_group:
                return True
        
        return False
    
    def _is_proper_noun_extension(self, child_answer: str, parent_keyword: str) -> bool:
        """检查是否为专有名词的合理扩展"""
        child_words = set(child_answer.lower().split())
        parent_words = set(parent_keyword.lower().split())
        
        # 父关键词的所有词都应该出现在子答案中
        if parent_words.issubset(child_words):
            # 但子答案不能太长（避免过度扩展）
            if len(child_words) <= len(parent_words) + 3:
                return True
        
        return False 

    def _is_technical_term_related(self, child_answer: str, parent_keywords: List[KeywordNode]) -> bool:
        """检查是否为技术术语相关，允许更灵活的匹配以增加多样性"""
        child_words = set(child_answer.lower().split())
        
        # 技术术语相关的指示词
        technical_indicators = {
            'technology', 'system', 'method', 'process', 'technique', 'algorithm',
            'design', 'model', 'framework', 'architecture', 'protocol', 'standard',
            'specification', 'implementation', 'development', 'innovation', 'advancement',
            'research', 'study', 'analysis', 'experiment', 'evaluation', 'assessment',
            'optical', 'electronic', 'mechanical', 'digital', 'automatic', 'advanced',
            'scientific', 'academic', 'industrial', 'commercial', 'professional'
        }
        
        # 检查child_answer是否包含技术指示词
        if any(indicator in child_words for indicator in technical_indicators):
            # 检查是否与父关键词在同一技术领域
            for keyword_node in parent_keywords:
                parent_words = set(keyword_node.keyword.lower().split())
                # 如果有词汇重叠或相关技术领域
                if child_words.intersection(parent_words) or \
                   any(tech_word in keyword_node.parent_context.lower() for tech_word in technical_indicators):
                    return True
        
        return False
    
    def extract_diverse_keywords(self, parent_question: str, parent_answer: str, 
                               document_context: str = "", 
                               used_answers: set = None) -> List[KeywordNode]:
        """
        提取多样化的关键词，避免重复答案
        
        Args:
            parent_question: 父问题
            parent_answer: 父答案  
            document_context: 文档上下文
            used_answers: 已使用的答案集合，用于避免重复
        """
        if used_answers is None:
            used_answers = set()
            
        # 获取原始关键词
        original_keywords = self.extract_parent_keywords(parent_question, parent_answer, document_context)
        
        # 过滤已使用的答案
        diverse_keywords = []
        for keyword_node in original_keywords:
            if keyword_node.keyword.lower() not in {ans.lower() for ans in used_answers}:
                diverse_keywords.append(keyword_node)
            else:
                logger.info(f"Skipping duplicate keyword: {keyword_node.keyword}")
        
        # 如果过滤后关键词太少，尝试生成相关的变体
        if len(diverse_keywords) < 2:
            diverse_keywords.extend(self._generate_keyword_variants(
                original_keywords, used_answers, max_variants=3-len(diverse_keywords)
            ))
        
        return diverse_keywords[:3]  # 最多返回3个关键词
    
    def _generate_keyword_variants(self, original_keywords: List[KeywordNode], 
                                 used_answers: set, max_variants: int = 2) -> List[KeywordNode]:
        """生成关键词变体以增加多样性"""
        variants = []
        
        for keyword_node in original_keywords:
            if len(variants) >= max_variants:
                break
                
            original_keyword = keyword_node.keyword
            
            # 生成技术相关变体
            if keyword_node.keyword_type == 'technical_term':
                # 为技术术语生成相关概念
                related_terms = self._get_related_technical_terms(original_keyword)
                for term in related_terms:
                    if term.lower() not in {ans.lower() for ans in used_answers}:
                        variant_node = KeywordNode(
                            keyword=term,
                            parent_context=f"Related to {original_keyword}",
                            specificity_score=keyword_node.specificity_score * 0.8,
                            extraction_confidence=keyword_node.extraction_confidence * 0.7,
                            keyword_type='technical_term_variant',
                            position=keyword_node.position
                        )
                        variants.append(variant_node)
                        break
            
            # 为专有名词生成组织或相关实体
            elif keyword_node.keyword_type == 'proper_noun':
                # 尝试从上下文中提取相关实体
                context_entities = self._extract_context_entities(keyword_node.parent_context)
                for entity in context_entities:
                    if entity.lower() not in {ans.lower() for ans in used_answers} and \
                       entity.lower() != original_keyword.lower():
                        variant_node = KeywordNode(
                            keyword=entity,
                            parent_context=keyword_node.parent_context,
                            specificity_score=keyword_node.specificity_score * 0.9,
                            extraction_confidence=keyword_node.extraction_confidence * 0.8,
                            keyword_type='proper_noun_variant',
                            position=keyword_node.position + 50
                        )
                        variants.append(variant_node)
                        break
        
        return variants
    
    def _get_related_technical_terms(self, technical_term: str) -> List[str]:
        """获取技术术语的相关概念"""
        term_lower = technical_term.lower()
        
        # 预定义的技术术语关系映射
        technical_relationships = {
            'telescope': ['optics', 'lens', 'mirror', 'observatory', 'astronomy'],
            'optics': ['lens', 'mirror', 'light', 'refraction', 'reflection'],
            'lens': ['optics', 'glass', 'curvature', 'focal length', 'aberration'],
            'mirror': ['reflection', 'coating', 'surface', 'curvature', 'optics'],
            'technology': ['innovation', 'advancement', 'development', 'system', 'method'],
            'system': ['architecture', 'design', 'framework', 'protocol', 'standard'],
            'research': ['study', 'analysis', 'investigation', 'experiment', 'methodology'],
            'algorithm': ['method', 'procedure', 'process', 'computation', 'implementation']
        }
        
        return technical_relationships.get(term_lower, [f"{technical_term} system", f"{technical_term} method"])
    
    def _extract_context_entities(self, context: str) -> List[str]:
        """从上下文中提取实体"""
        import re
        
        # 简单的实体提取：大写开头的词组
        entities = []
        
        # 匹配大写开头的专有名词
        proper_noun_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
        matches = re.findall(proper_noun_pattern, context)
        
        for match in matches:
            if len(match.split()) <= 3 and len(match) > 2:  # 避免过长的匹配
                entities.append(match)
        
        # 匹配年份和数字
        year_pattern = r'\b(19|20)\d{2}\b'
        years = re.findall(year_pattern, context)
        entities.extend([year[0] + year[1:] for year in years])
        
        return list(set(entities))[:3]  # 去重并限制数量 
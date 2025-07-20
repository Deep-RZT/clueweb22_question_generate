"""
Enhanced Question Generator for Tree Extension Deep Query Framework
Avoids "how" questions, ensures style consistency and evaluability following strict workflow requirements.
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
class QuestionTemplate:
    """Question template structure"""
    pattern: str
    question_type: str  # what, which, who, when, where
    target_answer_type: str  # proper_noun, number, date, location, technical_term
    example: str
    difficulty_level: str

@dataclass
class GeneratedQuestion:
    """Generated question with validation metadata"""
    question: str
    expected_answer: str
    question_type: str
    answer_type: str
    confidence: float
    validation_score: float
    reasoning: str
    template_used: str

class EnhancedQuestionGenerator:
    """Enhanced question generator following strict workflow requirements"""
    
    def __init__(self, api_client=None):
        self.config = get_config()
        self.api_client = api_client
        self.question_templates = self._initialize_question_templates()
        self.generation_cache = {}
        
        # NEW: 循环预防提示词增强器
        from circular_prevention_prompt_enhancer import CircularPreventionPromptEnhancer
        self.circular_preventer = CircularPreventionPromptEnhancer()
        
        # 历史问题记录（用于循环预防）
        self.question_history = []
        self.answer_history = []
        
    def set_api_client(self, api_client):
        """Set the API client for LLM calls"""
        self.api_client = api_client
    
    def generate_root_question(self, document_content: str, short_answer: str, 
                             answer_type: str) -> Optional[GeneratedQuestion]:
        """
        Generate root question following workflow requirements:
        1. Must be based on document (require web search, not common sense)
        2. Must have only one correct answer
        3. Must be solvable
        4. Must avoid subjective questions
        """
        logger.info(f"Generating root question for answer: {short_answer}")
        
        if not self.api_client:
            logger.error("No API client configured for question generation")
            return None
        
        try:
            # Select appropriate templates based on answer type
            suitable_templates = self._select_templates_for_answer_type(answer_type, "root")
            
            # Generate question using the best template
            for template in suitable_templates[:3]:  # Try top 3 templates
                generated_question = self._generate_question_with_template(
                    template, document_content, short_answer, "root"
                )
                
                if generated_question and generated_question.validation_score >= 0.7:
                    logger.info(f"Generated root question: {generated_question.question[:60]}...")
                    
                    # NEW: 记录到历史，用于后续循环预防
                    self.question_history.append(generated_question.question)
                    self.answer_history.append(short_answer)
                    
                    return generated_question
            
            logger.warning(f"Failed to generate valid root question for answer: {short_answer}")
            return None
            
        except Exception as e:
            logger.error(f"Error generating root question: {e}")
            return None
    
    def generate_child_question(self, parent_question: str, parent_answer: str, 
                              target_keyword: str, extension_context: str,
                              extension_type: str) -> Optional[GeneratedQuestion]:
        """
        Generate child question where target_keyword is the answer
        
        Workflow requirements:
        - Question style must be consistent with parent question
        - Must avoid "how" questions
        - Must be focused and evaluable (not subjective)  
        - Target keyword must be the ONLY correct answer
        """
        logger.info(f"Generating child question for keyword: {target_keyword}")
        
        if not self.api_client:
            logger.error("No API client configured for question generation")
            return None
        
        try:
            # Determine answer type of target keyword
            answer_type = self._determine_answer_type(target_keyword)
            
            # Select templates suitable for child questions
            suitable_templates = self._select_templates_for_answer_type(answer_type, "child")
            
            # Filter templates based on parent question style
            style_filtered_templates = self._filter_templates_by_parent_style(
                suitable_templates, parent_question
            )
            
            # Generate question using style-consistent templates
            for template in style_filtered_templates[:3]:
                generated_question = self._generate_child_question_with_template(
                    template, parent_question, parent_answer, target_keyword,
                    extension_context, extension_type
                )
                
                if generated_question and generated_question.validation_score >= 0.7:
                    logger.info(f"Generated child question: {generated_question.question[:60]}...")
                    return generated_question
            
            logger.warning(f"Failed to generate valid child question for keyword: {target_keyword}")
            return None
            
        except Exception as e:
            logger.error(f"Error generating child question: {e}")
            return None
    
    def _initialize_question_templates(self) -> List[QuestionTemplate]:
        """Initialize question templates avoiding 'how' questions"""
        templates = [
            # WHAT templates (most versatile)
            QuestionTemplate(
                pattern="What [specific_entity] {context} [constraint]?",
                question_type="what",
                target_answer_type="proper_noun",
                example="What telescope succeeded Hubble and was launched in 2021?",
                difficulty_level="intermediate"
            ),
            QuestionTemplate(
                pattern="What [measurement/number] {context} [constraint]?",
                question_type="what",
                target_answer_type="number",
                example="What percentage accuracy was achieved by the new algorithm?",
                difficulty_level="intermediate"
            ),
            QuestionTemplate(
                pattern="What is the name of [entity] that [distinctive_property]?",
                question_type="what",
                target_answer_type="proper_noun",
                example="What is the name of the company that developed ChatGPT?",
                difficulty_level="basic"
            ),
            
            # WHICH templates (for selection/identification)
            QuestionTemplate(
                pattern="Which [category] [action/property] [constraint]?",
                question_type="which",
                target_answer_type="proper_noun",
                example="Which university conducted the research on quantum computing?",
                difficulty_level="intermediate"
            ),
            QuestionTemplate(
                pattern="Which specific [entity] was [action] in [time/context]?",
                question_type="which",
                target_answer_type="proper_noun",
                example="Which specific algorithm was implemented in the 2023 study?",
                difficulty_level="advanced"
            ),
            
            # WHO templates (for attribution)
            QuestionTemplate(
                pattern="Who [action] [entity] [constraint]?",
                question_type="who",
                target_answer_type="proper_noun",
                example="Who developed the transformer architecture in 2017?",
                difficulty_level="intermediate"
            ),
            QuestionTemplate(
                pattern="Who first [action] that [outcome/property]?",
                question_type="who",
                target_answer_type="proper_noun",
                example="Who first proposed the attention mechanism that revolutionized NLP?",
                difficulty_level="advanced"
            ),
            
            # WHEN templates (for temporal)
            QuestionTemplate(
                pattern="When was [entity] [action] [constraint]?",
                question_type="when",
                target_answer_type="date",
                example="When was the James Webb telescope launched into space?",
                difficulty_level="basic"
            ),
            QuestionTemplate(
                pattern="In which [time_unit] did [event] [constraint]?",
                question_type="when",
                target_answer_type="date",
                example="In which year did OpenAI release GPT-4?",
                difficulty_level="intermediate"
            ),
            
            # WHERE templates (for location)
            QuestionTemplate(
                pattern="Where was [entity/event] [action/located] [constraint]?",
                question_type="where",
                target_answer_type="location",
                example="Where was the research conducted that achieved 95% accuracy?",
                difficulty_level="intermediate"
            ),
            
            # TECHNICAL SPECIFICATION templates
            QuestionTemplate(
                pattern="What [technical_parameter] was used in [system/study] [constraint]?",
                question_type="what",
                target_answer_type="technical_term",
                example="What learning rate was used in the transformer training?",
                difficulty_level="advanced"
            ),
        ]
        
        return templates
    
    def _select_templates_for_answer_type(self, answer_type: str, question_level: str) -> List[QuestionTemplate]:
        """Select appropriate templates based on answer type and question level"""
        # Filter templates by answer type compatibility
        compatible_templates = []
        
        for template in self.question_templates:
            if self._is_template_compatible(template, answer_type, question_level):
                compatible_templates.append(template)
        
        # Sort by difficulty and relevance
        compatible_templates.sort(key=lambda t: (
            t.difficulty_level == "intermediate",  # Prefer intermediate difficulty
            t.target_answer_type == answer_type,   # Prefer exact answer type match
        ), reverse=True)
        
        return compatible_templates
    
    def _is_template_compatible(self, template: QuestionTemplate, answer_type: str, question_level: str) -> bool:
        """Check if template is compatible with answer type and question level"""
        # Answer type compatibility
        type_compatibility = {
            'proper_noun': ['proper_noun', 'technical_term'],
            'number': ['number', 'technical_term'],
            'date': ['date', 'number'],
            'location': ['location', 'proper_noun'],
            'technical_term': ['technical_term', 'proper_noun']
        }
        
        if answer_type not in type_compatibility:
            answer_type = 'proper_noun'  # Default fallback
        
        if template.target_answer_type not in type_compatibility[answer_type]:
            return False
        
        # Question level compatibility (root questions can be simpler)
        if question_level == "root" and template.difficulty_level == "advanced":
            return False
        
        return True
    
    def _filter_templates_by_parent_style(self, templates: List[QuestionTemplate], 
                                        parent_question: str) -> List[QuestionTemplate]:
        """Filter templates to maintain style consistency with parent question"""
        parent_type = self._determine_question_type(parent_question)
        parent_complexity = self._assess_question_complexity(parent_question)
        
        filtered_templates = []
        
        for template in templates:
            # Prefer same question type as parent
            type_match_score = 1.0 if template.question_type == parent_type else 0.7
            
            # Match complexity level
            complexity_match_score = self._calculate_complexity_match(template, parent_complexity)
            
            # Overall compatibility score
            compatibility_score = (type_match_score + complexity_match_score) / 2
            
            if compatibility_score >= 0.6:
                filtered_templates.append(template)
        
        # Sort by compatibility
        filtered_templates.sort(key=lambda t: self._calculate_template_score(t, parent_question), reverse=True)
        
        return filtered_templates
    
    def _generate_question_with_template(self, template: QuestionTemplate, document_content: str,
                                       short_answer: str, question_level: str) -> Optional[GeneratedQuestion]:
        """Generate question using a specific template"""
        try:
            base_prompt = f"""You are generating a {question_level} question that follows a {template.question_type} pattern.

TARGET ANSWER: {short_answer}
ANSWER TYPE: {template.target_answer_type}
DOCUMENT CONTEXT: {document_content[:1500]}

QUESTION REQUIREMENTS:
1. Must start with "{template.question_type.capitalize()}" (e.g., "What", "Which", "Who", "When", "Where")
2. The question must have "{short_answer}" as the ONLY correct answer
3. Must be based on information from the document context
4. Must be a complete, natural language question without any placeholders
5. Must be solvable and unambiguous
6. Must avoid subjective or opinion-based elements
7. STRICTLY avoid "how" questions or process explanations

EXAMPLE STYLE (for reference only - create your own question):
- "What telescope succeeded Hubble and was launched in 2021?" → Answer: "James Webb Space Telescope"
- "Which company developed the ChatGPT language model?" → Answer: "OpenAI"
- "Who invented the telephone in 1876?" → Answer: "Alexander Graham Bell"

IMPORTANT: Generate a complete, natural question without any brackets [], braces {{}}, or placeholder text. The question should read naturally and professionally.

Generate exactly ONE complete question that answers to "{short_answer}":"""

            # NEW: 应用循环预防增强
            if question_level == "root":
                generation_prompt = self.circular_preventer.enhance_root_question_prompt(
                    base_prompt, document_content, short_answer, template.target_answer_type
                )
            else:
                generation_prompt = base_prompt

            response = self.api_client.generate_response(
                prompt=generation_prompt,
                temperature=0.4,
                max_tokens=150
            )
            
            # Extract and validate question
            question = self._extract_generated_question(response)
            
            if question:
                # Light cleanup only if needed (prompt should generate clean questions)
                if '[' in question or '{' in question:
                    logger.warning(f"Question contains placeholders, applying cleanup: {question[:50]}...")
                    question = self._clean_template_placeholders(question, document_content, short_answer)
                
                # Validate the generated question
                validation_result = self._validate_generated_question(
                    question, short_answer, template, document_content
                )
                
                if validation_result['score'] >= 0.7:
                    return GeneratedQuestion(
                        question=question,
                        expected_answer=short_answer,
                        question_type=template.question_type,
                        answer_type=template.target_answer_type,
                        confidence=validation_result['confidence'],
                        validation_score=validation_result['score'],
                        reasoning=validation_result['reasoning'],
                        template_used=template.pattern
                    )
            
        except Exception as e:
            logger.error(f"Error generating question with template: {e}")
        
        return None
    
    def _generate_child_question_with_template(self, template: QuestionTemplate, parent_question: str,
                                             parent_answer: str, target_keyword: str,
                                             extension_context: str, extension_type: str) -> Optional[GeneratedQuestion]:
        """Generate child question using template and extension context"""
        try:
            base_prompt = f"""You are generating a child question that follows a {template.question_type} pattern.

PARENT CONTEXT:
- Parent Question: {parent_question}
- Parent Answer: {parent_answer}
- Target Keyword (MUST be answer): {target_keyword}
- Extension Type: {extension_type}

EXTENSION CONTEXT (from web search):
{extension_context[:1000]}

CRITICAL WORKFLOW REQUIREMENT:
The answer to your question MUST be exactly "{target_keyword}" - this is a strict constraint from the parent keyword hierarchy.

CHILD QUESTION REQUIREMENTS:
1. Must start with "{template.question_type.capitalize()}" (e.g., "What", "Which", "Who", "When", "Where")
2. Must have "{target_keyword}" as the ONLY correct answer (WORKFLOW CONSTRAINT)
3. Must maintain style consistency with parent question
4. Must be based on extension context, not just parent document
5. Must be a complete, natural language question without any placeholders
6. AVOID "how" questions completely
7. Must be focused and objectively evaluable

GENERATION STRATEGY for {extension_type.upper()}:
"""

            if extension_type == "series":
                generation_prompt += f"""
SERIES EXTENSION: Drill deeper into the target keyword using extension context.
- Build upon parent question's domain/context
- Use extension context to find specific aspects of the keyword
- Make question more detailed/technical than parent
"""
            else:  # parallel
                generation_prompt += f"""
PARALLEL EXTENSION: Explore different aspect of the topic using extension context.
- Explore alternative perspective on the keyword
- Use extension context to find parallel/comparative elements
- Maintain topical relevance but different angle
"""

            generation_prompt += f"""

WORKFLOW COMPLIANCE EXAMPLES:
- Parent Q: "What telescope was launched in 2021?" Keywords: ["James Webb", "2021"]
  → Child Q for "James Webb": "What specific telescope succeeded Hubble?" Answer: "James Webb"
  → Child Q for "2021": "What year was the James Webb telescope launched?" Answer: "2021"
- Parent Q: "Which company developed GPT?" Keywords: ["OpenAI", "GPT"]
  → Child Q for "OpenAI": "Which organization created the ChatGPT model?" Answer: "OpenAI"
  → Child Q for "GPT": "What language model architecture was developed by OpenAI?" Answer: "GPT"

CRITICAL CONSTRAINT VERIFICATION:
- Your question must be answerable with exactly "{target_keyword}" and nothing else
- If someone reads your question, they should naturally arrive at "{target_keyword}" as the answer
- The question should not contain the answer or make it obvious

IMPORTANT: Generate a complete, natural question without any brackets [], braces {{}}, or placeholder text. The question should read naturally and professionally, with "{target_keyword}" as the definitive answer.

Generate exactly ONE complete child question that has "{target_keyword}" as its answer:"""

            # NEW: 应用循环预防增强（对子问题）
            if len(self.question_history) > 0:
                historical_context = self.circular_preventer.create_historical_context(
                    self.question_history, self.answer_history
                )
                generation_prompt = self.circular_preventer.enhance_child_question_prompt(
                    base_prompt, parent_question, parent_answer, target_keyword, historical_context
                )
            else:
                generation_prompt = base_prompt

            response = self.api_client.generate_response(
                prompt=generation_prompt,
                temperature=0.4,
                max_tokens=200
            )
            
            # Extract and validate question
            question = self._extract_generated_question(response)
            
            if question:
                # Light cleanup only if needed (prompt should generate clean questions)
                if '[' in question or '{' in question:
                    logger.warning(f"Child question contains placeholders, applying cleanup: {question[:50]}...")
                    question = self._clean_template_placeholders(question, extension_context, target_keyword)
                
                # Validate child question
                validation_result = self._validate_child_question(
                    question, target_keyword, parent_question, template, extension_context
                )
                
                if validation_result['score'] >= 0.7:
                    # ADDITIONAL WORKFLOW CONSTRAINT CHECK
                    # Ensure the question really leads to the target keyword
                    if self._verify_answer_constraint(question, target_keyword):
                        # NEW: 记录到历史，用于后续循环预防
                        self.question_history.append(question)
                        self.answer_history.append(target_keyword)
                        
                        return GeneratedQuestion(
                            question=question,
                            expected_answer=target_keyword,
                            question_type=template.question_type,
                            answer_type=template.target_answer_type,
                            confidence=validation_result['confidence'],
                            validation_score=validation_result['score'],
                            reasoning=validation_result['reasoning'],
                            template_used=template.pattern
                        )
                    else:
                        logger.warning(f"Generated question doesn't clearly lead to target keyword: {target_keyword}")
            
        except Exception as e:
            logger.error(f"Error generating child question with template: {e}")
        
        return None
    
    def _determine_answer_type(self, answer: str) -> str:
        """Determine the type of answer for template selection"""
        answer_lower = answer.lower().strip()
        
        # Number patterns
        if re.match(r'^\d+\.?\d*$', answer) or re.match(r'^\d+%$', answer) or re.match(r'^\$\d+', answer):
            return 'number'
        
        # Date patterns
        if re.match(r'^\d{4}$', answer) or re.match(r'\d{1,2}/\d{1,2}/\d{4}', answer):
            return 'date'
        
        # Location patterns (contains location indicators)
        location_indicators = ['university', 'institute', 'laboratory', 'center', 'college', 'city', 'country']
        if any(indicator in answer_lower for indicator in location_indicators):
            return 'location'
        
        # Technical term patterns
        technical_indicators = ['-', '_', 'algorithm', 'method', 'system', 'protocol', 'architecture']
        if any(indicator in answer_lower for indicator in technical_indicators):
            return 'technical_term'
        
        # Default to proper noun
        return 'proper_noun'
    
    def _determine_question_type(self, question: str) -> str:
        """Determine the type of question"""
        question_lower = question.lower().strip()
        
        if question_lower.startswith('what'):
            return 'what'
        elif question_lower.startswith('which'):
            return 'which'
        elif question_lower.startswith('who'):
            return 'who'
        elif question_lower.startswith('when'):
            return 'when'
        elif question_lower.startswith('where'):
            return 'where'
        else:
            return 'what'  # Default
    
    def _assess_question_complexity(self, question: str) -> str:
        """Assess the complexity level of a question"""
        # Simple heuristics for complexity assessment
        word_count = len(question.split())
        
        if word_count < 10:
            return 'basic'
        elif word_count < 15:
            return 'intermediate'
        else:
            return 'advanced'
    
    def _calculate_complexity_match(self, template: QuestionTemplate, parent_complexity: str) -> float:
        """Calculate how well template complexity matches parent complexity"""
        complexity_scores = {
            ('basic', 'basic'): 1.0,
            ('basic', 'intermediate'): 0.9,
            ('intermediate', 'intermediate'): 1.0,
            ('intermediate', 'advanced'): 0.9,
            ('advanced', 'advanced'): 1.0,
            ('advanced', 'intermediate'): 0.8,
        }
        
        return complexity_scores.get((template.difficulty_level, parent_complexity), 0.7)
    
    def _calculate_template_score(self, template: QuestionTemplate, parent_question: str) -> float:
        """Calculate overall template score for parent question"""
        parent_type = self._determine_question_type(parent_question)
        parent_complexity = self._assess_question_complexity(parent_question)
        
        type_score = 1.0 if template.question_type == parent_type else 0.7
        complexity_score = self._calculate_complexity_match(template, parent_complexity)
        
        return (type_score + complexity_score) / 2
    
    def _extract_generated_question(self, response: str) -> Optional[str]:
        """Extract generated question from LLM response"""
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines, headers, or explanatory text
            if not line or line.startswith('Question:') or line.startswith('Generated'):
                continue
            
            # Look for actual questions
            if '?' in line and len(line) > 10:
                # Clean up the question
                question = line.strip()
                
                # Remove quotes if present
                if question.startswith('"') and question.endswith('"'):
                    question = question[1:-1]
                
                # Validate it's a proper question
                if self._is_valid_question_format(question):
                    return question
        
        return None
    
    def _is_valid_question_format(self, question: str) -> bool:
        """Validate question format"""
        question_lower = question.lower().strip()
        
        # Must end with question mark
        if not question.endswith('?'):
            return False
        
        # Must start with valid question word (no "how")
        valid_starts = ['what', 'which', 'who', 'when', 'where', 'in which', 'at what']
        if not any(question_lower.startswith(start) for start in valid_starts):
            return False
        
        # Must not contain "how" anywhere
        if ' how ' in question_lower or question_lower.startswith('how '):
            return False
        
        # Must be reasonable length
        if len(question.split()) < 5 or len(question.split()) > 25:
            return False
        
        return True
    
    def _validate_generated_question(self, question: str, expected_answer: str, 
                                   template: QuestionTemplate, document_content: str) -> Dict[str, Any]:
        """Validate generated question quality"""
        score = 0.0
        issues = []
        
        # 1. Format validation
        if self._is_valid_question_format(question):
            score += 0.3
        else:
            issues.append("Invalid question format")
        
        # 2. Template compliance
        if question.lower().startswith(template.question_type):
            score += 0.2
        else:
            issues.append(f"Does not match template type: {template.question_type}")
        
        # 3. Answer presence in document
        if expected_answer in document_content:
            score += 0.2
        else:
            issues.append("Answer not found in document")
        
        # 4. Question specificity
        if len(question.split()) >= 8:  # Reasonably specific
            score += 0.2
        else:
            issues.append("Question too generic")
        
        # 5. No "how" questions
        if 'how' not in question.lower():
            score += 0.1
        else:
            issues.append("Contains 'how' - against requirements")
            score -= 0.3
        
        confidence = max(0.0, score)
        reasoning = f"Validation score: {score:.2f}; Issues: {len(issues)}"
        
        return {
            'score': confidence,
            'confidence': confidence,
            'issues': issues,
            'reasoning': reasoning
        }
    
    def _validate_child_question(self, question: str, expected_answer: str, parent_question: str,
                               template: QuestionTemplate, extension_context: str) -> Dict[str, Any]:
        """Validate child question quality"""
        score = 0.0
        issues = []
        
        # 1. Basic format validation
        if self._is_valid_question_format(question):
            score += 0.25
        else:
            issues.append("Invalid question format")
        
        # 2. Template compliance
        if question.lower().startswith(template.question_type):
            score += 0.2
        else:
            issues.append(f"Does not match template type: {template.question_type}")
        
        # 3. Style consistency with parent
        parent_type = self._determine_question_type(parent_question)
        child_type = self._determine_question_type(question)
        if parent_type == child_type:
            score += 0.15
        else:
            score += 0.05  # Partial credit for different but valid type
        
        # 4. Extension context usage
        if any(word in question.lower() for word in extension_context.lower().split()[:20]):
            score += 0.2
        else:
            issues.append("Does not use extension context")
        
        # 5. Answer specificity
        if len(expected_answer.split()) <= 3:  # Good for short answers
            score += 0.1
        
        # 6. No forbidden elements
        if 'how' not in question.lower():
            score += 0.1
        else:
            issues.append("Contains 'how' - forbidden")
            score -= 0.4
        
        confidence = max(0.0, score)
        reasoning = f"Child validation score: {score:.2f}; Parent style: {parent_type}; Issues: {len(issues)}"
        
        return {
            'score': confidence,
            'confidence': confidence,
            'issues': issues,
            'reasoning': reasoning
        }
    
    def _clean_template_placeholders(self, question: str, context: str, answer: str) -> str:
        """Clean up template placeholders that weren't properly replaced by LLM"""
        import re
        
        # Remove common template placeholders
        placeholders_to_remove = [
            r'\[specific_entity\]', r'\[entity\]', r'\[constraint\]', r'\[action\]',
            r'\[technical_specification\]', r'\[technical_advancement\]', r'\[technology\]',
            r'\[component\]', r'\[specific_aspect\]', r'\[category\]', r'\[measurement/number\]',
            r'\[time_unit\]', r'\[event\]', r'\[technical_parameter\]', r'\[system/study\]',
            r'\[distinctive_property\]', r'\[action/property\]', r'\[action/located\]',
            r'\[time/context\]', r'\[type of lens configuration\]', r'\[performance metric\]',
            r'\[specific design feature\]', r'\[optical configuration\]', r'\[inventor\]',
            r'\[individual\]', r'\[presenter\]', r'\[specific_entity\]'
        ]
        
        # Remove braced placeholders like {context}, {constraint}
        braced_placeholders = [
            r'\{context\}', r'\{constraint\}', r'\{announced a new lens-based seeing instrument in 1608\}',
            r'\{Telescope Presentation on Tue Dec 03 2013\}', r'\{telescope technology trends presentation on Tue Dec 03 2013\}',
            r'\{in the history of the telescope\}', r'\{context\}', r'\{who contributed to the development of the telescope\}',
            r'\{allegedly inventing the telescope\}', r'\{in advanced implementation research\}',
            r'\{Nick Yau\'s analysis of adaptive optics systems\}', r'\{first evidence of the invention of the telescope\}'
        ]
        
        cleaned_question = question
        
        # Remove placeholder patterns
        all_placeholders = placeholders_to_remove + braced_placeholders
        for placeholder in all_placeholders:
            cleaned_question = re.sub(placeholder, '', cleaned_question, flags=re.IGNORECASE)
        
        # Clean up extra spaces and punctuation
        cleaned_question = re.sub(r'\s+', ' ', cleaned_question)  # Multiple spaces to single
        cleaned_question = re.sub(r'\s+\?', '?', cleaned_question)  # Space before question mark
        cleaned_question = re.sub(r'\s+,', ',', cleaned_question)  # Space before comma
        cleaned_question = cleaned_question.strip()
        
        # If question becomes too short or broken, try to reconstruct
        if len(cleaned_question) < 20 or not cleaned_question.endswith('?'):
            # Try to create a simple, clean question
            question_word = self._extract_question_word(question)
            if question_word and answer:
                # Create a basic question pattern
                if question_word.lower() == 'what':
                    cleaned_question = f"What {answer.lower()} was mentioned in the document?"
                elif question_word.lower() == 'who':
                    cleaned_question = f"Who is {answer}?"
                elif question_word.lower() == 'when':
                    cleaned_question = f"When did the event involving {answer} occur?"
                elif question_word.lower() == 'which':
                    cleaned_question = f"Which entity is referred to as {answer}?"
                else:
                    cleaned_question = f"What is {answer}?"
        
        return cleaned_question
    
    def _extract_question_word(self, question: str) -> str:
        """Extract the question word from the beginning of a question"""
        question_words = ['what', 'which', 'who', 'when', 'where', 'how', 'why']
        first_word = question.lower().split()[0] if question.split() else ''
        
        if first_word in question_words:
            return first_word.capitalize()
        return 'What'  # Default
    
    def _verify_answer_constraint(self, question: str, target_keyword: str) -> bool:
        """Verify that the question naturally leads to the target keyword as answer"""
        question_lower = question.lower()
        target_lower = target_keyword.lower()
        
        # 1. Question should not make the answer too obvious (subtle leakage check)
        # Allow keyword mentions that are contextual, but avoid direct answers
        target_words = target_lower.split()
        question_words = question_lower.split()
        
        # If it's a short specific keyword (like a name), be more strict
        if len(target_words) == 1 and target_lower in question_lower:
            # Check if it's just a casual mention vs answer-giving
            target_index = question_lower.find(target_lower)
            context_around = question_lower[max(0, target_index-10):target_index+len(target_lower)+10]
            
            # Problematic patterns that give away the answer
            if any(pattern in context_around for pattern in ['is ', 'was ', 'called ', 'named ']):
                logger.warning(f"Question directly states the answer: {target_keyword}")
                return False
        
        # 2. Question should be specific enough to have a focused answer
        if len(question.split()) < 6:
            logger.warning(f"Question too short/generic to ensure specific answer")
            return False
        
        # 3. Question should have proper question structure
        if not question.endswith('?'):
            logger.warning(f"Question doesn't end with question mark")
            return False
        
        # 4. Question should start with valid question word
        valid_starts = ['what', 'which', 'who', 'when', 'where']
        if not any(question_lower.startswith(start) for start in valid_starts):
            logger.warning(f"Question doesn't start with valid question word")
            return False
        
        # 5. Question should not be too broad (allow multiple answers)
        broad_indicators = ['any', 'some', 'various', 'multiple', 'different', 'many']
        if any(indicator in question_lower for indicator in broad_indicators):
            logger.warning(f"Question contains broad indicators that may allow multiple answers")
            return False
        
        return True
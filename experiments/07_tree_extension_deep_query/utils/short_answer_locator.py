"""
Short Answer Locator for Tree Extension Deep Query Framework
Extracts objective facts (nouns, numbers, names, dates, locations) from documents to serve as short answers.
"""

import logging
import json
import re
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

try:
    from .document_loader import DocumentData
    from ..config import get_config
except ImportError:
    # Fallback for when running as script
    import sys
    from pathlib import Path
    current_dir = Path(__file__).parent
    parent_dir = current_dir.parent
    sys.path.append(str(current_dir))
    sys.path.append(str(parent_dir))
    from document_loader import DocumentData
    from config import get_config

# Setup logging
logger = logging.getLogger(__name__)

@dataclass
class ShortAnswer:
    """Data structure for a short answer"""
    answer_text: str
    answer_type: str  # noun, number, name, date, location
    context: str      # Surrounding context
    position: int     # Position in document
    confidence: float # Confidence score
    reasoning: str    # Why this is a good answer
    
    def is_valid(self) -> bool:
        """Check if answer meets quality criteria"""
        config = get_config()
        return (
            config.min_answer_length <= len(self.answer_text) <= config.max_answer_length
            and self.answer_type in config.answer_types
            and self.confidence > 0.5
            and bool(self.answer_text.strip())
        )

class ShortAnswerLocator:
    """Locates short, objective answers from documents"""
    
    def __init__(self, api_client=None):
        self.config = get_config()
        self.api_client = api_client
        self.answer_cache = {}
    
    def set_api_client(self, api_client):
        """Set the API client for LLM calls"""
        self.api_client = api_client
    
    def locate_short_answers(self, document: DocumentData) -> List[ShortAnswer]:
        """Locate multiple short answers from a document"""
        logger.info(f"Locating short answers in document: {document.doc_id}")
        
        if not self.api_client:
            logger.error("No API client configured for answer location")
            return []
        
        try:
            # Create prompt for answer location
            location_prompt = self._create_answer_location_prompt(document)
            
            # Call LLM for answer extraction
            response = self._call_llm_for_answer_location(location_prompt)
            
            # Parse response to extract answers
            answers = self._parse_answer_location_response(document.doc_id, response)
            
            # Validate and filter answers
            valid_answers = [answer for answer in answers if answer.is_valid()]
            
            logger.info(f"Located {len(valid_answers)} valid short answers from {len(answers)} candidates")
            
            # Cache results
            self.answer_cache[document.doc_id] = valid_answers
            
            return valid_answers
            
        except Exception as e:
            logger.error(f"Error locating answers in document {document.doc_id}: {e}")
            return []
    
    def locate_best_short_answer(self, document: DocumentData) -> Optional[ShortAnswer]:
        """Locate the single best short answer from a document"""
        answers = self.locate_short_answers(document)
        
        if not answers:
            return None
        
        # Select the answer with highest confidence
        best_answer = max(answers, key=lambda a: a.confidence)
        
        logger.info(f"Selected best answer: '{best_answer.answer_text}' ({best_answer.answer_type}, confidence: {best_answer.confidence:.2f})")
        
        return best_answer
    
    def _create_answer_location_prompt(self, document: DocumentData) -> str:
        """Create prompt for locating short answers"""
        
        # Truncate document if too long
        content = document.content
        if len(content) > 3000:
            content = content[:3000] + "..."
        
        prompt = f"""
Extract precise, objective facts from this document that can serve as definitive answers.

DOCUMENT TO ANALYZE:
{content}

TARGET ANSWER TYPES (in priority order):
1. NAMES: People, companies, organizations, products, technologies
2. NUMBERS: Specific quantities, measurements, percentages, years, prices
3. DATES: Specific time references, launch dates, establishment dates
4. LOCATIONS: Cities, countries, addresses, geographical references
5. SPECIFICATIONS: Technical details, model numbers, versions

CRITICAL REQUIREMENTS:
- Must be CONCRETE and FACTUAL (not abstract concepts)
- Must be VERIFIABLE through external sources  
- Must have UNIQUE, definitive answers (no ambiguity)
- Must avoid topics requiring explanations ("how", "why", "process")
- Must be extractable as SHORT PHRASES (1-8 words maximum)

PREFERRED CONTENT PATTERNS:
- "Company X was founded in [YEAR]" → Extract: [YEAR]
- "The device costs $[AMOUNT]" → Extract: $[AMOUNT]  
- "[PERSON] developed [TECHNOLOGY]" → Extract: [PERSON] or [TECHNOLOGY]
- "Located in [CITY], [COUNTRY]" → Extract: [CITY] or [COUNTRY]
- "[PRODUCT] version [NUMBER]" → Extract: [PRODUCT] or [NUMBER]

EXTRACTION RULES:
1. Extract 3-5 potential short answers
2. For each answer, provide the exact text and surrounding context
3. Classify the answer type (number/name/date/location/noun)
4. Explain why this makes a good objective answer
5. Rate confidence (0.0-1.0) based on objectivity and verifiability

Please respond in JSON format:
{{
    "short_answers": [
        {{
            "answer_text": "exact answer text",
            "answer_type": "number/name/date/location/noun",
            "context": "surrounding sentence or phrase",
            "position": approximate_character_position,
            "confidence": 0.0-1.0,
            "reasoning": "why this is a good objective answer"
        }}
    ]
}}

EXAMPLES OF GOOD ANSWERS:
- "2023" (year)
- "Apple Inc." (company name)
- "New York" (location)
- "50 million" (number)
- "iPhone 15" (product name)

EXAMPLES OF BAD ANSWERS:
- "very important" (subjective)
- "might be possible" (uncertain)
- "the best way" (opinion)
- "depends on factors" (vague)

Focus on extracting clear, factual information that can serve as definitive answers to specific questions.
"""
        
        return prompt
    
    def _call_llm_for_answer_location(self, prompt: str) -> str:
        """Call LLM API for answer location"""
        try:
            # Rate limiting
            time.sleep(0.5)
            
            response = self.api_client.generate_response(
                prompt=prompt,
                temperature=0.2,  # Low temperature for consistent extraction
                max_tokens=800
            )
            
            return response
            
        except Exception as e:
            logger.error(f"LLM API call failed for answer location: {e}")
            raise
    
    def _parse_answer_location_response(self, doc_id: str, response: str) -> List[ShortAnswer]:
        """Parse LLM response for short answers"""
        try:
            # Extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_text = response[json_start:json_end]
                answer_data = json.loads(json_text)
            else:
                # Fallback parsing
                answer_data = self._fallback_parse_answers(response)
            
            answers = []
            
            # Extract answer list
            short_answers_list = answer_data.get('short_answers', [])
            
            for answer_item in short_answers_list:
                try:
                    answer = ShortAnswer(
                        answer_text=str(answer_item.get('answer_text', '')).strip(),
                        answer_type=str(answer_item.get('answer_type', 'noun')),
                        context=str(answer_item.get('context', '')),
                        position=self._safe_int(answer_item.get('position', 0)),
                        confidence=self._safe_float(answer_item.get('confidence', 0.0)),
                        reasoning=str(answer_item.get('reasoning', ''))
                    )
                    
                    if answer.answer_text:  # Only add non-empty answers
                        answers.append(answer)
                        
                except Exception as e:
                    logger.warning(f"Error parsing individual answer: {e}")
                    continue
            
            logger.info(f"Successfully parsed {len(answers)} answers for {doc_id}")
            return answers
            
        except Exception as e:
            logger.warning(f"Failed to parse answer location response for {doc_id}: {e}")
            logger.debug(f"Response was: {response}")
            return []
    
    def _fallback_parse_answers(self, response: str) -> Dict:
        """Fallback parsing when JSON extraction fails"""
        logger.info("Using fallback parsing for answer extraction")
        
        # Simple regex-based extraction for common patterns
        answers = []
        
        # Look for numbers
        number_matches = re.findall(r'\b\d{1,4}(?:,\d{3})*(?:\.\d+)?\b', response)
        for match in number_matches[:2]:  # Limit to 2
            answers.append({
                'answer_text': match,
                'answer_type': 'number',
                'context': f"Number found: {match}",
                'position': 0,
                'confidence': 0.6,
                'reasoning': 'Fallback number extraction'
            })
        
        # Look for capitalized names/places
        name_matches = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', response)
        for match in name_matches[:2]:  # Limit to 2
            if len(match.split()) <= 3:  # Not too long
                answers.append({
                    'answer_text': match,
                    'answer_type': 'name',
                    'context': f"Name found: {match}",
                    'position': 0,
                    'confidence': 0.5,
                    'reasoning': 'Fallback name extraction'
                })
        
        return {'short_answers': answers}
    
    def _safe_int(self, value) -> int:
        """Safely convert value to integer"""
        try:
            if isinstance(value, (int, float)):
                return int(value)
            elif isinstance(value, str):
                return int(float(value))  # Handle "123.0" strings
            else:
                return 0
        except (ValueError, TypeError):
            return 0
    
    def _safe_float(self, value) -> float:
        """Safely convert value to float"""
        try:
            if isinstance(value, (int, float)):
                return float(value)
            elif isinstance(value, str):
                return float(value)
            else:
                return 0.0
        except (ValueError, TypeError):
            return 0.0
    
    def validate_answer_quality(self, answer: ShortAnswer, document: DocumentData) -> Tuple[bool, str]:
        """Validate the quality of a short answer"""
        issues = []
        
        # Length check
        if len(answer.answer_text) < self.config.min_answer_length:
            issues.append(f"Answer too short: {len(answer.answer_text)} chars")
        
        if len(answer.answer_text) > self.config.max_answer_length:
            issues.append(f"Answer too long: {len(answer.answer_text)} chars")
        
        # Type check
        if answer.answer_type not in self.config.answer_types:
            issues.append(f"Invalid answer type: {answer.answer_type}")
        
        # Confidence check
        if answer.confidence < 0.5:
            issues.append(f"Low confidence: {answer.confidence}")
        
        # Content check
        answer_lower = answer.answer_text.lower()
        for avoid_type in self.config.avoid_answer_types:
            if avoid_type in answer_lower:
                issues.append(f"Contains avoid type: {avoid_type}")
        
        # Verify answer exists in document
        if answer.answer_text not in document.content:
            issues.append("Answer not found in document")
        
        is_valid = len(issues) == 0
        return is_valid, "; ".join(issues) if issues else "Valid"
    
    def get_answer_statistics(self, answers: List[ShortAnswer]) -> Dict:
        """Get statistics about extracted answers"""
        if not answers:
            return {}
        
        # Type distribution
        type_counts = {}
        for answer in answers:
            type_counts[answer.answer_type] = type_counts.get(answer.answer_type, 0) + 1
        
        # Confidence distribution
        confidences = [a.confidence for a in answers]
        avg_confidence = sum(confidences) / len(confidences)
        
        # Length distribution
        lengths = [len(a.answer_text) for a in answers]
        avg_length = sum(lengths) / len(lengths)
        
        return {
            "total_answers": len(answers),
            "type_distribution": type_counts,
            "average_confidence": avg_confidence,
            "confidence_range": [min(confidences), max(confidences)],
            "average_length": avg_length,
            "length_range": [min(lengths), max(lengths)],
            "valid_answers": len([a for a in answers if a.is_valid()])
        }
    
    def save_answers(self, answers: List[ShortAnswer], output_file: str):
        """Save extracted answers to file"""
        try:
            answer_data = []
            for answer in answers:
                answer_data.append({
                    "answer_text": answer.answer_text,
                    "answer_type": answer.answer_type,
                    "context": answer.context,
                    "position": answer.position,
                    "confidence": answer.confidence,
                    "reasoning": answer.reasoning,
                    "is_valid": answer.is_valid()
                })
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(answer_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Answers saved to {output_file}")
            
        except Exception as e:
            logger.error(f"Failed to save answers: {e}")

def test_short_answer_locator():
    """Test function for short answer locator"""
    # Mock API client for testing
    class MockAPIClient:
        def generate_response(self, prompt, temperature=0.2, max_tokens=800):
            return '''
            {
                "short_answers": [
                    {
                        "answer_text": "iPhone 15",
                        "answer_type": "name",
                        "context": "Apple announced the iPhone 15 in 2023",
                        "position": 25,
                        "confidence": 0.9,
                        "reasoning": "Specific product name that can be objectively verified"
                    },
                    {
                        "answer_text": "2023",
                        "answer_type": "date",
                        "context": "iPhone 15 in 2023 with improved",
                        "position": 45,
                        "confidence": 0.95,
                        "reasoning": "Specific year that can be verified"
                    },
                    {
                        "answer_text": "48MP",
                        "answer_type": "number",
                        "context": "improved camera capabilities and 48MP main sensor",
                        "position": 85,
                        "confidence": 0.85,
                        "reasoning": "Technical specification that is objective and measurable"
                    }
                ]
            }
            '''
    
    # Create test document
    from .document_loader import DocumentData
    test_doc = DocumentData(
        doc_id="test_doc_001",
        file_path="/test/path",
        content="Apple announced the iPhone 15 in 2023 with improved camera capabilities and 48MP main sensor. The device features a new titanium design and starts at $799.",
        topic="en0001",
        length=150
    )
    
    # Test answer location
    locator = ShortAnswerLocator(MockAPIClient())
    answers = locator.locate_short_answers(test_doc)
    
    print(f"Located {len(answers)} short answers:")
    for i, answer in enumerate(answers):
        print(f"  {i+1}. '{answer.answer_text}' ({answer.answer_type})")
        print(f"     Context: {answer.context}")
        print(f"     Confidence: {answer.confidence:.2f}")
        print(f"     Valid: {answer.is_valid()}")
        print()
    
    # Test best answer selection
    best_answer = locator.locate_best_short_answer(test_doc)
    if best_answer:
        print(f"Best answer: '{best_answer.answer_text}' (confidence: {best_answer.confidence:.2f})")
    
    # Test statistics
    stats = locator.get_answer_statistics(answers)
    print(f"Answer statistics: {stats}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_short_answer_locator() 
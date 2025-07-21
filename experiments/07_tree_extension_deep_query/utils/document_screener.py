"""
Document Screener for Tree Extension Deep Query Framework
Uses LLM to assess document quality and suitability for short answer extraction.
"""

import logging
import json
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
class ScreeningResult:
    """Result of document screening"""
    doc_id: str
    is_suitable: bool
    quality_score: float
    reasoning: str
    potential_answers: List[str]
    content_type: str
    issues: List[str]
    
class DocumentScreener:
    """LLM-based document quality screener"""
    
    def __init__(self, api_client=None):
        self.config = get_config()
        self.api_client = api_client
        self.screening_results = {}
        
    def set_api_client(self, api_client):
        """Set the API client for LLM calls"""
        self.api_client = api_client
    
    def screen_document(self, document: DocumentData) -> ScreeningResult:
        """Screen a single document for quality and suitability"""
        logger.info(f"Screening document: {document.doc_id}")
        
        if not self.api_client:
            logger.error("No API client configured for screening")
            return self._create_default_result(document.doc_id, False, "No API client")
        
        try:
            # Prepare screening prompt
            screening_prompt = self._create_screening_prompt(document)
            
            # Call LLM for screening
            response = self._call_llm_for_screening(screening_prompt)
            
            # Parse response
            result = self._parse_screening_response(document.doc_id, response)
            
            # Cache result
            self.screening_results[document.doc_id] = result
            
            logger.info(f"Screening completed for {document.doc_id}: {'✓' if result.is_suitable else '✗'} (score: {result.quality_score:.2f})")
            
            return result
            
        except Exception as e:
            logger.error(f"Error screening document {document.doc_id}: {e}")
            return self._create_default_result(document.doc_id, False, f"Screening error: {e}")
    
    def _create_screening_prompt(self, document: DocumentData) -> str:
        """Create prompt for document screening focused on objective fact potential"""
        
        # Truncate content for prompt efficiency  
        content_preview = document.content[:1200]
        if len(document.content) > 1200:
            content_preview += "... [content truncated]"
        
        prompt = f"""
Assess this document's suitability for extracting precise, objective facts that can generate definitive questions.

DOCUMENT ID: {document.doc_id}
CONTENT SAMPLE:
{content_preview}

FACT EXTRACTION POTENTIAL:
Evaluate presence of CONCRETE, VERIFIABLE information including:
- SPECIFIC NAMES: People, companies, products, locations, organizations  
- QUANTIFIABLE DATA: Numbers, measurements, dates, statistics, prices
- TECHNICAL DETAILS: Model numbers, specifications, versions, features
- FACTUAL STATEMENTS: Clear, objective claims that can be verified

AUTOMATIC REJECTION CRITERIA:
- Advertisement/marketing content
- Error pages or technical glitches  
- Opinion pieces without factual basis
- How-to guides or process descriptions
- Abstract discussions lacking concrete data
- Corrupted or unintelligible text
- Pure navigation/menu content

QUALITY ASSESSMENT FOCUS:
- Can multiple objective facts be identified?
- Are facts specific enough for unique identification?
- Is information verifiable through external sources?
- Does content avoid subjective interpretations?

Evaluation response in JSON format:
{{
    "is_suitable": true/false,
    "quality_score": 0.0-1.0,
    "reasoning": "concise factual assessment",
    "potential_answers": ["extractable", "factual", "elements"],
    "content_type": "factual/biographical/technical/news/promotional/error/abstract",
    "issues": ["specific", "quality", "problems"],
    "fact_categories_present": ["names", "numbers", "dates", "locations", "specifications"]
}}

Priority: Documents with high density of verifiable, objective facts suitable for definitive question-answer pairs.
"""
        
        return prompt
    
    def _call_llm_for_screening(self, prompt: str) -> str:
        """Call LLM API for document screening"""
        try:
            # Wait to respect rate limits
            time.sleep(0.5)
            
            response = self.api_client.generate_response(
                prompt=prompt,
                temperature=0.3,
                max_tokens=500
            )
            
            return response
            
        except Exception as e:
            logger.error(f"LLM API call failed: {e}")
            raise
    
    def _parse_screening_response(self, doc_id: str, response: str) -> ScreeningResult:
        """Parse LLM response for screening result"""
        try:
            # Try to extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_text = response[json_start:json_end]
                screening_data = json.loads(json_text)
            else:
                # Fallback parsing if JSON is not found
                screening_data = self._fallback_parse_response(response)
            
            # Validate and extract fields
            is_suitable = bool(screening_data.get('is_suitable', False))
            quality_score = float(screening_data.get('quality_score', 0.0))
            reasoning = str(screening_data.get('reasoning', 'No reasoning provided'))
            potential_answers = screening_data.get('potential_answers', [])
            content_type = str(screening_data.get('content_type', 'unknown'))
            issues = screening_data.get('issues', [])
            
            # Ensure lists are actually lists
            if not isinstance(potential_answers, list):
                potential_answers = []
            if not isinstance(issues, list):
                issues = [str(issues)] if issues else []
            
            # Validate quality score range
            quality_score = max(0.0, min(1.0, quality_score))
            
            return ScreeningResult(
                doc_id=doc_id,
                is_suitable=is_suitable,
                quality_score=quality_score,
                reasoning=reasoning,
                potential_answers=potential_answers,
                content_type=content_type,
                issues=issues
            )
            
        except Exception as e:
            logger.warning(f"Failed to parse screening response for {doc_id}: {e}")
            logger.debug(f"Response was: {response}")
            return self._create_default_result(doc_id, False, f"Parse error: {e}")
    
    def _fallback_parse_response(self, response: str) -> Dict:
        """Fallback parsing when JSON extraction fails"""
        # Simple heuristic parsing
        is_suitable = any(word in response.lower() for word in ['suitable', 'good', 'yes', 'true'])
        
        # Extract potential score
        quality_score = 0.5  # Default
        import re
        score_match = re.search(r'(\d+\.?\d*)', response)
        if score_match:
            try:
                quality_score = float(score_match.group(1))
                if quality_score > 1.0:
                    quality_score = quality_score / 10.0  # Assume 0-10 scale
            except:
                pass
        
        return {
            'is_suitable': is_suitable,
            'quality_score': quality_score,
            'reasoning': 'Fallback parsing used',
            'potential_answers': [],
            'content_type': 'unknown',
            'issues': ['Parsing difficulties']
        }
    
    def _create_default_result(self, doc_id: str, is_suitable: bool, reason: str) -> ScreeningResult:
        """Create a default screening result"""
        return ScreeningResult(
            doc_id=doc_id,
            is_suitable=is_suitable,
            quality_score=0.0,
            reasoning=reason,
            potential_answers=[],
            content_type="unknown",
            issues=[reason]
        )
    
    def screen_documents(self, documents: List[DocumentData]) -> List[ScreeningResult]:
        """Screen multiple documents"""
        logger.info(f"Screening {len(documents)} documents")
        
        results = []
        suitable_count = 0
        
        for i, document in enumerate(documents):
            logger.info(f"Processing document {i+1}/{len(documents)}: {document.doc_id}")
            
            result = self.screen_document(document)
            results.append(result)
            
            if result.is_suitable:
                suitable_count += 1
            
            # Progress update
            if (i + 1) % 10 == 0:
                logger.info(f"Progress: {i+1}/{len(documents)} documents screened, {suitable_count} suitable")
        
        logger.info(f"Screening completed: {suitable_count}/{len(documents)} documents suitable")
        
        return results
    
    def filter_suitable_documents(self, documents: List[DocumentData], results: List[ScreeningResult]) -> List[DocumentData]:
        """Filter documents based on screening results"""
        suitable_docs = []
        
        # Create mapping of doc_id to result
        result_map = {result.doc_id: result for result in results}
        
        for document in documents:
            result = result_map.get(document.doc_id)
            if result and result.is_suitable and result.quality_score >= self.config.document_quality_threshold:
                suitable_docs.append(document)
        
        logger.info(f"Filtered to {len(suitable_docs)} suitable documents (threshold: {self.config.document_quality_threshold})")
        
        return suitable_docs
    
    def get_screening_statistics(self, results: List[ScreeningResult]) -> Dict:
        """Get statistics about screening results"""
        if not results:
            return {}
        
        suitable_results = [r for r in results if r.is_suitable]
        unsuitable_results = [r for r in results if not r.is_suitable]
        
        # Content type distribution
        content_types = {}
        for result in results:
            content_type = result.content_type
            content_types[content_type] = content_types.get(content_type, 0) + 1
        
        # Common issues
        all_issues = []
        for result in results:
            all_issues.extend(result.issues)
        
        issue_counts = {}
        for issue in all_issues:
            issue_counts[issue] = issue_counts.get(issue, 0) + 1
        
        # Quality score distribution
        quality_scores = [r.quality_score for r in results]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        return {
            "total_documents": len(results),
            "suitable_documents": len(suitable_results),
            "unsuitable_documents": len(unsuitable_results),
            "suitability_rate": len(suitable_results) / len(results) if results else 0,
            "average_quality_score": avg_quality,
            "content_type_distribution": content_types,
            "common_issues": dict(sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:10]),
            "quality_threshold_passed": len([r for r in results if r.quality_score >= self.config.document_quality_threshold])
        }
    
    def save_screening_results(self, results: List[ScreeningResult], output_file: str):
        """Save screening results to file"""
        try:
            results_data = []
            for result in results:
                results_data.append({
                    "doc_id": result.doc_id,
                    "is_suitable": result.is_suitable,
                    "quality_score": result.quality_score,
                    "reasoning": result.reasoning,
                    "potential_answers": result.potential_answers,
                    "content_type": result.content_type,
                    "issues": result.issues
                })
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Screening results saved to {output_file}")
            
        except Exception as e:
            logger.error(f"Failed to save screening results: {e}")

def test_document_screener():
    """Test function for document screener"""
    # Mock API client for testing
    class MockAPIClient:
        def generate_response(self, prompt, temperature=0.3, max_tokens=500):
            return '''
            {
                "is_suitable": true,
                "quality_score": 0.8,
                "reasoning": "This document contains factual information about technology with specific numbers and names that can serve as objective answers.",
                "potential_answers": ["2023", "Apple", "iPhone", "15"],
                "content_type": "technical",
                "issues": [],
                "fact_categories_present": ["names", "numbers", "dates", "locations", "specifications"]
            }
            '''
    
    # Create test document
            from .document_loader import DocumentData
    test_doc = DocumentData(
        doc_id="test_doc_001",
        file_path="/test/path",
        content="Apple announced the iPhone 15 in 2023 with improved camera capabilities and 48MP main sensor.",
        topic="en0001",
        length=95
    )
    
    # Test screening
    screener = DocumentScreener(MockAPIClient())
    result = screener.screen_document(test_doc)
    
    print(f"Screening result for {test_doc.doc_id}:")
    print(f"  Suitable: {result.is_suitable}")
    print(f"  Quality Score: {result.quality_score}")
    print(f"  Reasoning: {result.reasoning}")
    print(f"  Content Type: {result.content_type}")
    print(f"  Potential Answers: {result.potential_answers}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_document_screener() 
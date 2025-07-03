#!/usr/bin/env python3
"""
Answer Generation System for Deep Research Questions
Generates comprehensive answers based on domain reports for benchmark evaluation
"""

import json
import requests
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'core'))

from llm_clients.openai_api_client import OpenAIClient, get_difficulty_specific_system_prompt

class AnswerGenerationSystem:
    """System for generating comprehensive answers to deep research questions"""
    
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.api_key = api_key
        self.model = model
        self.openai_client = OpenAIClient(api_key, model)
        
    def generate_answer(self, question_data: Dict[str, Any], domain_report: str, 
                       topic_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a comprehensive answer for a research question with optimized prompts
        
        Args:
            question_data: Question information including text, difficulty, type
            domain_report: Domain report content for context
            topic_info: Topic metadata
            
        Returns:
            Dictionary containing answer and metadata
        """
        
        question_text = question_data.get('question_text', '')
        difficulty = question_data.get('difficulty', 'Medium')
        question_type = question_data.get('question_type', 'General')
        rationale = question_data.get('rationale', '')
        
        # Get difficulty-specific system prompt
        system_prompt = get_difficulty_specific_system_prompt(difficulty)
        
        # Create enhanced user prompt with explicit length requirements
        word_requirements = {
            'Easy': '400-600 words',
            'Medium': '800-1200 words', 
            'Hard': '1500-2000 words'
        }
        
        user_prompt = f"""Based on the domain report provided below, answer the following research question with a comprehensive, evidence-based analysis.

**QUESTION**: {question_text}

**QUESTION TYPE**: {question_type}
**DIFFICULTY LEVEL**: {difficulty}
**REQUIRED LENGTH**: {word_requirements.get(difficulty, '800-1200 words')}
**RATIONALE**: {rationale}

**DOMAIN REPORT**:
{domain_report}

**TOPIC CONTEXT**:
- Domain: {topic_info.get('domain', 'Unknown')}
- Document Count: {topic_info.get('document_count', 'Unknown')}
- Language: {topic_info.get('language', 'Unknown')}

**INSTRUCTIONS**:

1. **CRITICAL LENGTH REQUIREMENT**: Your response MUST meet the {word_requirements.get(difficulty, '800-1200 words')} requirement. This is essential for proper evaluation.

2. **Structure Requirements**:
   - **Introduction & Context**: Establish significance and approach
   - **Evidence-Based Analysis**: Detailed examination using domain report insights
   - **Synthesis & Integration**: Connect patterns and relationships
   - **Critical Evaluation**: Assess strengths, limitations, methodological considerations
   - **Conclusion**: Synthesize key findings and insights

3. **Quality Standards**:
   - Cite the domain report extensively throughout your analysis
   - Demonstrate deep research thinking with multi-step reasoning
   - Provide comprehensive coverage of all relevant aspects
   - Maintain academic rigor and analytical depth

4. **Length Verification**: After writing, ensure your response meets the {word_requirements.get(difficulty, '800-1200 words')} requirement. If too short, expand with additional analysis, examples, or deeper exploration of concepts.

Provide a thorough, well-structured analysis that fully addresses the research question while meeting all requirements."""

        # Generate answer with increased token limit
        max_tokens = self._get_max_tokens_for_difficulty(difficulty)
        
        answer_text = self.openai_client.generate_content(
            prompt=user_prompt,
            system_prompt=system_prompt,
            max_tokens=max_tokens,
            temperature=0.7
        )
        
        if not answer_text:
            return {
                'text': '',
                'status': 'failed',
                'generation_timestamp': datetime.now().isoformat(),
                'quality_metrics': {},
                'structural_analysis': {}
            }
        
        # Analyze answer quality
        quality_metrics = self._analyze_answer_quality(
            answer_text, difficulty, question_type
        )
        
        structural_analysis = self._analyze_answer_structure(answer_text)
        
        return {
            'text': answer_text,
            'status': 'success',
            'generation_timestamp': datetime.now().isoformat(),
            'quality_metrics': quality_metrics,
            'structural_analysis': structural_analysis
        }
    
    def _get_max_tokens_for_difficulty(self, difficulty: str) -> int:
        """Get appropriate max tokens based on difficulty level"""
        token_limits = {
            'Easy': 1000,    # ~400-600 words
            'Medium': 2000,  # ~800-1200 words  
            'Hard': 3500     # ~1500-2000 words
        }
        return token_limits.get(difficulty, 2000)
    
    def generate_answers_for_topic(self, topic_data: Dict[str, Any], 
                                 domain_report: str) -> Dict[str, Any]:
        """
        Generate comprehensive answers for all questions in a topic
        
        Args:
            topic_data: Topic information including questions
            domain_report: The domain report to base answers on
            
        Returns:
            Topic data with generated answers
        """
        
        print(f"🔄 Generating answers for topic: {topic_data.get('topic_id', 'Unknown')}")
        
        questions = topic_data.get('questions', [])
        if not questions:
            print("   ⚠️ No questions found for this topic")
            return topic_data
        
        # Generate answers for each question
        answered_questions = []
        
        for i, question in enumerate(questions, 1):
            print(f"   Processing question {i}/{len(questions)}")
            
            try:
                answer_data = self._generate_single_answer(
                    question, domain_report, topic_data
                )
                
                if answer_data:
                    question_with_answer = question.copy()
                    question_with_answer['answer'] = answer_data
                    answered_questions.append(question_with_answer)
                else:
                    # Keep question without answer if generation fails
                    question['answer'] = {
                        'text': 'Answer generation failed',
                        'status': 'failed',
                        'timestamp': datetime.now().isoformat()
                    }
                    answered_questions.append(question)
                    
            except Exception as e:
                print(f"     ⚠️ Error generating answer: {e}")
                question['answer'] = {
                    'text': f'Error: {str(e)}',
                    'status': 'error',
                    'timestamp': datetime.now().isoformat()
                }
                answered_questions.append(question)
            
            # Rate limiting
            time.sleep(1)
        
        # Update topic data with answered questions
        result_topic_data = topic_data.copy()
        result_topic_data['questions'] = answered_questions
        result_topic_data['answer_generation_status'] = 'completed'
        result_topic_data['answer_generation_timestamp'] = datetime.now().isoformat()
        
        successful_answers = sum(1 for q in answered_questions 
                               if q.get('answer', {}).get('status') == 'success')
        
        print(f"   ✅ Generated {successful_answers}/{len(questions)} answers successfully")
        
        return result_topic_data
    
    def _generate_single_answer(self, question: Dict[str, Any], 
                              domain_report: str, 
                              topic_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate a comprehensive answer for a single question"""
        
        question_text = question.get('question_text', '')
        difficulty = question.get('difficulty', 'Medium')
        question_type = question.get('question_type', 'Unknown')
        
        if not question_text:
            return None
        
        # Create answer generation prompt
        answer_prompt = self._create_answer_prompt(
            question_text, difficulty, question_type, domain_report, topic_data
        )
        
        # Call API to generate answer
        response = self._call_openai_api(answer_prompt)
        
        if not response:
            return None
        
        # Parse and structure the answer
        answer_data = self._parse_answer_response(response, difficulty)
        
        return answer_data
    
    def _create_answer_prompt(self, question_text: str, difficulty: str, 
                            question_type: str, domain_report: str, 
                            topic_data: Dict[str, Any]) -> str:
        """Create comprehensive prompt for answer generation"""
        
        domain_info = topic_data.get('topic_info', {})
        topic_id = topic_data.get('topic_id', 'Unknown')
        
        prompt = f"""You are a world-class researcher and expert in the domain covered by this report. Your task is to provide a comprehensive, research-grade answer to the given question based EXCLUSIVELY on the provided domain report.

DOMAIN CONTEXT:
- Topic ID: {topic_id}
- Primary Domain: {domain_info.get('primary_domain', 'Unknown')}
- Key Themes: {', '.join(domain_info.get('key_themes', []))}
- Scope: {domain_info.get('scope', 'Unknown')}

QUESTION TO ANSWER:
{question_text}

QUESTION METADATA:
- Difficulty Level: {difficulty}
- Question Type: {question_type}

DOMAIN REPORT (YOUR KNOWLEDGE BASE):
{domain_report}

ANSWER REQUIREMENTS:

For {difficulty} difficulty questions, provide:

{"**COMPREHENSIVE ANALYSIS** (1500-2000 words):" if difficulty == "Hard" else "**DETAILED ANALYSIS** (800-1200 words):" if difficulty == "Medium" else "**FOCUSED ANALYSIS** (400-600 words):"}

1. **INTRODUCTION & CONTEXT**
   - Establish the question's significance within the domain
   - Provide necessary background from the report
   - Outline your analytical approach

2. **EVIDENCE-BASED ANALYSIS**
   - Draw specific evidence from the domain report
   - Cite relevant sections and findings
   - Present multiple perspectives where applicable

3. **SYNTHESIS & INTEGRATION**
   - Connect different aspects covered in the report
   - Identify patterns, relationships, and implications
   - Address the question's core components systematically

{"4. **CRITICAL EVALUATION**" if difficulty in ["Medium", "Hard"] else ""}
{"   - Assess strengths and limitations of available evidence" if difficulty in ["Medium", "Hard"] else ""}
{"   - Discuss methodological considerations" if difficulty in ["Medium", "Hard"] else ""}
{"   - Identify areas of uncertainty or debate" if difficulty in ["Medium", "Hard"] else ""}

{"5. **MULTI-DIMENSIONAL PERSPECTIVE**" if difficulty == "Hard" else ""}
{"   - Consider interdisciplinary implications" if difficulty == "Hard" else ""}
{"   - Examine systemic relationships and interactions" if difficulty == "Hard" else ""}
{"   - Address potential future developments" if difficulty == "Hard" else ""}

{len(str(difficulty)) + 3}. **CONCLUSION**
   - Synthesize key findings
   - Provide a clear, evidence-based response to the question
   - Highlight the most significant insights

CRITICAL CONSTRAINTS:
- Base your answer EXCLUSIVELY on information from the provided domain report
- Do not introduce external knowledge not present in the report
- If the report lacks sufficient information, explicitly state this limitation
- Maintain academic rigor and cite specific sections of the report
- Ensure your answer demonstrates the deep research capabilities expected for {difficulty} level questions

Your answer should demonstrate sophisticated understanding and analysis that would require multiple steps of reasoning to arrive at, making it suitable for evaluating LLM deep research capabilities.

COMPREHENSIVE ANSWER:"""

        return prompt
    
    def _call_openai_api(self, prompt: str) -> Optional[str]:
        """Call OpenAI API for answer generation"""
        
        return self.openai_client.generate_with_retry(
            prompt=prompt,
            system_prompt="You are an expert researcher providing comprehensive answers to deep research questions.",
            max_tokens=4000,
            temperature=0.7,
            max_retries=3,
            retry_delay=2.0
        )
    
    def _parse_answer_response(self, response: str, difficulty: str) -> Dict[str, Any]:
        """Parse and structure the answer response"""
        
        # Clean up the response
        answer_text = response.strip()
        
        # Extract quality metrics
        word_count = len(answer_text.split())
        char_count = len(answer_text)
        
        # Check for structural elements
        has_sections = any(marker in answer_text for marker in 
                          ['##', '###', '1.', '2.', '3.', '**', 'Introduction', 'Conclusion'])
        
        has_citations = any(marker in answer_text for marker in 
                           ['report', 'section', 'findings', 'evidence', 'according to'])
        
        # Assess answer quality based on difficulty expectations
        expected_word_ranges = {
            'Easy': (400, 600),
            'Medium': (800, 1200),
            'Hard': (1500, 2000)
        }
        
        expected_min, expected_max = expected_word_ranges.get(difficulty, (600, 1000))
        meets_length_requirement = expected_min <= word_count <= expected_max * 1.2  # Allow 20% over
        
        # Determine answer quality
        quality_score = 0.0
        if meets_length_requirement:
            quality_score += 0.4
        if has_sections:
            quality_score += 0.3
        if has_citations:
            quality_score += 0.3
        
        quality_level = 'high' if quality_score >= 0.8 else 'medium' if quality_score >= 0.5 else 'low'
        
        answer_data = {
            'text': answer_text,
            'status': 'success',
            'generation_timestamp': datetime.now().isoformat(),
            'quality_metrics': {
                'word_count': word_count,
                'char_count': char_count,
                'has_sections': has_sections,
                'has_citations': has_citations,
                'meets_length_requirement': meets_length_requirement,
                'quality_score': quality_score,
                'quality_level': quality_level,
                'expected_word_range': f"{expected_min}-{expected_max}",
                'difficulty_level': difficulty
            },
            'structural_analysis': {
                'sections_detected': self._detect_sections(answer_text),
                'citation_count': self._count_citations(answer_text),
                'conclusion_present': 'conclusion' in answer_text.lower()
            }
        }
        
        return answer_data
    
    def _detect_sections(self, text: str) -> List[str]:
        """Detect structural sections in the answer"""
        sections = []
        
        section_indicators = [
            'introduction', 'context', 'background',
            'analysis', 'evidence', 'findings',
            'synthesis', 'integration', 'evaluation',
            'perspective', 'implications', 'conclusion'
        ]
        
        text_lower = text.lower()
        for indicator in section_indicators:
            if indicator in text_lower:
                sections.append(indicator)
        
        return sections
    
    def _count_citations(self, text: str) -> int:
        """Count citation-like references in the answer"""
        citation_indicators = [
            'report', 'section', 'findings', 'evidence', 
            'according to', 'as noted', 'documented', 'observed'
        ]
        
        text_lower = text.lower()
        citation_count = sum(text_lower.count(indicator) for indicator in citation_indicators)
        
        return citation_count

    def _analyze_answer_quality(self, answer_text: str, difficulty: str, question_type: str) -> Dict[str, Any]:
        """Analyze the quality metrics of generated answer"""
        
        word_count = len(answer_text.split())
        char_count = len(answer_text)
        
        # Check for structural elements
        has_sections = any(marker in answer_text for marker in 
                          ['##', '###', '1.', '2.', '3.', '**', 'Introduction', 'Conclusion'])
        
        has_citations = any(marker in answer_text for marker in 
                           ['report', 'section', 'findings', 'evidence', 'according to'])
        
        # Assess length requirements based on difficulty
        expected_word_ranges = {
            'Easy': (400, 600),
            'Medium': (800, 1200),
            'Hard': (1500, 2000)
        }
        
        expected_min, expected_max = expected_word_ranges.get(difficulty, (600, 1000))
        meets_length_requirement = expected_min <= word_count <= expected_max * 1.2  # Allow 20% over
        
        # Calculate quality score
        quality_score = 0.0
        if meets_length_requirement:
            quality_score += 0.4
        if has_sections:
            quality_score += 0.3
        if has_citations:
            quality_score += 0.3
        
        quality_level = 'high' if quality_score >= 0.8 else 'medium' if quality_score >= 0.5 else 'low'
        
        return {
            'word_count': word_count,
            'char_count': char_count,
            'has_sections': has_sections,
            'has_citations': has_citations,
            'meets_length_requirement': meets_length_requirement,
            'quality_score': quality_score,
            'quality_level': quality_level,
            'expected_word_range': f"{expected_min}-{expected_max}",
            'difficulty_level': difficulty
        }
    
    def _analyze_answer_structure(self, answer_text: str) -> Dict[str, Any]:
        """Analyze structural elements of the answer"""
        
        return {
            'sections_detected': self._detect_sections(answer_text),
            'citation_count': self._count_citations(answer_text),
            'conclusion_present': 'conclusion' in answer_text.lower(),
            'paragraph_count': len([p for p in answer_text.split('\n\n') if p.strip()]),
            'has_headings': any(marker in answer_text for marker in ['##', '###', '**'])
        }

def generate_answers_for_all_topics(topics_with_reports: Dict[str, Any], 
                                  api_key: str) -> Dict[str, Any]:
    """
    Generate answers for all topics and questions
    
    Args:
        topics_with_reports: Dictionary containing topics with their reports and questions
        api_key: Claude API key
        
    Returns:
        Complete dataset with questions and answers
    """
    
    print("🚀 Starting Answer Generation for All Topics")
    print("=" * 50)
    
    answer_generator = AnswerGenerationSystem(api_key)
    
    results = {
        'generation_metadata': {
            'generation_timestamp': datetime.now().isoformat(),
            'system_version': '1.0',
            'total_topics': 0,
            'total_questions': 0,
            'total_answers_generated': 0
        },
        'topics': {}
    }
    
    total_topics = 0
    total_questions = 0
    total_successful_answers = 0
    
    for topic_id, topic_data in topics_with_reports.items():
        if 'domain_report' not in topic_data or 'questions' not in topic_data:
            print(f"⚠️ Skipping {topic_id} - missing report or questions")
            continue
        
        total_topics += 1
        topic_questions = len(topic_data['questions'])
        total_questions += topic_questions
        
        print(f"\n📝 Processing Topic: {topic_id}")
        print(f"   Questions to answer: {topic_questions}")
        
        # Generate answers for this topic
        topic_with_answers = answer_generator.generate_answers_for_topic(
            topic_data, topic_data['domain_report']
        )
        
        # Count successful answers
        successful_answers = sum(1 for q in topic_with_answers['questions'] 
                               if q.get('answer', {}).get('status') == 'success')
        total_successful_answers += successful_answers
        
        # Store results
        results['topics'][topic_id] = topic_with_answers
        
        print(f"   ✅ Generated {successful_answers}/{topic_questions} answers")
    
    # Update metadata
    results['generation_metadata'].update({
        'total_topics': total_topics,
        'total_questions': total_questions,
        'total_answers_generated': total_successful_answers,
        'success_rate': (total_successful_answers / total_questions * 100) if total_questions > 0 else 0
    })
    
    print(f"\n🎯 Answer Generation Summary:")
    print(f"   Topics processed: {total_topics}")
    print(f"   Total questions: {total_questions}")
    print(f"   Successful answers: {total_successful_answers}")
    print(f"   Success rate: {results['generation_metadata']['success_rate']:.1f}%")
    
    return results

def save_complete_qa_dataset(qa_dataset: Dict[str, Any], 
                           output_path: str = None) -> str:
    """
    Save the complete QA dataset with questions and answers
    
    Args:
        qa_dataset: Complete dataset with questions and answers
        output_path: Optional output file path
        
    Returns:
        Path to saved file
    """
    
    if not output_path:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"complete_qa_dataset_{timestamp}.json"
    
    # Prepare final dataset structure
    final_dataset = {
        'dataset_metadata': {
            'dataset_name': 'Deep Research QA Benchmark',
            'version': '1.0',
            'creation_timestamp': datetime.now().isoformat(),
            'description': 'High-quality question-answer pairs for evaluating LLM deep research capabilities',
            'total_topics': qa_dataset['generation_metadata']['total_topics'],
            'total_qa_pairs': qa_dataset['generation_metadata']['total_questions'],
            'success_rate': qa_dataset['generation_metadata']['success_rate']
        },
        
        'topics': qa_dataset['topics'],
        
        'quality_summary': _generate_quality_summary(qa_dataset),
        
        'usage_instructions': {
            'purpose': 'Benchmark for evaluating LLM deep research capabilities',
            'difficulty_levels': ['Easy', 'Medium', 'Hard'],
            'expected_reasoning': 'Multi-step thinking required for Medium and Hard questions',
            'evaluation_focus': 'Deep research and analytical capabilities'
        }
    }
    
    # Save to file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_dataset, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Complete QA dataset saved to: {output_path}")
    
    return output_path

def _generate_quality_summary(qa_dataset: Dict[str, Any]) -> Dict[str, Any]:
    """Generate quality summary for the dataset"""
    
    total_questions = 0
    difficulty_distribution = {'Easy': 0, 'Medium': 0, 'Hard': 0}
    quality_distribution = {'high': 0, 'medium': 0, 'low': 0}
    avg_word_count_by_difficulty = {'Easy': [], 'Medium': [], 'Hard': []}
    
    for topic_id, topic_data in qa_dataset['topics'].items():
        for question in topic_data.get('questions', []):
            total_questions += 1
            
            difficulty = question.get('difficulty', 'Medium')
            difficulty_distribution[difficulty] = difficulty_distribution.get(difficulty, 0) + 1
            
            answer = question.get('answer', {})
            if answer.get('status') == 'success':
                quality_metrics = answer.get('quality_metrics', {})
                quality_level = quality_metrics.get('quality_level', 'medium')
                quality_distribution[quality_level] = quality_distribution.get(quality_level, 0) + 1
                
                word_count = quality_metrics.get('word_count', 0)
                if difficulty in avg_word_count_by_difficulty:
                    avg_word_count_by_difficulty[difficulty].append(word_count)
    
    # Calculate averages
    avg_word_counts = {}
    for difficulty, word_counts in avg_word_count_by_difficulty.items():
        avg_word_counts[difficulty] = sum(word_counts) / len(word_counts) if word_counts else 0
    
    return {
        'total_questions': total_questions,
        'difficulty_distribution': difficulty_distribution,
        'quality_distribution': quality_distribution,
        'average_word_count_by_difficulty': avg_word_counts,
        'quality_percentage': {
            level: (count / total_questions * 100) if total_questions > 0 else 0
            for level, count in quality_distribution.items()
        }
    }

def main():
    """Main function for testing answer generation"""
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python answer_generation_system.py <topics_with_reports.json> <api_key> [output_path]")
        return
    
    topics_file = sys.argv[1]
    api_key = sys.argv[2]
    output_path = sys.argv[3] if len(sys.argv) > 3 else None
    
    # Load topics with reports and questions
    with open(topics_file, 'r', encoding='utf-8') as f:
        topics_data = json.load(f)
    
    # Generate answers
    qa_dataset = generate_answers_for_all_topics(topics_data, api_key)
    
    # Save complete dataset
    saved_path = save_complete_qa_dataset(qa_dataset, output_path)
    
    print(f"\n🎉 Complete QA dataset ready: {saved_path}")

if __name__ == "__main__":
    main() 
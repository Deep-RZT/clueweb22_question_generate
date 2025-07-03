#!/usr/bin/env python3
"""
Question Refinement and Regeneration System
Automatically improves questions based on deep research evaluation results
"""

import json
import requests
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
from deep_research_evaluation_framework import DeepResearchEvaluator, QuestionDepth
from ..llm_clients.openai_api_client import OpenAIClient

class QuestionRefinementSystem:
    """System for refining questions to meet deep research criteria"""
    
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.api_key = api_key
        self.model = model
        self.openai_client = OpenAIClient(api_key, model)
        self.evaluator = DeepResearchEvaluator()
        
    def refine_question_dataset(self, evaluation_results: Dict[str, Any], 
                              target_deep_percentage: float = 70.0,
                              max_iterations: int = 3) -> Dict[str, Any]:
        """
        Refine entire question dataset to meet deep research criteria
        
        Args:
            evaluation_results: Results from deep research evaluation
            target_deep_percentage: Target percentage of deep research questions
            max_iterations: Maximum refinement iterations
            
        Returns:
            Refined dataset with improved questions
        """
        
        print(f"🔧 Starting question refinement process...")
        print(f"   Target: {target_deep_percentage}% deep research questions")
        print(f"   Max iterations: {max_iterations}")
        
        current_results = evaluation_results.copy()
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            print(f"\n🔄 Refinement Iteration {iteration}")
            
            # Get current statistics
            current_deep_percentage = current_results['summary_statistics'].get('percentage_deep', 0.0)
            print(f"   Current deep research percentage: {current_deep_percentage:.1f}%")
            
            if current_deep_percentage >= target_deep_percentage:
                print(f"✅ Target achieved! Deep research percentage: {current_deep_percentage:.1f}%")
                break
            
            # Identify questions that need refinement
            questions_to_refine = current_results.get('recommended_actions', [])
            
            # If no recommended_actions, identify low-scoring questions
            if not questions_to_refine or not isinstance(questions_to_refine, list):
                evaluations = current_results.get('evaluations', [])
                questions_to_refine = [
                    e for e in evaluations 
                    if e.get('depth_scores', {}).get('overall_depth', 0) < 0.4
                ]
            
            print(f"   Questions to refine: {len(questions_to_refine)}")
            
            if not questions_to_refine:
                print("   No questions identified for refinement")
                break
            
            # Refine questions in batches
            refined_questions = []
            batch_size = 10
            
            for i in range(0, len(questions_to_refine), batch_size):
                batch = questions_to_refine[i:i+batch_size]
                print(f"   Processing batch {i//batch_size + 1}: {len(batch)} questions")
                
                batch_refined = self._refine_question_batch(batch)
                refined_questions.extend(batch_refined)
                
                # Rate limiting
                time.sleep(2)
            
            # Update dataset with refined questions
            current_results = self._update_dataset_with_refined_questions(
                current_results, refined_questions
            )
            
            # Re-evaluate the updated dataset
            print(f"   Re-evaluating refined questions...")
            current_results = self._re_evaluate_dataset(current_results)
        
        # Final statistics
        final_deep_percentage = current_results['summary_statistics'].get('percentage_deep', 0.0)
        print(f"\n🎯 Refinement Complete!")
        print(f"   🎯 Final deep research percentage: {final_deep_percentage:.1f}%")
        print(f"   Improvement: {final_deep_percentage - evaluation_results['summary_statistics'].get('percentage_deep', 0.0):.1f} percentage points")
        
        return current_results
    
    def _refine_question_batch(self, questions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Refine a batch of questions using AI"""
        
        refined_questions = []
        
        for question_data in questions:
            try:
                refined_question = self._refine_single_question(question_data)
                if refined_question:
                    refined_questions.append(refined_question)
                else:
                    # Keep original if refinement fails
                    refined_questions.append(question_data)
                    
            except Exception as e:
                print(f"   ⚠️ Error refining question: {e}")
                refined_questions.append(question_data)  # Keep original
                
        return refined_questions
    
    def _refine_single_question(self, question_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Refine a single question to increase research depth"""
        
        original_question = question_data['question_text']
        current_score = question_data['depth_scores']['overall_depth']
        recommendations = question_data['recommendations']['suggestions']
        
        # Create refinement prompt
        refinement_prompt = self._create_refinement_prompt(
            original_question, current_score, recommendations
        )
        
        # Call API to refine question
        response = self._call_openai_api(refinement_prompt)
        
        if not response:
            return None
        
        # Parse refined question
        refined_question_text = self._parse_refined_question(response)
        
        if not refined_question_text:
            return None
        
        # Evaluate refined question
        evaluation = self.evaluator.evaluate_question(refined_question_text)
        
        # Only accept if improvement is significant
        if evaluation['depth_scores']['overall_depth'] > current_score + 0.1:
            # Create refined question data
            refined_data = question_data.copy()
            refined_data.update({
                'question_text': refined_question_text,
                'depth_scores': evaluation['depth_scores'],
                'classifications': evaluation['classifications'],
                'analysis_details': evaluation['analysis_details'],
                'recommendations': evaluation['recommendations'],
                'refinement_history': {
                    'original_question': original_question,
                    'original_score': current_score,
                    'refined_score': evaluation['depth_scores']['overall_depth'],
                    'improvement': evaluation['depth_scores']['overall_depth'] - current_score,
                    'refinement_timestamp': datetime.now().isoformat()
                }
            })
            
            return refined_data
        
        return None  # No significant improvement
    
    def _create_refinement_prompt(self, original_question: str, current_score: float, 
                                recommendations: List[str]) -> str:
        """Create prompt for question refinement"""
        
        prompt = f"""You are an expert in creating deep research questions for academic benchmarks. Your task is to refine the given question to increase its research depth and complexity.

ORIGINAL QUESTION:
{original_question}

CURRENT DEPTH SCORE: {current_score:.3f} (out of 1.0)

IMPROVEMENT RECOMMENDATIONS:
{chr(10).join(f"• {rec}" for rec in recommendations)}

REFINEMENT GUIDELINES:
1. **Increase Cognitive Complexity**: Add analytical components (analyze, evaluate, compare, synthesize)
2. **Add Synthesis Requirements**: Require integration of multiple perspectives or sources
3. **Include Systems Thinking**: Focus on relationships, interactions, and interdependencies
4. **Add Conditional Elements**: Include contextual or conditional complexity
5. **Increase Domain Expertise**: Add technical depth and methodological considerations
6. **Ensure Research Value**: Make sure the question addresses meaningful research gaps

QUALITY CRITERIA FOR DEEP RESEARCH QUESTIONS:
- Requires cross-document synthesis and analysis
- Involves critical reasoning and evaluation
- Addresses complex systems or methodological understanding
- Has clear research value and significance
- Cannot be answered with simple fact lookup
- Requires domain expertise to answer comprehensively

Please provide a refined version of the question that significantly increases its research depth while maintaining clarity and focus. The refined question should score >0.7 on the depth scale.

REFINED QUESTION:"""

        return prompt
    
    def _call_openai_api(self, prompt: str) -> Optional[str]:
        """Call OpenAI API for question refinement"""
        
        return self.openai_client.generate_with_retry(
            prompt=prompt,
            system_prompt="You are an expert question designer tasked with refining research questions to meet deep research standards.",
            max_tokens=1000,
            temperature=0.7,
            max_retries=3,
            retry_delay=2.0
        )
    
    def _parse_refined_question(self, response: str) -> Optional[str]:
        """Parse refined question from API response"""
        
        # Look for the refined question after "REFINED QUESTION:"
        if "REFINED QUESTION:" in response:
            refined_part = response.split("REFINED QUESTION:")[-1].strip()
        else:
            refined_part = response.strip()
        
        # Clean up the response
        lines = refined_part.split('\n')
        question_lines = []
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('*'):
                question_lines.append(line)
        
        if question_lines:
            refined_question = ' '.join(question_lines)
            # Ensure it ends with a question mark
            if not refined_question.endswith('?'):
                refined_question += '?'
            return refined_question
        
        return None
    
    def _update_dataset_with_refined_questions(self, current_results: Dict[str, Any], 
                                             refined_questions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Update dataset with refined questions"""
        
        # Create mapping of original IDs to refined questions
        refined_map = {q['original_id']: q for q in refined_questions if 'refinement_history' in q}
        
        # Update detailed evaluations
        updated_evaluations = []
        for evaluation in current_results['detailed_evaluations']:
            original_id = evaluation.get('original_id', '')
            if original_id in refined_map:
                updated_evaluations.append(refined_map[original_id])
            else:
                updated_evaluations.append(evaluation)
        
        current_results['detailed_evaluations'] = updated_evaluations
        
        return current_results
    
    def _re_evaluate_dataset(self, dataset_results: Dict[str, Any]) -> Dict[str, Any]:
        """Re-evaluate dataset after refinement"""
        
        evaluations = dataset_results['detailed_evaluations']
        
        # Recalculate statistics
        total_questions = len(evaluations)
        deep_count = sum(1 for e in evaluations if e['classifications']['question_depth'] == 'deep')
        moderate_count = sum(1 for e in evaluations if e['classifications']['question_depth'] == 'moderate')
        simple_count = total_questions - deep_count - moderate_count
        
        # Calculate average scores
        avg_scores = {
            'cognitive_complexity': sum(e['depth_scores']['cognitive_complexity'] for e in evaluations) / total_questions,
            'research_depth': sum(e['depth_scores']['research_depth'] for e in evaluations) / total_questions,
            'synthesis_requirement': sum(e['depth_scores']['synthesis_requirement'] for e in evaluations) / total_questions,
            'expertise_requirement': sum(e['depth_scores']['expertise_requirement'] for e in evaluations) / total_questions,
            'overall_depth': sum(e['depth_scores']['overall_depth'] for e in evaluations) / total_questions
        }
        
        # Update summary statistics
        dataset_results['summary_statistics'] = {
            'depth_distribution': {
                'deep_research_questions': deep_count,
                'moderate_questions': moderate_count,
                'simple_questions': simple_count,
            },
            'percentage_deep': (deep_count / total_questions * 100) if total_questions > 0 else 0,
            'average_scores': avg_scores,
            'quality_threshold_met': avg_scores['overall_depth'] >= 0.5
        }
        
        # Update categorized questions
        dataset_results['deep_research_questions'] = [e for e in evaluations if e['classifications']['is_deep_research']]
        dataset_results['simple_questions'] = [e for e in evaluations if e['classifications']['question_depth'] == 'simple']
        
        # Update recommendations
        dataset_results['recommendations'] = {
            'questions_to_refine': [e for e in evaluations if e['depth_scores']['overall_depth'] < 0.4],
            'high_quality_questions': [e for e in evaluations if e['depth_scores']['overall_depth'] >= 0.7],
            'improvement_suggestions': self._generate_improvement_suggestions(evaluations)
        }
        
        return dataset_results
    
    def _generate_improvement_suggestions(self, evaluations: List[Dict]) -> List[str]:
        """Generate improvement suggestions for the dataset"""
        
        total_questions = len(evaluations)
        deep_count = sum(1 for e in evaluations if e['classifications']['question_depth'] == 'deep')
        simple_count = sum(1 for e in evaluations if e['classifications']['question_depth'] == 'simple')
        
        suggestions = []
        
        # Check deep research percentage
        deep_percentage = (deep_count / total_questions * 100) if total_questions > 0 else 0
        if deep_percentage < 30:
            suggestions.append(f"Increase deep research questions: currently {deep_percentage:.1f}%, target >30%")
        
        # Check simple question percentage
        simple_percentage = (simple_count / total_questions * 100) if total_questions > 0 else 0
        if simple_percentage > 20:
            suggestions.append(f"Reduce simple questions: currently {simple_percentage:.1f}%, target <20%")
        
        return suggestions

def generate_new_deep_questions(topic_info: Dict[str, Any], api_key: str, 
                              num_questions: int = 20) -> List[Dict[str, Any]]:
    """
    Generate new deep research questions for a specific topic
    
    Args:
        topic_info: Information about the topic/domain
        api_key: Claude API key
        num_questions: Number of questions to generate
        
    Returns:
        List of newly generated deep research questions
    """
    
    system = QuestionRefinementSystem(api_key)
    
    # Create generation prompt
    generation_prompt = f"""You are an expert in creating deep research questions for academic benchmarks. Generate {num_questions} high-quality, deep research questions for the following domain:

DOMAIN INFORMATION:
- Primary Domain: {topic_info.get('primary_domain', 'Unknown')}
- Key Themes: {', '.join(topic_info.get('key_themes', []))}
- Scope: {topic_info.get('scope', 'Unknown')}
- Complexity Level: {topic_info.get('complexity_level', 'Unknown')}

REQUIREMENTS FOR DEEP RESEARCH QUESTIONS:
1. **High Cognitive Complexity**: Must require analysis, synthesis, evaluation, or critical reasoning
2. **Cross-Document Synthesis**: Should require integration of multiple sources or perspectives
3. **Systems Thinking**: Focus on relationships, interactions, and complex systems
4. **Domain Expertise**: Require significant domain knowledge to answer comprehensively
5. **Research Value**: Address meaningful gaps or challenges in the field
6. **Methodological Depth**: Consider approaches, frameworks, or methodologies

QUESTION TYPES TO INCLUDE:
- Analytical: Breaking down complex topics into components
- Comparative: Comparing different approaches, methods, or systems
- Evaluative: Assessing effectiveness, value, or impact
- Synthetic: Combining multiple concepts or perspectives
- Predictive: Forecasting trends or future developments
- Critical: Examining limitations, assumptions, or biases

Please generate {num_questions} questions that meet these criteria. Each question should:
- Be clear and specific
- Require deep domain expertise
- Have significant research value
- Score >0.7 on depth evaluation criteria

Format each question on a separate line, numbered 1-{num_questions}."""

    # Call API
    response = system._call_openai_api(generation_prompt)
    
    if not response:
        return []
    
    # Parse questions
    questions = []
    lines = response.split('\n')
    
    for line in lines:
        line = line.strip()
        if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
            # Extract question text
            question_text = line
            # Remove numbering
            if '. ' in question_text:
                question_text = question_text.split('. ', 1)[1]
            elif '- ' in question_text:
                question_text = question_text.split('- ', 1)[1]
            elif '• ' in question_text:
                question_text = question_text.split('• ', 1)[1]
            
            question_text = question_text.strip()
            
            if question_text and len(question_text) > 20:
                # Evaluate the generated question
                evaluation = system.evaluator.evaluate_question(question_text, topic_info)
                
                question_data = {
                    'id': f'NEW_{len(questions)+1:03d}',
                    'question_text': question_text,
                    'generation_method': 'deep_research_focused',
                    'generation_timestamp': datetime.now().isoformat(),
                    'topic_info': topic_info,
                    **evaluation
                }
                
                questions.append(question_data)
    
    # Filter for high-quality questions
    high_quality_questions = [q for q in questions if q['depth_scores']['overall_depth'] >= 0.6]
    
    print(f"✅ Generated {len(questions)} questions, {len(high_quality_questions)} meet quality criteria")
    
    return high_quality_questions

def main():
    """Main function for testing the refinement system"""
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python question_refinement_system.py <evaluation_results.json> <api_key> [output_path]")
        return
    
    evaluation_file = sys.argv[1]
    api_key = sys.argv[2]
    output_path = sys.argv[3] if len(sys.argv) > 3 else None
    
    # Load evaluation results
    with open(evaluation_file, 'r', encoding='utf-8') as f:
        evaluation_results = json.load(f)
    
    # Initialize refinement system
    refinement_system = QuestionRefinementSystem(api_key)
    
    # Refine dataset
    refined_results = refinement_system.refine_question_dataset(evaluation_results)
    
    # Save results
    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(refined_results, f, indent=2, ensure_ascii=False)
        print(f"✅ Refined results saved to: {output_path}")
    
    print("\n🎯 Refinement Summary:")
    original_deep = evaluation_results['summary_statistics'].get('percentage_deep', 0.0)
    refined_deep = refined_results['summary_statistics'].get('percentage_deep', 0.0)
    print(f"  Original deep research questions: {original_deep:.1f}%")
    print(f"  Refined deep research questions: {refined_deep:.1f}%")
    print(f"  Improvement: {refined_deep - original_deep:.1f} percentage points")

if __name__ == "__main__":
    main() 
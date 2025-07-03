#!/usr/bin/env python3
"""
Deep Research Question Evaluation Framework
Implements criteria to distinguish simple vs deep research questions
"""

import json
import re
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from enum import Enum

class QuestionDepth(Enum):
    SIMPLE = "simple"
    MODERATE = "moderate" 
    DEEP = "deep"

class ResearchType(Enum):
    FACT_LOOKUP = "fact_lookup"
    SHALLOW_SUMMARY = "shallow_summary"
    CROSS_DOCUMENT_SYNTHESIS = "cross_document_synthesis"
    CRITICAL_REASONING = "critical_reasoning"
    METHODOLOGICAL_UNDERSTANDING = "methodological_understanding"
    SYSTEMS_ANALYSIS = "systems_analysis"
    INTERDISCIPLINARY_INTEGRATION = "interdisciplinary_integration"

@dataclass
class EvaluationCriteria:
    """Criteria for evaluating question depth and research value"""
    
    # Cognitive complexity indicators
    cognitive_complexity_keywords = [
        # Analysis & Synthesis
        "analyze", "synthesize", "integrate", "compare", "contrast", "evaluate",
        "assess", "examine", "investigate", "explore", "determine",
        
        # Systems thinking
        "relationship", "interaction", "interdependence", "system", "framework",
        "mechanism", "process", "dynamics", "trade-offs", "implications",
        
        # Critical reasoning
        "why", "how", "what factors", "what conditions", "what circumstances",
        "under what", "to what extent", "in what ways", "what are the limitations",
        
        # Methodological depth
        "methodology", "approach", "strategy", "model", "theory", "principle",
        "concept", "paradigm", "perspective", "lens"
    ]
    
    # Simple question indicators
    simple_question_keywords = [
        "what is", "who is", "when did", "where is", "list", "name",
        "define", "identify", "state", "mention", "give examples"
    ]
    
    # Deep research indicators
    deep_research_keywords = [
        "multi-dimensional", "interdisciplinary", "cross-domain", "systemic",
        "holistic", "comprehensive", "integrated", "complex", "nuanced",
        "sophisticated", "advanced", "cutting-edge", "emerging", "future"
    ]

class DeepResearchEvaluator:
    """Evaluates questions for deep research characteristics"""
    
    def __init__(self):
        self.criteria = EvaluationCriteria()
        
    def evaluate_question(self, question_text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Comprehensive evaluation of question depth and research value
        
        Args:
            question_text: The question to evaluate
            context: Additional context (domain, difficulty, etc.)
            
        Returns:
            Evaluation results with scores and classifications
        """
        
        # Basic text analysis
        word_count = len(question_text.split())
        sentence_count = len([s for s in question_text.split('.') if s.strip()])
        
        # Cognitive complexity analysis
        cognitive_score = self._analyze_cognitive_complexity(question_text)
        
        # Research depth analysis
        depth_score = self._analyze_research_depth(question_text)
        
        # Question type classification
        question_type = self._classify_question_type(question_text)
        
        # Cross-document synthesis requirement
        synthesis_score = self._analyze_synthesis_requirement(question_text)
        
        # Domain expertise requirement
        expertise_score = self._analyze_expertise_requirement(question_text, context)
        
        # Calculate overall depth score
        overall_depth_score = self._calculate_overall_depth_score(
            cognitive_score, depth_score, synthesis_score, expertise_score
        )
        
        # Classify question depth
        depth_classification = self._classify_question_depth(overall_depth_score)
        
        # Generate detailed evaluation
        evaluation = {
            'question_text': question_text,
            'evaluation_timestamp': self._get_timestamp(),
            
            # Basic metrics
            'basic_metrics': {
                'word_count': word_count,
                'sentence_count': sentence_count,
                'question_length_category': self._categorize_length(word_count)
            },
            
            # Depth analysis scores (0-1 scale)
            'depth_scores': {
                'cognitive_complexity': cognitive_score,
                'research_depth': depth_score,
                'synthesis_requirement': synthesis_score,
                'expertise_requirement': expertise_score,
                'overall_depth': overall_depth_score
            },
            
            # Classifications
            'classifications': {
                'question_depth': depth_classification.value,
                'research_type': question_type.value,
                'is_deep_research': depth_classification == QuestionDepth.DEEP
            },
            
            # Detailed analysis
            'analysis_details': {
                'cognitive_complexity_indicators': self._find_cognitive_indicators(question_text),
                'research_depth_indicators': self._find_depth_indicators(question_text),
                'simple_question_indicators': self._find_simple_indicators(question_text),
                'synthesis_indicators': self._find_synthesis_indicators(question_text)
            },
            
            # Recommendations
            'recommendations': self._generate_recommendations(
                depth_classification, question_type, overall_depth_score
            )
        }
        
        return evaluation
    
    def _analyze_cognitive_complexity(self, question_text: str) -> float:
        """Analyze cognitive complexity based on keywords and structure"""
        text_lower = question_text.lower()
        
        # Count cognitive complexity indicators
        complexity_count = sum(1 for keyword in self.criteria.cognitive_complexity_keywords 
                             if keyword in text_lower)
        
        # Count simple question indicators (negative score)
        simple_count = sum(1 for keyword in self.criteria.simple_question_keywords 
                          if keyword in text_lower)
        
        # Calculate complexity score
        max_possible = len(self.criteria.cognitive_complexity_keywords)
        complexity_score = min(complexity_count / max_possible * 2, 1.0)  # Scale to 0-1
        simple_penalty = min(simple_count * 0.2, 0.5)  # Penalty for simple indicators
        
        return max(0.0, complexity_score - simple_penalty)
    
    def _analyze_research_depth(self, question_text: str) -> float:
        """Analyze research depth requirements"""
        text_lower = question_text.lower()
        
        # Count deep research indicators
        deep_count = sum(1 for keyword in self.criteria.deep_research_keywords 
                        if keyword in text_lower)
        
        # Check for multi-part questions
        multi_part_score = 0.3 if ('and' in text_lower and '?' in question_text) else 0.0
        
        # Check for conditional/contextual complexity
        conditional_score = 0.2 if any(phrase in text_lower for phrase in 
                                     ['given that', 'considering', 'in the context of', 
                                      'under conditions', 'assuming']) else 0.0
        
        # Calculate depth score
        depth_score = min(deep_count * 0.15, 0.5) + multi_part_score + conditional_score
        
        return min(depth_score, 1.0)
    
    def _classify_question_type(self, question_text: str) -> ResearchType:
        """Classify the type of research question"""
        text_lower = question_text.lower()
        
        # Check for different question types
        if any(phrase in text_lower for phrase in ['what is', 'define', 'list', 'name']):
            return ResearchType.FACT_LOOKUP
        
        elif any(phrase in text_lower for phrase in ['summarize', 'overview', 'describe']):
            return ResearchType.SHALLOW_SUMMARY
        
        elif any(phrase in text_lower for phrase in ['compare', 'contrast', 'relationship', 'interaction']):
            return ResearchType.CROSS_DOCUMENT_SYNTHESIS
        
        elif any(phrase in text_lower for phrase in ['evaluate', 'assess', 'critique', 'analyze']):
            return ResearchType.CRITICAL_REASONING
        
        elif any(phrase in text_lower for phrase in ['methodology', 'approach', 'method', 'technique']):
            return ResearchType.METHODOLOGICAL_UNDERSTANDING
        
        elif any(phrase in text_lower for phrase in ['system', 'framework', 'model', 'paradigm']):
            return ResearchType.SYSTEMS_ANALYSIS
        
        elif any(phrase in text_lower for phrase in ['interdisciplinary', 'cross-domain', 'multi-dimensional']):
            return ResearchType.INTERDISCIPLINARY_INTEGRATION
        
        else:
            return ResearchType.CRITICAL_REASONING  # Default for complex questions
    
    def _analyze_synthesis_requirement(self, question_text: str) -> float:
        """Analyze requirement for cross-document synthesis"""
        text_lower = question_text.lower()
        
        synthesis_indicators = [
            'multiple', 'various', 'different', 'across', 'between', 'among',
            'integrate', 'combine', 'synthesize', 'comprehensive', 'holistic'
        ]
        
        synthesis_count = sum(1 for indicator in synthesis_indicators 
                            if indicator in text_lower)
        
        return min(synthesis_count * 0.2, 1.0)
    
    def _analyze_expertise_requirement(self, question_text: str, context: Dict[str, Any] = None) -> float:
        """Analyze domain expertise requirement"""
        text_lower = question_text.lower()
        
        # Technical terminology indicators
        technical_indicators = [
            'efficiency', 'optimization', 'algorithm', 'model', 'theory',
            'principle', 'mechanism', 'process', 'methodology', 'framework'
        ]
        
        technical_count = sum(1 for indicator in technical_indicators 
                            if indicator in text_lower)
        
        # Context-based expertise requirement
        context_score = 0.0
        if context:
            if context.get('difficulty') == 'Hard':
                context_score += 0.3
            if context.get('category') == 'Cross_Subdomain':
                context_score += 0.2
        
        expertise_score = min(technical_count * 0.15, 0.5) + context_score
        
        return min(expertise_score, 1.0)
    
    def _calculate_overall_depth_score(self, cognitive: float, depth: float, 
                                     synthesis: float, expertise: float) -> float:
        """Calculate weighted overall depth score"""
        weights = {
            'cognitive': 0.3,
            'depth': 0.3,
            'synthesis': 0.2,
            'expertise': 0.2
        }
        
        overall_score = (
            cognitive * weights['cognitive'] +
            depth * weights['depth'] +
            synthesis * weights['synthesis'] +
            expertise * weights['expertise']
        )
        
        return min(overall_score, 1.0)
    
    def _classify_question_depth(self, overall_score: float) -> QuestionDepth:
        """Classify question depth based on overall score"""
        if overall_score >= 0.7:
            return QuestionDepth.DEEP
        elif overall_score >= 0.4:
            return QuestionDepth.MODERATE
        else:
            return QuestionDepth.SIMPLE
    
    def _find_cognitive_indicators(self, question_text: str) -> List[str]:
        """Find cognitive complexity indicators in question"""
        text_lower = question_text.lower()
        return [keyword for keyword in self.criteria.cognitive_complexity_keywords 
                if keyword in text_lower]
    
    def _find_depth_indicators(self, question_text: str) -> List[str]:
        """Find research depth indicators in question"""
        text_lower = question_text.lower()
        return [keyword for keyword in self.criteria.deep_research_keywords 
                if keyword in text_lower]
    
    def _find_simple_indicators(self, question_text: str) -> List[str]:
        """Find simple question indicators"""
        text_lower = question_text.lower()
        return [keyword for keyword in self.criteria.simple_question_keywords 
                if keyword in text_lower]
    
    def _find_synthesis_indicators(self, question_text: str) -> List[str]:
        """Find synthesis requirement indicators"""
        text_lower = question_text.lower()
        synthesis_indicators = [
            'multiple', 'various', 'different', 'across', 'between', 'among',
            'integrate', 'combine', 'synthesize', 'comprehensive', 'holistic'
        ]
        return [indicator for indicator in synthesis_indicators if indicator in text_lower]
    
    def _categorize_length(self, word_count: int) -> str:
        """Categorize question length"""
        if word_count < 10:
            return "short"
        elif word_count < 20:
            return "medium"
        else:
            return "long"
    
    def _generate_recommendations(self, depth: QuestionDepth, question_type: ResearchType, 
                                score: float) -> Dict[str, Any]:
        """Generate recommendations for question improvement"""
        recommendations = {
            'current_assessment': f"Question classified as {depth.value} with score {score:.3f}",
            'suggestions': []
        }
        
        if depth == QuestionDepth.SIMPLE:
            recommendations['suggestions'].extend([
                "Add analytical components (analyze, evaluate, compare)",
                "Include synthesis requirements (integrate multiple perspectives)",
                "Increase complexity with conditional or contextual elements",
                "Focus on relationships and interactions rather than facts"
            ])
        
        elif depth == QuestionDepth.MODERATE:
            recommendations['suggestions'].extend([
                "Add interdisciplinary elements",
                "Include systems thinking components",
                "Increase methodological complexity",
                "Add critical evaluation requirements"
            ])
        
        else:  # DEEP
            recommendations['suggestions'].append(
                "Question meets deep research criteria - suitable for benchmark"
            )
        
        return recommendations
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()

def evaluate_question_dataset(dataset_path: str) -> Dict[str, Any]:
    """
    Evaluate a complete dataset of questions for deep research characteristics
    
    Args:
        dataset_path: Path to JSON file containing questions
        
    Returns:
        Dictionary containing evaluation results and statistics
    """
    
    with open(dataset_path, 'r', encoding='utf-8') as f:
        dataset = json.load(f)
    
    evaluator = DeepResearchEvaluator()
    
    # Extract all questions from dataset
    all_questions = []
    
    # Handle different dataset formats
    if 'queries' in dataset:
        # Standard format with queries
        for question in dataset['queries']:
            all_questions.append(question)
    elif isinstance(dataset, dict):
        # Topic-based format
        for topic_id, topic_data in dataset.items():
            if isinstance(topic_data, dict) and 'questions' in topic_data:
                questions = topic_data.get('questions', [])
                for question in questions:
                    question['topic_id'] = topic_id
                    all_questions.append(question)
    elif isinstance(dataset, list):
        # List of questions
        all_questions = dataset
    
    if not all_questions:
        print("⚠️ No questions found in dataset")
        return {
            'total_questions': 0,
            'evaluations': [],
            'summary_statistics': {
                'depth_distribution': {'Simple': 0, 'Moderate': 0, 'Deep': 0},
                'percentage_deep': 0.0,
                'average_scores': {'cognitive_complexity': 0.0, 'research_depth': 0.0, 'synthesis_requirement': 0.0, 'expertise_requirement': 0.0},
                'research_type_distribution': {}
            },
            'meets_deep_research_criteria': False,
            'recommended_actions': ['No questions to evaluate - check dataset generation']
        }
    
    print(f"🔍 Evaluating {len(all_questions)} questions for deep research characteristics...")
    
    # Evaluate each question
    evaluations = []
    for i, question in enumerate(all_questions, 1):
        if i % 10 == 0:
            print(f"   Progress: {i}/{len(all_questions)}")
        
        evaluation = evaluator.evaluate_question(
            question.get('question_text', question.get('query_text', '')),
            {
                'difficulty': question.get('difficulty', 'Medium'),
                'question_type': question.get('question_type', 'General'),
                'rationale': question.get('rationale', '')
            }
        )
        
        evaluation['topic_id'] = question.get('topic_id', 'unknown')
        evaluation['question_id'] = question.get('question_id', question.get('id', f'Q{i:03d}'))
        evaluations.append(evaluation)
    
    # Calculate summary statistics
    total_questions = len(evaluations)
    
    # Depth distribution
    depth_counts = {'Simple': 0, 'Moderate': 0, 'Deep': 0}
    for evaluation in evaluations:
        depth = evaluation['classifications']['question_depth']
        # Normalize depth values
        if depth.lower() == 'simple':
            depth_counts['Simple'] += 1
        elif depth.lower() == 'moderate':
            depth_counts['Moderate'] += 1
        elif depth.lower() == 'deep':
            depth_counts['Deep'] += 1
    
    # Average scores
    average_scores = {
        'cognitive_complexity': sum(e['depth_scores']['cognitive_complexity'] for e in evaluations) / total_questions,
        'research_depth': sum(e['depth_scores']['research_depth'] for e in evaluations) / total_questions,
        'synthesis_requirement': sum(e['depth_scores']['synthesis_requirement'] for e in evaluations) / total_questions,
        'expertise_requirement': sum(e['depth_scores']['expertise_requirement'] for e in evaluations) / total_questions
    }
    
    # Research type distribution
    research_types = [e['classifications']['research_type'] for e in evaluations]
    research_type_counts = {rtype: research_types.count(rtype) for rtype in set(research_types)}
    
    # Calculate percentage of deep research questions
    deep_questions = depth_counts['Deep']
    percentage_deep = (deep_questions / total_questions) * 100
    
    # Determine if criteria are met (target: 70% deep)
    meets_criteria = percentage_deep >= 70.0
    
    summary_stats = {
        'depth_distribution': depth_counts,
        'percentage_deep': percentage_deep,
        'average_scores': average_scores,
        'research_type_distribution': research_type_counts
    }
    
    # Generate recommendations
    recommendations = []
    if not meets_criteria:
        recommendations.append(f"Increase deep research questions: {percentage_deep:.1f}% < 70% target")
    if average_scores['cognitive_complexity'] < 0.6:
        recommendations.append("Enhance cognitive complexity of questions")
    if average_scores['research_depth'] < 0.6:
        recommendations.append("Increase research depth requirements")
    if len(set(research_types)) < 5:
        recommendations.append("Diversify research question types")
    
    results = {
        'total_questions': total_questions,
        'evaluations': evaluations,
        'summary_statistics': summary_stats,
        'meets_deep_research_criteria': meets_criteria,
        'recommended_actions': recommendations if recommendations else ['Dataset meets deep research criteria']
    }
    
    print(f"✅ Evaluation completed")
    print(f"   Deep research questions: {deep_questions}/{total_questions} ({percentage_deep:.1f}%)")
    print(f"   Meets criteria (≥70%): {'✅ Yes' if meets_criteria else '❌ No'}")
    
    return results

if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) > 1:
        dataset_path = sys.argv[1]
        
        results = evaluate_question_dataset(dataset_path)
        
    else:
        print("Usage: python deep_research_evaluation_framework.py <dataset_path>")
        print("Example: python deep_research_evaluation_framework.py output/energy_dataset.json") 
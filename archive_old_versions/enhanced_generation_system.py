#!/usr/bin/env python3
"""
Enhanced Energy Domain Question Generation System
Uses new Claude API + RAG fusion for high-quality ground truth generation
Optimized for FastText classifier training with improved research design
"""

import json
import sys
import os
import time
import random
from pathlib import Path
from typing import List, Dict, Any, Tuple
from datetime import datetime
import requests
import pandas as pd

# Add paths
sys.path.append('PROMPT')
sys.path.append('RAG')

class EnhancedEnergyGenerator:
    """Enhanced generator with RAG fusion and ground truth construction"""
    
    def __init__(self, claude_api_key: str):
        self.claude_api_key = claude_api_key
        self.claude_api_url = "https://api.anthropic.com/v1/messages"
        self.headers = {
            "Content-Type": "application/json",
            "x-api-key": claude_api_key,
            "anthropic-version": "2023-06-01"
        }
        
        # Energy domain configuration - MUST be defined before loading RAG corpus
        self.subdomains = [
            'Renewable', 'Fossil_Fuels', 'Nuclear', 'Grid_Storage',
            'Policy', 'Economics', 'Environmental'
        ]
        
        self.difficulties = ['Easy', 'Medium', 'Hard']
        self.categories = ['General', 'Cross_Subdomain']
        
        # Enhanced keyword sets for better coverage
        self.energy_keywords = {
            'Renewable': [
                'solar energy', 'wind power', 'photovoltaic', 'wind turbine',
                'renewable integration', 'variable generation', 'solar panel',
                'offshore wind', 'biomass energy', 'hydroelectric power',
                'geothermal energy', 'renewable portfolio', 'clean energy'
            ],
            'Fossil_Fuels': [
                'natural gas', 'coal power', 'oil extraction', 'fossil fuel',
                'carbon capture', 'gas turbine', 'coal plant', 'petroleum',
                'shale gas', 'lng terminal', 'fossil infrastructure',
                'carbon emissions', 'methane leakage'
            ],
            'Nuclear': [
                'nuclear reactor', 'nuclear power', 'uranium fuel',
                'nuclear waste', 'reactor safety', 'nuclear policy',
                'small modular reactor', 'nuclear economics',
                'radioactive waste', 'nuclear security', 'reactor design'
            ],
            'Grid_Storage': [
                'energy storage', 'battery storage', 'grid storage',
                'pumped hydro', 'storage system', 'battery technology',
                'grid integration', 'storage deployment', 'energy arbitrage',
                'storage economics', 'grid stability', 'storage capacity'
            ],
            'Policy': [
                'energy policy', 'renewable incentive', 'carbon pricing',
                'energy regulation', 'policy framework', 'energy transition',
                'climate policy', 'energy market', 'policy design',
                'regulatory framework', 'energy governance'
            ],
            'Economics': [
                'energy economics', 'energy cost', 'energy market',
                'energy investment', 'energy finance', 'cost analysis',
                'economic impact', 'energy pricing', 'market design',
                'energy valuation', 'economic optimization'
            ],
            'Environmental': [
                'environmental impact', 'carbon footprint', 'lifecycle assessment',
                'environmental policy', 'climate impact', 'emission reduction',
                'environmental sustainability', 'ecological impact',
                'environmental assessment', 'green technology'
            ]
        }
        
        # Load RAG corpus AFTER defining energy_keywords
        self.rag_corpus = self.load_rag_corpus()
        print(f"✅ Loaded RAG corpus with {len(self.rag_corpus)} papers")
    
    def load_rag_corpus(self) -> List[Dict]:
        """Load RAG literature corpus"""
        possible_files = [
            "RAG/data/metadata/papers_20250526_182607.json",
            "RAG/data/processed/energy_rag_corpus.json"
        ]
        
        for file_path in possible_files:
            if os.path.exists(file_path):
                print(f"📚 Loading RAG corpus: {file_path}")
                with open(file_path, 'r', encoding='utf-8') as f:
                    papers = json.load(f)
                
                # Build searchable corpus
                corpus = []
                for paper in papers:
                    if isinstance(paper, dict):
                        title = paper.get('title', '')
                        abstract = paper.get('abstract', '')
                        
                        if title and abstract and len(abstract) > 50:
                            corpus.append({
                                'id': paper.get('id', ''),
                                'title': title,
                                'abstract': abstract,
                                'authors': paper.get('authors', []),
                                'source': paper.get('source', ''),
                                'full_text': f"{title} {abstract}",
                                'keywords': self.extract_paper_keywords(title, abstract)
                            })
                return corpus
        
        raise FileNotFoundError("RAG corpus file not found")
    
    def extract_paper_keywords(self, title: str, abstract: str) -> List[str]:
        """Extract energy keywords from paper"""
        text = f"{title} {abstract}".lower()
        found_keywords = []
        
        for subdomain, keywords in self.energy_keywords.items():
            for keyword in keywords:
                if keyword.lower() in text:
                    found_keywords.append(keyword)
        
        return list(set(found_keywords))
    
    def call_claude_api(self, messages: List[Dict], max_tokens: int = 4000) -> str:
        """Call Claude API with new authentication"""
        payload = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": max_tokens,
            "messages": messages
        }
        
        try:
            response = requests.post(
                self.claude_api_url,
                headers=self.headers,
                json=payload,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['content'][0]['text']
            else:
                print(f"❌ API Error {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ API Call failed: {e}")
            return None
    
    def generate_balanced_requirements(self, total_questions: int = 200) -> List[Dict]:
        """Generate balanced question requirements"""
        requirements = []
        
        # Distribution based on research needs
        easy_count = int(total_questions * 0.30)    # 30% Easy
        medium_count = int(total_questions * 0.45)  # 45% Medium  
        hard_count = total_questions - easy_count - medium_count  # 25% Hard
        
        general_count = int(total_questions * 0.60)  # 60% General
        cross_count = total_questions - general_count  # 40% Cross-subdomain
        
        print(f"📋 Question distribution:")
        print(f"  Difficulty: Easy({easy_count}), Medium({medium_count}), Hard({hard_count})")
        print(f"  Category: General({general_count}), Cross-subdomain({cross_count})")
        
        # Generate requirements
        for i in range(total_questions):
            # Determine difficulty
            if i < easy_count:
                difficulty = 'Easy'
            elif i < easy_count + medium_count:
                difficulty = 'Medium'
            else:
                difficulty = 'Hard'
            
            # Determine category
            category = 'General' if i < general_count else 'Cross_Subdomain'
            
            # Select subdomains
            primary_subdomain = random.choice(self.subdomains)
            
            if category == 'Cross_Subdomain':
                remaining = [s for s in self.subdomains if s != primary_subdomain]
                if difficulty == 'Easy':
                    secondary = random.sample(remaining, 1)
                elif difficulty == 'Medium':
                    secondary = random.sample(remaining, min(2, len(remaining)))
                else:  # Hard
                    secondary = random.sample(remaining, min(3, len(remaining)))
            else:
                secondary = []
            
            requirements.append({
                'id': f'EQ{i+1:03d}',
                'difficulty': difficulty,
                'category': category,
                'primary_subdomain': primary_subdomain,
                'secondary_subdomains': secondary,
                'target_keywords': self.energy_keywords[primary_subdomain][:5]  # Top 5 keywords
            })
        
        # Shuffle to avoid patterns
        random.shuffle(requirements)
        return requirements
    
    def generate_question_with_claude(self, requirement: Dict) -> str:
        """Generate question using Claude API"""
        
        # Create generation prompt
        subdomain_info = f"Primary: {requirement['primary_subdomain']}"
        if requirement['secondary_subdomains']:
            subdomain_info += f", Secondary: {', '.join(requirement['secondary_subdomains'])}"
        
        keywords_str = ', '.join(requirement['target_keywords'])
        
        difficulty_guidelines = {
            'Easy': "Focus on fundamental concepts, basic comparisons, or straightforward explanations. Questions should be answerable with basic domain knowledge.",
            'Medium': "Require multi-factor analysis, trade-off evaluations, or moderate synthesis. Questions should integrate 2-3 concepts.",
            'Hard': "Demand complex system thinking, comprehensive frameworks, or novel solution design. Questions should require deep expertise and interdisciplinary knowledge."
        }
        
        category_guidelines = {
            'General': "Focus primarily on one subdomain with deep technical focus.",
            'Cross_Subdomain': "Meaningfully integrate multiple subdomains, exploring their interdependencies and interactions."
        }
        
        messages = [
            {
                "role": "user",
                "content": f"""Generate 1 high-quality energy domain research question based on these requirements:

**Difficulty Level**: {requirement['difficulty']}
**Category**: {requirement['category']}
**Subdomains**: {subdomain_info}
**Target Keywords**: {keywords_str}

**Difficulty Guidelines**: {difficulty_guidelines[requirement['difficulty']]}

**Category Guidelines**: {category_guidelines[requirement['category']]}

**Quality Requirements**:
- Clear and specific
- Require deep domain knowledge
- Focus on research value, not simple facts
- Match the specified difficulty level
- Cover the specified domains thoroughly
- Suitable for academic research or industry analysis

**Output Format**: Return only the question text, no explanations or numbering."""
            }
        ]
        
        return self.call_claude_api(messages, max_tokens=500)
    
    def retrieve_relevant_papers(self, query: str, top_k: int = 5) -> List[Dict]:
        """Retrieve relevant papers for RAG"""
        scores = []
        query_words = set(query.lower().split())
        
        for paper in self.rag_corpus:
            # Calculate similarity scores
            title_words = set(paper['title'].lower().split())
            abstract_words = set(paper['abstract'].lower().split())
            keyword_words = set(' '.join(paper['keywords']).lower().split())
            
            # Multi-field scoring
            title_sim = len(query_words.intersection(title_words)) / len(query_words.union(title_words)) if query_words.union(title_words) else 0
            abstract_sim = len(query_words.intersection(abstract_words)) / len(query_words.union(abstract_words)) if query_words.union(abstract_words) else 0
            keyword_sim = len(query_words.intersection(keyword_words)) / len(query_words.union(keyword_words)) if query_words.union(keyword_words) else 0
            
            # Weighted combined score
            combined_score = title_sim * 0.4 + abstract_sim * 0.4 + keyword_sim * 0.2
            
            if combined_score > 0.05:  # Minimum threshold
                scores.append((combined_score, paper))
        
        # Sort and return top papers
        scores.sort(key=lambda x: x[0], reverse=True)
        return [paper for score, paper in scores[:top_k]]
    
    def generate_rag_fused_answer(self, question: str, relevant_papers: List[Dict]) -> Dict[str, Any]:
        """Generate RAG-fused answer using Claude + literature"""
        
        if not relevant_papers:
            return {
                'answer': "Insufficient literature found for comprehensive analysis.",
                'sources': [],
                'confidence': 0.0,
                'method': 'no_literature'
            }
        
        # Prepare literature context
        literature_context = []
        sources = []
        
        for i, paper in enumerate(relevant_papers, 1):
            context_entry = f"""
Paper {i}: {paper['title']}
Authors: {', '.join(paper.get('authors', [])[:3])}
Abstract: {paper['abstract'][:500]}...
Keywords: {', '.join(paper['keywords'][:5])}
"""
            literature_context.append(context_entry)
            
            sources.append({
                'title': paper['title'],
                'authors': paper.get('authors', []),
                'source': paper.get('source', ''),
                'id': paper.get('id', ''),
                'keywords': paper['keywords']
            })
        
        # Generate fused answer with Claude
        messages = [
            {
                "role": "user",
                "content": f"""You are an expert energy researcher. Based on the following research literature, provide a comprehensive answer to the question.

**Question**: {question}

**Relevant Literature**:
{''.join(literature_context)}

**Instructions**:
1. Synthesize information from the provided literature
2. Provide a structured, research-grade answer
3. Cite specific findings from the papers
4. Identify research gaps or areas needing further investigation
5. Maintain scientific rigor and accuracy

**Answer Structure**:
- **Overview**: Brief summary of the topic
- **Key Findings**: Main insights from literature (cite papers)
- **Technical Analysis**: Detailed technical discussion
- **Research Gaps**: Areas needing further research
- **Conclusion**: Summary and implications

Provide a comprehensive answer (800-1200 words) that demonstrates deep understanding while staying grounded in the literature."""
            }
        ]
        
        answer_text = self.call_claude_api(messages, max_tokens=2000)
        
        if answer_text:
            return {
                'answer': answer_text,
                'sources': sources,
                'confidence': min(len(relevant_papers) / 5.0, 1.0),
                'method': 'rag_fused',
                'literature_count': len(relevant_papers)
            }
        else:
            # Fallback to literature-only answer
            key_findings = []
            for paper in relevant_papers:
                sentences = paper['abstract'].split('.')
                for sentence in sentences[:2]:  # Top 2 sentences per paper
                    if any(word in sentence.lower() for word in question.lower().split()):
                        key_findings.append(sentence.strip())
            
            fallback_answer = "Based on the literature review: " + " ".join(key_findings[:3])
            
            return {
                'answer': fallback_answer,
                'sources': sources,
                'confidence': 0.6,
                'method': 'literature_fallback',
                'literature_count': len(relevant_papers)
            }
    
    def assess_answer_quality(self, question: str, answer: str, sources: List[Dict]) -> Dict[str, Any]:
        """Comprehensive answer quality assessment"""
        
        # Basic metrics
        word_count = len(answer.split())
        char_count = len(answer)
        
        # Structure analysis
        has_sections = any(marker in answer for marker in ['##', '###', '**', '1.', '2.', '3.'])
        has_citations = any(marker in answer for marker in ['Paper', 'study', 'research', 'findings'])
        
        # Content depth analysis
        technical_terms = 0
        energy_terms = []
        for subdomain, keywords in self.energy_keywords.items():
            for keyword in keywords:
                if keyword.lower() in answer.lower():
                    technical_terms += 1
                    energy_terms.append(keyword)
        
        # Literature grounding
        literature_integration = len(sources) > 0
        source_diversity = len(set(src.get('source', '') for src in sources))
        
        # Quality scoring
        length_score = min(word_count / 800, 1.0)  # Target 800+ words
        structure_score = (has_sections + has_citations) / 2
        technical_score = min(technical_terms / 10, 1.0)  # Target 10+ technical terms
        literature_score = min(len(sources) / 5, 1.0)  # Target 5+ sources
        
        overall_quality = (length_score + structure_score + technical_score + literature_score) / 4
        
        return {
            'word_count': word_count,
            'char_count': char_count,
            'has_sections': has_sections,
            'has_citations': has_citations,
            'technical_terms_count': technical_terms,
            'energy_terms': energy_terms[:10],  # Top 10 terms
            'literature_integration': literature_integration,
            'source_count': len(sources),
            'source_diversity': source_diversity,
            'quality_scores': {
                'length': length_score,
                'structure': structure_score,
                'technical': technical_score,
                'literature': literature_score,
                'overall': overall_quality
            }
        }
    
    def generate_enhanced_dataset(self, num_questions: int = 200) -> List[Dict]:
        """Generate enhanced dataset with RAG fusion and ground truth"""
        
        print(f"🚀 Starting enhanced dataset generation for {num_questions} questions")
        print("=" * 70)
        
        # Generate balanced requirements
        requirements = self.generate_balanced_requirements(num_questions)
        
        results = []
        failed_generations = 0
        
        for i, req in enumerate(requirements, 1):
            print(f"\n📝 Generating question {i}/{num_questions}")
            print(f"   Difficulty: {req['difficulty']}, Category: {req['category']}")
            print(f"   Primary: {req['primary_subdomain']}")
            
            # Generate question
            question_text = self.generate_question_with_claude(req)
            
            if not question_text:
                print(f"   ❌ Failed to generate question")
                failed_generations += 1
                continue
            
            print(f"   ✅ Question: {question_text[:80]}...")
            
            # Retrieve relevant literature
            relevant_papers = self.retrieve_relevant_papers(question_text, top_k=5)
            print(f"   📚 Found {len(relevant_papers)} relevant papers")
            
            # Generate RAG-fused answer
            rag_result = self.generate_rag_fused_answer(question_text, relevant_papers)
            print(f"   💡 Answer generated using {rag_result['method']}")
            
            # Assess quality
            quality_metrics = self.assess_answer_quality(
                question_text, rag_result['answer'], rag_result['sources']
            )
            
            # Create comprehensive result
            result = {
                'id': req['id'],
                'question_text': question_text,
                'difficulty': req['difficulty'],
                'category': req['category'],
                'primary_subdomain': req['primary_subdomain'],
                'secondary_subdomains': req['secondary_subdomains'],
                'target_keywords': req['target_keywords'],
                
                # RAG-fused answer (ground truth)
                'ground_truth_answer': rag_result['answer'],
                'answer_method': rag_result['method'],
                'literature_sources': rag_result['sources'],
                'rag_confidence': rag_result['confidence'],
                'literature_count': rag_result.get('literature_count', 0),
                
                # Quality assessment
                'quality_metrics': quality_metrics,
                
                # Metadata
                'generation_timestamp': datetime.now().isoformat(),
                'api_model': 'claude-3-5-sonnet-20241022'
            }
            
            results.append(result)
            
            # Progress reporting
            if i % 20 == 0:
                success_rate = (i - failed_generations) / i * 100
                print(f"\n📊 Progress: {i}/{num_questions} ({success_rate:.1f}% success rate)")
            
            # Rate limiting
            time.sleep(1)  # 1 second between API calls
        
        print(f"\n✅ Dataset generation completed!")
        print(f"   Successful: {len(results)}")
        print(f"   Failed: {failed_generations}")
        print(f"   Success rate: {len(results)/(len(results)+failed_generations)*100:.1f}%")
        
        return results
    
    def save_enhanced_dataset(self, results: List[Dict], output_dir: str = "output") -> Tuple[str, str]:
        """Save enhanced dataset with comprehensive metadata"""
        
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Prepare comprehensive metadata
        metadata = {
            'dataset_info': {
                'total_questions': len(results),
                'generation_timestamp': datetime.now().isoformat(),
                'system': 'Enhanced_PROMPT_RAG_Fusion',
                'api_model': 'claude-3-5-sonnet-20241022',
                'description': 'Energy domain questions with RAG-fused ground truth answers'
            },
            'quality_statistics': self.calculate_dataset_statistics(results),
            'methodology': {
                'question_generation': 'Claude API with balanced requirements',
                'answer_generation': 'RAG fusion with literature grounding',
                'literature_corpus': f'{len(self.rag_corpus)} energy research papers',
                'quality_assessment': 'Multi-dimensional quality metrics'
            }
        }
        
        # Save JSON format
        json_file = output_path / f"enhanced_energy_dataset_{timestamp}.json"
        output_data = {
            'metadata': metadata,
            'questions': results
        }
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ JSON dataset saved: {json_file}")
        
        # Save Excel format for analysis
        excel_file = output_path / f"enhanced_energy_dataset_{timestamp}.xlsx"
        
        try:
            excel_data = []
            for result in results:
                row = {
                    'ID': result['id'],
                    'Question': result['question_text'],
                    'Difficulty': result['difficulty'],
                    'Category': result['category'],
                    'Primary_Subdomain': result['primary_subdomain'],
                    'Secondary_Subdomains': ', '.join(result['secondary_subdomains']),
                    'Target_Keywords': ', '.join(result['target_keywords']),
                    'Ground_Truth_Answer': result['ground_truth_answer'],
                    'Answer_Method': result['answer_method'],
                    'Literature_Count': result['literature_count'],
                    'RAG_Confidence': f"{result['rag_confidence']:.3f}",
                    'Word_Count': result['quality_metrics']['word_count'],
                    'Technical_Terms': result['quality_metrics']['technical_terms_count'],
                    'Overall_Quality': f"{result['quality_metrics']['quality_scores']['overall']:.3f}",
                    'Literature_Sources': '; '.join([src['title'] for src in result['literature_sources'][:3]])
                }
                excel_data.append(row)
            
            df = pd.DataFrame(excel_data)
            df.to_excel(excel_file, index=False, engine='openpyxl')
            
            print(f"✅ Excel dataset saved: {excel_file}")
            
        except ImportError:
            print("⚠️ pandas/openpyxl not available, skipping Excel export")
            excel_file = None
        
        return str(json_file), str(excel_file) if excel_file else None
    
    def calculate_dataset_statistics(self, results: List[Dict]) -> Dict[str, Any]:
        """Calculate comprehensive dataset statistics"""
        
        if not results:
            return {}
        
        # Basic statistics
        total_questions = len(results)
        
        # Difficulty distribution
        difficulty_counts = {}
        for result in results:
            diff = result['difficulty']
            difficulty_counts[diff] = difficulty_counts.get(diff, 0) + 1
        
        # Subdomain distribution
        subdomain_counts = {}
        for result in results:
            primary = result['primary_subdomain']
            subdomain_counts[primary] = subdomain_counts.get(primary, 0) + 1
            
            for secondary in result['secondary_subdomains']:
                subdomain_counts[secondary] = subdomain_counts.get(secondary, 0) + 1
        
        # Quality metrics
        quality_scores = [r['quality_metrics']['quality_scores']['overall'] for r in results]
        word_counts = [r['quality_metrics']['word_count'] for r in results]
        literature_counts = [r['literature_count'] for r in results]
        
        # Answer methods
        method_counts = {}
        for result in results:
            method = result['answer_method']
            method_counts[method] = method_counts.get(method, 0) + 1
        
        return {
            'total_questions': total_questions,
            'difficulty_distribution': difficulty_counts,
            'subdomain_distribution': subdomain_counts,
            'quality_metrics': {
                'average_quality_score': sum(quality_scores) / len(quality_scores),
                'average_word_count': sum(word_counts) / len(word_counts),
                'average_literature_count': sum(literature_counts) / len(literature_counts),
                'min_quality': min(quality_scores),
                'max_quality': max(quality_scores)
            },
            'answer_methods': method_counts,
            'literature_coverage': {
                'questions_with_literature': sum(1 for r in results if r['literature_count'] > 0),
                'coverage_percentage': sum(1 for r in results if r['literature_count'] > 0) / total_questions * 100
            }
        }

def main():
    """Main execution function"""
    
    print("🔋 Enhanced Energy Domain Question Generation System")
    print("=" * 70)
    print("Features:")
    print("• New Claude API integration")
    print("• RAG-fused ground truth answers")
    print("• Comprehensive quality assessment")
    print("• Optimized for FastText training")
    print("=" * 70)
    
    # Initialize with new API key
    api_key = "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"
    
    try:
        generator = EnhancedEnergyGenerator(api_key)
        
        # Start with a test batch of 20 questions
        print("🧪 Starting with test batch of 20 questions...")
        results = generator.generate_enhanced_dataset(num_questions=20)
        
        if results:
            # Save results
            json_file, excel_file = generator.save_enhanced_dataset(results)
            
            # Print final statistics
            stats = generator.calculate_dataset_statistics(results)
            
            print(f"\n📊 Test Batch Statistics:")
            print(f"   Total Questions: {stats['total_questions']}")
            print(f"   Average Quality Score: {stats['quality_metrics']['average_quality_score']:.3f}")
            print(f"   Average Word Count: {stats['quality_metrics']['average_word_count']:.0f}")
            print(f"   Literature Coverage: {stats['literature_coverage']['coverage_percentage']:.1f}%")
            
            print(f"\n🎯 Test Batch Complete!")
            print(f"   JSON: {json_file}")
            if excel_file:
                print(f"   Excel: {excel_file}")
            
            # Ask if user wants to continue with full dataset
            print(f"\n✅ Test successful! Ready to generate full 200-question dataset.")
        
        else:
            print("❌ No questions generated successfully")
    
    except Exception as e:
        print(f"❌ System error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 
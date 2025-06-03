#!/usr/bin/env python3
"""
Energy Domain PROMPT+RAG System
Read PROMPT-generated questions and use RAG to generate literature-based answers
Build high-quality energy question dataset for FastText training
"""

import json
import sys
import os
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import pandas as pd

# Add RAG path
sys.path.append('RAG')

def load_prompt_questions():
    """Load PROMPT-generated questions"""
    json_file = "PROMPT/output/energy_benchmark_20250521_135210_complete.json"
    
    if not os.path.exists(json_file):
        print(f"❌ PROMPT data file not found: {json_file}")
        return None
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data

def load_rag_corpus():
    """Load RAG literature corpus"""
    # Try to load existing literature data
    possible_files = [
        "RAG/data/metadata/papers_20250526_182607.json",
        "RAG/data/processed/energy_rag_corpus.json"
    ]
    
    for file_path in possible_files:
        if os.path.exists(file_path):
            print(f"📚 Loading literature corpus: {file_path}")
            with open(file_path, 'r', encoding='utf-8') as f:
                papers = json.load(f)
            return papers
    
    print("❌ Literature corpus file not found")
    return None

class EnergyRAGSystem:
    """Literature-based RAG system"""
    
    def __init__(self, papers_data: List[Dict]):
        self.papers = papers_data
        self.corpus = self.build_corpus()
        print(f"✅ RAG system initialized with {len(self.corpus)} papers")
    
    def build_corpus(self):
        """Build retrieval corpus"""
        corpus = []
        for paper in self.papers:
            # Handle different paper data formats
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
                        'full_text': f"{title} {abstract}"
                    })
        
        return corpus
    
    def simple_similarity(self, query: str, document: str) -> float:
        """Calculate similarity score"""
        query_words = set(query.lower().split())
        doc_words = set(document.lower().split())
        
        if not query_words or not doc_words:
            return 0.0
        
        intersection = query_words.intersection(doc_words)
        union = query_words.union(doc_words)
        
        return len(intersection) / len(union)
    
    def retrieve_relevant_papers(self, query: str, top_k: int = 5) -> List[Dict]:
        """Retrieve relevant papers"""
        scores = []
        
        for paper in self.corpus:
            # Calculate similarity with title and abstract
            title_sim = self.simple_similarity(query, paper['title'])
            abstract_sim = self.simple_similarity(query, paper['abstract'])
            
            # Combined similarity with higher weight for title
            combined_score = title_sim * 0.6 + abstract_sim * 0.4
            
            if combined_score > 0.05:  # Minimum similarity threshold
                scores.append((combined_score, paper))
        
        # Sort by similarity
        scores.sort(key=lambda x: x[0], reverse=True)
        
        # Return top_k most relevant papers
        return [paper for score, paper in scores[:top_k]]
    
    def generate_literature_based_answer(self, query: str, relevant_papers: List[Dict]) -> Dict[str, Any]:
        """Generate answer based on literature"""
        if not relevant_papers:
            return {
                'answer': "Based on the current literature corpus, insufficient relevant research was found to answer this question comprehensively.",
                'sources': [],
                'confidence': 0.0
            }
        
        # Extract key findings
        key_findings = []
        sources = []
        
        for paper in relevant_papers:
            # Extract relevant sentences from abstract
            abstract_sentences = paper['abstract'].split('.')
            relevant_sentences = []
            
            query_words = set(query.lower().split())
            for sentence in abstract_sentences:
                sentence_words = set(sentence.lower().split())
                if len(query_words.intersection(sentence_words)) > 0:
                    relevant_sentences.append(sentence.strip())
            
            if relevant_sentences:
                key_findings.extend(relevant_sentences[:2])  # Max 2 sentences per paper
            
            sources.append({
                'title': paper['title'],
                'authors': paper.get('authors', []),
                'source': paper.get('source', ''),
                'id': paper.get('id', '')
            })
        
        # Generate comprehensive answer
        if key_findings:
            answer = "Based on relevant research literature, " + " ".join(key_findings[:3])  # Max 3 key findings
        else:
            answer = f"According to {len(relevant_papers)} relevant papers retrieved, this question involves complex energy system issues requiring further interdisciplinary research."
        
        return {
            'answer': answer,
            'sources': sources,
            'confidence': min(len(relevant_papers) / 5.0, 1.0)  # Based on number of papers retrieved
        }

def extract_answer_quality_metrics(answer_text: str) -> Dict[str, Any]:
    """Extract quality metrics from answer text"""
    if not answer_text or answer_text.startswith('Failed'):
        return {
            'has_answer': False,
            'word_count': 0,
            'char_count': 0,
            'has_sections': False,
            'has_references': False
        }
    
    word_count = len(answer_text.split())
    char_count = len(answer_text)
    has_sections = any(marker in answer_text for marker in ['##', '###', '1.', '2.', '3.'])
    has_references = any(marker in answer_text for marker in ['et al.', 'doi:', 'http', 'www.'])
    
    return {
        'has_answer': True,
        'word_count': word_count,
        'char_count': char_count,
        'has_sections': has_sections,
        'has_references': has_references
    }

def process_questions_with_rag(prompt_data: Dict, rag_system: EnergyRAGSystem) -> List[Dict]:
    """Process PROMPT questions with RAG"""
    questions = prompt_data['queries']
    processed_results = []
    
    print(f"🔄 Processing {len(questions)} questions...")
    
    for i, question_data in enumerate(questions, 1):
        query_text = question_data['query_text']
        
        print(f"Processing question {i}/{len(questions)}: {query_text[:50]}...")
        
        # Get original AI answer if exists
        original_answer = ""
        original_quality = {'has_answer': False}
        if 'answer' in question_data and 'text' in question_data['answer']:
            original_answer = question_data['answer']['text']
            original_quality = extract_answer_quality_metrics(original_answer)
        
        # Use RAG to retrieve relevant literature and generate answer
        relevant_papers = rag_system.retrieve_relevant_papers(query_text, top_k=5)
        rag_result = rag_system.generate_literature_based_answer(query_text, relevant_papers)
        rag_quality = extract_answer_quality_metrics(rag_result['answer'])
        
        # Build result with comparison
        result = {
            'id': question_data.get('id', f'Q{i:03d}'),
            'query_text': query_text,
            'subdomains': question_data.get('subdomains', []),
            'difficulty': question_data.get('difficulty', 'Unknown'),
            'category': question_data.get('category', 'Unknown'),
            
            # Original AI answer
            'original_ai_answer': original_answer,
            'original_answer_quality': original_quality,
            
            # RAG literature-based answer
            'rag_literature_answer': rag_result['answer'],
            'rag_answer_quality': rag_quality,
            'literature_sources': rag_result['sources'],
            'rag_confidence_score': rag_result['confidence'],
            'num_literature_sources': len(rag_result['sources']),
            
            # Comparison metrics
            'answer_comparison': {
                'both_have_answers': original_quality['has_answer'] and rag_quality['has_answer'],
                'original_longer': original_quality['word_count'] > rag_quality['word_count'],
                'rag_has_sources': len(rag_result['sources']) > 0,
                'original_has_sections': original_quality['has_sections'],
                'original_has_references': original_quality['has_references']
            },
            
            'timestamp': datetime.now().isoformat()
        }
        
        processed_results.append(result)
        
        if i % 10 == 0:
            print(f"  Processed {i} questions")
    
    return processed_results

def save_results(results: List[Dict], output_dir: str = "output"):
    """Save results in JSON and Excel formats"""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save JSON format
    json_file = output_path / f"energy_prompt_rag_comparison_{timestamp}.json"
    output_data = {
        'metadata': {
            'total_questions': len(results),
            'generation_timestamp': datetime.now().isoformat(),
            'system': 'PROMPT+RAG_Literature_Comparison',
            'description': 'Energy domain questions with AI vs Literature-based RAG answer comparison'
        },
        'results': results
    }
    
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ JSON results saved: {json_file}")
    
    # Save Excel format
    try:
        excel_file = output_path / f"energy_prompt_rag_comparison_{timestamp}.xlsx"
        
        # Prepare Excel data
        excel_data = []
        for result in results:
            row = {
                'ID': result['id'],
                'Question': result['query_text'],
                'Subdomains': ', '.join(result['subdomains']),
                'Difficulty': result['difficulty'],
                'Category': result['category'],
                
                # Original AI answer info
                'Has_Original_AI_Answer': 'Yes' if result['original_answer_quality']['has_answer'] else 'No',
                'Original_Word_Count': result['original_answer_quality']['word_count'],
                'Original_Has_Sections': 'Yes' if result['original_answer_quality']['has_sections'] else 'No',
                'Original_Has_References': 'Yes' if result['original_answer_quality']['has_references'] else 'No',
                
                # RAG answer info
                'RAG_Literature_Answer': result['rag_literature_answer'],
                'RAG_Word_Count': result['rag_answer_quality']['word_count'],
                'RAG_Confidence_Score': f"{result['rag_confidence_score']:.3f}",
                'Num_Literature_Sources': result['num_literature_sources'],
                'Literature_Sources': '; '.join([src['title'] for src in result['literature_sources']]),
                
                # Comparison
                'Both_Have_Answers': 'Yes' if result['answer_comparison']['both_have_answers'] else 'No',
                'Original_Longer': 'Yes' if result['answer_comparison']['original_longer'] else 'No',
                'RAG_Has_Literature_Sources': 'Yes' if result['answer_comparison']['rag_has_sources'] else 'No'
            }
            excel_data.append(row)
        
        df = pd.DataFrame(excel_data)
        df.to_excel(excel_file, index=False, engine='openpyxl')
        
        print(f"✅ Excel results saved: {excel_file}")
        
    except ImportError:
        print("⚠️ pandas or openpyxl not installed, skipping Excel export")
        excel_file = None
    
    return json_file, excel_file

def generate_comparison_statistics(results: List[Dict]):
    """Generate comparison statistics report"""
    print("\n📊 Processing Statistics:")
    print(f"  Total questions: {len(results)}")
    
    # Answer availability
    original_answers = sum(1 for r in results if r['original_answer_quality']['has_answer'])
    rag_answers = sum(1 for r in results if r['rag_answer_quality']['has_answer'])
    both_answers = sum(1 for r in results if r['answer_comparison']['both_have_answers'])
    
    print(f"  Original AI answers: {original_answers} ({original_answers/len(results)*100:.1f}%)")
    print(f"  RAG literature answers: {rag_answers} ({rag_answers/len(results)*100:.1f}%)")
    print(f"  Both have answers: {both_answers} ({both_answers/len(results)*100:.1f}%)")
    
    # Quality comparison
    if both_answers > 0:
        original_longer = sum(1 for r in results if r['answer_comparison']['both_have_answers'] and r['answer_comparison']['original_longer'])
        original_with_sections = sum(1 for r in results if r['original_answer_quality']['has_sections'])
        original_with_refs = sum(1 for r in results if r['original_answer_quality']['has_references'])
        rag_with_sources = sum(1 for r in results if r['answer_comparison']['rag_has_sources'])
        
        print(f"\n📈 Quality Comparison:")
        print(f"  Original answers longer: {original_longer}/{both_answers} ({original_longer/both_answers*100:.1f}%)")
        print(f"  Original with sections: {original_with_sections} ({original_with_sections/len(results)*100:.1f}%)")
        print(f"  Original with references: {original_with_refs} ({original_with_refs/len(results)*100:.1f}%)")
        print(f"  RAG with literature sources: {rag_with_sources} ({rag_with_sources/len(results)*100:.1f}%)")
    
    # RAG confidence statistics
    confidences = [r['rag_confidence_score'] for r in results]
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0
    print(f"\n🎯 RAG Performance:")
    print(f"  Average confidence score: {avg_confidence:.3f}")
    
    # Literature sources statistics
    total_sources = sum(r['num_literature_sources'] for r in results)
    avg_sources = total_sources / len(results) if results else 0
    print(f"  Average literature sources per question: {avg_sources:.1f}")
    
    # Subdomain distribution
    subdomain_counts = {}
    for result in results:
        for subdomain in result['subdomains']:
            subdomain_counts[subdomain] = subdomain_counts.get(subdomain, 0) + 1
    
    print(f"\n🏷️ Subdomain Distribution:")
    for subdomain, count in sorted(subdomain_counts.items()):
        print(f"    {subdomain}: {count}")
    
    # Difficulty distribution
    difficulty_counts = {}
    for result in results:
        diff = result['difficulty']
        difficulty_counts[diff] = difficulty_counts.get(diff, 0) + 1
    
    print(f"\n⚡ Difficulty Distribution:")
    for diff, count in sorted(difficulty_counts.items()):
        print(f"    {diff}: {count}")

def main():
    print("🔋 Energy Domain PROMPT+RAG Literature Comparison System")
    print("=" * 70)
    print("Objective: Compare AI-generated vs Literature-based answers for energy questions")
    print("=" * 70)
    
    # 1. Load PROMPT-generated questions
    print("📋 Loading PROMPT-generated questions...")
    prompt_data = load_prompt_questions()
    if not prompt_data:
        return
    
    print(f"✅ Loaded {len(prompt_data['queries'])} questions")
    
    # 2. Load RAG literature corpus
    print("\n📚 Loading literature corpus...")
    papers_data = load_rag_corpus()
    if not papers_data:
        print("❌ Cannot load literature data, ensure RAG directory contains literature files")
        return
    
    # 3. Initialize RAG system
    print("\n🔧 Initializing RAG system...")
    rag_system = EnergyRAGSystem(papers_data)
    
    # 4. Process all questions with RAG
    print("\n🔄 Starting RAG processing...")
    results = process_questions_with_rag(prompt_data, rag_system)
    
    # 5. Save results
    print("\n💾 Saving results...")
    json_file, excel_file = save_results(results)
    
    # 6. Generate comparison statistics
    generate_comparison_statistics(results)
    
    print(f"\n🎉 Processing completed!")
    print(f"📄 JSON file: {json_file}")
    if excel_file:
        print(f"📊 Excel file: {excel_file}")
    print(f"🎯 Ready for FastText classifier training to filter ClueWeb22")
    print(f"📚 Dataset includes both AI-generated and literature-based answers for comparison")

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
"""
Test script for ClueWeb22 PROMPT+RAG System
Tests processing of a single topic with 10 questions to verify functionality
"""

import json
from pathlib import Path
from datetime import datetime
from clueweb22_prompt_rag_generator import ClueWeb22PromptRAGGenerator

def test_prompt_rag_single_topic():
    """Test PROMPT+RAG processing of a single topic"""
    
    print("🧪 Testing ClueWeb22 PROMPT+RAG Generation System")
    print("=" * 60)
    print("PROMPT: Domain report + question generation")
    print("RAG: Energy literature-grounded answers")
    print("=" * 60)
    
    # Configuration
    data_dir = "task_file/clueweb22_query_results"
    claude_api_key = "xxxxx"
    
    try:
        # Initialize generator
        generator = ClueWeb22PromptRAGGenerator(data_dir, claude_api_key)
        
        # Get available topics
        topics = list(generator.topics.keys())
        print(f"📋 Available topics: {topics}")
        
        # Select first English topic for testing
        test_topic = None
        for topic in topics:
            if "en" in topic:
                test_topic = topic
                break
        
        if not test_topic:
            test_topic = topics[0]  # Fallback to first topic
        
        print(f"🎯 Testing with topic: {test_topic}")
        print(f"📄 Documents available: {len(generator.topics[test_topic])}")
        
        # Load documents
        print("📚 Loading documents...")
        documents = generator.load_topic_documents(test_topic, max_docs=100)
        print(f"   Loaded {len(documents)} documents")
        
        if not documents:
            print("❌ No valid documents found for this topic")
            return False
        
        # PROMPT Phase 1: Identify domain
        print("🔬 Analyzing domain characteristics (PROMPT)...")
        domain_info = generator.identify_topic_domain(test_topic, documents[:10])
        print(f"   Domain: {domain_info.get('primary_domain', 'Unknown')}")
        print(f"   Themes: {', '.join(domain_info.get('key_themes', []))}")
        
        # PROMPT Phase 2: Generate domain report
        print("📝 Generating domain report (PROMPT)...")
        domain_report = generator.generate_domain_report_prompt(test_topic, documents, domain_info)
        print(f"   Report generated ({len(domain_report.split())} words)")
        
        # PROMPT Phase 3: Generate research questions (only 10 for testing)
        print("❓ Generating research questions (PROMPT - 10 for testing)...")
        questions = generator.generate_research_questions_prompt(test_topic, domain_report, domain_info, num_questions=10)
        print(f"   Generated {len(questions)} questions")
        
        # RAG Phase: Generate answers using energy literature
        print("💡 Generating answers using energy literature (RAG)...")
        qa_pairs = []
        
        for i, question in enumerate(questions):
            print(f"  Generating answer {i+1}/{len(questions)}: {question['question_text'][:60]}...")
            
            # Retrieve relevant papers
            relevant_papers = generator.retrieve_relevant_papers_rag(question['question_text'], top_k=5)
            print(f"    Found {len(relevant_papers)} relevant papers")
            
            # Generate RAG answer
            rag_result = generator.generate_rag_answer(question['question_text'], relevant_papers, domain_info)
            
            qa_pair = {
                **question,
                'answer': rag_result['answer'],
                'answer_method': rag_result['method'],
                'literature_sources': rag_result['sources'],
                'rag_confidence': rag_result['confidence'],
                'literature_count': rag_result.get('literature_count', 0),
                'domain': domain_info.get('primary_domain', 'Unknown'),
                'themes': domain_info.get('key_themes', []),
                'generation_timestamp': datetime.now().isoformat()
            }
            
            qa_pairs.append(qa_pair)
        
        print(f"   Generated {len(qa_pairs)} QA pairs")
        
        # Compile test results
        test_result = {
            'topic_id': test_topic,
            'domain_info': domain_info,
            'document_stats': {
                'total_documents': len(documents),
                'total_words': sum(doc['word_count'] for doc in documents),
                'avg_doc_length': sum(doc['word_count'] for doc in documents) / len(documents)
            },
            'domain_report': domain_report,
            'qa_pairs': qa_pairs,
            'generation_metadata': {
                'timestamp': datetime.now().isoformat(),
                'api_model': 'claude-3-5-sonnet-20241022',
                'prompt_method': 'domain_report_and_questions',
                'rag_method': 'energy_literature_grounded',
                'num_questions_requested': 10,
                'num_questions_generated': len(qa_pairs),
                'test_mode': True
            }
        }
        
        # Save test result
        test_output_dir = Path("test_prompt_rag_output")
        test_output_dir.mkdir(exist_ok=True)
        
        test_file = test_output_dir / f"test_{test_topic}_prompt_rag_result.json"
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(test_result, f, indent=2, ensure_ascii=False)
        
        # Print summary
        print(f"\n✅ Test completed successfully!")
        print(f"📊 Results summary:")
        print(f"   Topic: {test_result['topic_id']}")
        print(f"   Domain: {test_result['domain_info'].get('primary_domain', 'Unknown')}")
        print(f"   Documents: {test_result['document_stats']['total_documents']}")
        print(f"   Report words: {len(test_result['domain_report'].split())}")
        print(f"   QA Pairs: {len(test_result['qa_pairs'])}")
        print(f"💾 Test result saved: {test_file}")
        
        # Show sample questions and answers
        print(f"\n📝 Sample questions and answers:")
        for i, qa in enumerate(test_result['qa_pairs'][:3], 1):
            print(f"\n   {i}. [{qa['difficulty']}] {qa['question_text']}")
            print(f"      Answer method: {qa['answer_method']}")
            print(f"      Literature count: {qa['literature_count']}")
            print(f"      RAG confidence: {qa['rag_confidence']:.3f}")
            print(f"      Answer preview: {qa['answer'][:150]}...")
        
        # Show difficulty and method distribution
        difficulties = [qa['difficulty'] for qa in test_result['qa_pairs']]
        diff_counts = {diff: difficulties.count(diff) for diff in set(difficulties)}
        print(f"\n📊 Difficulty distribution: {diff_counts}")
        
        methods = [qa['answer_method'] for qa in test_result['qa_pairs']]
        method_counts = {method: methods.count(method) for method in set(methods)}
        print(f"📊 Answer method distribution: {method_counts}")
        
        # Show RAG performance
        literature_counts = [qa['literature_count'] for qa in test_result['qa_pairs']]
        avg_literature = sum(literature_counts) / len(literature_counts) if literature_counts else 0
        literature_coverage = sum(1 for c in literature_counts if c > 0) / len(literature_counts) * 100 if literature_counts else 0
        
        print(f"📊 RAG performance:")
        print(f"   Average literature sources per question: {avg_literature:.1f}")
        print(f"   Literature coverage: {literature_coverage:.1f}%")
        
        return True
        
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_prompt_rag_single_topic()
    if success:
        print(f"\n🎉 Test passed! PROMPT+RAG system is working correctly.")
        print(f"💡 To run full processing with all topics and 50 questions each, use:")
        print(f"   python clueweb22_prompt_rag_generator.py")
    else:
        print(f"\n💥 Test failed! Please check the system before full processing.") 
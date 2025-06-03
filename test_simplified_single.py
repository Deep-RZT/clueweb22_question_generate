#!/usr/bin/env python3
"""
Test script for ClueWeb22 Simplified Generator
Tests single topic processing to verify the system works correctly
"""

import json
from datetime import datetime
from pathlib import Path
from clueweb22_simplified_generator import ClueWeb22SimplifiedGenerator

def test_simplified_single_topic():
    """Test simplified processing of a single topic"""
    print("🧪 Testing ClueWeb22 Simplified Generator")
    print("=" * 60)
    print("PROMPT-only approach: Documents → Report → Questions")
    print("No RAG - pure PROMPT-based generation")
    print("=" * 60)
    
    # Configuration
    clueweb_data_dir = "task_file/clueweb22_query_results"
    claude_api_key = "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"
    
    try:
        # Initialize generator
        generator = ClueWeb22SimplifiedGenerator(clueweb_data_dir, claude_api_key)
        
        # Show available topics
        print(f"📋 Available topics:")
        clueweb_topics = list(generator.clueweb_topics.keys())
        energy_topics = list(generator.energy_topics.keys())
        
        print(f"   ClueWeb22 topics: {clueweb_topics}")
        print(f"   Energy topics: {energy_topics}")
        
        # Test with first ClueWeb22 topic
        test_topic = clueweb_topics[0] if clueweb_topics else None
        if not test_topic:
            print("❌ No ClueWeb22 topics available for testing")
            return
        
        print(f"🎯 Testing with topic: {test_topic}")
        topic_data = generator.all_topics[test_topic]
        print(f"📄 Documents available: {topic_data['document_count']}")
        
        # Process single topic with reduced questions for testing
        print("\n🔄 Processing topic...")
        
        # Load documents
        print("📚 Loading documents...")
        documents = generator.load_topic_documents(test_topic, topic_data)
        print(f"   Loaded {len(documents)} documents")
        
        # Identify domain
        print("🔬 Analyzing domain characteristics...")
        domain_info = generator.identify_topic_domain(test_topic, topic_data, documents[:min(10, len(documents))])
        print(f"   Domain: {domain_info.get('primary_domain', 'Unknown')}")
        print(f"   Themes: {', '.join(domain_info.get('key_themes', []))}")
        
        # Generate domain report
        print("📝 Generating domain report...")
        domain_report = generator.generate_domain_report(test_topic, topic_data, documents, domain_info)
        print(f"   Report generated ({len(domain_report.split())} words)")
        
        # Generate research questions (reduced for testing)
        print("❓ Generating research questions (10 for testing)...")
        questions = generator.generate_research_questions(test_topic, topic_data, domain_report, domain_info, num_questions=10)
        print(f"   Generated {len(questions)} questions")
        
        # Compile test results
        test_results = {
            'topic_id': test_topic,
            'topic_type': topic_data['type'],
            'topic_source': topic_data['source'],
            'domain_info': domain_info,
            'document_stats': {
                'total_documents': len(documents),
                'total_words': sum(doc['word_count'] for doc in documents),
                'avg_doc_length': sum(doc['word_count'] for doc in documents) / len(documents)
            },
            'domain_report': domain_report,
            'research_questions': questions,
            'generation_metadata': {
                'timestamp': datetime.now().isoformat(),
                'api_model': 'claude-sonnet-4-20250514',
                'method': 'PROMPT_only_test',
                'num_questions_requested': 10,
                'num_questions_generated': len(questions)
            }
        }
        
        # Save test results
        output_dir = Path("test_simplified_output")
        output_dir.mkdir(exist_ok=True)
        
        test_file = output_dir / f"test_{test_topic}_simplified_result.json"
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(test_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ Test completed successfully!")
        print(f"📊 Results summary:")
        print(f"   Topic: {test_topic}")
        print(f"   Domain: {domain_info.get('primary_domain', 'Unknown')}")
        print(f"   Documents: {len(documents)}")
        print(f"   Report words: {len(domain_report.split())}")
        print(f"   Questions: {len(questions)}")
        print(f"💾 Test result saved: {test_file}")
        
        # Show sample questions
        print(f"\n📝 Sample questions and details:")
        difficulty_counts = {}
        question_type_counts = {}
        
        for i, question in enumerate(questions[:5], 1):
            difficulty = question['difficulty']
            question_type = question['question_type']
            
            difficulty_counts[difficulty] = difficulty_counts.get(difficulty, 0) + 1
            question_type_counts[question_type] = question_type_counts.get(question_type, 0) + 1
            
            print(f"\n   {i}. [{difficulty}] {question['question_text']}")
            print(f"      Type: {question_type}")
            print(f"      Rationale: {question.get('rationale', 'N/A')}")
        
        print(f"\n📊 Question distribution:")
        print(f"   Difficulty: {difficulty_counts}")
        print(f"   Types: {question_type_counts}")
        
        print(f"\n🎉 Test passed! Simplified PROMPT-only system is working correctly.")
        print(f"💡 To run full processing with all topics, use:")
        print(f"   python clueweb22_simplified_generator.py")
        
        # Test energy topic if available
        if energy_topics:
            print(f"\n🔋 Testing energy topic: {energy_topics[0]}")
            energy_test_topic = energy_topics[0]
            energy_topic_data = generator.all_topics[energy_test_topic]
            
            print(f"📄 Energy papers available: {energy_topic_data['document_count']}")
            print(f"📚 Subdomain: {energy_topic_data['subdomain']}")
            
            # Quick test of energy topic loading
            energy_documents = generator.load_topic_documents(energy_test_topic, energy_topic_data)
            print(f"   Loaded {len(energy_documents)} energy papers")
            
            if energy_documents:
                print(f"   Sample paper: {energy_documents[0].get('paper_title', 'Unknown')[:60]}...")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_simplified_single_topic() 
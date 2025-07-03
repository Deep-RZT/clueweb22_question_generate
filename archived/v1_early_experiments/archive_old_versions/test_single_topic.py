#!/usr/bin/env python3
"""
Test script for ClueWeb22 Synthetic Research Generation
Tests processing of a single topic to verify system functionality
"""

import json
from pathlib import Path
from datetime import datetime
from clueweb22_synthetic_research_generator import ClueWeb22SyntheticGenerator

def test_single_topic():
    """Test processing of a single topic"""
    
    print("🧪 Testing ClueWeb22 Synthetic Research Generation")
    print("=" * 60)
    
    # Configuration
    data_dir = "task_file/clueweb22_query_results"
    claude_api_key = "xxxxx"
    
    try:
        # Initialize generator
        generator = ClueWeb22SyntheticGenerator(data_dir, claude_api_key)
        
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
        
        # Identify domain
        print("🔬 Analyzing domain characteristics...")
        domain_info = generator.identify_topic_domain(test_topic, documents[:10])
        print(f"   Domain: {domain_info.get('primary_domain', 'Unknown')}")
        print(f"   Themes: {', '.join(domain_info.get('key_themes', []))}")
        
        # Generate domain report
        print("📝 Generating domain report...")
        domain_report = generator.generate_domain_report(test_topic, documents, domain_info)
        print(f"   Report generated ({len(domain_report.split())} words)")
        
        # Generate research questions (only 10 for testing)
        print("❓ Generating research questions (10 for testing)...")
        questions = generator.generate_research_questions(test_topic, domain_report, domain_info, num_questions=10)
        print(f"   Generated {len(questions)} questions")
        
        # Generate answers
        print("💡 Generating question answers...")
        qa_pairs = generator.generate_question_answers(questions, domain_report, domain_info)
        print(f"   Generated {len(qa_pairs)} QA pairs")
        
        # Compile results
        result = {
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
                'num_questions_requested': 10,
                'num_questions_generated': len(qa_pairs),
                'test_mode': True
            }
        }
        
        if result:
            # Save test result
            test_output_dir = Path("test_output")
            test_output_dir.mkdir(exist_ok=True)
            
            test_file = test_output_dir / f"test_{test_topic}_result.json"
            with open(test_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            # Print summary
            print(f"\n✅ Test completed successfully!")
            print(f"📊 Results summary:")
            print(f"   Topic: {result['topic_id']}")
            print(f"   Domain: {result['domain_info'].get('primary_domain', 'Unknown')}")
            print(f"   Documents: {result['document_stats']['total_documents']}")
            print(f"   QA Pairs: {len(result['qa_pairs'])}")
            print(f"   Report words: {len(result['domain_report'].split())}")
            print(f"💾 Test result saved: {test_file}")
            
            # Show sample questions
            print(f"\n📝 Sample questions generated:")
            for i, qa in enumerate(result['qa_pairs'][:5], 1):
                print(f"   {i}. [{qa['difficulty']}] {qa['question_text'][:80]}...")
            
            # Show difficulty distribution
            difficulties = [qa['difficulty'] for qa in result['qa_pairs']]
            diff_counts = {diff: difficulties.count(diff) for diff in set(difficulties)}
            print(f"\n📊 Difficulty distribution: {diff_counts}")
            
            return True
            
        else:
            print("❌ Test failed - no results generated")
            return False
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_single_topic()
    if success:
        print(f"\n🎉 Test passed! System is ready for full processing.")
        print(f"💡 To run full processing with 50 questions per topic, use:")
        print(f"   python clueweb22_synthetic_research_generator.py")
    else:
        print(f"\n💥 Test failed! Please check the system before full processing.") 
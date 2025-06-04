#!/usr/bin/env python3
"""
快速版本：跳过refinement直接生成答案
利用已有的checkpoint继续
"""

import json
import os
from pathlib import Path
from client_focused_pipeline import ClientFocusedPipeline

def main():
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python skip_refinement_pipeline.py <openai_api_key>")
        return
    
    api_key = sys.argv[1]
    pipeline = ClientFocusedPipeline(api_key, "gpt-4o")
    
    output_dir = Path(pipeline.config['output_directory'])
    
    # Load checkpoints
    questions_checkpoint = output_dir / "checkpoint_step3_questions.json"
    reports_checkpoint = output_dir / "checkpoint_step2_reports.json"
    
    if not questions_checkpoint.exists() or not reports_checkpoint.exists():
        print("❌ Checkpoints not found. Please run main pipeline first.")
        return
    
    print("🚀 Quick Pipeline: Skip Refinement, Generate Answers")
    print("=" * 50)
    
    # Load data
    with open(questions_checkpoint, 'r', encoding='utf-8') as f:
        questions = json.load(f)
    
    with open(reports_checkpoint, 'r', encoding='utf-8') as f:
        reports = json.load(f)
    
    print(f"✅ Loaded {len(questions)} question sets")
    print(f"✅ Loaded {len(reports)} reports")
    
    # Skip refinement, go directly to answer generation
    print("\n📚 Step 5: Answer Generation (Skip Refinement)")
    complete_qa_dataset = pipeline._generate_answers(questions, reports)
    
    # Save final results
    print("\n💾 Step 6: Save Complete QA Benchmark")
    final_results = pipeline._save_final_results(complete_qa_dataset, output_dir)
    
    print("\n🎉 Quick Pipeline Complete!")
    print(f"📁 Results saved to: {output_dir}")
    
    # Print summary
    summary_stats = final_results['summary_statistics']
    print(f"\n📊 Summary:")
    print(f"  Topics: {summary_stats['total_topics']}")
    print(f"  Questions: {summary_stats['total_questions']}")
    print(f"  Answers: {summary_stats['total_answers']}")
    print(f"  Success rate: {summary_stats['success_rate']:.1f}%")

if __name__ == "__main__":
    main() 
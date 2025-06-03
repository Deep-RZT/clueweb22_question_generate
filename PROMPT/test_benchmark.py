#!/usr/bin/env python
# test_benchmark.py - Test the benchmark generator with a small sample

import os
from benchmark_generator import BenchmarkGenerator
from config import Config

def test_benchmark_generator():
    """Test the benchmark generator with a small number of queries"""
    print("=" * 60)
    print("TESTING BENCHMARK GENERATOR")
    print("=" * 60)
    
    # Use a minimal configuration for testing
    test_config = {
        "total_queries": 4,       # Very small number for quick testing
        "deep_thinking_count": 2, # 2 deep thinking
        "standard_count": 2,      # 2 standard
        "easy_pct": 50,           # Half easy, half medium
        "medium_pct": 50,         # Half easy, half medium
        "hard_pct": 0,            # No hard questions for faster testing
        "general_pct": 50,        # Half general, half cross-domain
        "cross_pct": 50,          # Half general, half cross-domain
        "batch_size": 2,          # Process in small batches to test batching functionality
        "generate_answers": True  # Generate answers for testing
    }
    
    # Ensure the output directory exists
    os.makedirs(Config.OUTPUT_DIR, exist_ok=True)
    
    # Create generator instance
    print("Creating benchmark generator...")
    generator = BenchmarkGenerator()
    
    # Generate benchmark with test configuration
    print(f"Generating benchmark with {test_config['total_queries']} queries...")
    generated = generator.generate_benchmark(
        total_queries=test_config["total_queries"],
        deep_thinking_count=test_config["deep_thinking_count"],
        standard_count=test_config["standard_count"],
        easy_pct=test_config["easy_pct"],
        medium_pct=test_config["medium_pct"],
        hard_pct=test_config["hard_pct"],
        general_pct=test_config["general_pct"],
        cross_pct=test_config["cross_pct"],
        batch_size=test_config["batch_size"],
        generate_answers=test_config["generate_answers"]
    )
    
    print(f"\nTest complete! Generated {generated} queries with answers.")
    print("=" * 60)

if __name__ == "__main__":
    test_benchmark_generator() 
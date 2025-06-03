# main.py - Main execution file
import os
import json
import pandas as pd
from dotenv import load_dotenv
from energy_query_generator import EnergyQueryGenerator, QueryRequirement, Difficulty, Category
from config import Config
import datetime
import random

# Load environment variables
load_dotenv()

def create_balanced_requirements(total_queries: int = 50) -> list:
    """Create balanced query requirements"""
    requirements = []
    
    # Based on config distribution
    easy_count = int(total_queries * Config.DIFFICULTY_DISTRIBUTION['Easy'] / 100)
    medium_count = int(total_queries * Config.DIFFICULTY_DISTRIBUTION['Medium'] / 100)
    hard_count = total_queries - easy_count - medium_count
    
    general_count = int(total_queries * Config.CATEGORY_DISTRIBUTION['General'] / 100)
    cross_count = total_queries - general_count
    
    # Subdomains list
    subdomains = Config.SUBDOMAINS
    
    # Distribution table for planning (not using exact nums from config yet)
    distribution = [
        # (Difficulty, Category, Count)
        (Difficulty.EASY, Category.GENERAL, int(easy_count * general_count / total_queries)),
        (Difficulty.EASY, Category.CROSS_SUBDOMAIN, easy_count - int(easy_count * general_count / total_queries)),
        (Difficulty.MEDIUM, Category.GENERAL, int(medium_count * general_count / total_queries)),
        (Difficulty.MEDIUM, Category.CROSS_SUBDOMAIN, medium_count - int(medium_count * general_count / total_queries)),
        (Difficulty.HARD, Category.GENERAL, int(hard_count * general_count / total_queries)),
        (Difficulty.HARD, Category.CROSS_SUBDOMAIN, hard_count - int(hard_count * general_count / total_queries))
    ]
    
    # Create requirements
    for difficulty, category, count in distribution:
        for i in range(count):
            # Randomly select primary subdomain
            primary = random.choice(subdomains)
            
            # For cross-domain, select random secondary subdomains
            if category == Category.CROSS_SUBDOMAIN:
                remaining = [s for s in subdomains if s != primary]
                # Easy: 1 secondary, Medium: 2 secondary, Hard: 3 secondary
                sec_count = 1
                if difficulty == Difficulty.MEDIUM:
                    sec_count = 2
                elif difficulty == Difficulty.HARD:
                    sec_count = 3
                
                secondary = random.sample(remaining, min(sec_count, len(remaining)))
                requirements.append(QueryRequirement(
                    difficulty=difficulty,
                    category=category,
                    primary_subdomain=primary,
                    secondary_subdomains=secondary,
                    count=1
                ))
            else:
                # General category - no secondary domains
                requirements.append(QueryRequirement(
                    difficulty=difficulty,
                    category=category,
                    primary_subdomain=primary,
                    count=1
                ))
    
    # Shuffle to avoid patterns
    random.shuffle(requirements)
    return requirements

def generate_sample_queries(count=10):
    """Generate sample queries for demonstration"""
    samples = []
    
    # Define some sample queries across different difficulties and categories
    sample_data = [
        # Easy queries
        {
            "text": "Explain the basic operating principles of nuclear fission reactors and their role in baseload power generation.",
            "category": "General",
            "subdomains": ["Nuclear"],
            "difficulty": "Easy"
        },
        {
            "text": "Describe the process of hydraulic fracturing (fracking) and explain its environmental considerations.",
            "category": "Cross_Subdomain",
            "subdomains": ["Fossil_Fuels", "Environmental"],
            "difficulty": "Easy"
        },
        
        # Medium queries
        {
            "text": "Compare the environmental impacts of solar PV and wind power throughout their lifecycle.",
            "category": "Cross_Subdomain",
            "subdomains": ["Renewable", "Environmental"],
            "difficulty": "Medium"
        },
        {
            "text": "What are the key challenges in scaling grid-scale battery storage systems to support intermittent renewable energy sources?",
            "category": "Cross_Subdomain",
            "subdomains": ["Grid_Storage", "Renewable"],
            "difficulty": "Medium"
        },
        {
            "text": "Describe the concept of energy return on investment (EROI) and explain how it differs across various energy sources.",
            "category": "General",
            "subdomains": ["Economics"],
            "difficulty": "Medium"
        },
        
        # Hard queries
        {
            "text": "Analyze how carbon pricing mechanisms impact the economic competitiveness of different energy generation technologies.",
            "category": "Cross_Subdomain",
            "subdomains": ["Economics", "Policy", "Environmental"],
            "difficulty": "Hard"
        },
        {
            "text": "Evaluate the potential of hydrogen as an energy carrier in a low-carbon economy, considering production methods, storage challenges, and end-use applications.",
            "category": "Cross_Subdomain",
            "subdomains": ["Grid_Storage", "Renewable", "Economics"],
            "difficulty": "Hard"
        },
        {
            "text": "Develop a comprehensive framework for assessing the social equity implications of energy transition policies in developing economies.",
            "category": "Cross_Subdomain",
            "subdomains": ["Policy", "Economics", "Environmental"],
            "difficulty": "Hard"
        }
    ]
    
    # Select random samples if we need fewer than available
    if count < len(sample_data):
        samples_data = random.sample(sample_data, count)
    else:
        samples_data = sample_data
        
    # Convert to proper format
    for i, sample in enumerate(samples_data, 1):
        samples.append({
            "id": f"MQ{i:03d}",
            "query_text": sample["text"],
            "category": sample["category"],
            "subdomains": sample["subdomains"],
            "difficulty": sample["difficulty"],
            "source": "Manual",
            "timestamp": datetime.datetime.now().isoformat()
        })
    
    return samples

def main():
    """Main execution function"""
    print("Energy Query Generator Starting...")
    print(f"Target: Generate {Config.TOTAL_QUERIES} queries")
    print(f"  - {Config.AI_GENERATED} AI-generated queries")
    print(f"  - {Config.MANUAL_GENERATED} manual queries (will be simulated)")
    
    # Ensure output directory exists
    os.makedirs(Config.OUTPUT_DIR, exist_ok=True)
    
    # Simulate manual queries
    manual_queries = generate_sample_queries(Config.MANUAL_GENERATED)
    print(f"\nSimulated {len(manual_queries)} manual queries")
    
    # Check API key (for AI-generated queries)
    ai_queries = []
    if Config.CLAUDE_API_KEY:
        try:
            # Calculate number of AI queries needed
            ai_target = min(Config.AI_GENERATED, Config.TOTAL_QUERIES - len(manual_queries))
            
            if ai_target > 0:
                print(f"\nGenerating {ai_target} AI queries...")
                
                # Initialize generator
                generator = EnergyQueryGenerator()
                
                # Create balanced generation requirements
                requirements = create_balanced_requirements(ai_target)
                
                print(f"\nGeneration Plan:")
                print(f"  Total requirements: {len(requirements)}")
                
                # Summarize requirement distribution
                req_stats = {}
                for req in requirements:
                    key = f"{req.difficulty.value}_{req.category.value}"
                    req_stats[key] = req_stats.get(key, 0) + 1
                
                for key, count in req_stats.items():
                    print(f"  {key}: {count}")
                
                # Batch generate
                ai_queries = generator.batch_generate(requirements)
                
                if not ai_queries:
                    print("No queries were generated successfully.")
                else:
                    # Quality filtering
                    ai_queries = generator.filter_high_quality_queries(ai_queries)
                    print(f"\nSuccessfully generated {len(ai_queries)} high-quality AI queries")
            else:
                print("\nNo need to generate AI queries, manual queries already meet or exceed target")
                
        except Exception as e:
            print(f"❌ Error generating AI queries: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("\nCLAUDE_API_KEY not set, can't generate AI queries")
        print("Set your API key in the .env file")
    
    # Combine queries
    combined_queries = []
    combined_queries.extend(manual_queries)
    combined_queries.extend(ai_queries)
    
    print(f"\nCombined {len(combined_queries)} queries in total")
    
    # Using generator functions to save results
    if combined_queries:
        try:
            # Initialize generator (if not already initialized)
            if 'generator' not in locals():
                if Config.CLAUDE_API_KEY:
                    generator = EnergyQueryGenerator()
                else:
                    # Create minimal generator for saving functionality if no API key
                    from energy_query_generator import QualityAssessor
                    class MinimalGenerator:
                        def __init__(self):
                            self.quality_assessor = QualityAssessor()
                        
                        def save_queries_json(self, queries, filename):
                            output_data = {
                                "metadata": {
                                    "total_queries": len(queries),
                                    "generation_timestamp": datetime.datetime.now().isoformat(),
                                    "source": "Mixed (AI and Manual)",
                                    "configuration": {
                                        "total_target": Config.TOTAL_QUERIES,
                                        "ai_target": Config.AI_GENERATED,
                                        "manual_target": Config.MANUAL_GENERATED
                                    }
                                },
                                "queries": queries
                            }
                            
                            with open(filename, 'w', encoding='utf-8') as f:
                                json.dump(output_data, f, indent=2, ensure_ascii=False)
                            
                            return filename
                        
                        def save_queries_excel(self, queries, filename):
                            rows = []
                            for query in queries:
                                row = {
                                    'ID': query['id'],
                                    'Query Text': query['query_text'],
                                    'Category': query['category'],
                                    'Subdomains': ', '.join(query['subdomains']),
                                    'Difficulty': query['difficulty'],
                                    'Source': query['source']
                                }
                                
                                if 'quality_scores' in query:
                                    row['Overall Quality Score'] = f"{query['quality_scores']['overall']:.3f}"
                                
                                rows.append(row)
                            
                            df = pd.DataFrame(rows)
                            df.to_excel(filename, index=False)
                            
                            return filename
                        
                        def generate_statistics_report(self, queries):
                            print("\n" + "=" * 50)
                            print("BENCHMARK STATISTICS REPORT")
                            print("=" * 50)
                            
                            # Basic stats
                            print(f"Total queries: {len(queries)}")
                            
                            # Source distribution
                            source_counts = {}
                            for query in queries:
                                src = query['source']
                                source_counts[src] = source_counts.get(src, 0) + 1
                            
                            print("\nSource Distribution:")
                            for src, count in source_counts.items():
                                percentage = (count / len(queries)) * 100
                                print(f"  {src}: {count} ({percentage:.1f}%)")
                            
                            # Difficulty distribution
                            difficulty_counts = {}
                            for query in queries:
                                diff = query['difficulty']
                                difficulty_counts[diff] = difficulty_counts.get(diff, 0) + 1
                            
                            print("\nDifficulty Distribution:")
                            for diff, count in difficulty_counts.items():
                                percentage = (count / len(queries)) * 100
                                print(f"  {diff}: {count} ({percentage:.1f}%)")
                            
                            # Category distribution
                            category_counts = {}
                            for query in queries:
                                cat = query['category']
                                category_counts[cat] = category_counts.get(cat, 0) + 1
                            
                            print("\nCategory Distribution:")
                            for cat, count in category_counts.items():
                                percentage = (count / len(queries)) * 100
                                print(f"  {cat}: {count} ({percentage:.1f}%)")
                            
                            # Subdomain distribution
                            subdomain_counts = {}
                            for query in queries:
                                for subdomain in query['subdomains']:
                                    subdomain_counts[subdomain] = subdomain_counts.get(subdomain, 0) + 1
                            
                            print("\nSubdomain Distribution:")
                            for subdomain, count in sorted(subdomain_counts.items()):
                                print(f"  {subdomain}: {count}")
                            
                            print("=" * 50)
                    
                    generator = MinimalGenerator()
            
            # Generate filenames
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            json_file = f"{Config.OUTPUT_DIR}/energy_benchmark_{timestamp}.json"
            excel_file = f"{Config.OUTPUT_DIR}/energy_benchmark_{timestamp}.xlsx"
            
            # Save results
            json_file = generator.save_queries_json(combined_queries, json_file)
            excel_file = generator.save_queries_excel(combined_queries, excel_file)
            
            # Generate statistics report
            generator.generate_statistics_report(combined_queries)
            
            print(f"\n✅ Benchmark creation complete!")
            print(f"📁 Output files:")
            print(f"  - JSON: {json_file}")
            print(f"  - Excel: {excel_file}")
            
            # Report gap from target
            if len(combined_queries) < Config.TOTAL_QUERIES:
                missing = Config.TOTAL_QUERIES - len(combined_queries)
                print(f"\n⚠️ Warning: Generated queries less than target ({missing} missing)")
            
        except Exception as e:
            print(f"❌ Error saving results: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("\n⚠️ No queries to save.")

if __name__ == "__main__":
    main()
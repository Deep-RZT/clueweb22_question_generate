#!/usr/bin/env python
# benchmark_generator.py - Generate energy domain benchmark queries

import os
import json
import pandas as pd
import random
import time
from datetime import datetime
from config import Config
from deep_thinking_api import call_deep_thinking
from standard_api import call_standard
from answer_generator import generate_answers_for_queries

# Define subdomains 
SUBDOMAINS = [
    "Renewable", 
    "Fossil_Fuels", 
    "Nuclear", 
    "Grid_Storage",
    "Policy", 
    "Economics", 
    "Environmental"
]

# Define difficulties
DIFFICULTIES = ["Easy", "Medium", "Hard"]

# Define categories
CATEGORIES = ["General", "Cross_Subdomain"]

class BenchmarkGenerator:
    """Energy domain benchmark query generator"""
    
    def __init__(self):
        """Initialize the benchmark generator"""
        self.queries = []
        self.generated_dt_count = 0  # Track total Deep Thinking queries generated
        self.generated_st_count = 0  # Track total Standard queries generated
        os.makedirs(Config.OUTPUT_DIR, exist_ok=True)
    
    def generate_benchmark(self, total_queries=200, deep_thinking_count=100, standard_count=100,
                          easy_pct=30, medium_pct=40, hard_pct=30,
                          general_pct=40, cross_pct=60, batch_size=20,
                          generate_answers=Config.GENERATE_ANSWERS):
        """
        Generate the complete benchmark based on specifications
        
        Parameters:
        - total_queries: Total number of queries to generate
        - deep_thinking_count: Number of deep thinking queries to generate
        - standard_count: Number of standard queries to generate
        - easy_pct: Percentage of Easy queries
        - medium_pct: Percentage of Medium queries
        - hard_pct: Percentage of Hard queries
        - general_pct: Percentage of General queries
        - cross_pct: Percentage of Cross-subdomain queries
        - batch_size: Number of queries to generate and save in each batch
        - generate_answers: Whether to generate answers for the queries
        """
        print(f"Generating Energy Domain Benchmark - {total_queries} Queries")
        print(f"  - {deep_thinking_count} Deep Thinking queries")
        print(f"  - {standard_count} Standard queries")
        print(f"Difficulty distribution: {easy_pct}% Easy, {medium_pct}% Medium, {hard_pct}% Hard")
        print(f"Category distribution: {general_pct}% General, {cross_pct}% Cross-subdomain")
        print(f"Using batch size of {batch_size} queries")
        print(f"Generate answers: {generate_answers}")
        
        # Timestamp for this batch
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Initialize batch counters
        total_generated = 0
        batch_number = 1
        
        # Create file paths for final merged outputs
        final_json_path = f"{Config.OUTPUT_DIR}/energy_benchmark_{timestamp}_complete.json"
        final_excel_path = f"{Config.OUTPUT_DIR}/energy_benchmark_{timestamp}_complete.xlsx"
        
        # Plan requirements for deep thinking queries
        deep_thinking_reqs = self._create_balanced_requirements(
            deep_thinking_count, 
            easy_pct, medium_pct, hard_pct,
            general_pct, cross_pct
        )
        
        # Plan requirements for standard queries
        standard_reqs = self._create_balanced_requirements(
            standard_count,
            easy_pct, medium_pct, hard_pct,
            general_pct, cross_pct
        )
        
        # Process in batches
        all_batches_info = []
        
        # Process Deep Thinking queries in batches
        remaining_dt = deep_thinking_count
        while remaining_dt > 0:
            # Determine current batch size
            current_batch_size = min(batch_size, remaining_dt)
            print(f"\nGenerating batch {batch_number}: {current_batch_size} Deep Thinking queries...")
            
            # Get requirements for this batch
            batch_dt_reqs = deep_thinking_reqs[:current_batch_size]
            deep_thinking_reqs = deep_thinking_reqs[current_batch_size:]
            
            # Generate batch
            batch_queries = self._generate_queries_deep_thinking(batch_dt_reqs)
            
            # Assign IDs and save batch
            self._assign_query_ids_batch(batch_queries, "Deep_Thinking")
            
            # Generate answers if enabled
            if generate_answers:
                batch_queries = generate_answers_for_queries(batch_queries)
            
            # Save this batch
            batch_info = self._save_batch(batch_queries, batch_number, timestamp)
            all_batches_info.append(batch_info)
            
            # Update counters
            remaining_dt -= current_batch_size
            total_generated += len(batch_queries)
            batch_number += 1
            
            print(f"Batch {batch_number-1} complete. Total generated: {total_generated}/{total_queries}")
        
        # Process Standard queries in batches
        remaining_st = standard_count
        while remaining_st > 0:
            # Determine current batch size
            current_batch_size = min(batch_size, remaining_st)
            print(f"\nGenerating batch {batch_number}: {current_batch_size} Standard queries...")
            
            # Get requirements for this batch
            batch_st_reqs = standard_reqs[:current_batch_size]
            standard_reqs = standard_reqs[current_batch_size:]
            
            # Generate batch
            batch_queries = self._generate_queries_standard(batch_st_reqs)
            
            # Assign IDs and save batch
            self._assign_query_ids_batch(batch_queries, "Standard")
            
            # Generate answers if enabled
            if generate_answers:
                batch_queries = generate_answers_for_queries(batch_queries)
            
            # Save this batch
            batch_info = self._save_batch(batch_queries, batch_number, timestamp)
            all_batches_info.append(batch_info)
            
            # Update counters
            remaining_st -= current_batch_size
            total_generated += len(batch_queries)
            batch_number += 1
            
            print(f"Batch {batch_number-1} complete. Total generated: {total_generated}/{total_queries}")
        
        print(f"\nGeneration complete! {total_generated} queries generated in {batch_number-1} batches.")
        
        # Combine all batches into final files if needed
        if batch_number > 2:  # If we have multiple batches
            print("Merging all batches into final files...")
            self._merge_batches(all_batches_info, final_json_path, final_excel_path)
            print(f"Merged files saved to:\n  - {final_json_path}\n  - {final_excel_path}")
        
        return total_generated
    
    def _save_batch(self, queries, batch_number, timestamp):
        """Save a batch of queries to both JSON and Excel"""
        # Create filenames for this batch
        json_filename = f"{Config.OUTPUT_DIR}/energy_benchmark_{timestamp}_batch{batch_number:02d}.json"
        excel_filename = f"{Config.OUTPUT_DIR}/energy_benchmark_{timestamp}_batch{batch_number:02d}.xlsx"
        
        # Temporarily set the queries list for saving
        self.queries = queries
        
        # Save to files
        json_path = self.save_to_json(json_filename)
        excel_path = self.save_to_excel(excel_filename)
        
        # Clear queries after saving to free memory
        batch_info = {
            "batch_number": batch_number,
            "query_count": len(queries),
            "json_path": json_path,
            "excel_path": excel_path
        }
        self.queries = []
        
        return batch_info
    
    def _merge_batches(self, batches_info, final_json_path, final_excel_path):
        """Merge all generated batches into complete files"""
        # All merged queries
        all_queries = []
        
        # Load all batch JSON files
        for batch in batches_info:
            with open(batch['json_path'], 'r', encoding='utf-8') as f:
                batch_data = json.load(f)
                all_queries.extend(batch_data['queries'])
        
        # Sort by ID
        all_queries.sort(key=lambda q: q['id'])
        
        # Save complete JSON
        data = {
            "metadata": {
                "total_queries": len(all_queries),
                "generation_timestamp": datetime.now().isoformat(),
                "configuration": {
                    "model": Config.MODEL_NAME,
                    "difficulties": DIFFICULTIES,
                    "categories": CATEGORIES,
                    "subdomains": SUBDOMAINS
                }
            },
            "queries": all_queries
        }
        
        with open(final_json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Save complete Excel
        # Prepare data for Excel
        rows = []
        for query in all_queries:
            # Base fields for all queries
            row = {
                'ID': query['id'],
                'Query Text': query['query_text'],
                'Category': query['category'],
                'Subdomains': ', '.join(query['subdomains']),
                'Difficulty': query['difficulty'],
                'Source': query['source'],
                'Generation Date': query['timestamp'].split('T')[0]
            }
            
            # Add answer if available
            if 'answer' in query:
                row['Answer'] = query['answer']['text']
                if 'generation_details' in query['answer']:
                    row['Answer Prompt'] = query['answer']['generation_details'].get('prompt', '')
            
            # Add prompt information if available
            if 'generation_details' in query:
                if query['source'] == 'Deep_Thinking':
                    if 'prompts' in query['generation_details'] and query['generation_details']['prompts']:
                        prompts = query['generation_details']['prompts']
                        row['Understanding Prompt'] = prompts.get('understanding_prompt', '')
                        row['Generation Prompt'] = prompts.get('generation_prompt', '')
                        row['Refinement Prompt'] = prompts.get('refinement_prompt', '')
                    else:
                        # Legacy data without prompt tracking
                        row['Thinking Process'] = query['generation_details'].get('thinking_process', '')
                        row['Initial Questions'] = query['generation_details'].get('initial_questions', '')
                elif query['source'] == 'Standard':
                    row['Prompt'] = query['generation_details'].get('prompt', '')
            
            rows.append(row)
        
        # Create DataFrame and save
        df = pd.DataFrame(rows)
        
        # Save to Excel
        with pd.ExcelWriter(final_excel_path, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Energy Benchmark')
            
            # Auto-adjust columns (limited to avoid excessive width)
            for column in df:
                column_width = max(df[column].astype(str).map(len).max(), len(column))
                col_idx = df.columns.get_loc(column)
                writer.sheets['Energy Benchmark'].column_dimensions[chr(65 + col_idx)].width = min(column_width + 2, 100)
    
    def _create_balanced_requirements(self, count, easy_pct, medium_pct, hard_pct, 
                                     general_pct, cross_pct):
        """Create balanced query generation requirements"""
        requirements = []
        
        # Calculate counts for each difficulty
        easy_count = int(count * easy_pct / 100)
        medium_count = int(count * medium_pct / 100)
        hard_count = count - easy_count - medium_count
        
        # Calculate counts for each category
        general_count = int(count * general_pct / 100)
        cross_count = count - general_count
        
        # Distribution table
        distribution = [
            # (Difficulty, Category, Count)
            ("Easy", "General", int(easy_count * general_count / count)),
            ("Easy", "Cross_Subdomain", easy_count - int(easy_count * general_count / count)),
            ("Medium", "General", int(medium_count * general_count / count)),
            ("Medium", "Cross_Subdomain", medium_count - int(medium_count * general_count / count)),
            ("Hard", "General", int(hard_count * general_count / count)),
            ("Hard", "Cross_Subdomain", hard_count - int(hard_count * general_count / count))
        ]
        
        # Create requirements
        primary_domains = [d for d in SUBDOMAINS if d not in ["Policy", "Economics", "Environmental"]]
        secondary_domains = [d for d in SUBDOMAINS if d not in primary_domains]
        
        for difficulty, category, count in distribution:
            for i in range(count):
                # Randomly select primary subdomain
                primary = random.choice(primary_domains)
                
                # For cross-domain, select random secondary subdomains
                if category == "Cross_Subdomain":
                    remaining = [s for s in SUBDOMAINS if s != primary]
                    # Easy: 1 secondary, Medium: 2 secondary, Hard: 3 secondary
                    sec_count = 1
                    if difficulty == "Medium":
                        sec_count = 2
                    elif difficulty == "Hard":
                        sec_count = 3
                    
                    secondary = random.sample(remaining, min(sec_count, len(remaining)))
                    requirements.append({
                        "difficulty": difficulty,
                        "category": category,
                        "primary_domain": primary,
                        "secondary_domains": secondary,
                        "count": 1
                    })
                else:
                    # General category - no secondary domains
                    requirements.append({
                        "difficulty": difficulty,
                        "category": category,
                        "primary_domain": primary,
                        "count": 1
                    })
        
        # Shuffle to avoid patterns
        random.shuffle(requirements)
        return requirements
    
    def _generate_queries_deep_thinking(self, requirements):
        """Generate queries using the deep thinking method"""
        queries = []
        
        for i, req in enumerate(requirements, 1):
            print(f"  [{i}/{len(requirements)}] Deep Thinking: {req['difficulty']} {req['category']} - {req['primary_domain']}")
            
            # Add delay to prevent rate limiting
            if i > 1:
                time.sleep(Config.DELAY_BETWEEN_CALLS)
            
            # Call deep thinking API
            result = call_deep_thinking(req)
            
            if result['success']:
                # Extract query text
                query_text = result['final_questions'].strip()
                
                # Create query object
                query = {
                    "query_text": query_text,
                    "category": req['category'],
                    "subdomains": [req['primary_domain']] + (req.get('secondary_domains', []) or []),
                    "difficulty": req['difficulty'],
                    "source": "Deep_Thinking",
                    "timestamp": datetime.now().isoformat(),
                    "generation_details": {
                        "thinking_process": result['thinking_process'],
                        "initial_questions": result['initial_questions'],
                        "prompts": result['prompts'] if 'prompts' in result else None
                    }
                }
                
                queries.append(query)
                print(f"    ✓ Generated: {query_text[:100]}...")
            else:
                print(f"    ✗ Failed: {result.get('error', 'Unknown error')}")
        
        return queries
    
    def _generate_queries_standard(self, requirements):
        """Generate queries using the standard method"""
        queries = []
        
        for i, req in enumerate(requirements, 1):
            print(f"  [{i}/{len(requirements)}] Standard: {req['difficulty']} {req['category']} - {req['primary_domain']}")
            
            # Add delay to prevent rate limiting
            if i > 1:
                time.sleep(Config.DELAY_BETWEEN_CALLS)
            
            # Call standard API
            result = call_standard(req)
            
            if result['success']:
                # Extract query text
                query_text = result['content'].strip()
                
                # Create query object
                query = {
                    "query_text": query_text,
                    "category": req['category'],
                    "subdomains": [req['primary_domain']] + (req.get('secondary_domains', []) or []),
                    "difficulty": req['difficulty'],
                    "source": "Standard",
                    "timestamp": datetime.now().isoformat(),
                    "generation_details": {
                        "prompt": result['prompt'] if 'prompt' in result else None
                    }
                }
                
                queries.append(query)
                print(f"    ✓ Generated: {query_text[:100]}...")
            else:
                print(f"    ✗ Failed: {result.get('error', 'Unknown error')}")
        
        return queries
    
    def _assign_query_ids(self):
        """Assign unique IDs to all queries"""
        deep_thinking_count = 0
        standard_count = 0
        
        for query in self.queries:
            if query["source"] == "Deep_Thinking":
                deep_thinking_count += 1
                query["id"] = f"DT{deep_thinking_count:03d}"
            else:
                standard_count += 1
                query["id"] = f"ST{standard_count:03d}"
    
    def _assign_query_ids_batch(self, queries, source_type):
        """Assign unique IDs to a batch of queries"""
        for query in queries:
            if source_type == "Deep_Thinking":
                self.generated_dt_count += 1
                query["id"] = f"DT{self.generated_dt_count:03d}"
            else:
                self.generated_st_count += 1
                query["id"] = f"ST{self.generated_st_count:03d}"
    
    def save_to_json(self, filename=None):
        """Save benchmark to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{Config.OUTPUT_DIR}/energy_benchmark_{timestamp}.json"
        
        data = {
            "metadata": {
                "total_queries": len(self.queries),
                "generation_timestamp": datetime.now().isoformat(),
                "configuration": {
                    "model": Config.MODEL_NAME,
                    "difficulties": DIFFICULTIES,
                    "categories": CATEGORIES,
                    "subdomains": SUBDOMAINS
                }
            },
            "queries": self.queries
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"Benchmark saved to JSON: {filename}")
        return filename
    
    def save_to_excel(self, filename=None):
        """Save benchmark to Excel file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{Config.OUTPUT_DIR}/energy_benchmark_{timestamp}.xlsx"
        
        # Prepare data for Excel
        rows = []
        for query in self.queries:
            # Base fields for all queries
            row = {
                'ID': query['id'],
                'Query Text': query['query_text'],
                'Category': query['category'],
                'Subdomains': ', '.join(query['subdomains']),
                'Difficulty': query['difficulty'],
                'Source': query['source'],
                'Generation Date': query['timestamp'].split('T')[0]
            }
            
            # Add answer if available
            if 'answer' in query:
                row['Answer'] = query['answer']['text']
                if 'generation_details' in query['answer']:
                    row['Answer Prompt'] = query['answer']['generation_details'].get('prompt', '')
            
            # Add prompt information if available
            if 'generation_details' in query:
                if query['source'] == 'Deep_Thinking':
                    if 'prompts' in query['generation_details'] and query['generation_details']['prompts']:
                        prompts = query['generation_details']['prompts']
                        row['Understanding Prompt'] = prompts.get('understanding_prompt', '')
                        row['Generation Prompt'] = prompts.get('generation_prompt', '')
                        row['Refinement Prompt'] = prompts.get('refinement_prompt', '')
                    else:
                        # Legacy data without prompt tracking
                        row['Thinking Process'] = query['generation_details'].get('thinking_process', '')
                        row['Initial Questions'] = query['generation_details'].get('initial_questions', '')
                elif query['source'] == 'Standard':
                    row['Prompt'] = query['generation_details'].get('prompt', '')
            
            rows.append(row)
        
        # Create DataFrame and save
        df = pd.DataFrame(rows)
        
        # Optimize column widths
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Energy Benchmark')
            
            # Auto-adjust columns
            for column in df:
                column_width = max(df[column].astype(str).map(len).max(), len(column))
                col_idx = df.columns.get_loc(column)
                writer.sheets['Energy Benchmark'].column_dimensions[chr(65 + col_idx)].width = min(column_width + 2, 100)
        
        print(f"Benchmark saved to Excel: {filename}")
        return filename
    
    def generate_statistics(self):
        """Generate and display statistics about the benchmark"""
        if not self.queries:
            print("No queries to analyze.")
            return
        
        print("\n" + "=" * 60)
        print("BENCHMARK STATISTICS")
        print("=" * 60)
        
        total = len(self.queries)
        print(f"Total Queries: {total}")
        
        # Source distribution
        sources = {}
        for q in self.queries:
            source = q['source']
            sources[source] = sources.get(source, 0) + 1
        
        print("\nSource Distribution:")
        for source, count in sources.items():
            print(f"  {source}: {count} ({count/total*100:.1f}%)")
        
        # Difficulty distribution
        difficulties = {}
        for q in self.queries:
            diff = q['difficulty']
            difficulties[diff] = difficulties.get(diff, 0) + 1
        
        print("\nDifficulty Distribution:")
        for diff in DIFFICULTIES:
            count = difficulties.get(diff, 0)
            print(f"  {diff}: {count} ({count/total*100:.1f}%)")
        
        # Category distribution
        categories = {}
        for q in self.queries:
            cat = q['category']
            categories[cat] = categories.get(cat, 0) + 1
        
        print("\nCategory Distribution:")
        for cat in CATEGORIES:
            count = categories.get(cat, 0)
            print(f"  {cat}: {count} ({count/total*100:.1f}%)")
        
        # Subdomain distribution
        subdomains = {}
        for q in self.queries:
            for sub in q['subdomains']:
                subdomains[sub] = subdomains.get(sub, 0) + 1
        
        print("\nSubdomain Coverage:")
        for sub in SUBDOMAINS:
            count = subdomains.get(sub, 0)
            print(f"  {sub}: {count} ({count/total*100:.1f}%)")
        
        # Answer statistics if available
        answers_present = sum(1 for q in self.queries if 'answer' in q)
        if answers_present:
            print(f"\nQueries with Answers: {answers_present} ({answers_present/total*100:.1f}%)")
        
        print("=" * 60)

def main():
    """Main function to generate the benchmark"""
    generator = BenchmarkGenerator()
    
    # Generate benchmark with specified distribution
    # 200 total queries (100 deep thinking, 100 standard)
    # Difficulty: 30% Easy, 40% Medium, 30% Hard
    # Category: 40% General, 60% Cross-Subdomain
    generator.generate_benchmark(
        total_queries=Config.TOTAL_QUERIES,
        deep_thinking_count=Config.DEEP_THINKING_GENERATED,
        standard_count=Config.STANDARD_GENERATED,
        easy_pct=Config.DIFFICULTY_DISTRIBUTION['Easy'],
        medium_pct=Config.DIFFICULTY_DISTRIBUTION['Medium'],
        hard_pct=Config.DIFFICULTY_DISTRIBUTION['Hard'],
        general_pct=Config.CATEGORY_DISTRIBUTION['General'],
        cross_pct=Config.CATEGORY_DISTRIBUTION['Cross_Subdomain'],
        batch_size=20,  # Process in batches of 20 queries
        generate_answers=Config.GENERATE_ANSWERS
    )

if __name__ == "__main__":
    main() 
#!/usr/bin/env python
# supplement_benchmark.py - Supplement incomplete benchmark by adding missing queries

import os
import json
import pandas as pd
import glob
import time
from datetime import datetime
from config import Config
from deep_thinking_api import call_deep_thinking
from standard_api import call_standard
from answer_generator import generate_answers_for_queries
from benchmark_generator import BenchmarkGenerator, SUBDOMAINS, DIFFICULTIES, CATEGORIES
import shutil

def find_latest_benchmark():
    """Find the latest complete benchmark file"""
    json_files = glob.glob(f"{Config.OUTPUT_DIR}/energy_benchmark_*_complete.json")
    if not json_files:
        print("No complete benchmark files found.")
        return None
    
    latest_file = max(json_files, key=os.path.getctime)
    print(f"Found latest benchmark file: {latest_file}")
    return latest_file

def analyze_benchmark(benchmark_file):
    """Analyze the benchmark to identify missing queries and failed answers"""
    with open(benchmark_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Count queries by source
    queries = data['queries']
    dt_queries = [q for q in queries if q['source'] == 'Deep_Thinking']
    st_queries = [q for q in queries if q['source'] == 'Standard']
    
    # Find failed answers
    failed_answers = [q for q in queries if 'answer' in q and q['answer']['text'] == 'Failed to generate answer']
    
    # Count by ID to find missing IDs
    dt_ids = set([q['id'] for q in dt_queries])
    st_ids = set([q['id'] for q in st_queries])
    
    dt_missing = set([f"DT{i:03d}" for i in range(1, 101)]) - dt_ids
    st_missing = set([f"ST{i:03d}" for i in range(1, 101)]) - st_ids
    
    print(f"\nAnalysis of benchmark {os.path.basename(benchmark_file)}:")
    print(f"  Total queries: {len(queries)}")
    print(f"  Deep_Thinking queries: {len(dt_queries)}/100")
    print(f"  Standard queries: {len(st_queries)}/100")
    print(f"  Queries with failed answers: {len(failed_answers)}")
    print(f"  Missing Deep_Thinking IDs: {sorted(dt_missing)}")
    print(f"  Missing Standard IDs: {sorted(st_missing)}")
    
    return {
        'original_file': benchmark_file,
        'queries': queries,
        'dt_queries': dt_queries,
        'st_queries': st_queries,
        'failed_answers': failed_answers,
        'dt_missing': dt_missing,
        'st_missing': st_missing
    }

def extract_requirements(query):
    """Extract requirements from an existing query to match its properties"""
    return {
        "difficulty": query['difficulty'],
        "category": query['category'],
        "primary_domain": query['subdomains'][0],
        "secondary_domains": query['subdomains'][1:] if len(query['subdomains']) > 1 else None,
        "count": 1
    }

def create_requirements_for_missing(missing_ids, existing_queries, source_type):
    """Create balanced requirements for missing queries based on existing distribution"""
    requirements = []
    
    # Convert missing_ids to a list for easier assignment
    missing_ids_list = list(missing_ids)
    
    # Calculate how many queries of each type are needed
    needed_count = len(missing_ids)
    
    if needed_count == 0:
        return []
    
    print(f"\nCreating {needed_count} new requirements for {source_type} queries...")
    
    # Count existing distribution of difficulty and category
    difficulty_counts = {}
    category_counts = {}
    subdomain_counts = {}
    
    for q in existing_queries:
        diff = q['difficulty']
        cat = q['category']
        
        difficulty_counts[diff] = difficulty_counts.get(diff, 0) + 1
        category_counts[cat] = category_counts.get(cat, 0) + 1
        
        for sub in q['subdomains']:
            subdomain_counts[sub] = subdomain_counts.get(sub, 0) + 1
    
    # Calculate target counts for each difficulty and category
    target_difficulty = {}
    for diff in DIFFICULTIES:
        current = difficulty_counts.get(diff, 0)
        target_difficulty[diff] = min(round((current / len(existing_queries)) * 100), needed_count)
    
    # Ensure we hit the needed total
    total_assigned = sum(target_difficulty.values())
    if total_assigned < needed_count:
        # Distribute the remainder proportionally
        for diff in sorted(target_difficulty.keys(), key=lambda d: target_difficulty[d]):
            target_difficulty[diff] += 1
            total_assigned += 1
            if total_assigned >= needed_count:
                break
    
    # Same for categories
    target_category = {}
    for cat in CATEGORIES:
        current = category_counts.get(cat, 0)
        target_category[cat] = min(round((current / len(existing_queries)) * 100), needed_count)
    
    total_assigned = sum(target_category.values())
    if total_assigned < needed_count:
        for cat in sorted(target_category.keys(), key=lambda c: target_category[c]):
            target_category[cat] += 1
            total_assigned += 1
            if total_assigned >= needed_count:
                break
    
    # Create a distribution grid similar to benchmark_generator
    distribution = []
    for diff in DIFFICULTIES:
        for cat in CATEGORIES:
            diff_pct = target_difficulty[diff] / needed_count
            cat_pct = target_category[cat] / needed_count
            count = round(needed_count * diff_pct * cat_pct)
            if count > 0:
                distribution.append((diff, cat, count))
    
    # Adjust to ensure we get exactly the needed count
    total = sum(count for _, _, count in distribution)
    if total != needed_count:
        # Add or subtract from the largest category
        largest_idx = max(range(len(distribution)), key=lambda i: distribution[i][2])
        diff, cat, count = distribution[largest_idx]
        distribution[largest_idx] = (diff, cat, count + (needed_count - total))
    
    # Create requirements based on distribution
    primary_domains = [d for d in SUBDOMAINS if d not in ["Policy", "Economics", "Environmental"]]
    secondary_domains = [d for d in SUBDOMAINS if d not in primary_domains]
    
    # Sort subdomains by frequency in existing queries to prioritize underrepresented domains
    sorted_primaries = sorted(primary_domains, key=lambda d: subdomain_counts.get(d, 0))
    
    for difficulty, category, count in distribution:
        for i in range(count):
            # Cycle through subdomains to ensure balanced representation
            primary = sorted_primaries[i % len(sorted_primaries)]
            
            if category == "Cross_Subdomain":
                remaining = [s for s in SUBDOMAINS if s != primary]
                # Easy: 1 secondary, Medium: 2 secondary, Hard: 3 secondary
                sec_count = 1
                if difficulty == "Medium":
                    sec_count = 2
                elif difficulty == "Hard":
                    sec_count = 3
                
                secondary = sorted(remaining, key=lambda d: subdomain_counts.get(d, 0))[:sec_count]
                requirements.append({
                    "difficulty": difficulty,
                    "category": category,
                    "primary_domain": primary,
                    "secondary_domains": secondary,
                    "count": 1,
                    "target_id": None  # Will be filled later
                })
            else:
                requirements.append({
                    "difficulty": difficulty,
                    "category": category,
                    "primary_domain": primary,
                    "count": 1,
                    "target_id": None  # Will be filled later
                })
    
    # Assign target IDs - ensure each requirement gets a valid ID
    missing_ids_list = sorted(list(missing_ids))
    
    # 清除任何已存在的target_id
    for req in requirements:
        if "target_id" in req:
            del req["target_id"]
    
    # 重新分配ID，确保不超出范围
    for i, req in enumerate(requirements):
        if i < len(missing_ids_list):
            req["target_id"] = missing_ids_list[i]
            print(f"  Assigned target ID {missing_ids_list[i]} to requirement {i+1}")
    
    print(f"Created {len(requirements)} balanced requirements for {source_type} queries")
    return requirements

def supplement_benchmark(analysis, batch_size=5):
    """Generate missing queries and fix failed answers"""
    benchmark_gen = BenchmarkGenerator()
    original_queries = analysis['queries']
    
    # Timestamp for this supplementary run
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create requirements for missing Deep_Thinking queries
    dt_requirements = create_requirements_for_missing(
        analysis['dt_missing'], 
        analysis['dt_queries'],
        "Deep_Thinking"
    )
    
    # 只保留我们需要的数量的requirements(与missing数量一致)
    if dt_requirements and len(dt_requirements) > len(analysis['dt_missing']):
        dt_requirements = dt_requirements[:len(analysis['dt_missing'])]
        print(f"Reduced DT requirements to {len(dt_requirements)} to match missing count")
    
    # Create requirements for missing Standard queries
    st_requirements = create_requirements_for_missing(
        analysis['st_missing'], 
        analysis['st_queries'],
        "Standard"
    )
    
    # 只保留我们需要的数量的requirements(与missing数量一致)
    if st_requirements and len(st_requirements) > len(analysis['st_missing']):
        st_requirements = st_requirements[:len(analysis['st_missing'])]
        print(f"Reduced ST requirements to {len(st_requirements)} to match missing count")
    
    # Requirements for regenerating failed answers
    failed_requirements = []
    for query in analysis['failed_answers']:
        req = extract_requirements(query)
        req["original_query"] = query
        failed_requirements.append(req)
    
    # Process in batches
    all_new_queries = []
    
    # Process Deep_Thinking queries in batches
    dt_batches = [dt_requirements[i:i+batch_size] for i in range(0, len(dt_requirements), batch_size)]
    for batch_idx, batch_reqs in enumerate(dt_batches, 1):
        print(f"\nGenerating batch {batch_idx}: {len(batch_reqs)} supplementary Deep_Thinking queries...")
        
        batch_queries = []
        for i, req in enumerate(batch_reqs, 1):
            print(f"  [{i}/{len(batch_reqs)}] Deep_Thinking: {req['difficulty']} {req['category']} - {req['primary_domain']}")
            
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
                
                # 确保查询有ID
                if req.get("target_id"):
                    # 使用指定的目标ID（来自missing_ids）
                    query["id"] = req.get("target_id")
                    print(f"  Using target ID: {query['id']}")
                else:
                    # 这种情况不应该发生，因为我们已经为每个requirement分配了target_id
                    # 但作为后备，我们会分配一个特殊ID
                    query["id"] = f"DT_EXTRA_{len(all_new_queries)+1}"
                    print(f"  Warning: No target_id for requirement. Assigned special ID: {query['id']}")
                
                batch_queries.append(query)
                print(f"    ✓ Generated: {query_text[:100]}...")
            else:
                print(f"    ✗ Failed: {result.get('error', 'Unknown error')}")
        
        # Generate answers if enabled
        if Config.GENERATE_ANSWERS and batch_queries:
            batch_queries = generate_answers_for_queries(batch_queries)
        
        all_new_queries.extend(batch_queries)
        print(f"Completed batch {batch_idx}. Generated {len(batch_queries)} new Deep_Thinking queries.")
        
        # 加载原始数据以便增量更新
        with open(analysis['original_file'], 'r', encoding='utf-8') as f:
            original_data = json.load(f)
        
        # 创建备份一次
        backup_file = f"{analysis['original_file']}.bak"
        if not os.path.exists(backup_file):
            shutil.copy(analysis['original_file'], backup_file)
            print(f"Created backup of original file at: {backup_file}")
        
        # 初始化最终查询列表为原始查询
        original_queries = analysis['queries']
        final_queries = original_queries.copy()
        existing_ids = set(q['id'] for q in final_queries if 'id' in q)
        
        # 生成每个查询后立即添加到final_queries
        for new_query in batch_queries:
            # 确保查询有ID
            if 'id' not in new_query or new_query['id'] is None:
                print(f"Warning: Query missing ID, assigning new ID...")
                # 生成唯一ID
                new_id = f"DT{len([q for q in final_queries if 'id' in q and q['id'].startswith('DT')])+1:03d}"
                new_query['id'] = new_id
            
            # 如果ID不存在，添加到final_queries
            if new_query['id'] not in existing_ids:
                existing_ids.add(new_query['id'])
                final_queries.append(new_query)
                
                # 实时保存增量更新
                original_data['queries'] = final_queries
                original_data['metadata']['total_queries'] = len(final_queries)
                with open(analysis['original_file'] + '.temp', 'w', encoding='utf-8') as f:
                    json.dump(original_data, f, indent=2, ensure_ascii=False)
                
                # 安全替换原始文件
                if os.path.exists(analysis['original_file'] + '.temp'):
                    os.replace(analysis['original_file'] + '.temp', analysis['original_file'])
                    
                print(f"  ✓ Added and saved query {new_query['id']}")
    
    # Process Standard queries in batches
    st_batches = [st_requirements[i:i+batch_size] for i in range(0, len(st_requirements), batch_size)]
    for batch_idx, batch_reqs in enumerate(st_batches, 1):
        print(f"\nGenerating batch {batch_idx}: {len(batch_reqs)} supplementary Standard queries...")
        
        batch_queries = []
        for i, req in enumerate(batch_reqs, 1):
            print(f"  [{i}/{len(batch_reqs)}] Standard: {req['difficulty']} {req['category']} - {req['primary_domain']}")
            
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
                
                # 确保查询有ID
                if req.get("target_id"):
                    # 使用指定的目标ID（来自missing_ids）
                    query["id"] = req.get("target_id")
                    print(f"  Using target ID: {query['id']}")
                else:
                    # 这种情况不应该发生，因为我们已经为每个requirement分配了target_id
                    # 但作为后备，我们会分配一个特殊ID
                    query["id"] = f"ST_EXTRA_{len(all_new_queries)+1}"
                    print(f"  Warning: No target_id for requirement. Assigned special ID: {query['id']}")
                
                batch_queries.append(query)
                print(f"    ✓ Generated: {query_text[:100]}...")
            else:
                print(f"    ✗ Failed: {result.get('error', 'Unknown error')}")
        
        # Generate answers if enabled
        if Config.GENERATE_ANSWERS and batch_queries:
            batch_queries = generate_answers_for_queries(batch_queries)
        
        all_new_queries.extend(batch_queries)
        print(f"Completed batch {batch_idx}. Generated {len(batch_queries)} new Standard queries.")
        
        # 加载原始数据以便增量更新
        with open(analysis['original_file'], 'r', encoding='utf-8') as f:
            original_data = json.load(f)
        
        # 创建备份一次
        backup_file = f"{analysis['original_file']}.bak"
        if not os.path.exists(backup_file):
            shutil.copy(analysis['original_file'], backup_file)
            print(f"Created backup of original file at: {backup_file}")
        
        # 初始化最终查询列表为原始查询
        original_queries = analysis['queries']
        final_queries = original_queries.copy()
        existing_ids = set(q['id'] for q in final_queries if 'id' in q)
        
        # 生成每个查询后立即添加到final_queries
        for new_query in batch_queries:
            # 确保查询有ID
            if 'id' not in new_query or new_query['id'] is None:
                print(f"Warning: Query missing ID, assigning new ID...")
                # 生成唯一ID
                new_id = f"ST{len([q for q in final_queries if 'id' in q and q['id'].startswith('ST')])+1:03d}"
                new_query['id'] = new_id
            
            # 如果ID不存在，添加到final_queries
            if new_query['id'] not in existing_ids:
                existing_ids.add(new_query['id'])
                final_queries.append(new_query)
                
                # 实时保存增量更新
                original_data['queries'] = final_queries
                original_data['metadata']['total_queries'] = len(final_queries)
                with open(analysis['original_file'] + '.temp', 'w', encoding='utf-8') as f:
                    json.dump(original_data, f, indent=2, ensure_ascii=False)
                
                # 安全替换原始文件
                if os.path.exists(analysis['original_file'] + '.temp'):
                    os.replace(analysis['original_file'] + '.temp', analysis['original_file'])
                    
                print(f"  ✓ Added and saved query {new_query['id']}")
    
    # Process failed answers in batches
    failed_batches = [failed_requirements[i:i+batch_size] for i in range(0, len(failed_requirements), batch_size)]
    for batch_idx, batch_reqs in enumerate(failed_batches, 1):
        print(f"\nRegenerating batch {batch_idx}: {len(batch_reqs)} failed answers...")
        
        queries_to_regenerate = []
        for i, req in enumerate(batch_reqs, 1):
            original_query = req["original_query"]
            print(f"  [{i}/{len(batch_reqs)}] Regenerating answer for: {original_query['id']}")
            queries_to_regenerate.append(original_query)
        
        # Generate new answers
        if queries_to_regenerate and Config.GENERATE_ANSWERS:
            regenerated_queries = generate_answers_for_queries(queries_to_regenerate)
            
            # Replace the original queries with regenerated ones
            for original_idx, query in enumerate(original_queries):
                for regen_query in regenerated_queries:
                    if query['id'] == regen_query['id']:
                        original_queries[original_idx] = regen_query
                        break
    
    # Merge new queries with original ones (excluding regenerated ones)
    final_queries = []
    existing_ids = set()
    
    # First add all original queries
    for query in original_queries:
        existing_ids.add(query['id'])
        final_queries.append(query)
    
    # Then add supplementary queries that don't already exist
    for query in all_new_queries:
        if query['id'] not in existing_ids:
            existing_ids.add(query['id'])
            final_queries.append(query)
    
    # Sort by ID
    final_queries.sort(key=lambda q: q['id'])
    
    # Append to the original complete json file
    output_json = analysis['original_file']
    
    # Create a backup of the original file
    backup_file = f"{output_json}.bak"
    os.rename(output_json, backup_file)
    print(f"Created backup of original file at: {backup_file}")
    
    # Use the original filename for Excel
    output_excel = output_json.replace('.json', '.xlsx')
    
    # Create a backup of the original Excel file if it exists
    if os.path.exists(output_excel):
        excel_backup = f"{output_excel}.bak"
        shutil.copy(output_excel, excel_backup)
        print(f"Created backup of original Excel file at: {excel_backup}")
    
    # Load original data from backup
    with open(backup_file, 'r', encoding='utf-8') as f:
        original_data = json.load(f)
    
    # Update metadata
    original_data['metadata']['generation_timestamp'] = datetime.now().isoformat()
    original_data['metadata']['total_queries'] = len(final_queries)
    if 'updates' not in original_data['metadata']:
        original_data['metadata']['updates'] = []
    
    # Add update record
    original_data['metadata']['updates'].append({
        "timestamp": datetime.now().isoformat(),
        "added_queries": len(all_new_queries),
        "fixed_answers": len(failed_requirements)
    })
    
    # Replace queries with the combined set
    original_data['queries'] = final_queries
    
    # Write updated data back to original file
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(original_data, f, indent=2, ensure_ascii=False)
    
    print(f"\nUpdated benchmark saved to original JSON: {output_json}")
    
    # Save to Excel with error handling
    benchmark_gen.queries = final_queries
    try:
        # 尝试保存Excel文件
        excel_path = benchmark_gen.save_to_excel(output_excel)
        print(f"Successfully saved Excel file to: {excel_path}")
    except Exception as e:
        # 如果保存失败，记录错误并尝试使用新文件名
        print(f"Error saving to Excel: {str(e)}")
        fallback_excel = f"{Config.OUTPUT_DIR}/energy_benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}_updated.xlsx"
        try:
            excel_path = benchmark_gen.save_to_excel(fallback_excel)
            print(f"Saved Excel to alternative location: {fallback_excel}")
        except Exception as e2:
            print(f"Failed to save Excel file: {str(e2)}")
            excel_path = None
    
    # Generate final statistics
    dt_count = len([q for q in final_queries if q['source'] == 'Deep_Thinking'])
    st_count = len([q for q in final_queries if q['source'] == 'Standard'])
    failed_count = len([q for q in final_queries if 'answer' in q and q['answer']['text'] == 'Failed to generate answer'])
    
    print(f"\nUpdate complete!")
    print(f"Final benchmark statistics:")
    print(f"  Total queries: {len(final_queries)}")
    print(f"  Deep_Thinking queries: {dt_count}/100")
    print(f"  Standard queries: {st_count}/100")
    print(f"  Queries with failed answers: {failed_count}")
    print(f"  Updated JSON file: {output_json}")
    print(f"  Updated Excel file: {excel_path}")
    print(f"  Backup of original JSON file: {backup_file}")
    if os.path.exists(f"{output_excel}.bak"):
        print(f"  Backup of original Excel file: {output_excel}.bak")

def main():
    """Main function to update an existing benchmark"""
    print("=" * 60)
    print("BENCHMARK UPDATE TOOL")
    print("=" * 60)
    
    # Find the latest benchmark file
    latest_benchmark = find_latest_benchmark()
    if not latest_benchmark:
        print("No benchmark files found to supplement.")
        return
    
    # Analyze the benchmark
    analysis = analyze_benchmark(latest_benchmark)
    
    # Only proceed if there are missing queries or failed answers
    dt_missing = len(analysis['dt_missing'])
    st_missing = len(analysis['st_missing'])
    failed_answers = len(analysis['failed_answers'])
    
    if dt_missing == 0 and st_missing == 0 and failed_answers == 0:
        print("\nThe benchmark is already complete with no failed answers. No update needed.")
        return
    
    print(f"\nUpdate needed:")
    print(f"  - {dt_missing} missing Deep_Thinking queries")
    print(f"  - {st_missing} missing Standard queries")
    print(f"  - {failed_answers} failed answers to regenerate")
    
    # Generate missing queries and fix failed answers
    supplement_benchmark(analysis, batch_size=5)

if __name__ == "__main__":
    main() 
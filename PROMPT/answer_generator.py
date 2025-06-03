#!/usr/bin/env python
# answer_generator.py - Generate answers for energy domain benchmark queries

import json
import requests
import time
from config import Config

def generate_answer(query_object):
    """
    Generate a comprehensive answer for a given query object
    
    Parameters:
    - query_object: The complete query object containing query_text and other metadata
    
    Returns:
    - Dictionary with success flag and answer content or error message
    """
    query_text = query_object['query_text']
    difficulty = query_object['difficulty']
    subdomains = query_object['subdomains']
    category = query_object['category']
    
    # Format metadata for context
    metadata_context = f"This is a {difficulty} difficulty question in the energy domain, "
    if category == "General":
        metadata_context += f"focusing on {', '.join(subdomains)}."
    else:
        metadata_context += f"exploring connections between {', '.join(subdomains)}."
    
    # Build full prompt for the answer - enhanced for deep research capabilities
    prompt = f"""Please provide a comprehensive, research-grade analysis of the following energy domain question:

Question: {query_text}

{metadata_context}

Your answer should demonstrate deep research capabilities and expert knowledge. Structure your response as follows:

1. INTRODUCTION & CONTEXT
   - Frame the question within current energy research
   - Identify key concepts, terminology, and relevance
   - Establish the scope and boundaries of your analysis

2. METHODOLOGY & ANALYTICAL FRAMEWORK
   - Outline the theoretical frameworks relevant to addressing this question
   - Describe appropriate methodological approaches (e.g., systems analysis, lifecycle assessment, techno-economic modeling)
   - Identify key parameters, variables, and considerations that should be included in a rigorous analysis

3. STATE OF RESEARCH
   - Synthesize current research findings and debates
   - Evaluate competing perspectives and methodologies
   - Identify research gaps and limitations in current understanding
   - Reference specific research traditions, methodologies, or paradigms

4. MULTI-DIMENSIONAL ANALYSIS
   - Technical dimensions (technological feasibility, scalability, integration challenges)
   - Economic dimensions (cost structures, market dynamics, financial mechanisms)
   - Policy/regulatory dimensions (governance frameworks, international agreements)
   - Environmental dimensions (emissions profiles, resource implications, ecosystem impacts)
   - Social dimensions (equity considerations, public acceptance, stakeholder interests)

5. SYNTHESIS & INTERCONNECTIONS
   - Analyze how different factors interact with and influence each other
   - Identify potential trade-offs, synergies, and systemic effects
   - Consider temporal dimensions (short vs. long-term implications)
   - Examine cross-scale interactions (local to global considerations)

6. RESEARCH FRONTIERS
   - Identify emerging research directions and methodological innovations
   - Discuss what further research would be necessary to advance understanding
   - Highlight promising approaches for addressing limitations in current knowledge

Ensure your response demonstrates:
- Critical evaluation of evidence and claims
- Multi-step reasoning that connects concepts across domains
- Awareness of methodological considerations and limitations
- Integration of quantitative and qualitative perspectives
- Recognition of complexity and systemic interconnections
- Balanced consideration of different viewpoints and interpretations

Your answer should reflect the depth and rigor expected in scholarly energy research, while remaining accessible and clear in its structure and explanations."""

    # Make API call
    response = _make_api_call(prompt, Config.ANSWER_SYSTEM_PROMPT)
    
    if response['success']:
        # Add answer information to the result
        response['answer'] = response['content']
        response['prompt'] = prompt
        response['system_prompt'] = Config.ANSWER_SYSTEM_PROMPT
    
    return response

def generate_answers_for_queries(queries, delay_between_calls=Config.DELAY_BETWEEN_CALLS):
    """
    Generate answers for a list of query objects
    
    Parameters:
    - queries: List of query objects
    - delay_between_calls: Delay between API calls to avoid rate limiting
    
    Returns:
    - Modified list of query objects with answers added
    """
    print(f"\nGenerating answers for {len(queries)} queries...")
    
    queries_with_answers = []
    
    for i, query in enumerate(queries, 1):
        # 确保查询有ID
        if 'id' not in query or query['id'] is None:
            print(f"Warning: Query at index {i} missing ID, assigning temporary ID...")
            query['id'] = f"#{i}"
        
        query_id = query['id']
        print(f"  [{i}/{len(queries)}] Generating answer for query {query_id}: {query['query_text'][:50]}...")
        
        # Add delay to prevent rate limiting (except for first query)
        if i > 1:
            time.sleep(delay_between_calls)
        
        # Generate answer
        result = generate_answer(query)
        
        # 在返回的查询对象中确保ID被保留
        query_copy = query.copy()
        if result['success']:
            # 确保查询ID被保留
            query_copy['answer'] = {
                'text': result['answer'],
                'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S'),
                'generation_details': {
                    'prompt': result['prompt'],
                    'system_prompt': result['system_prompt']
                }
            }
            queries_with_answers.append(query_copy)
            print(f"    ✓ Answer generated: {result['answer'][:100]}...")
        else:
            query_copy['answer'] = {
                'text': "Failed to generate answer",
                'error': result.get('error', 'Unknown error'),
                'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S')
            }
            queries_with_answers.append(query_copy)
            print(f"    ✗ Failed: {result.get('error', 'Unknown error')}")
    
    print(f"Answer generation complete for {len(queries_with_answers)} queries.")
    return queries_with_answers

def _make_api_call(prompt, system_prompt=None):
    """Make a single API call to Claude"""
    
    # API URL
    url = "https://api.anthropic.com/v1/messages"
    
    # Headers
    headers = {
        "x-api-key": Config.CLAUDE_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    
    # Build request body
    payload = {
        "model": Config.MODEL_NAME,
        "max_tokens": Config.ANSWER_MAX_TOKENS,
        "temperature": Config.ANSWER_TEMPERATURE,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    
    # Add system prompt if provided
    if system_prompt:
        payload["system"] = system_prompt
    
    # Make request
    try:
        response = requests.post(url, headers=headers, json=payload)
        
        # Process response
        if response.status_code == 200:
            response_json = response.json()
            if 'content' in response_json and len(response_json['content']) > 0:
                return {
                    "success": True,
                    "content": response_json['content'][0]['text'],
                    "full_response": response_json
                }
            else:
                return {
                    "success": False,
                    "error": "No content in response",
                    "full_response": response_json
                }
        else:
            return {
                "success": False,
                "error": response.text,
                "status_code": response.status_code
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def test_answer_generation():
    """Test the answer generation functionality"""
    test_query = {
        "id": "TEST001",
        "query_text": "Analyze the challenges and opportunities in integrating electric vehicle battery technology with renewable energy sources.",
        "difficulty": "Medium",
        "category": "Cross_Subdomain",
        "subdomains": ["Renewable", "Grid_Storage", "Environmental"]
    }
    
    print(f"Testing answer generation for query: {test_query['query_text']}")
    
    result = generate_answer(test_query)
    
    if result['success']:
        print("\n=== Generated Answer ===")
        print(result['answer'][:500] + "...\n")
        
        if 'prompt' in result:
            print("=== Prompt Used ===")
            print(result['prompt'])
    else:
        print(f"Error: {result.get('error')}")
        if 'status_code' in result:
            print(f"Status code: {result['status_code']}")

if __name__ == "__main__":
    test_answer_generation() 
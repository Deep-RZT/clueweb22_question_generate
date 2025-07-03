#!/usr/bin/env python
# deep_thinking_api.py - Deep thinking implementation for Claude API calls

import json
import requests
from config import Config

def call_deep_thinking(requirements, system_prompt=None):
    """
    Call Claude API using a multi-step deep thinking approach
    
    This implementation uses a three-step process:
    1. Initial domain understanding and analysis
    2. Generate initial questions based on thinking
    3. Refine and improve questions
    """
    
    # Format requirements into a string
    req_str = f"Difficulty Level: {requirements['difficulty']}\n"
    req_str += f"Category: {requirements['category']}\n"
    req_str += f"Primary Subdomain: {requirements['primary_domain']}\n"
    
    if requirements.get('secondary_domains'):
        req_str += f"Secondary Subdomains: {', '.join(requirements['secondary_domains'])}\n"
    
    # STEP 1: Domain understanding and analysis
    understanding_prompt = f"""You are an expert in energy research. I need to generate high-quality research questions based on the following requirements:

{req_str}

Before generating questions, please think deeply about:
1. What are the cutting-edge research frontiers in these domains?
2. What key challenges and opportunities exist in these fields?
3. What important connections exist between these domains?
4. What types of questions would demonstrate depth and breadth in these areas?

Please provide your thinking process but do not generate specific questions yet."""

    # Make the first API call
    understanding_system_prompt = "You are an expert energy researcher with deep domain knowledge. Provide thoughtful analysis of energy research domains."
    understanding_response = _make_api_call(understanding_prompt, understanding_system_prompt)
    
    if not understanding_response['success']:
        return understanding_response
        
    thinking_result = understanding_response['content']
    
    # STEP 2: Generate initial questions based on thinking
    generation_prompt = f"""Based on your previous thinking:

{thinking_result}

Now, please generate {requirements.get('count', 1)} high-quality research question(s) that meet the following criteria:

{req_str}

Remember:
- Questions should be clear, specific, and deep
- Questions should have research value, not simple fact queries
- Questions should demonstrate understanding of the relevant domains

List only the questions themselves, no explanations."""

    # Make the second API call
    generation_system_prompt = "You are an expert energy researcher. Generate high-quality research questions based on your domain knowledge."
    generation_response = _make_api_call(generation_prompt, generation_system_prompt)
    
    if not generation_response['success']:
        return generation_response
        
    initial_questions = generation_response['content']
    
    # STEP 3: Refine and improve questions
    refinement_prompt = f"""Please review and refine the following research questions:

{initial_questions}

The goal is to make these questions:
1. More precise and clear
2. With better research depth and breadth
3. Better at testing the respondent's analytical and synthesis abilities
4. Maintaining appropriate difficulty level ({requirements['difficulty']})

Provide the improved final version of the questions. List only the improved questions, no explanation of improvements."""

    # Make the third API call
    refinement_system_prompt = "You are an expert research question designer focused on quality and precision."
    refinement_response = _make_api_call(refinement_prompt, refinement_system_prompt)
    
    if not refinement_response['success']:
        return refinement_response
        
    final_questions = refinement_response['content']
    
    # Save all prompts used
    prompts = {
        "understanding_prompt": understanding_prompt,
        "understanding_system_prompt": understanding_system_prompt,
        "generation_prompt": generation_prompt,
        "generation_system_prompt": generation_system_prompt,
        "refinement_prompt": refinement_prompt,
        "refinement_system_prompt": refinement_system_prompt
    }
    
    # Return successful result with all intermediate steps
    return {
        'success': True,
        'content': final_questions,
        'thinking_process': thinking_result,
        'initial_questions': initial_questions,
        'final_questions': final_questions,
        'prompts': prompts
    }

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
        "max_tokens": Config.MAX_TOKENS,
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

def test_deep_thinking():
    """Test the deep thinking API"""
    requirements = {
        "difficulty": "Medium",
        "category": "Cross_Subdomain",
        "primary_domain": "Renewable",
        "secondary_domains": ["Economics", "Policy"],
        "count": 1
    }
    
    print(f"Testing deep thinking API with requirements: {json.dumps(requirements, indent=2)}")
    
    result = call_deep_thinking(requirements)
    
    if result['success']:
        print("\n=== Thinking Process ===")
        print(result['thinking_process'][:500] + "...\n")
        
        print("=== Initial Questions ===")
        print(result['initial_questions'] + "\n")
        
        print("=== Final Refined Question ===")
        print(result['final_questions'])
        
        if 'prompts' in result:
            print("\n=== Prompts Used ===")
            for name, prompt in result['prompts'].items():
                if name.endswith('_prompt'):
                    print(f"\n--- {name} ---")
                    print(prompt[:100] + "...")
    else:
        print(f"Error: {result.get('error')}")
        if 'status_code' in result:
            print(f"Status code: {result['status_code']}")

if __name__ == "__main__":
    test_deep_thinking() 
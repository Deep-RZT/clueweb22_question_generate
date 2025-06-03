#!/usr/bin/env python
# standard_api.py - Standard single-pass implementation for Claude API calls

import json
import requests
from config import Config

def call_standard(requirements, system_prompt=None):
    """
    Call Claude API using a standard single-pass approach
    
    This implementation uses a direct one-shot generation approach
    without the multi-step reasoning of the deep thinking method.
    """
    
    # Format requirements into a string
    req_str = f"Difficulty Level: {requirements['difficulty']}\n"
    req_str += f"Category: {requirements['category']}\n"
    req_str += f"Primary Subdomain: {requirements['primary_domain']}\n"
    
    if requirements.get('secondary_domains'):
        req_str += f"Secondary Subdomains: {', '.join(requirements['secondary_domains'])}\n"
    
    # Build a comprehensive prompt
    prompt = f"""Generate {requirements.get('count', 1)} high-quality energy domain research question(s) based on the following requirements:

{req_str}

Guidelines for different difficulty levels:
- Easy: Focus on fundamental concepts, basic comparisons, or straightforward explanations
- Medium: Require multi-factor analysis, trade-off evaluations, or moderate synthesis
- Hard: Demand complex system thinking, comprehensive frameworks, or novel solution design

Guidelines for different categories:
- General: Focus primarily on one subdomain or broad energy topics
- Cross_Subdomain: Meaningfully integrate multiple subdomains, exploring their interdependencies

The question(s) should be:
- Clear and specific
- Require deep domain knowledge
- Focus on research value, not simple facts
- Match the specified difficulty level
- Cover the specified domains thoroughly

List only the question(s) directly, one per line, without explanations or numbering."""

    # Default system prompt if none provided
    if system_prompt is None:
        system_prompt = "You are an expert energy researcher. Generate high-quality research questions based on your domain knowledge."

    # Make the API call
    response = _make_api_call(prompt, system_prompt)
    
    # Add prompt information to the response
    if response['success']:
        response['prompt'] = prompt
        response['system_prompt'] = system_prompt
    
    return response

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

def test_standard():
    """Test the standard API"""
    requirements = {
        "difficulty": "Medium",
        "category": "Cross_Subdomain",
        "primary_domain": "Renewable",
        "secondary_domains": ["Economics", "Policy"],
        "count": 1
    }
    
    print(f"Testing standard API with requirements: {json.dumps(requirements, indent=2)}")
    
    result = call_standard(requirements)
    
    if result['success']:
        print("\n=== Generated Question ===")
        print(result['content'])
        
        if 'prompt' in result:
            print("\n=== Prompt Used ===")
            print(result['prompt'][:200] + "...")
            
            if 'system_prompt' in result:
                print("\n=== System Prompt Used ===")
                print(result['system_prompt'])
    else:
        print(f"Error: {result.get('error')}")
        if 'status_code' in result:
            print(f"Status code: {result['status_code']}")

if __name__ == "__main__":
    test_standard() 
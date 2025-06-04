#!/usr/bin/env python3
"""
OpenAI API Client for Deep Research QA Benchmark
Replaces Claude API with OpenAI GPT-4o for all content generation
"""

import json
import requests
import time
from typing import Dict, List, Any, Optional

class OpenAIClient:
    """OpenAI API client for content generation"""
    
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.api_key = api_key
        self.model = model
        self.api_url = "https://api.openai.com/v1/chat/completions"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
    def generate_content(self, prompt: str, system_prompt: str = None, 
                        max_tokens: int = 6000, temperature: float = 0.7) -> Optional[str]:
        """
        Generate content using OpenAI API with optimized parameters for longer responses
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate (increased for longer responses)
            temperature: Sampling temperature
            
        Returns:
            Generated content or None if failed
        """
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        data = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": 0.9,
            "frequency_penalty": 0.1,
            "presence_penalty": 0.1
        }
        
        try:
            response = requests.post(self.api_url, headers=self.headers, json=data, timeout=120)
            response.raise_for_status()
            
            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                return result['choices'][0]['message']['content'].strip()
            else:
                print(f"❌ No choices in OpenAI response: {result}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ OpenAI API request failed: {e}")
            return None
        except Exception as e:
            print(f"❌ OpenAI API error: {e}")
            return None

    def generate_with_retry(self, prompt: str, system_prompt: str = None,
                           max_tokens: int = 4000, temperature: float = 0.7,
                           max_retries: int = 3, retry_delay: float = 2.0) -> Optional[str]:
        """
        Generate content with retry logic
        
        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation
            max_retries: Maximum number of retries
            retry_delay: Delay between retries in seconds
            
        Returns:
            Generated content or None if all retries failed
        """
        
        for attempt in range(max_retries + 1):
            result = self.generate_content(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            if result is not None:
                return result
            
            if attempt < max_retries:
                print(f"   🔄 Retrying in {retry_delay} seconds... (attempt {attempt + 1}/{max_retries})")
                time.sleep(retry_delay)
        
        print(f"   ❌ All {max_retries + 1} attempts failed")
        return None

# Compatibility functions for easy migration from Claude API
def call_openai_api(prompt: str, api_key: str, system_prompt: str = None,
                   max_tokens: int = 4000, temperature: float = 0.7) -> Optional[str]:
    """
    Compatibility function for easy migration from Claude API calls
    
    Args:
        prompt: User prompt
        api_key: OpenAI API key
        system_prompt: System prompt (optional)
        max_tokens: Maximum tokens to generate
        temperature: Temperature for generation
        
    Returns:
        Generated content or None if failed
    """
    client = OpenAIClient(api_key)
    return client.generate_content(
        prompt=prompt,
        system_prompt=system_prompt,
        max_tokens=max_tokens,
        temperature=temperature
    )

def call_openai_with_messages(api_key: str, messages: List[Dict[str, str]], 
                             model: str = "gpt-4o", max_tokens: int = 6000, 
                             temperature: float = 0.7) -> Optional[str]:
    """
    Call OpenAI API with messages format - optimized for longer responses
    
    Args:
        api_key: OpenAI API key
        messages: List of message dictionaries
        model: Model to use
        max_tokens: Maximum tokens (increased default)
        temperature: Sampling temperature
        
    Returns:
        Generated content or None if failed
    """
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    data = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": 0.9,
        "frequency_penalty": 0.1,
        "presence_penalty": 0.1
    }
    
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions", 
            headers=headers, 
            json=data, 
            timeout=120
        )
        response.raise_for_status()
        
        result = response.json()
        if 'choices' in result and len(result['choices']) > 0:
            return result['choices'][0]['message']['content'].strip()
        else:
            print(f"❌ No choices in OpenAI response: {result}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ OpenAI API request failed: {e}")
        return None
    except Exception as e:
        print(f"❌ OpenAI API error: {e}")
        return None

def get_difficulty_specific_system_prompt(difficulty: str) -> str:
    """
    Get system prompt optimized for specific difficulty levels
    
    Args:
        difficulty: Question difficulty (Easy, Medium, Hard)
        
    Returns:
        Optimized system prompt for the difficulty level
    """
    
    base_prompt = """You are an expert researcher providing comprehensive, evidence-based analysis. Your responses must be:

- Structured with clear sections (Introduction, Analysis, Synthesis, Conclusion)
- Well-cited with references to the domain report
- Academically rigorous and detailed
- Written in a formal, analytical style"""

    if difficulty == "Hard":
        return base_prompt + """

CRITICAL REQUIREMENTS FOR HARD QUESTIONS:
- Minimum 1500-2000 words
- Multi-dimensional analysis with interdisciplinary perspectives
- Deep synthesis of complex relationships and patterns
- Critical evaluation of methodological considerations
- Exploration of systemic implications and future developments
- Comprehensive evidence integration from multiple angles
- Sophisticated argumentation with nuanced conclusions

Focus on depth, complexity, and comprehensive coverage of all aspects."""

    elif difficulty == "Medium":
        return base_prompt + """

REQUIREMENTS FOR MEDIUM QUESTIONS:
- Target 800-1200 words
- Multi-step analytical thinking
- Synthesis of different aspects from the domain report
- Critical evaluation of evidence and limitations
- Clear pattern identification and relationship mapping
- Integration of theoretical and practical perspectives

Provide thorough analysis with moderate complexity."""

    else:  # Easy
        return base_prompt + """

REQUIREMENTS FOR EASY QUESTIONS:
- Target 400-600 words
- Clear, direct analysis
- Evidence-based reasoning
- Logical structure and flow
- Accessible but comprehensive coverage

Provide complete but concise analysis.""" 
"""
ClueWeb22 Question Generation - Core Components

This package contains the shared components used across all experimental approaches:
- LLM clients (OpenAI, Claude)
- Data processing utilities
- Evaluation frameworks
- Output formatters
"""

__version__ = "2.0.0"
__author__ = "ClueWeb22 Research Team"

# Core imports for easy access
from .llm_clients.openai_api_client import OpenAIClient
from .llm_clients.claude_api_client import ClaudeAPIClient
from .llm_clients.llm_manager import DynamicLLMManager

__all__ = [
    'OpenAIClient',
    'ClaudeAPIClient', 
    'DynamicLLMManager'
] 
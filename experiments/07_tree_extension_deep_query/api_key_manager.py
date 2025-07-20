"""
API Key Manager for Tree Extension Deep Query Framework  
Handles secure API key management with automatic loading from environment variables.
"""

import os
import logging
from typing import Optional, Dict
from pathlib import Path

logger = logging.getLogger(__name__)

class APIKeyManager:
    """Manages API keys with automatic loading from multiple sources"""
    
    def __init__(self):
        self.api_keys = {}
        self._load_api_keys()
    
    def _load_api_keys(self):
        """Load API keys from multiple sources in priority order"""
        # 1. Environment variables (highest priority)
        self._load_from_environment()
        
        # 2. .env file in project root
        self._load_from_env_file()
        
        # 3. User config file
        self._load_from_config_file()
        
        logger.info(f"Loaded API keys for: {list(self.api_keys.keys())}")
    
    def _load_from_environment(self):
        """Load from environment variables"""
        env_mappings = {
            'OPENAI_API_KEY': 'openai',
            'CLAUDE_API_KEY': 'claude',
            'ANTHROPIC_API_KEY': 'claude',  # Alternative name
            'GOOGLE_API_KEY': 'google',
            'BING_API_KEY': 'bing'
        }
        
        for env_var, service in env_mappings.items():
            key = os.getenv(env_var)
            if key:
                self.api_keys[service] = key
                logger.info(f"✅ Loaded {service} API key from {env_var}")
    
    def _load_from_env_file(self):
        """Load from .env file"""
        try:
            # Try to import python-dotenv
            from dotenv import load_dotenv
            
            # Look for .env file in current directory and parent directories
            env_paths = [
                Path('.env'),
                Path('../.env'),
                Path('../../.env'),
                Path.home() / '.env'
            ]
            
            for env_path in env_paths:
                if env_path.exists():
                    load_dotenv(env_path)
                    logger.info(f"📁 Loaded .env file from {env_path}")
                    # Re-check environment variables after loading .env
                    self._load_from_environment()
                    break
                    
        except ImportError:
            logger.debug("python-dotenv not available, skipping .env file loading")
    
    def _load_from_config_file(self):
        """Load from user config file"""
        config_paths = [
            Path.home() / '.config' / 'tree_extension' / 'api_keys.json',
            Path.home() / '.tree_extension_keys.json',
            Path('api_keys.json')
        ]
        
        for config_path in config_paths:
            if config_path.exists():
                try:
                    import json
                    with open(config_path, 'r') as f:
                        config_keys = json.load(f)
                    
                    for service, key in config_keys.items():
                        if service not in self.api_keys:  # Don't override env vars
                            self.api_keys[service] = key
                            logger.info(f"📄 Loaded {service} API key from {config_path}")
                            
                except Exception as e:
                    logger.warning(f"Failed to load config from {config_path}: {e}")
    
    def get_openai_key(self) -> Optional[str]:
        """Get OpenAI API key"""
        return self.api_keys.get('openai')
    
    def get_claude_key(self) -> Optional[str]:
        """Get Claude API key"""
        return self.api_keys.get('claude')
    
    def has_openai_key(self) -> bool:
        """Check if OpenAI API key is available"""
        return 'openai' in self.api_keys
    
    def has_claude_key(self) -> bool:
        """Check if Claude API key is available"""
        return 'claude' in self.api_keys
    
    def get_available_services(self) -> list:
        """Get list of services with available API keys"""
        return list(self.api_keys.keys())
    
    def setup_openai_client(self):
        """Setup OpenAI client with available API key"""
        openai_key = self.get_openai_key()
        if not openai_key:
            logger.warning("⚠️ OpenAI API key not found")
            logger.info("💡 To add OpenAI API key, set environment variable:")
            logger.info("   export OPENAI_API_KEY='your-key-here'")
            logger.info("💡 Or create a .env file with:")
            logger.info("   OPENAI_API_KEY=your-key-here")
            return None
        
        try:
            from core.llm_clients.openai_api_client import OpenAIClient
            client = OpenAIClient(api_key=openai_key)
            logger.info("✅ OpenAI client setup successful")
            return client
        except Exception as e:
            logger.error(f"❌ Failed to setup OpenAI client: {e}")
            return None

# Global instance
_api_manager = None

def get_api_manager() -> APIKeyManager:
    """Get global API manager instance"""
    global _api_manager
    if _api_manager is None:
        _api_manager = APIKeyManager()
    return _api_manager

def setup_api_client(service: str = 'openai'):
    """Setup API client for specified service"""
    manager = get_api_manager()
    
    if service == 'openai':
        return manager.setup_openai_client()
    else:
        logger.error(f"Unsupported service: {service}")
        return None

def check_api_keys() -> Dict[str, bool]:
    """Check availability of all API keys"""
    manager = get_api_manager()
    return {
        'openai': manager.has_openai_key(),
        'claude': manager.has_claude_key(),
        'available_services': manager.get_available_services()
    }

# Backward compatibility functions
def prompt_for_openai_key():
    """Legacy function - now uses automatic detection"""
    manager = get_api_manager()
    return manager.get_openai_key()

def setup_openai_client():
    """Legacy function - now uses automatic setup"""
    return setup_api_client('openai') 
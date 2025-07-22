#!/usr/bin/env python3

import os

# API Keys - 使用环境变量
CLAUDE_API_KEY = os.getenv('CLAUDE_API_KEY', '')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')

# Web Search
WEB_SEARCH_ENABLED = True
MAX_SEARCH_RESULTS = 3

# Generation Settings
MAX_SHORT_ANSWERS = 3
MAX_REASONING_TREES = 5
MAX_LAYERS = 3

# Output Settings
OUTPUT_DIR = "output"
SAVE_INTERMEDIATE = True 
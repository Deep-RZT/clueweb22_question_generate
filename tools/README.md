# 🛠️ Tools Directory

## 📋 Overview

This directory contains utility scripts and tools for data collection, analysis, and system management.

## 📁 Directory Structure

```
tools/
├── crawlers/                    # Data collection tools
│   ├── academic_document_crawler.py  # Academic paper crawler
│   └── random_documents_crawler.py   # Random document collector
│
├── analysis/                    # Analysis tools
│   └── clueweb22_comparative_analysis.py  # ClueWeb22 specific analysis
│
├── answer_generation_system.py # Answer generation utilities
└── README.md                   # This file
```

## 🔧 Available Tools

### 📚 Data Crawlers (`crawlers/`)

#### Academic Document Crawler
- **File**: `academic_document_crawler.py`
- **Purpose**: Crawl academic papers from various sources
- **Usage**: Collect research literature for RAG corpus
- **Features**: Multi-source crawling, metadata extraction

#### Random Documents Crawler  
- **File**: `random_documents_crawler.py`
- **Purpose**: Collect diverse document samples
- **Usage**: Generate varied dataset for testing
- **Features**: Domain-balanced sampling, quality filtering

### 📊 Analysis Tools (`analysis/`)

#### ClueWeb22 Comparative Analysis
- **File**: `clueweb22_comparative_analysis.py`
- **Purpose**: Specialized analysis for ClueWeb22 experiments
- **Usage**: Generate detailed performance comparisons
- **Features**: Multi-metric analysis, visualization support

### 💬 Generation Tools

#### Answer Generation System
- **File**: `answer_generation_system.py`
- **Purpose**: Standalone answer generation utilities
- **Usage**: Generate answers independently from full pipeline
- **Features**: Configurable quality levels, batch processing

## 🚀 Usage Examples

### Data Collection
```bash
# Crawl academic papers
cd tools/crawlers
python academic_document_crawler.py --domain=energy --count=100

# Collect random documents
python random_documents_crawler.py --output=../data/random_samples/
```

### Analysis
```bash
# Run comparative analysis
cd tools/analysis
python clueweb22_comparative_analysis.py --input=../../results/comparative/
```

### Answer Generation
```bash
# Generate answers for existing questions
cd tools
python answer_generation_system.py --questions=questions.json --model=claude
```

## 📋 Tool Configuration

Most tools support configuration through:
- Command line arguments
- Environment variables
- Configuration files (`.json` or `.yaml`)

## 🔗 Integration

These tools are designed to work with:
- **Core components**: Use `../core/` modules
- **Data sources**: Read from `../data/` directory
- **Experiments**: Support all experimental approaches
- **Results**: Output to `../results/` directory

## 📝 Adding New Tools

To add a new tool:

1. **Create the script** in appropriate subdirectory
2. **Add documentation** explaining purpose and usage
3. **Update this README** with tool description
4. **Ensure integration** with core components

### Template Structure
```python
#!/usr/bin/env python3
"""
Tool Name - Brief Description

Usage:
    python tool_name.py [options]
"""

import sys
import os

# Add core modules to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'core'))

# Import core components
from llm_clients import OpenAIClient, ClaudeAPIClient

def main():
    # Tool implementation
    pass

if __name__ == "__main__":
    main()
```

## 🐛 Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure core modules are accessible
   - Check Python path configuration

2. **API Limitations**
   - Tools respect rate limits
   - Configure retry mechanisms

3. **Data Access**
   - Verify data directory structure
   - Check file permissions

### Debug Mode

Most tools support verbose/debug modes:
```bash
python tool_name.py --debug --verbose
```

---

*These tools complement the main experimental frameworks and provide additional functionality for data management and analysis.* 
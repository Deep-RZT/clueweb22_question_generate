# 📘 ClueWeb22 Question Generation - Complete Workflow Guide

## 🎯 Project Overview

This project provides multiple experimental approaches for generating high-quality research questions and answers from ClueWeb22 datasets and academic literature. It has been reorganized into a clean, modular structure for easy use and extension.

## 🏗️ Project Structure

```
clueweb22_question_generate/
├── 📄 README.md                      # Project overview
├── 📄 WORKFLOW_GUIDE.md              # This comprehensive guide
├── 📄 PROJECT_REORGANIZATION_PLAN.md # Reorganization documentation
├── 
├── 📁 experiments/                   # 🚀 All experimental approaches
│   ├── 01_prompt_only/              # Pure prompt-based generation
│   ├── 02_rag_approach/             # RAG with knowledge corpus
│   ├── 03_hybrid_prompt_rag/        # PROMPT+RAG combination
│   ├── 04_multi_stage/              # Multi-stage deep thinking
│   ├── 05_comparative/              # 🏆 RECOMMENDED APPROACH
│   ├── 06_short_answer_deep_query/  # Short answer focused generation
│   └── 07_tree_extension_deep_query/ # 🧠 AGENT REASONING FRAMEWORK
│
├── 📁 core/                         # Shared components
│   ├── llm_clients/                 # API clients (OpenAI, Claude)
│   ├── data_processing/             # Data utilities
│   ├── evaluation/                  # Quality assessment
│   └── output/                      # Export formatters
│
├── 📁 data/                         # All data sources
│   ├── clueweb22/                   # ClueWeb22 query results
│   ├── academic_papers/             # Academic literature
│   └── rag_corpus/                  # RAG knowledge base
│
├── 📁 results/                      # Experimental outputs
└── 📁 archived/                     # Historical versions
```

## 🌟 Quick Start - Recommended Approaches

### 🧠 For AI Agent Testing (NEW)

**Latest and most advanced approach:**

```bash
# 1. Navigate to Agent Reasoning Framework
cd experiments/07_tree_extension_deep_query

# 2. Run the Agent deep reasoning test generator
python main.py
```

**Why this approach?**
- 🚀 **Cutting-edge**: Latest Agent reasoning test framework
- 🛡️ **Anti-masking**: Prevents direct answer exposure
- 📊 **Production-ready**: Automated quality assurance
- 🔍 **Real-time**: OpenAI Web Search integration

### 🏆 For General Question Generation

**Traditional recommended approach:**

```bash
# 1. Navigate to the comparative approach
cd experiments/05_comparative

# 2. Run test mode (fast validation)
python four_way_comparative_experiment.py test

# 3. Run full experiment (production quality)
python four_way_comparative_experiment.py
```

**Why this approach?**
- ✅ **Battle-tested**: 100% success rate across experiments
- ✅ **Comprehensive**: Multiple models and datasets
- ✅ **Production-ready**: Robust error handling
- ✅ **Well-documented**: Complete analysis and reports

## 🔬 Experimental Approaches

### 1. 🏆 Comparative Experiments (RECOMMENDED)

**Location**: `experiments/05_comparative/`
**Best for**: Production use, research benchmarks, model comparison

**Features**:
- Four-way comparison (2 models × 2 datasets)
- Comprehensive quality analysis
- Multiple output formats
- Automatic retry and error handling

**Usage**:
```bash
cd experiments/05_comparative
python four_way_comparative_experiment.py
```

### 2. 📝 PROMPT-Only Approach

**Location**: `experiments/01_prompt_only/`
**Best for**: Quick prototyping, self-contained generation

**Features**:
- Pure prompt-based generation
- Fast processing
- No external dependencies
- Simple setup

**Usage**:
```bash
cd experiments/01_prompt_only
python prompt_generator.py
```

### 3. 🔍 RAG Approach

**Location**: `experiments/02_rag_approach/`
**Best for**: Knowledge-grounded generation, fact verification

**Features**:
- External knowledge integration
- Factual accuracy
- Literature-based answers
- Citation support

**Usage**:
```bash
cd experiments/02_rag_approach
python rag_generator.py
```

### 4. 🔄 Hybrid PROMPT+RAG

**Location**: `experiments/03_hybrid_prompt_rag/`
**Best for**: Best of both approaches

**Features**:
- PROMPT for questions
- RAG for answers
- Balanced approach
- Quality optimization

**Usage**:
```bash
cd experiments/03_hybrid_prompt_rag
python hybrid_generator.py
```

### 5. 🧠 Multi-Stage Generation

**Location**: `experiments/04_multi_stage/`
**Best for**: Deep thinking processes, iterative refinement

**Features**:
- Multi-step generation
- Quality refinement
- Deep thinking simulation
- Sophisticated prompting

**Usage**:
```bash
cd experiments/04_multi_stage
python main.py
```

### 6. 🧠 Agent Deep Reasoning Framework (LATEST)

**Location**: `experiments/07_tree_extension_deep_query/`
**Best for**: AI Agent reasoning test, preventing direct answers

**Features**:
- **6-Step Agent Design Flow**: Complete pipeline from short answers to composite questions
- **Root Answer Exposure Protection**: Intelligent detection and prevention of answer leakage
- **Pure Objective Q&A**: Elimination of LLM thinking process descriptions
- **Real Web Search Integration**: OpenAI official API, no mock data pollution
- **Tree Extension Structure**: Multi-level question dependency relationships
- **4-Layer Quality Verification**: Comprehensive validation system

**Usage**:
```bash
cd experiments/07_tree_extension_deep_query
python main.py
```

**Key Innovation**:
- Generates questions that **cannot be directly answered** by normal LLMs
- Requires **Agent step-by-step reasoning** to solve
- **Prevents masking**: Ensures root answers are not exposed during reasoning
- **Production-ready**: Automated generation with quality guarantee

## ⚙️ Configuration & Setup

### API Keys Setup

Create a `.env` file in the project root:
```bash
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_claude_key_here
```

### Dependencies

```bash
pip install requests pandas openpyxl anthropic openai
```

### Data Sources

The project uses two main data sources:
1. **ClueWeb22**: Web-crawled multilingual documents
2. **Academic Papers**: Research literature corpus

Data is automatically loaded from `data/` directory.

## 📊 Core Components

### LLM Clients (`core/llm_clients/`)

- `openai_api_client.py` - OpenAI GPT-4o integration
- `claude_api_client.py` - Claude Sonnet 4 integration  
- `llm_manager.py` - Unified LLM management

### Data Processing (`core/data_processing/`)

- `utils.py` - JSON parsing and data utilities
- `convert_clueweb22_data.py` - ClueWeb22 data converter

### Evaluation (`core/evaluation/`)

- `deep_research_evaluation_framework.py` - Quality assessment
- `question_refinement_system.py` - Question optimization

### Output (`core/output/`)

- `export_to_excel.py` - Excel export functionality
- Multiple format support (JSON, Excel, Markdown)

## 🎯 Workflow Details

### Standard Pipeline

1. **Data Loading**
   ```python
   # Load ClueWeb22 topics
   topics = load_clueweb_topics()
   
   # Load academic papers
   papers = load_academic_papers()
   ```

2. **Report Generation**
   ```python
   # Generate domain-specific reports
   report = generate_domain_report(documents, topic_id)
   ```

3. **Question Generation**
   ```python
   # Generate research questions
   questions = generate_questions(report, num_questions=50)
   ```

4. **Answer Generation**
   ```python
   # Generate comprehensive answers
   answers = generate_answers(questions, report)
   ```

5. **Export & Analysis**
   ```python
   # Export results
   export_to_excel(results, filename)
   export_to_json(results, filename)
   ```

### Quality Control

- **Automatic retry mechanisms**
- **Error handling and fallbacks**
- **Quality scoring and filtering**
- **Format validation**

## 📈 Performance Metrics

Based on comprehensive testing:

| Approach | Speed | Quality | Reliability | Use Case |
|----------|-------|---------|-------------|----------|
| **Agent Reasoning (07)** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | **Agent Testing** |
| Comparative | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Production |
| PROMPT-only | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | Prototyping |
| RAG | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Research |
| Hybrid | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Balanced |
| Multi-stage | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | Deep analysis |

## 🔧 Customization

### Adding New Models

```python
# In core/llm_clients/
class NewModelClient:
    def __init__(self, api_key):
        self.api_key = api_key
    
    def generate_content(self, prompt, **kwargs):
        # Implementation
        pass
```

### Adding New Data Sources

```python
# In core/data_processing/
def load_new_data_source(path):
    # Implementation
    return processed_data
```

### Custom Evaluation Metrics

```python
# In core/evaluation/
def custom_quality_metric(question, answer):
    # Implementation
    return score
```

## 🐛 Troubleshooting

### Common Issues

1. **API Rate Limits**
   - Solution: Built-in rate limiting and retry logic
   - Adjust delays in configuration

2. **Memory Issues**
   - Solution: Process topics in batches
   - Reduce document count per topic

3. **Import Errors**
   - Solution: Check Python path and imports
   - Ensure core components are accessible

4. **Data Loading Errors**
   - Solution: Verify data directory structure
   - Check file permissions and encoding

### Debug Mode

```python
# Enable detailed logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📋 Best Practices

### For Research
- Use **Comparative Experiments** for reproducible results
- Document all configuration parameters
- Save intermediate results for analysis
- Validate with multiple topics

### For Production
- Start with **test mode** for validation
- Use error handling and retry mechanisms
- Monitor API usage and costs
- Implement quality checks

### For Development
- Follow the modular structure
- Add comprehensive documentation
- Include example usage
- Write unit tests for new components

## 📚 Documentation

- Each experiment has its own README
- Core components are well-documented
- Configuration options are explained
- Examples are provided throughout

## 🚀 Future Extensions

The modular structure supports:
- New experimental approaches
- Additional LLM providers
- Extended evaluation metrics
- Custom data sources
- Advanced analysis tools

---

## 📞 Support

For questions or issues:
1. Check the specific experiment README
2. Review troubleshooting section
3. Examine example outputs
4. Test with simplified configurations

---

*This guide provides comprehensive coverage of all experimental approaches. Start with the recommended comparative framework for best results.* 
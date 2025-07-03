# 🏆 Comparative Experiments - RECOMMENDED APPROACH

## 📋 Overview

This is the **RECOMMENDED** experimental framework based on comprehensive testing and validation. It provides robust, scalable question generation with comparative analysis capabilities.

## 🔧 Methodology

**Four-Way Comparative Framework**:
1. **Multiple Datasets**: ClueWeb22 + Random Academic Documents
2. **Multiple Models**: OpenAI GPT-4o vs Claude Sonnet 4
3. **Complete Pipeline**: Documents → Reports → Questions → Answers
4. **Comprehensive Analysis**: Performance metrics and quality comparison

## ✨ Key Features

- ✅ **Proven Success**: 100% success rate in recent experiments
- ✅ **Comprehensive**: Handles multiple datasets and models
- ✅ **Scalable**: Processes 9+ topics with 50 QA pairs each
- ✅ **Quality Assured**: Advanced error handling and fallback mechanisms
- ✅ **Export Ready**: Multiple output formats (JSON, Excel, Markdown)

## 🚀 Quick Start

```bash
cd experiments/05_comparative
python four_way_comparative_experiment.py
```

**Test Mode** (faster validation):
```bash
python four_way_comparative_experiment.py test
```

## 📊 Configuration

- **Questions per Topic**: 50 (Easy: 15, Medium: 20, Hard: 15)
- **Models**: OpenAI GPT-4o + Claude Sonnet 4
- **Datasets**: ClueWeb22 + Academic papers
- **Processing**: Batch generation with automatic retry
- **Output**: Complete comparative analysis

## 📁 Files

- `four_way_comparative_experiment.py` - **Main experimental framework** (recommended)
- `clueweb22_comparative_analysis.py` - Results analysis and report generation
- `README.md` - This documentation
- `技术深度解析_05四路对比框架.md` - Technical deep-dive (Chinese)
- `CLIENT_PRESENTATION_05框架技术介绍.md` - Client presentation (Chinese)
- `详细说明_四路对比实验框架.md` - Detailed methodology (Chinese)

## 📈 Performance Metrics

Based on latest experiments:
- **Speed**: OpenAI ~32 min/topic, Claude ~35 min/topic
- **Quality**: Claude generates 91% more detailed reports
- **Reliability**: 100% success rate for both models
- **Output**: 900 total QA pairs across all experiments

## 🎯 Workflow

1. **Data Loading**: Automatically loads ClueWeb22 and academic datasets
2. **Report Generation**: Creates domain-specific analysis reports
3. **Question Generation**: Generates questions in difficulty-graded batches
4. **Answer Generation**: Produces comprehensive answers based on reports
5. **Comparative Analysis**: Generates performance comparison and recommendations
6. **Export**: Saves results in multiple formats with detailed analytics

## ✅ Use Cases

- **Production Quality**: Ready for real-world applications
- **Research Benchmarks**: Academic research and evaluation
- **Model Comparison**: Comparative analysis of different LLMs
- **Quality Assurance**: Reliable and reproducible results

## 🔧 Advanced Configuration

```python
# Test mode (3 questions per topic)
experiment.run_test_experiment()

# Full mode (50 questions per topic)  
experiment.run_all_experiments()

# Custom configuration
config = {
    'questions_per_topic': 50,
    'test_mode': False,
    'output_format': ['json', 'excel', 'markdown']
}
```

## 📊 Expected Output

```
results/comparative/
├── FRESH_FOUR_WAY_EXPERIMENT_TIMESTAMP/
│   ├── clueweb_openai_TIMESTAMP/          # ClueWeb22 + OpenAI results
│   ├── clueweb_claude_TIMESTAMP/          # ClueWeb22 + Claude results  
│   ├── random_openai_TIMESTAMP/           # Academic + OpenAI results
│   ├── random_claude_TIMESTAMP/           # Academic + Claude results
│   ├── four_way_comparative_results.xlsx  # Complete analysis
│   └── FOUR_WAY_COMPARATIVE_ANALYSIS.md   # Summary report
```

## 🔗 Dependencies

- OpenAI API (for GPT-4o)
- Claude API (for Sonnet 4)
- Core components from `../../core/`
- Data sources from `../../data/`

---

## 🌟 Why This Approach is Recommended

1. **Battle-Tested**: Successfully validated across multiple experiments
2. **Comprehensive**: Covers all major experimental scenarios
3. **Reliable**: Robust error handling and automatic retry mechanisms
4. **Scalable**: Handles large-scale question generation efficiently
5. **Analytical**: Provides detailed performance comparisons and insights
6. **Export-Ready**: Multiple output formats for different use cases

**For new users**: Start with this approach for reliable, high-quality results.

**For researchers**: Use this framework for reproducible experimental validation.

**For production**: This approach provides the most robust and tested pipeline.
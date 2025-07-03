# Energy Domain Benchmark Generator

A tool for generating a benchmark of 200 queries with corresponding expert-level answers to evaluate large language models' (LLMs) deep research capabilities in the energy domain, comparing deep thinking methods with standard generation approaches.

## Overview

This benchmark generator creates a balanced set of energy domain research questions with comprehensive, research-grade answers, based on specified distributions across:
- Source methods: 100 using deep thinking method, 100 using standard method
- Difficulty: 30% Easy, 40% Medium, 30% Hard
- Category: 40% General energy questions, 60% Cross-subdomain questions

## Research Goal

The primary research goal is to investigate how LLMs perform deep research in specialized domains like energy. This benchmark evaluates:

1. Whether a multi-step deep thinking approach produces higher quality research questions compared to a standard single-pass generation approach
2. How well LLMs can produce comprehensive, scholarly analyses that demonstrate deep domain knowledge and research capabilities
3. The quality of responses across varying difficulty levels and domain intersections

The benchmark provides paired data points to enable this comparison, preserving both the generated questions, generation prompts, and expert-level answers that serve as reference responses for evaluating LLM performance.

## Features

- Two different AI generation methods:
  - **Deep Thinking**: Multi-round generation with domain analysis, initial questions, and refinement
  - **Standard**: Single-pass direct generation
- Expert-level answer generation for each query, demonstrating:
  - Methodological rigor and analytical frameworks
  - Interdisciplinary integration across technical, economic, policy dimensions
  - Critical evaluation of evidence and research gaps
  - Systems thinking and complex interdependencies
  - Research awareness of frontiers and scholarly debates
- Batch processing to handle large query sets without memory issues
- Balanced coverage of energy subdomains
- Detailed statistics reporting
- Recording of all generation prompts for research purposes
- Export to both JSON and Excel formats with query-answer pairs and prompt data included

## Files

- `benchmark_generator.py` - Main class for generating the complete benchmark
- `deep_thinking_api.py` - Implementation of the deep thinking generation method
- `standard_api.py` - Implementation of the standard generation method
- `answer_generator.py` - Implementation of the expert-level answer generation for queries
- `supplement_benchmark.py` - Tool to detect and fill gaps in incomplete benchmarks
- `test_benchmark.py` - Small-scale test of the benchmark generator
- `config.py` - Configuration settings

## Usage

### Full Benchmark Generation

To generate the complete 200-query benchmark with answers:

```bash
python benchmark_generator.py
```

This will:
1. Generate 100 deep thinking queries in configurable batch sizes
2. Generate 100 standard method queries in configurable batch sizes
3. Generate expert-level answers for each query using a structured research framework
4. Save each batch to JSON and Excel incrementally
5. Merge all batches into a final comprehensive set

### Supplementing an Incomplete Benchmark

If you encounter API errors or other issues that result in missing queries or failed answers:

```bash
python supplement_benchmark.py
```

The tool will:
1. Find the latest complete benchmark file in the output directory
2. Analyze gaps and failures (missing IDs, failed answers)
3. Generate targeted queries to fill specific missing IDs
4. Regenerate answers for queries that failed during the initial process
5. Update the original benchmark file with the supplementary content
6. Generate updated statistics on the completed benchmark

### Small-Scale Testing

To run a small-scale test with minimal queries:

```bash
python test_benchmark.py
```

This is useful for verifying that the system works correctly without spending time generating a full benchmark.

## Configuration

The `config.py` file contains all necessary settings:

- `CLAUDE_API_KEY` - Your Anthropic API key
- `MODEL_NAME` - The Claude model to use
- `TOTAL_QUERIES` - Total number of queries (default: 200)
- `DEEP_THINKING_GENERATED` - Number of deep thinking queries (default: 100)
- `STANDARD_GENERATED` - Number of standard queries (default: 100)
- `DIFFICULTY_DISTRIBUTION` - Percentage distribution across difficulty levels
- `CATEGORY_DISTRIBUTION` - Percentage distribution across categories
- `SUBDOMAINS` - List of energy subdomains covered
- `INCLUDE_PROMPTS` - Whether to include generation prompts in the output
- `GENERATE_ANSWERS` - Whether to generate answers for each query
- `ANSWER_MAX_TOKENS` - Maximum tokens for generated answers
- `ANSWER_SYSTEM_PROMPT` - System prompt for answer generation

## Query-Answer Structure

### Query Component

Each generated query includes:

- `id` - Unique identifier (DT### for deep thinking, ST### for standard)
- `query_text` - The actual query text
- `category` - "General" or "Cross_Subdomain"
- `subdomains` - List of relevant subdomains
- `difficulty` - "Easy", "Medium", or "Hard"
- `source` - Where the query came from ("Deep_Thinking" or "Standard")
- `timestamp` - When the query was generated
- `generation_details` - Contains all prompts and intermediate generation steps

### Answer Component

Each answer follows a structured research framework:
- **Introduction & Context**: Framing the question, key concepts, and boundaries
- **Methodology & Analytical Framework**: Theoretical frameworks and methodological approaches
- **State of Research**: Synthesis of current findings, debates, and research gaps
- **Multi-Dimensional Analysis**: Technical, economic, policy, environmental, and social dimensions
- **Synthesis & Interconnections**: Analysis of interactions, trade-offs, and systemic effects
- **Research Frontiers**: Emerging directions and methodological innovations

The answers demonstrate scholarly depth while remaining accessible, showcasing the kind of comprehensive analysis expected in high-quality energy research publications.

## Generation Methods

### Deep Thinking Method (Three-Step Process)
1. **Domain Understanding**: The AI first deeply analyzes the energy subdomains specified, exploring frontiers, challenges, and connections
2. **Initial Question Generation**: Based on this understanding, it generates initial questions
3. **Refinement**: These questions are then refined for precision, depth, and quality

### Standard Method (Single-Step Process)
A comprehensive prompt directly generates questions without the multi-step thinking process, producing the final output in one pass.

### Answer Generation
For each query, a detailed expert-level answer is generated using domain-specific system prompts and contextual information about the query's difficulty and subdomains. The answer generation process employs a structured research framework that guides the model to produce comprehensive scholarly analysis.

This approach enables rigorous comparison between multi-step and single-step generation for research questions, with all prompts preserved for analysis. The included answers provide a reference point for evaluating the performance of different LLMs on these research questions.

## Supplementing Incomplete Benchmarks

If API errors or other issues result in an incomplete benchmark, the supplement tool can be used to detect and fill gaps:

```bash
python supplement_benchmark.py
```

This tool performs several key functions:
1. **Analysis**: Identifies missing queries (by ID gaps) and failed answers
2. **Balanced Generation**: Creates missing queries following the same distribution patterns as the existing benchmark
3. **Answer Regeneration**: Attempts to regenerate any failed answers while preserving the original query
4. **Seamless Integration**: Updates the original benchmark file, maintaining proper ID sequences
5. **Incremental Saving**: Saves progress after each query to prevent data loss during long processes

The supplement tool ensures benchmark completeness by:
- Using the exact missing IDs (e.g., DT100, ST097) rather than creating new ones
- Maintaining the proper balance of difficulties, categories, and subdomains in new content
- Preserving all properties of original queries when regenerating failed answers
- Creating comprehensive backup files before making any changes

## Batch Processing

To handle large numbers of queries without memory issues, the system:
1. Processes queries in configurable batch sizes (default: 20)
2. Generates answers for each batch
3. Saves each batch to separate JSON and Excel files
4. Merges all batches into comprehensive files at the end
5. Maintains consistent query IDs across all batches

## Output Files

Files are saved in the `output` directory using timestamp-based naming:
- Individual batch files:
  - `energy_benchmark_YYYYMMDD_HHMMSS_batch01.json`
  - `energy_benchmark_YYYYMMDD_HHMMSS_batch01.xlsx`
  - etc.
- Merged complete files:
  - `energy_benchmark_YYYYMMDD_HHMMSS_complete.json`
  - `energy_benchmark_YYYYMMDD_HHMMSS_complete.xlsx`
- Backup files (created during supplement process):
  - `energy_benchmark_YYYYMMDD_HHMMSS_complete.json.bak`

The Excel files contain all query-answer pairs including the prompts used for generation, supporting comprehensive analysis of the relationship between generation methodology and query/answer quality.

## Data Integrity and Error Handling

The system includes several features to ensure data integrity:

1. **Incremental Saving**: Each batch of queries is saved as soon as it's generated
2. **Backup Creation**: Backup files are automatically created before making updates
3. **ID Validation**: Unique ID assignments are validated to prevent duplicates
4. **Error Recovery**: The supplement tool can recover from API errors by regenerating failed content
5. **Progress Tracking**: The system tracks and reports on progress, making it clear what has been completed

These safeguards ensure that even if errors occur during the generation process, valuable work is preserved and can be supplemented rather than restarting from scratch. 
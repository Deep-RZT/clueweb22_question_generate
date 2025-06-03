# Energy Domain PROMPT+RAG Pipeline Documentation

## Overview

This document describes the complete pipeline for generating high-quality energy domain question-answer datasets using a combination of PROMPT-based AI generation and RAG (Retrieval-Augmented Generation) with real literature. The pipeline is designed to support FastText classifier training for filtering ClueWeb22 corpus to extract energy-related documents.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    ENERGY PROMPT+RAG PIPELINE                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐    ┌─────────────────┐    ┌──────────────┐ │
│  │   PROMPT SYSTEM │    │   RAG SYSTEM    │    │   COMPARISON │ │
│  │                 │    │                 │    │   & OUTPUT   │ │
│  │ • Claude API    │───▶│ • 588 Papers   │───▶│ • JSON/Excel │ │
│  │ • 200 Questions │    │ • Literature    │    │ • Statistics │ │
│  │ • AI Answers    │    │ • RAG Answers   │    │ • Analysis   │ │
│  └─────────────────┘    └─────────────────┘    └──────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Phase 1: PROMPT System Details

### 1.1 System Components

The PROMPT system consists of several key components located in the `PROMPT/` directory:

#### Core Files:
- **`energy_query_generator.py`**: Main query generation engine using Claude API
- **`config.py`**: Configuration parameters for generation
- **`benchmark_generator.py`**: Batch processing for large-scale generation
- **`answer_generator.py`**: AI answer generation for questions

#### Configuration Parameters:
```python
# From PROMPT/config.py
MODEL_NAME = "claude-3-7-sonnet-20250219"
DIFFICULTY_DISTRIBUTION = {
    'Easy': 32,      # 32% of questions
    'Medium': 40,    # 40% of questions  
    'Hard': 28       # 28% of questions
}
CATEGORY_DISTRIBUTION = {
    'General': 60,           # 60% single subdomain
    'Cross_Subdomain': 40    # 40% multiple subdomains
}
SUBDOMAINS = [
    'Renewable', 'Fossil_Fuels', 'Nuclear', 'Grid_Storage',
    'Policy', 'Economics', 'Environmental'
]
```

### 1.2 Question Generation Process

#### Step 1: Requirement Definition
The system creates balanced query requirements across:
- **Difficulty Levels**: Easy (fundamental concepts), Medium (multi-factor analysis), Hard (complex system thinking)
- **Categories**: General (single subdomain focus) vs Cross-Subdomain (interdisciplinary)
- **Subdomains**: 7 energy domains with specific keyword coverage

#### Step 2: AI Generation via Claude API
```python
# Generation process
for requirement in requirements:
    prompt = create_generation_prompt(
        difficulty=requirement.difficulty,
        category=requirement.category,
        primary_subdomain=requirement.primary_subdomain,
        secondary_subdomains=requirement.secondary_subdomains
    )
    
    response = claude_api.generate(
        model="claude-3-7-sonnet-20250219",
        prompt=prompt,
        max_tokens=4000
    )
    
    questions.append(parse_response(response))
```

#### Step 3: Quality Filtering
Generated questions undergo quality assessment:
- **Clarity Score**: Linguistic clarity and specificity
- **Depth Score**: Technical depth and research value
- **Domain Relevance**: Alignment with energy domain requirements
- **Overall Quality**: Composite score for final selection

### 1.3 Answer Generation Process

#### Expert-Level Answer Generation:
```python
# Answer generation with research-grade depth
system_prompt = """
You are a world-class energy researcher with expertise across 
multiple energy domains. Your analytical approach is characterized by:
1. Methodological rigor
2. Interdisciplinary integration  
3. Critical evaluation
4. Systems thinking
5. Multi-scale perspective
6. Research awareness
"""

answer_prompt = """
Provide a comprehensive, research-grade analysis with:
1. INTRODUCTION & CONTEXT
2. METHODOLOGY & ANALYTICAL FRAMEWORK  
3. STATE OF RESEARCH
4. MULTI-DIMENSIONAL ANALYSIS
5. SYNTHESIS & INTERCONNECTIONS
6. RESEARCH FRONTIERS
"""
```

### 1.4 Output Format
```json
{
  "metadata": {
    "total_queries": 200,
    "generation_timestamp": "2025-05-21T18:22:47.667518",
    "model": "claude-3-7-sonnet-20250219",
    "configuration": {
      "difficulties": ["Easy", "Medium", "Hard"],
      "categories": ["General", "Cross_Subdomain"],
      "subdomains": [...]
    }
  },
  "queries": [
    {
      "id": "ST001",
      "query_text": "How can grid-scale energy storage...",
      "category": "Cross_Subdomain",
      "subdomains": ["Grid_Storage", "Renewable"],
      "difficulty": "Medium",
      "source": "AI_generated",
      "answer": {
        "text": "# Comprehensive Analysis...",
        "timestamp": "2025-05-21T18:15:02"
      }
    }
  ]
}
```

## Phase 2: RAG System Details

### 2.1 Literature Corpus Construction

#### Data Sources:
The RAG system is built on a comprehensive literature corpus:
- **Total Papers**: 588 high-quality energy research papers
- **Sources**: arXiv, OpenAlex, CrossRef APIs
- **Coverage**: All 7 energy subdomains with balanced representation
- **Quality Control**: Abstracts >50 characters, valid metadata

#### Corpus Structure:
```python
# Each paper in corpus contains:
{
    'id': 'unique_identifier',
    'title': 'paper_title',
    'abstract': 'paper_abstract',
    'authors': ['author1', 'author2'],
    'source': 'arxiv|openalex|crossref',
    'full_text': 'title + abstract for search'
}
```

### 2.2 Retrieval Mechanism

#### Similarity Calculation:
```python
def simple_similarity(query: str, document: str) -> float:
    """Jaccard similarity for keyword overlap"""
    query_words = set(query.lower().split())
    doc_words = set(document.lower().split())
    
    intersection = query_words.intersection(doc_words)
    union = query_words.union(doc_words)
    
    return len(intersection) / len(union)
```

#### Multi-Field Retrieval:
```python
def retrieve_relevant_papers(query: str, top_k: int = 5):
    """Retrieve papers using weighted similarity"""
    for paper in corpus:
        # Calculate similarity with title and abstract
        title_sim = simple_similarity(query, paper['title'])
        abstract_sim = simple_similarity(query, paper['abstract'])
        
        # Combined score with higher weight for title
        combined_score = title_sim * 0.6 + abstract_sim * 0.4
        
        if combined_score > 0.05:  # Minimum threshold
            scores.append((combined_score, paper))
    
    # Return top_k most relevant papers
    return sorted(scores, reverse=True)[:top_k]
```

### 2.3 Answer Generation from Literature

#### Literature-Based Answer Synthesis:
```python
def generate_literature_based_answer(query: str, relevant_papers: List[Dict]):
    """Generate answer from retrieved literature"""
    key_findings = []
    sources = []
    
    for paper in relevant_papers:
        # Extract relevant sentences from abstract
        abstract_sentences = paper['abstract'].split('.')
        query_words = set(query.lower().split())
        
        for sentence in abstract_sentences:
            sentence_words = set(sentence.lower().split())
            if len(query_words.intersection(sentence_words)) > 0:
                key_findings.append(sentence.strip())
        
        sources.append({
            'title': paper['title'],
            'authors': paper['authors'],
            'source': paper['source'],
            'id': paper['id']
        })
    
    # Synthesize comprehensive answer
    if key_findings:
        answer = "Based on relevant research literature, " + \
                " ".join(key_findings[:3])  # Top 3 findings
    else:
        answer = f"According to {len(relevant_papers)} relevant papers, " + \
                "this involves complex energy system issues requiring " + \
                "further interdisciplinary research."
    
    return {
        'answer': answer,
        'sources': sources,
        'confidence': min(len(relevant_papers) / 5.0, 1.0)
    }
```

## Phase 3: Integration and Comparison Pipeline

### 3.1 Main Pipeline Execution

#### Complete Workflow:
```python
def main_pipeline():
    # 1. Load PROMPT-generated questions
    prompt_data = load_prompt_questions()
    print(f"✅ Loaded {len(prompt_data['queries'])} questions")
    
    # 2. Initialize RAG system with literature corpus  
    papers_data = load_rag_corpus()
    rag_system = EnergyRAGSystem(papers_data)
    print(f"✅ RAG system with {len(rag_system.corpus)} papers")
    
    # 3. Process each question with both systems
    results = []
    for question in prompt_data['queries']:
        # Extract original AI answer
        original_answer = question.get('answer', {}).get('text', '')
        
        # Generate RAG answer from literature
        relevant_papers = rag_system.retrieve_relevant_papers(
            question['query_text'], top_k=5
        )
        rag_result = rag_system.generate_literature_based_answer(
            question['query_text'], relevant_papers
        )
        
        # Create comparison result
        result = create_comparison_result(
            question, original_answer, rag_result
        )
        results.append(result)
    
    # 4. Save results and generate statistics
    save_results(results)
    generate_comparison_statistics(results)
```

### 3.2 Quality Assessment Framework

#### Answer Quality Metrics:
```python
def extract_answer_quality_metrics(answer_text: str):
    """Comprehensive quality assessment"""
    return {
        'has_answer': bool(answer_text and not answer_text.startswith('Failed')),
        'word_count': len(answer_text.split()),
        'char_count': len(answer_text),
        'has_sections': any(marker in answer_text for marker in 
                           ['##', '###', '1.', '2.', '3.']),
        'has_references': any(marker in answer_text for marker in 
                             ['et al.', 'doi:', 'http', 'www.'])
    }
```

#### Comparison Metrics:
```python
def create_comparison_metrics(original_quality, rag_quality, rag_sources):
    """Generate comparative analysis"""
    return {
        'both_have_answers': original_quality['has_answer'] and rag_quality['has_answer'],
        'original_longer': original_quality['word_count'] > rag_quality['word_count'],
        'rag_has_sources': len(rag_sources) > 0,
        'original_has_sections': original_quality['has_sections'],
        'original_has_references': original_quality['has_references']
    }
```

### 3.3 Output Generation

#### Comprehensive Result Structure:
```json
{
  "id": "ST001",
  "query_text": "How can grid-scale energy storage...",
  "subdomains": ["Grid_Storage", "Renewable"],
  "difficulty": "Medium",
  "category": "Cross_Subdomain",
  
  "original_ai_answer": "# Comprehensive Analysis...",
  "original_answer_quality": {
    "has_answer": true,
    "word_count": 2389,
    "has_sections": true,
    "has_references": true
  },
  
  "rag_literature_answer": "Based on relevant research literature...",
  "rag_answer_quality": {
    "has_answer": true,
    "word_count": 102,
    "has_sections": false,
    "has_references": false
  },
  
  "literature_sources": [
    {
      "title": "Modeling renewable energy systems with storage",
      "authors": ["Author1", "Author2"],
      "source": "arxiv",
      "id": "arxiv_id"
    }
  ],
  
  "rag_confidence_score": 0.8,
  "num_literature_sources": 5,
  
  "answer_comparison": {
    "both_have_answers": true,
    "original_longer": true,
    "rag_has_sources": true,
    "original_has_sections": true,
    "original_has_references": true
  }
}
```

## Phase 4: Statistical Analysis and Reporting

### 4.1 Performance Metrics

#### System Performance:
- **Question Coverage**: 200/200 questions processed (100%)
- **AI Answer Availability**: 200/200 (100%)
- **RAG Answer Generation**: 200/200 (100%)
- **Literature Source Coverage**: 199/200 questions have sources (99.5%)

#### Quality Comparison:
- **Original AI Answers**: Average 2,389 words, 98.5% with references
- **RAG Literature Answers**: Average 102 words, 99.5% with literature sources
- **Answer Length**: 100% of AI answers longer than RAG answers
- **Structural Complexity**: 100% of AI answers have sections vs 0% RAG answers

### 4.2 Domain Coverage Analysis

#### Subdomain Distribution:
```
Fossil_Fuels: 81 questions (40.5%)
Renewable: 81 questions (40.5%)  
Nuclear: 78 questions (39.0%)
Grid_Storage: 73 questions (36.5%)
Environmental: 49 questions (24.5%)
Policy: 39 questions (19.5%)
Economics: 35 questions (17.5%)
```

#### Difficulty Distribution:
```
Medium: 80 questions (40.0%)
Easy: 64 questions (32.0%)
Hard: 56 questions (28.0%)
```

### 4.3 RAG System Performance

#### Retrieval Effectiveness:
- **Average Confidence Score**: 0.990
- **Average Literature Sources per Question**: 5.0
- **Successful Retrieval Rate**: 99.5%
- **Source Diversity**: Papers from arXiv, OpenAlex, CrossRef

## Usage Instructions

### Prerequisites:
```bash
# Install required packages
pip install pandas openpyxl

# Ensure directory structure:
energy_fasttext/
├── main.py
├── PROMPT/output/energy_benchmark_20250521_135210_complete.json
└── RAG/data/metadata/papers_20250526_182607.json
```

### Execution:
```bash
# Run complete pipeline
python main.py

# Output files generated:
# - output/energy_prompt_rag_comparison_TIMESTAMP.json
# - output/energy_prompt_rag_comparison_TIMESTAMP.xlsx
```

### Output Analysis:
The generated files contain:
1. **JSON**: Complete structured data for programmatic analysis
2. **Excel**: Human-readable format for manual review and analysis
3. **Statistics**: Comprehensive performance and quality metrics

## Applications for FastText Training

### Dataset Preparation:
The generated dataset can be used for FastText classifier training:

1. **Positive Samples**: Use both AI-generated and RAG literature answers as energy-related content
2. **Negative Samples**: Generate non-energy content for binary classification
3. **Training Format**: Convert to FastText format with `__label__energy` and `__label__nonenergy`

### Quality Advantages:
- **Expert-Level Content**: AI answers demonstrate research-grade depth
- **Literature Grounding**: RAG answers provide empirical foundation
- **Domain Coverage**: Comprehensive coverage across 7 energy subdomains
- **Difficulty Spectrum**: Questions span from fundamental to advanced concepts

## Conclusion

This PROMPT+RAG pipeline successfully combines the generative capabilities of large language models with the empirical grounding of scientific literature to create a high-quality energy domain question-answer dataset. The system demonstrates:

1. **Scalability**: Processes 200 questions with full automation
2. **Quality**: Generates research-grade content with literature backing
3. **Comprehensiveness**: Covers all major energy subdomains and difficulty levels
4. **Comparability**: Enables analysis of AI vs literature-based approaches
5. **Applicability**: Produces datasets suitable for FastText classifier training

The pipeline provides a robust foundation for energy domain text classification tasks and can be extended to other technical domains with appropriate corpus adaptation. 
# Deep Research QA Benchmark - Complete Workflow Documentation

## 项目总览

本项目是一个专门为评估LLM深度研究能力而设计的自动化问答对生成系统，完全满足所有要求。

## 系统架构

### 核心组件

```
1. ClueWeb22 Document Processing
   ↓
2. Domain Report Generation (AI-powered)
   ↓
3. Deep Research Question Generation (AI-powered)
   ↓
4. Question Quality Evaluation & Refinement
   ↓
5. Comprehensive Answer Generation (AI-powered)
   ↓
6. Final QA Benchmark Dataset
```

## 详细工作流程

### Phase 1: Topic Selection & Document Processing

**文件**: `clueweb22_simplified_generator.py`

**功能**: 
- 自动选择10个ClueWeb22 topics
- 处理每个topic下的100篇文档
- 提取文档内容并进行预处理

**关键代码**:
```python
def select_clueweb22_topics(self, count: int = 10) -> List[str]:
    """Select diverse ClueWeb22 topics for processing"""
    # 从ClueWeb22数据集中选择多样化的topics
```

### Phase 2: Domain Report Generation

**文件**: `clueweb22_simplified_generator.py`

**功能**: 
- 基于100篇文档生成1500-2000词的高质量domain report
- 使用Claude API进行内容综合分析

**核心Prompt**:
```
You are a research analyst tasked with creating a comprehensive domain report.

Based on the following documents from the ClueWeb22 dataset, create a detailed domain analysis report (1500-2000 words) that covers:

1. **Domain Overview**: What is the primary domain/field represented by these documents?
2. **Key Themes**: What are the main topics, concepts, and themes discussed?
3. **Methodological Approaches**: What research methods, analytical frameworks, or approaches are mentioned?
4. **Current Research**: What current research trends, findings, or developments are highlighted?
5. **Applications**: What practical applications, use cases, or implementations are discussed?
6. **Future Directions**: What future research directions, challenges, or opportunities are mentioned?

Requirements:
- Write in a scholarly, analytical tone
- Provide specific examples and evidence from the documents
- Ensure the report is comprehensive and well-structured
- Focus on research depth and academic rigor
- Target length: 1500-2000 words

Documents:
{documents_content}
```

### Phase 3: Deep Research Question Generation

**文件**: `clueweb22_simplified_generator.py`

**功能**: 
- 每个topic生成50个深度研究问题
- 按照难度分级: Easy(20%), Medium(40%), Hard(40%)

**核心Prompt**:
```
You are an expert researcher tasked with generating deep research questions for academic evaluation.

Based on the following domain report, generate exactly 50 high-quality research questions that test deep research capabilities.

Requirements:
1. **Question Distribution**:
   - 10 Easy questions (20%): Basic understanding, factual recall
   - 20 Medium questions (40%): Analysis, comparison, requires multi-step thinking
   - 20 Hard questions (40%): Complex synthesis, evaluation, expert-level reasoning

2. **Question Quality Standards**:
   - Questions should require deep domain knowledge
   - Medium/Hard questions must require multi-step reasoning
   - Avoid simple factual questions
   - Focus on analysis, synthesis, evaluation, and critical thinking
   - Questions should be answerable based on the domain report

3. **Question Types to Include**:
   - Analytical questions requiring evidence evaluation
   - Comparative questions examining relationships
   - Synthesis questions integrating multiple concepts
   - Evaluation questions requiring expert judgment
   - Methodological questions about research approaches
   - Application questions about practical implementation

Domain Report:
{domain_report}

Generate exactly 50 questions in the following JSON format:
[
  {
    "question_text": "Your question here",
    "difficulty": "Easy/Medium/Hard",
    "question_type": "Analytical/Comparative/Synthesis/Evaluation/Methodological/Application",
    "reasoning_steps": "Brief description of thinking steps required"
  }
]
```

### Phase 4: Question Quality Evaluation

**文件**: `deep_research_evaluation_framework.py`

**功能**: 
- 自动评估问题的深度研究质量
- 使用4个维度评分系统

**评估标准**:
```python
EVALUATION_CRITERIA = {
    'cognitive_complexity': {
        'weight': 0.30,
        'description': 'Requires analysis, synthesis, evaluation'
    },
    'research_depth': {
        'weight': 0.30, 
        'description': 'Involves complex concepts and professional knowledge'
    },
    'synthesis_requirement': {
        'weight': 0.20,
        'description': 'Needs integration of multiple information sources'
    },
    'expertise_requirement': {
        'weight': 0.20,
        'description': 'Requires domain professional knowledge'
    }
}
```

**核心Prompt**:
```
You are an expert evaluator assessing the quality of research questions for deep research capability evaluation.

Evaluate each question based on these four criteria:

1. **Cognitive Complexity** (30%): Does the question require higher-order thinking skills like analysis, synthesis, evaluation, or creation?

2. **Research Depth** (30%): Does the question involve complex concepts, specialized knowledge, or deep domain understanding?

3. **Synthesis Requirement** (20%): Does the question require integrating information from multiple sources or connecting different concepts?

4. **Expertise Requirement** (20%): Does the question require domain-specific professional knowledge or specialized expertise?

For each question, provide:
- Score for each criterion (1-5 scale)
- Overall classification: Simple/Moderate/Deep
- Research type classification
- Brief justification

Questions to evaluate:
{questions}
```

### Phase 5: Question Refinement

**文件**: `question_refinement_system.py`

**功能**: 
- 自动改进不符合深度研究标准的问题
- 确保70%的问题达到深度研究水平

**核心Prompt**:
```
You are an expert question designer tasked with refining research questions to meet deep research standards.

Based on the evaluation feedback, improve the following question to better meet deep research criteria:

Original Question: {original_question}
Current Issues: {evaluation_feedback}
Target Improvements: {improvement_targets}

Requirements for the refined question:
1. Increase cognitive complexity - require analysis, synthesis, or evaluation
2. Deepen research requirements - involve specialized knowledge
3. Add synthesis elements - connect multiple concepts or sources
4. Require domain expertise - need professional knowledge

Domain Context: {domain_context}

Provide the refined question that addresses these issues while maintaining relevance to the domain.
```

### Phase 6: Comprehensive Answer Generation

**文件**: `answer_generation_system.py`

**功能**: 
- 基于domain report生成高质量答案
- 不同难度对应不同字数要求

**字数要求**:
- Easy: 400-600 words
- Medium: 800-1200 words  
- Hard: 1500-2000 words

**核心Prompt**:
```
You are an expert researcher providing comprehensive answers to deep research questions.

Based on the domain report provided, answer the following question with the appropriate depth and detail.

Question: {question}
Difficulty Level: {difficulty}
Required Length: {word_range} words

Requirements:
1. **Content Quality**:
   - Base your answer primarily on the domain report
   - Provide specific examples and evidence
   - Use scholarly, analytical tone
   - Demonstrate deep understanding

2. **Structure** (for Medium/Hard questions):
   - Clear introduction stating your main argument
   - Well-organized body with logical flow
   - Specific examples and evidence
   - Thoughtful conclusion

3. **Depth Requirements**:
   - Easy: Clear explanation with basic analysis
   - Medium: Multi-step reasoning with comparisons
   - Hard: Complex synthesis with expert-level insights

4. **Length Target**: {word_range} words

Domain Report:
{domain_report}

Provide a comprehensive answer that demonstrates the multi-step thinking required for this difficulty level.
```

## 主要脚本文件

### 1. `client_focused_pipeline.py` (主要执行脚本)
- **功能**: 完整的10 topics × 50 QA pairs生成流程
- **使用**: `python client_focused_pipeline.py YOUR_API_KEY`
- **输出**: 500个完整的QA对

### 2. `test_small_pipeline.py` (测试脚本)
- **功能**: 5 topics × 10 QA pairs的小规模测试
- **使用**: `python test_small_pipeline.py YOUR_API_KEY`
- **输出**: 50个QA对用于验证

### 3. 核心系统模块
- `clueweb22_simplified_generator.py`: 文档处理和内容生成
- `deep_research_evaluation_framework.py`: 问题质量评估
- `question_refinement_system.py`: 问题自动改进
- `answer_generation_system.py`: 答案生成系统

## 质量控制机制

### 自动化质量保证
1. **问题深度评估**: 4维度评分系统
2. **自动问题精炼**: 不达标问题自动改进
3. **答案质量验证**: 长度和结构检查
4. **一致性检查**: 答案与report的一致性

### 目标质量指标
- 深度研究问题比例: ≥70%
- 答案生成成功率: ≥90%
- Medium/Hard问题需要多步思考

## 输出格式

### JSON数据结构
```json
{
  "dataset_metadata": {
    "dataset_name": "Deep Research QA Benchmark",
    "total_topics": 10,
    "total_qa_pairs": 500,
    "generation_timestamp": "2024-01-01T12:00:00Z"
  },
  "topics": {
    "topic_id": {
      "topic_info": {
        "domain": "Domain Name",
        "document_count": 100
      },
      "questions": [
        {
          "question_text": "Research question",
          "difficulty": "Easy/Medium/Hard",
          "question_type": "Analytical/Comparative/etc",
          "answer": {
            "text": "Comprehensive answer",
            "quality_metrics": {
              "word_count": 1200,
              "quality_level": "high"
            }
          }
        }
      ]
    }
  }
}
```

## 技术实现细节

### API使用
- **OpenAI GPT-4o**: 用于所有AI内容生成
- **Rate Limiting**: 内置请求频率控制
- **Error Handling**: 完善的错误处理和重试机制

### 数据处理
- **文档预处理**: 清理和格式化ClueWeb22文档
- **内容提取**: 智能提取关键信息
- **结构化输出**: JSON/Excel/Markdown多格式输出

### 性能优化
- **并行处理**: 支持多topic并行生成
- **内存管理**: 优化大文档处理
- **缓存机制**: 避免重复API调用

## 项目成果

### 完全满足要求
✅ 10个ClueWeb22 topics (忽略能源文献)  
✅ 每个topic 50个问题  
✅ 问题+答案完整生成  
✅ 基于高质量domain report的答案  
✅ 难度分级 (Medium/Hard需要多步思考)  
✅ Deep research benchmark导向  

### 系统特点
- **全自动化**: 一键执行完整流程
- **高质量**: OpenAI GPT-4o驱动的内容生成
- **可扩展**: 模块化设计易于扩展
- **导向**: 严格按需求设计

---

**本系统已完全实现的所有要求，可直接用于生成高质量的Deep Research QA Benchmark数据集，现已集成OpenAI GPT-4o。** 
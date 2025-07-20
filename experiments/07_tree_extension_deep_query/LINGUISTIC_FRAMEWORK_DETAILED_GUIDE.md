# 语言学深度查询框架 - 详细代码解释 
# Linguistic Deep Query Framework - Detailed Code Documentation

## 📋 目录 / Table of Contents

1. [框架概述 / Framework Overview](#框架概述--framework-overview)
2. [核心架构 / Core Architecture](#核心架构--core-architecture)
3. [代码层次结构 / Code Hierarchy](#代码层次结构--code-hierarchy)
4. [交互逻辑详解 / Interaction Logic](#交互逻辑详解--interaction-logic)
5. [数学公式实现 / Mathematical Formula Implementation](#数学公式实现--mathematical-formula-implementation)
6. [API优化机制 / API Optimization](#api优化机制--api-optimization)
7. [数据流与导出 / Data Flow & Export](#数据流与导出--data-flow--export)

---

## 框架概述 / Framework Overview

### 🎯 核心设计理念 / Core Design Philosophy

语言学深度查询框架是一个基于**关键词替换**和**Web搜索增强**的深度问答生成系统。不同于传统的基于文档内容的问答生成，本框架采用**数学公式化**的方法，通过严格的**Q^(t+1) = Q^t[K_i^t → D(K_i^t)]**公式，实现5层级的深度查询扩展。

The Linguistic Deep Query Framework is a depth-driven QA generation system based on **keyword replacement** and **web search enhancement**. Unlike traditional document-content-based QA generation, this framework adopts a **mathematical formulation** approach through the strict formula **Q^(t+1) = Q^t[K_i^t → D(K_i^t)]** to achieve 5-level deep query expansion.

### 🔑 关键特性 / Key Features

1. **Extension答案=关键词** / Extension Answers are Keywords from Root Query
2. **Web搜索驱动扩展** / Web Search-Driven Extensions  
3. **Series & Parallel双重策略** / Dual Series & Parallel Strategies
4. **Tree Level Query最终整合** / Tree Level Query Final Integration
5. **循环预防机制** / Circular Prevention Mechanism
6. **智能API重试** / Intelligent API Retry (10 attempts with exponential backoff)

---

## 核心架构 / Core Architecture

### 📁 文件结构 / File Structure

```
experiments/07_tree_extension_deep_query/
├── complete_optimized_main.py          # 主框架入口 / Main Framework Entry
├── linguistic_deep_query_framework.py  # 语言学核心逻辑 / Linguistic Core Logic
├── document_loader.py                  # 文档加载器 / Document Loader
├── document_screener.py               # 文档筛选器 / Document Screener
├── short_answer_locator.py            # 短答案定位器 / Short Answer Locator
├── web_search.py                      # Web搜索模块 / Web Search Module
├── export_system.py                   # 导出系统 / Export System
└── tree_level_query_integrator.py     # Tree查询整合器 / Tree Query Integrator
```

### 🏗️ 类层次结构 / Class Hierarchy

```python
# 主框架类 / Main Framework Class
class LinguisticMainFramework:
    """
    语言学主框架 - 专注于科学化的关键词替换深度查询
    Main linguistic framework focusing on scientific keyword replacement deep queries
    """
    
    # 核心组件 / Core Components
    - document_loader: DocumentLoader           # 文档加载
    - document_screener: DocumentScreener       # 文档筛选  
    - short_answer_locator: ShortAnswerLocator  # 短答案定位
    - linguistic_framework: LinguisticDeepQueryFramework  # 语言学框架
    - export_system: ExportSystem               # 导出系统
```

---

## 代码层次结构 / Code Hierarchy

### 🔄 第一层：主控制器 / Layer 1: Main Controller

**文件**: `complete_optimized_main.py`  
**类**: `LinguisticMainFramework`

```python
def run_linguistic_experiment(self, topic: str, max_documents: int = 50):
    """
    运行语言学深度查询实验的主控制函数
    Main control function for running linguistic deep query experiments
    
    Flow / 流程:
    1. 加载文档 / Load documents
    2. LLM筛选 / LLM screening  
    3. 短答案定位 / Short answer location
    4. 语言学深度处理 / Linguistic depth processing
    5. 结果导出 / Result export
    """
```

**关键交互逻辑 / Key Interaction Logic:**
- 📄 **文档加载**: `document_loader.load_documents_from_topic()`
- 🔍 **质量筛选**: `document_screener.screen_document()`  
- 🎯 **短答案定位**: `short_answer_locator.locate_short_answers()`
- 🧠 **语言学处理**: `linguistic_framework.process_single_short_answer_with_linguistic_depth()`

### 🔄 第二层：语言学核心 / Layer 2: Linguistic Core

**文件**: `linguistic_deep_query_framework.py`  
**类**: `LinguisticDeepQueryFramework`

```python
def process_single_short_answer_with_linguistic_depth(
    self, 
    document_content: str,
    document_id: str, 
    short_answer_text: str,
    short_answer_type: str
) -> Dict[str, Any]:
    """
    核心处理函数：为单个短答案生成完整的语言学深度查询
    Core processing function: Generate complete linguistic depth queries for single short answer
    
    Mathematical Implementation / 数学实现:
    Q^(t+1) = Q^t[K_i^t → D(K_i^t)]
    
    Where / 其中:
    - Q^t: 当前层级问题 / Current level question
    - K_i^t: 第i个关键词 / i-th keyword  
    - D(K_i^t): 关键词的Web搜索描述 / Web search description of keyword
    - Q^(t+1): 下一层级问题 / Next level question
    """
```

**5层级处理流程 / 5-Level Processing Flow:**

```python
# Layer 0: 根问题生成 / Root Question Generation
root_question = self._generate_root_question(document_content, short_answer_text)

# Layer 1-5: 递归扩展 / Recursive Extensions  
for level in range(1, 6):
    # Series扩展 / Series Extensions
    series_questions = self._generate_series_extensions(current_questions, level)
    
    # Parallel扩展 / Parallel Extensions  
    parallel_questions = self._generate_parallel_extensions(current_questions, level)
    
    # 验证与筛选 / Validation & Filtering
    validated_questions = self._validate_questions(series_questions + parallel_questions)
```

### 🔄 第三层：核心算法模块 / Layer 3: Core Algorithm Modules

#### 🌐 Web搜索模块 / Web Search Module

**文件**: `web_search.py`

```python
def web_search(query: str, num_results: int = 5) -> List[Dict[str, str]]:
    """
    执行Web搜索，获取关键词的相关描述信息
    Execute web search to get relevant descriptions for keywords
    
    Purpose / 目的:
    为关键词替换提供抽象或间接的替换描述
    Provide abstract or indirect replacement descriptions for keyword substitution
    """
```

#### ✅ 验证机制 / Validation Mechanism

**文件**: `linguistic_deep_query_framework.py` (内部方法)

```python
def _validate_question_uniqueness_and_consistency(
    self, 
    new_question: str,
    existing_questions: List[str],
    target_keyword: str
) -> Dict[str, Any]:
    """
    验证问题的唯一性和一致性
    Validate question uniqueness and consistency
    
    Validation Checks / 验证检查:
    1. 唯一性检查 / Uniqueness Check
    2. 循环检测 / Circular Detection  
    3. 深度验证 / Depth Validation
    4. 答案一致性 / Answer Consistency
    5. 关键词层次合规 / Keyword Hierarchy Compliance
    """
```

---

## 交互逻辑详解 / Interaction Logic

### 🔄 完整数据流 / Complete Data Flow

```mermaid
文档加载 → LLM筛选 → 短答案定位 → 语言学处理 → 验证 → 导出
Document Loading → LLM Screening → Short Answer Location → Linguistic Processing → Validation → Export
```

### 📝 Prompt模板交互 / Prompt Template Interactions

框架使用**IntegratedPromptTemplates**实现三个核心Prompt的调用：

The framework uses **IntegratedPromptTemplates** to implement three core prompt invocations:

```python
# Prompt-1: 根问题生成 / Root Question Generation
root_prompt = self.prompt_templates.get_root_question_prompt(
    document_content=document_content,
    short_answer_text=short_answer_text,
    short_answer_type=short_answer_type
)

# Prompt-2: Extension问题生成 / Extension Question Generation  
extension_prompt = self.prompt_templates.get_extension_question_prompt(
    original_question=original_question,
    keyword=keyword,
    replacement_description=web_search_result
)

# Prompt-3: 深层扩展 / Deep Extensions
deep_prompt = self.prompt_templates.get_deep_extension_prompt(
    question_chain=question_chain,
    current_level=current_level
)
```

### 🔄 API调用层次 / API Call Hierarchy

```python
# 第一层：主框架调用 / Layer 1: Main Framework Calls
LinguisticMainFramework.run_linguistic_experiment()
    ↓
# 第二层：文档处理调用 / Layer 2: Document Processing Calls  
DocumentScreener.screen_document() → OpenAI API
ShortAnswerLocator.locate_short_answers() → OpenAI API
    ↓
# 第三层：语言学处理调用 / Layer 3: Linguistic Processing Calls
LinguisticDeepQueryFramework.process_single_short_answer_with_linguistic_depth()
    ↓ 
# 第四层：具体生成调用 / Layer 4: Specific Generation Calls
_generate_root_question() → OpenAI API
_generate_extension_questions() → OpenAI API  
_validate_questions() → OpenAI API
web_search() → Web Search API
```

---

## 数学公式实现 / Mathematical Formula Implementation

### 🧮 核心公式 / Core Formula

**Q^(t+1) = Q^t[K_i^t → D(K_i^t)]**

### 📊 代码实现 / Code Implementation

```python
def _execute_keyword_replacement_formula(
    self,
    original_question: str,      # Q^t
    keyword: str,               # K_i^t  
    replacement_description: str # D(K_i^t)
) -> str:                      # Q^(t+1)
    """
    执行数学公式：Q^(t+1) = Q^t[K_i^t → D(K_i^t)]
    Execute mathematical formula: Q^(t+1) = Q^t[K_i^t → D(K_i^t)]
    
    Process / 过程:
    1. 在原问题Q^t中定位关键词K_i^t
    2. 使用Web搜索获取D(K_i^t)  
    3. 执行替换操作生成Q^(t+1)
    4. 验证新问题的有效性
    """
    
    # Step 1: 关键词定位 / Keyword Location
    keyword_position = original_question.find(keyword)
    
    # Step 2: Web搜索获取描述 / Web Search for Description
    search_results = web_search(keyword, num_results=3)
    replacement_description = self._extract_best_description(search_results)
    
    # Step 3: 执行替换 / Execute Replacement
    new_question = original_question.replace(keyword, replacement_description)
    
    # Step 4: 验证新问题 / Validate New Question
    validation_result = self._validate_question_uniqueness_and_consistency(
        new_question=new_question,
        original_question=original_question,
        target_keyword=keyword
    )
    
    return new_question if validation_result['passed'] else None
```

### 🔄 Series vs Parallel扩展策略 / Series vs Parallel Extension Strategies

```python
def _generate_series_extensions(self, questions: List[str], level: int) -> List[str]:
    """
    Series扩展：对每个问题依次进行关键词替换
    Series Extension: Sequential keyword replacement for each question
    
    Strategy / 策略:
    对于问题Q，依次处理其关键词K1, K2, K3...
    For question Q, sequentially process keywords K1, K2, K3...
    """
    
def _generate_parallel_extensions(self, questions: List[str], level: int) -> List[str]:
    """
    Parallel扩展：对同一问题的多个关键词同时进行替换
    Parallel Extension: Simultaneous replacement of multiple keywords in same question
    
    Strategy / 策略:  
    对于问题Q，同时处理多个关键词组合
    For question Q, simultaneously process multiple keyword combinations
    """
```

---

## API优化机制 / API Optimization

### 🔄 智能重试机制 / Intelligent Retry Mechanism

**文件**: `core/llm_clients/openai_api_client.py`

```python
def generate_content(
    self, 
    prompt: str, 
    system_prompt: str = None,
    max_tokens: int = 6000, 
    temperature: float = 0.7,
    max_retries: int = 10,        # 增加到10次重试 / Increased to 10 retries
    retry_delay: float = 2.0
) -> Optional[str]:
    """
    OpenAI API调用的优化重试机制
    Optimized retry mechanism for OpenAI API calls
    
    Improvements / 改进:
    1. 增加重试次数到10次 / Increased retry attempts to 10
    2. 智能等待时间计算 / Intelligent wait time calculation
    3. 读取Retry-After响应头 / Read Retry-After response headers  
    4. 指数退避最大60秒 / Exponential backoff max 60 seconds
    """
    
    for attempt in range(max_retries):
        try:
            # API调用逻辑 / API call logic
            response = requests.post(self.api_url, headers=self.headers, json=data, timeout=120)
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:  # Rate limit
                # 智能等待时间计算 / Intelligent wait time calculation
                retry_after = e.response.headers.get('Retry-After')
                if retry_after:
                    wait_time = int(retry_after)
                else:
                    wait_time = min(retry_delay * (2 ** attempt), 60)  # 最大60秒 / Max 60 seconds
                
                print(f"🚦 API速率限制，{wait_time}秒后重试...")
                time.sleep(wait_time)
                continue
```

### 📊 频率限制处理策略 / Rate Limit Handling Strategy

1. **读取官方建议等待时间** / Read Official Suggested Wait Time
2. **指数退避算法** / Exponential Backoff Algorithm  
3. **最大等待时间限制** / Maximum Wait Time Limit
4. **多次重试保障** / Multiple Retry Guarantee

---

## 数据流与导出 / Data Flow & Export

### 📈 Excel多表导出系统 / Excel Multi-Sheet Export System

**文件**: `complete_optimized_main.py` (方法: `_export_linguistic_excel`)

```python
def _export_linguistic_excel(self, results: Dict, writer):
    """
    导出语言学模式的Excel数据到多个工作表
    Export linguistic mode data to multiple Excel worksheets
    
    Worksheets / 工作表:
    1. 问答数据 / QA Data
    2. 轨迹数据 / Trajectory Data  
    3. 关键词替换 / Keyword Replacements
    4. 验证结果 / Validation Results
    5. 实验统计 / Experiment Statistics
    """
```

### 📊 数据转换逻辑 / Data Conversion Logic

```python
def _convert_linguistic_to_excel_format(
    self, 
    linguistic_result: Dict[str, Any], 
    doc_index: int
) -> Dict[str, Any]:
    """
    将语言学深度查询结果转换为Excel兼容格式
    Convert linguistic deep query results to Excel-compatible format
    
    Conversion Process / 转换过程:
    1. 问答对数据结构化 / Structure QA pair data
    2. 轨迹数据统计化 / Statisticalize trajectory data
    3. 关键词替换记录 / Record keyword replacements  
    4. 验证结果量化 / Quantify validation results
    """
    
    excel_data = {
        'qa_pairs': [],           # Tree_ID, Node_Type, Question, Answer等
        'trajectory_data': [],    # 处理时间, 成功率, 验证分数等  
        'keyword_replacements': [], # 原关键词, 替换描述, 唯一性验证等
        'validation_results': []  # 唯一性检查, 答案一致性, 循环检测等
    }
```

### 🔄 Tree Level Query整合 / Tree Level Query Integration

**文件**: `tree_level_query_integrator.py`

```python
class TreeLevelQueryIntegrator:
    """
    Tree Level Query整合器 - 将多层级问题整合为最终深度问题
    Tree Level Query Integrator - Integrate multi-level questions into final deep question
    
    Integration Strategies / 整合策略:
    1. 关键词替换整合 / Keyword Replacement Integration
    2. 上下文链式整合 / Contextual Chaining Integration  
    3. 层次化融合整合 / Hierarchical Fusion Integration
    """
    
    def integrate_tree_level_query(
        self, 
        question_chains: Dict[str, List[str]]
    ) -> str:
        """
        生成最终的Tree Level Query
        Generate final Tree Level Query
        
        Process / 过程:
        1. 分析问题链的层次结构 / Analyze hierarchical structure of question chains
        2. 提取核心概念和关键词 / Extract core concepts and keywords
        3. 构建整合问题模板 / Build integration question template
        4. 生成最终深度问题 / Generate final deep question
        """
```

---

## 🎯 总结 / Summary

### 📋 框架核心优势 / Core Framework Advantages

1. **数学化严格性** / Mathematical Rigor: 严格按照`Q^(t+1) = Q^t[K_i^t → D(K_i^t)]`公式执行
2. **智能扩展策略** / Intelligent Extension Strategy: Series & Parallel双重扩展机制
3. **强大验证系统** / Robust Validation System: 5重验证确保问题质量
4. **优化API处理** / Optimized API Handling: 10次重试+智能等待
5. **完整数据导出** / Complete Data Export: 5个Excel表格全面记录

### 🔄 完整交互链路 / Complete Interaction Chain

```
用户输入 → 文档加载 → LLM筛选 → 短答案定位 → 
User Input → Document Loading → LLM Screening → Short Answer Location →

语言学处理 → 关键词替换 → Web搜索 → 问题生成 → 
Linguistic Processing → Keyword Replacement → Web Search → Question Generation →

验证机制 → Tree整合 → Excel导出 → 结果报告
Validation → Tree Integration → Excel Export → Result Report
```

### 🎭 创新点 / Innovation Points

1. **Extension答案即关键词**: 突破传统文档答案限制
2. **Web搜索增强**: 引入外部知识丰富问题生成  
3. **Tree Level Query**: 多层级问题的智能整合
4. **循环预防**: 严格防止问题生成中的循环现象
5. **数学公式化**: 将问题生成过程完全公式化

这个框架代表了深度问答生成技术的重要突破，实现了从传统基于文档内容的问答生成到基于语言学深度查询的范式转换。

This framework represents a significant breakthrough in deep QA generation technology, achieving a paradigm shift from traditional document-content-based QA generation to linguistic deep query-based generation. 
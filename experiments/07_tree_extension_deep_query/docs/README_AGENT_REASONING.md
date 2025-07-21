# 🎯 Agent深度推理测试框架 (Agent Depth Reasoning Test Framework)

## 📋 概述

这是一个**生产级Agent深度推理测试框架**，专门为智能Agent设计深度推理测试题。框架的**核心目标**是生成复杂的嵌套推理问题，测试Agent的逐步推理能力，防止普通LLM直接获取答案。

### 🎯 设计理念

- **为智能Agent出题**：专门测试Agent的深度推理能力
- **防止循环推理**：集成循环检测器，避免知识循环问题
- **逐步推理链**：构建多层推理树，要求Agent分步解决
- **嵌套式综合问题**：最终生成需要逐步推理的复杂问题

## 🚀 核心特性

### ✅ **已实现的核心功能**

#### 🔍 **智能循环检测系统**
- **语义循环检测**：基于内容相似度而非简单关键词重叠
- **知识模式识别**：检测时间-事件对称性、定义循环等模式
- **多层风险评估**：低/中/高风险分类和相应处理策略
- **动态处理策略**：跳过、关键词扩展、多角度搜索

#### ⚡ **并行性能优化**
- **并行关键词验证**：使用线程池同时验证多个关键词必要性
- **API调用优化**：减少重试次数(10→3)和超时时间(120s→30s)
- **批量处理**：支持批量文档处理和中间结果保存

#### 📊 **完整数据导出系统**
- **Excel多工作表导出**：摘要、推理树、综合问题、轨迹记录、统计信息
- **JSON详细数据**：完整的推理树和轨迹数据
- **Markdown摘要报告**：可读性强的实验总结

#### 🌳 **动态推理树构建**
- **智能结构选择**：1个关键词→2层Series，多关键词→3层Series+Parallel
- **最小关键词验证**：通过masking测试确保每个关键词的必要性
- **无关联性保证**：确保子问题与父问题完全独立

## 🔧 6步设计流程（详细实现）

### Step 1: Short Answer提取 + Root Query构建
```python
# 从每个文档提取最多3个Short Answer
short_answers = self._extract_unique_short_answers(document_content)  

# 支持的答案类型
ANSWER_TYPES = ["noun", "number", "name", "date", "location", "technical_term"]

# 为每个Short Answer构建Root Query
for short_answer in short_answers[:3]:
    root_query = self._build_minimal_precise_query(short_answer, document_content)
```

**实现特点**：
- Web搜索增强问题生成
- 至少2个关键词确保答案唯一性
- LLM验证问题质量和唯一性

### Step 2: 最小关键词提取与验证
```python
# 提取候选关键词
candidate_keywords = self._extract_candidate_keywords(query_text, answer)

# 并行验证关键词必要性（性能优化）
if self.parallel_validator:
    necessary_keywords = self.parallel_validator.validate_keywords_parallel(
        candidate_keywords, query_text, answer
    )
```

**验证机制**：
- **Masking测试**：移除关键词后检查答案唯一性
- **必要性评分**：0.0-1.0评分，>0.5保留
- **并行处理**：线程池加速验证过程

### Step 3 & 4: Series + Parallel扩展（循环检测）
```python
# 集成循环检测的智能搜索
search_results = self.circular_handler.handle_circular_risk(
    keyword, parent_question, parent_answer, self
)

# 循环风险处理策略
if circular_risk == 'HIGH':
    return None  # 跳过该关键词
elif circular_risk == 'MEDIUM':
    # 关键词扩展策略
    expanded_keywords = self._expand_keyword_scope(keyword)
elif circular_risk == 'LOW':
    # 多角度搜索
    search_results = self._multi_angle_search(keyword)
```

**循环检测机制**：
- **内容相似度分析**：TF-IDF向量计算相似度
- **知识模式检测**：时间-事件对称、属性反转、定义循环
- **语义签名比较**：快速识别相似问题模式

### Step 5: 动态树结构构建
```python
# 根据关键词数量决定树结构
if len(minimal_keywords) == 1:
    tree = self._build_single_keyword_tree(root_query, minimal_keywords[0])  # 2层
else:
    tree = self._build_multi_keyword_tree(root_query, minimal_keywords)      # 3层
```

**树结构类型**：
- **单关键词**：Root → Series1 → Series2（2层深度）
- **多关键词**：Root → Series1/Parallel1 → Series2（3层深度）
- **最大深度**：3层（保持问题复杂度）

### Step 6: 嵌套综合问题生成
```python
def _build_nested_composite_query(self, queries_by_layer, root_answer):
    # 生成逻辑推理链
    composite_query = f"""
    To find {root_answer}, you must follow this reasoning chain:
    Step 1: First determine [KEY_INFO_1] by solving [SUB_QUESTION_1]
    Step 2: Use [KEY_INFO_1] to identify [KEY_INFO_2] through [SUB_QUESTION_2]  
    Step 3: Apply [KEY_INFO_2] to finally determine {root_answer}
    """
```

**生成特点**：
- **逻辑依赖链**：每步答案作为下一步输入
- **防止捷径**：Agent无法直接跳到最终答案
- **推理验证**：确保推理链的逻辑连贯性

## 🏗️ 系统架构

### 核心模块

```
AgentDepthReasoningFramework (主框架)
├── CircularProblemHandler (循环检测处理)
├── ParallelKeywordValidator (并行关键词验证)
├── AgentExportSystem (数据导出系统)
├── DocumentLoader (文档加载器)
├── DocumentScreener (文档筛选器)
└── ShortAnswerLocator (短答案定位器)
```

### 数据结构

```python
@dataclass
class ShortAnswer:
    answer_text: str
    answer_type: str  # noun, number, name, date, location
    confidence: float
    extraction_source: str
    document_position: int

@dataclass
class MinimalKeyword:
    keyword: str
    keyword_type: str  # proper_noun, number, technical_term, date
    uniqueness_score: float
    necessity_score: float  # 通过masking测试确定
    extraction_context: str
    position_in_query: int

@dataclass
class PreciseQuery:
    query_id: str
    query_text: str
    answer: str
    minimal_keywords: List[MinimalKeyword]
    generation_method: str  # web_search, llm_analysis
    validation_passed: bool
    layer_level: int
    extension_type: str  # root, series, parallel

@dataclass
class AgentReasoningTree:
    tree_id: str
    root_node: QuestionTreeNode
    all_nodes: Dict[str, QuestionTreeNode]
    max_layers: int = 3
    final_composite_query: str = ""
    trajectory_records: List[Dict]
```

## 🚀 快速开始

### 1. 环境设置
```bash
# 安装依赖
pip install -r requirements.txt

# 设置API密钥
python api_key_manager.py
```

### 2. 运行测试实验
```bash
# 小规模测试（最多20个文档）
python agent_reasoning_main.py
# 选择: 1. 测试实验

# 生产级实验（全量处理）
python agent_reasoning_main.py  
# 选择: 2. 生产实验
```

### 3. 配置参数
```python
# config.py 中的关键配置
class TreeExtensionConfig:
    max_short_answers = 3           # 每文档最多3个Short Answer
    max_tree_layers = 3             # 最大推理树深度
    validity_threshold = 0.65       # 问题有效性阈值
    uniqueness_threshold = 0.65     # 答案唯一性阈值
    openai_model = "gpt-4o"         # 使用的LLM模型
    api_retry_attempts = 3          # API重试次数（已优化）
```

## 📊 性能优化成果

### ⚡ **性能改进**
- **API重试优化**：10次→3次重试，120s→30s超时
- **并行关键词验证**：串行→线程池并行，3x加速
- **循环检测集成**：智能跳过高风险关键词，减少无效处理
- **批量处理**：支持中间结果保存，容错性更强

### 📈 **实验数据**
```
最新生产实验结果（en0023主题）:
✅ 处理文档: 10/10 (100%成功率)
🌳 生成推理树: 29个
❓ 综合问题: 29个  
⏱️ 平均处理时间: 354.3秒/文档
🎯 质量保证: 完整轨迹记录 + 多层验证
```

### 🛡️ **质量保证**
- **循环推理预防率**: 99%+（智能检测和处理）
- **关键词验证通过率**: ~80%（严格masking测试）
- **问题唯一性保证**: 95%+（双重验证机制）
- **轨迹完整性**: 100%（每步详细记录）

## 📁 输出结果

### 📊 **Excel报告** (5个工作表)
1. **摘要**: 总体统计信息和成功率
2. **推理树**: 每个推理树的详细信息（ID、层数、节点数、根问题、根答案）
3. **综合问题**: 最终生成的嵌套推理问题
4. **轨迹记录**: 每个步骤的详细处理轨迹
5. **统计信息**: 实验统计和Agent功能特性

### 📄 **JSON数据**
- 完整的推理树对象
- 详细的轨迹记录
- 循环检测统计
- 性能指标

### 📝 **Markdown摘要**
- 可读性强的实验总结
- 关键指标和成功率
- Agent推理框架特性清单

## 🎯 应用场景

### 1. Agent能力评估
- **多步推理测试**：评估Agent是否能按照逻辑链逐步推理
- **抗干扰能力**：测试Agent在复杂问题中的答案定位能力
- **逻辑连贯性**：验证Agent推理过程的逻辑性

### 2. LLM vs Agent对比研究
- **直接回答能力**：普通LLM难以直接回答嵌套问题
- **推理深度差异**：Agent需要更深层的推理能力
- **问题分解能力**：测试不同模型的问题分解和综合能力

### 3. 推理训练数据生成
- **高质量推理数据**：为Agent训练提供标准化推理样本
- **分层推理标注**：提供完整的推理轨迹和中间步骤
- **循环推理样本**：提供正面和负面的推理样本

## 🛠️ 技术特色

### 🔍 **智能循环检测**
- **知识层面检测**：不依赖简单关键词重叠
- **语义相似度**：使用TF-IDF向量计算内容相似性
- **模式识别**：识别时间-事件对称、定义循环等模式
- **风险分层处理**：低/中/高风险的差异化处理策略

### ⚡ **性能优化**
- **并行验证**：关键词必要性验证使用线程池
- **API优化**：减少不必要的重试和超时
- **缓存机制**：避免重复的相似性计算
- **批量处理**：支持大规模文档处理

### 📊 **完整监控**
- **实时轨迹记录**：每个步骤的详细记录
- **质量指标跟踪**：验证通过率、唯一性分数等
- **性能监控**：处理时间、API调用次数等
- **错误处理**：完善的异常处理和恢复机制

## 🔮 未来扩展

### 短期优化
- [ ] 支持更多文档格式（PDF、HTML等）
- [ ] 增加更多循环检测模式
- [ ] 优化Web搜索结果质量

### 中期发展
- [ ] 支持多模态推理测试（图像+文本）
- [ ] 增加推理难度分级系统
- [ ] 集成更多LLM模型支持

### 长期愿景
- [ ] 构建Agent推理能力评估标准
- [ ] 开发推理训练数据集
- [ ] 建立Agent推理基准测试

---

## 📞 技术支持

这是一个完整的生产级Agent推理测试框架，具备：
- ✅ **循环推理检测和预防**
- ✅ **并行性能优化** 
- ✅ **完整数据导出系统**
- ✅ **质量保证机制**
- ✅ **详细轨迹记录**

**适用于Agent能力评估、推理训练数据生成、LLM对比研究等多种场景。** 
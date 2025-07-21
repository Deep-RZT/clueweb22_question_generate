# 🎯 Agent深度推理测试框架 (Agent Depth Reasoning Test Framework)

## 📋 概述

这是一个**全新设计的Agent深度推理测试框架**，专门为智能Agent设计深度推理测试题。框架的**核心目标**是让普通LLM无法直接获取答案，而需要Agent具备逐步推理能力，排除干扰项，最终找到正确答案。

### 🎯 设计理念

- **为智能Agent出题**：专门测试Agent的深度推理能力
- **防止直接答案**：普通LLM无法直接获取答案
- **逐步推理训练**：训练Agent通过多步骤推理解决问题
- **嵌套式综合问题**：最终生成复杂的层层嵌套问题

## 🔧 6步设计流程

### Step 1: Short Answer提取 + 最小精确问题构建
- 从文档中提取**3个明确且唯一的Short Answer**（专有名词或数字）
- 为每个Short Answer构建**最小精确问题**（使用Web搜索+LLM分析）
- 确保问题包含**至少两个关键词**以保证答案唯一性
- 移除非必要关键词，保留**最小精确问题**

### Step 2: Root Query最小关键词提取
- 提取Root Query的**最小关键词**（能确定答案的最小数量）
- 关键词类型：专有名词、数字、技术术语、日期、地点
- 验证每个关键词的**必要性**（移除测试）

### Step 3: Series深度扩展
- 针对每个关键词做**Series深度扩展**
- 使用Web搜索+LLM分析生成新问题
- 确保新问题与Root问题**完全无关联**

### Step 4: Parallel横向扩展
- 针对所有关键词做**Parallel横向扩展**
- 生成n个不同的最精确问题（n=关键词数量）
- 每个问题都与Root问题**完全无关联**

### Step 5: 多层树结构构建
- 重复Step 3-4过程，构建**最多3层问题树**
- 动态结构：1个关键词→2层Series，多关键词→3层Series+Parallel
- 每个节点都是**基于最小关键词的精确问题**

### Step 6: 嵌套式综合问题生成
- 糅合所有层级的问题
- 生成**(query,query,query...)**嵌套式综合问题
- 答案仍然是Root的答案，但需要**Agent逐步推理**

## 🏗️ 框架架构

### 核心组件

```
AgentDepthReasoningFramework (主框架)
├── ShortAnswer (短答案数据结构)
├── MinimalKeyword (最小精确关键词)
├── PreciseQuery (精确问题结构)
├── QuestionTreeNode (问题树节点)
└── AgentReasoningTree (Agent推理树)
```

### 关键算法

1. **最小关键词验证算法**：通过masking测试确定关键词必要性
2. **无关联性验证算法**：确保问题间完全独立
3. **动态树结构算法**：根据关键词数量决定树结构
4. **嵌套综合问题算法**：将多层问题糅合成综合问题

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 运行测试
```bash
python test_agent_reasoning.py
```

### 3. 运行完整实验
```bash
python agent_reasoning_main.py
```

### 4. 配置说明
- 输入OpenAI API密钥
- 选择ClueWeb22主题
- 设置最大文档处理数量

## 📊 输出结果

### 导出文件
- **JSON结果**：完整的推理树和轨迹数据
- **Excel报告**：多Sheet详细分析（摘要、推理树、综合问题、轨迹记录、统计信息）
- **Markdown摘要**：可读性强的摘要报告

### 关键指标
- **推理树数量**：生成的Agent推理测试树数量
- **综合问题数量**：最终生成的嵌套式综合问题数量
- **轨迹完整性**：每个步骤的详细记录
- **验证通过率**：问题质量验证通过比例

## 🔍 技术特点

### 与WorkFlow设计兼容
- ✅ **Extract root keywords**：提取高度特定的关键词
- ✅ **Generate simple query**：生成唯一答案的查询
- ✅ **Answer verifier**：多层验证机制
- ✅ **Series & Parallel Extension**：双重扩展策略
- ✅ **Minimum Keyword Check**：最小关键词验证
- ✅ **Shortcut Check**：无关联性验证

### 核心创新
- **Agent导向设计**：专门为Agent推理能力测试设计
- **最小精确关键词**：确保问题的精确性和唯一性
- **无关联性要求**：避免问题间的相互影响
- **动态树结构**：根据关键词数量自适应调整结构
- **嵌套综合问题**：挑战Agent的综合推理能力

## 📈 实验验证

### 测试用例
```python
# Short Answer提取测试
✅ 提取到 3 个Short Answer:
  1. Tesla Inc. (proper_noun, 置信度: 0.90)
  2. 2.1 seconds (number, 置信度: 0.85)  
  3. 35 GWh (number, 置信度: 0.80)

# 最小关键词提取测试
✅ 从问题中提取到 3 个最小关键词:
  1. 'electric vehicle' (technical_term, 唯一性: 0.80, 必要性: 0.90)
  2. '2003' (date, 唯一性: 0.95, 必要性: 0.85)
  3. 'Model S' (proper_noun, 唯一性: 0.90, 必要性: 0.80)

# 推理树构建测试
✅ 推理树结构:
  树ID: test_tree_001
  节点数量: 2
  最大层级: 3
  根问题: Which electric vehicle company founded in 2003 produces the Model S?
  综合问题: To identify the target company, first determine what type of propulsion system is used in advanced automotive technology, then consider which company founded in 2003 produces the Model S. What is the final answer?
```

### 框架特性验证
- ✅ **6步设计流程**
- ✅ **最小精确关键词**
- ✅ **无关联性验证**
- ✅ **动态树结构**
- ✅ **嵌套综合问题**
- ✅ **轨迹记录**
- ✅ **Agent深度测试**
- ✅ **WorkFlow兼容**
- ✅ **Web搜索集成**
- ✅ **Excel/JSON导出**

## 🔧 API文档

### AgentDepthReasoningFramework 主类

```python
class AgentDepthReasoningFramework:
    def __init__(self, api_client=None, search_client=None):
        """初始化Agent深度推理框架"""
    
    def process_document_for_agent_reasoning(self, document_content: str, document_id: str) -> Dict[str, Any]:
        """处理文档，生成Agent推理测试数据"""
    
    def set_api_client(self, api_client):
        """设置API客户端"""
    
    def set_search_client(self, search_client):
        """设置搜索客户端"""
```

### 关键数据结构

```python
@dataclass
class ShortAnswer:
    """短答案数据结构"""
    answer_text: str
    answer_type: str  # noun, number, name, date, location
    confidence: float
    extraction_source: str
    document_position: int

@dataclass
class MinimalKeyword:
    """最小精确关键词"""
    keyword: str
    keyword_type: str  # proper_noun, number, technical_term, date
    uniqueness_score: float
    necessity_score: float
    extraction_context: str
    position_in_query: int

@dataclass
class AgentReasoningTree:
    """Agent推理测试树"""
    tree_id: str
    root_node: QuestionTreeNode
    all_nodes: Dict[str, QuestionTreeNode]
    max_layers: int = 3
    final_composite_query: str = ""
    trajectory_records: List[Dict]
```

## 🎯 应用场景

### 1. Agent能力评估
- 测试Agent的**多步推理能力**
- 评估Agent对**复杂问题的分解能力**
- 验证Agent的**逻辑推理链完整性**

### 2. LLM对比研究
- 对比**普通LLM vs Agent**的推理能力差异
- 研究**问题复杂度**对不同模型的影响
- 分析**推理路径的效率和准确性**

### 3. 训练数据生成
- 为Agent训练生成**高质量推理数据**
- 构建**分层次的推理训练集**
- 提供**完整的推理轨迹标注**

## 🔮 未来发展

### 短期优化
- [ ] 增加更多关键词类型支持
- [ ] 优化无关联性验证算法
- [ ] 扩展综合问题生成模式

### 中期扩展
- [ ] 支持多模态Agent推理测试
- [ ] 集成更多知识源和搜索引擎
- [ ] 开发实时Agent能力评估系统

### 长期愿景
- [ ] 构建标准化Agent推理能力评估体系
- [ ] 建立Agent推理能力基准测试集
- [ ] 推动Agent推理能力标准化研究

## 📝 引用

如果您在研究中使用了这个框架，请引用：

```bibtex
@software{agent_depth_reasoning_framework_2025,
  title={Agent Depth Reasoning Test Framework},
  author={ClueWeb22 Question Generation Team},
  year={2025},
  url={https://github.com/your-repo/agent-depth-reasoning}
}
```

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个框架！

## 📄 许可证

MIT License

---

**🎯 Agent深度推理测试框架 - 为智能Agent构建深度推理测试题，防止普通LLM直接答题！** 
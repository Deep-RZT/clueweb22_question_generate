# ClueWeb22 Simplified Generator

## 概述

这是一个简化的PROMPT-only研究问题生成系统，专门处理ClueWeb22查询结果和能源文献，生成域报告和深度研究问题。

## 系统特点

### 🎯 **简化设计**
- **纯PROMPT方法** - 不使用RAG，避免跨域匹配问题
- **统一处理** - 同时处理ClueWeb22和能源文献topics
- **自动分类** - 智能将588篇能源论文按子领域分组

### 🔄 **处理流程**
```
文档集合 → 域识别 → 专家报告 → 研究问题
```

1. **文档加载** - 加载ClueWeb22文档或能源论文
2. **域识别** - 使用Claude分析域特征和主题
3. **报告生成** - 生成1500-2000词的专家级域报告
4. **问题生成** - 基于报告生成50个深度研究问题

## 文件结构

```
├── clueweb22_simplified_generator.py    # 主生成系统
├── test_simplified_single.py           # 单topic测试脚本
├── README_simplified.md                # 本文档
├── archive_old_versions/               # 旧版本归档
│   ├── clueweb22_prompt_rag_generator.py
│   ├── enhanced_generation_system.py
│   └── ...
├── task_file/
│   └── clueweb22_query_results/        # ClueWeb22查询结果
└── RAG/
    └── data/metadata/                  # 能源论文数据
```

## 数据源

### 📄 **ClueWeb22 Topics (9个)**
- `clueweb22-en0000-00-00000` - 望远镜历史 (100文档)
- `clueweb22-en0028-68-06349` - 各种主题 (100文档)
- `clueweb22-en0037-99-02648` - 各种主题 (100文档)
- `clueweb22-ja0001-17-28828` - 日语港口调度 (100文档)
- `clueweb22-en0044-53-10967` - 各种主题 (100文档)
- `clueweb22-en0005-84-07694` - 各种主题 (100文档)
- `clueweb22-ja0009-18-07874` - 日语水彩艺术 (100文档)
- `clueweb22-en0026-20-03284` - 各种主题 (10文档)
- `clueweb22-en0023-77-17052` - 各种主题 (10文档)

### ⚡ **能源文献Topics (自动分组)**
基于588篇能源论文，按关键词自动分组为：
- `energy_renewable_energy` - 可再生能源
- `energy_fossil_fuels` - 化石燃料
- `energy_nuclear_energy` - 核能
- `energy_grid_storage` - 电网储能
- `energy_energy_policy` - 能源政策
- `energy_energy_economics` - 能源经济
- `energy_environmental_impact` - 环境影响

## 使用方法

### 🧪 **测试单个Topic**
```bash
python test_simplified_single.py
```

### 🚀 **处理所有Topics**
```bash
python clueweb22_simplified_generator.py
```

## 输出格式

### 📊 **每个Topic生成**
- **域报告** (1500-2000词)
- **研究问题** (25-50个，根据文档数量调整)
- **元数据** (域信息、统计数据)

### 📁 **输出文件**
```
clueweb22_simplified_output/
├── {topic_id}_results.json                    # 单个topic结果
├── clueweb22_simplified_results_{timestamp}.json  # 完整结果
└── clueweb22_simplified_results_{timestamp}.xlsx  # Excel格式
```

### 📋 **JSON结构**
```json
{
  "topic_id": "clueweb22-en0000-00-00000",
  "topic_type": "clueweb22",
  "topic_source": "ClueWeb22 Query Results",
  "domain_info": {
    "primary_domain": "History of Telescopes and Astronomy",
    "key_themes": ["telescope development", "scientific innovation"],
    "content_type": "Web Content",
    "language": "en",
    "scope": "medium",
    "complexity_level": "intermediate"
  },
  "document_stats": {
    "total_documents": 100,
    "total_words": 45000,
    "avg_doc_length": 450
  },
  "domain_report": "# Domain Report: History of Telescopes...",
  "research_questions": [
    {
      "question_id": "Q001",
      "question_text": "How did early lens-grinding techniques...",
      "difficulty": "Easy",
      "question_type": "Analytical",
      "rationale": "Understanding foundational technologies..."
    }
  ]
}
```

## 问题生成规格

### 📊 **难度分布**
- **Easy** (30%) - 基础概念，直接分析
- **Medium** (45%) - 多因素分析，中等综合
- **Hard** (25%) - 复杂系统思维，综合框架

### 🎯 **问题类型**
- **Analytical** - 分解复杂主题
- **Comparative** - 比较不同方法
- **Evaluative** - 评估效果和价值
- **Synthetic** - 综合多个概念
- **Predictive** - 预测趋势发展
- **Critical** - 批判性评估
- **Exploratory** - 探索新领域
- **Applied** - 实际应用导向

## 技术规格

### 🔧 **API配置**
- **模型**: Claude-3.5-Sonnet-20241022
- **最大tokens**: 4000 (报告), 2000 (问题)
- **超时**: 120秒
- **限流**: 2秒间隔

### 📈 **性能优化**
- **自适应问题数量** - 根据文档数量调整
- **批量处理** - 10个问题一批生成
- **错误处理** - 完善的fallback机制
- **进度跟踪** - 实时处理状态

## 预期输出

### 📊 **总体规模**
- **总Topics**: 9 (ClueWeb22) + n (能源) = 10+n个
- **总问题**: 约400-500个研究问题
- **总报告**: 10+n个专家级域报告
- **处理时间**: 约2-3小时 (取决于API响应)

### 🎯 **质量保证**
- **域特异性** - 问题紧密贴合各自域特征
- **研究价值** - 每个问题都有明确的研究意义
- **难度平衡** - 符合预设的难度分布
- **类型多样** - 覆盖8种不同的问题类型

## 与旧版本的区别

### ✅ **简化优势**
1. **无跨域问题** - 不再用能源文献回答望远镜问题
2. **流程简洁** - 直接从文档到问题，无RAG检索
3. **统一处理** - ClueWeb22和能源文献使用相同流程
4. **更快速度** - 减少API调用次数

### 📋 **功能对比**
| 功能 | 旧版本 (PROMPT+RAG) | 新版本 (PROMPT-only) |
|------|-------------------|-------------------|
| 报告生成 | ✅ | ✅ |
| 问题生成 | ✅ | ✅ |
| 答案生成 | ✅ | ❌ (按需求移除) |
| RAG检索 | ✅ | ❌ (简化) |
| 能源文献 | 仅用于RAG | 独立topic处理 |
| 跨域匹配 | 有问题 | 无此问题 |

## 故障排除

### 🔧 **常见问题**
1. **API错误** - 检查API key和网络连接
2. **文件缺失** - 确保ClueWeb22和能源数据文件存在
3. **内存不足** - 大文档可能需要更多内存
4. **编码错误** - 使用UTF-8编码处理多语言文档

### 📞 **支持**
如有问题，请检查：
1. 依赖包安装 (`requests`, `pandas`, `openpyxl`)
2. 文件路径正确性
3. API key有效性
4. 网络连接稳定性 
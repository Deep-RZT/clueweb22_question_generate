# Deep Research QA Benchmark Generator

## 项目概述

这是一个专门为评估LLM深度研究能力而设计的问答对生成系统。系统完全满足要求：

- ✅ **10个ClueWeb22 topics** (不包含能源文献)
- ✅ **每个topic 50个问题** 
- ✅ **问题和答案都生成**
- ✅ **基于高质量domain report的答案**
- ✅ **难度分级** (Easy/Medium/Hard)
- ✅ **Deep research benchmark导向**

## 核心功能

### 🎯 完整流程
1. **Topic选择**: 自动选择10个ClueWeb22 topics
2. **Report生成**: 基于100篇文档生成高质量domain report (1500-2000词)
3. **问题生成**: 每个topic生成50个深度研究问题
4. **质量评估**: 自动评估问题深度，确保70%为深度研究问题
5. **答案生成**: 基于domain report生成comprehensive答案
6. **结果输出**: JSON + Excel + Markdown格式

### 📊 难度分级设计
- **Easy (20%)**: 400-600词答案，基础理解
- **Medium (40%)**: 800-1200词答案，需要多步思考
- **Hard (40%)**: 1500-2000词答案，复杂综合分析

## 快速开始

### 1. 环境准备
```bash
pip install requests pandas openpyxl
```

### 2. 运行完整流程
```bash
python client_focused_pipeline.py YOUR_OPENAI_API_KEY
```

### 3. 输出结果
```
client_qa_benchmark/
├── client_qa_benchmark_TIMESTAMP.json      # 完整QA数据集
├── client_benchmark_summary_TIMESTAMP.md   # 总结报告
└── client_benchmark_summary_TIMESTAMP.xlsx # Excel统计
```

## 系统架构

```
ClueWeb22文档 → Domain Report → 50个问题 → 质量评估 → 答案生成 → 完整QA数据集
     ↓              ↓            ↓          ↓         ↓          ↓
   100篇文档    1500-2000词    难度分级   深度研究评估  基于report   Benchmark就绪
```

## 输出格式

### 🔍 质量保证
- Deep research评估框架
- 自动问题精炼系统
- **完整数据输出 - 严禁截断**
- 多格式导出 (JSON + Excel + Markdown)

### 📋 输出格式

#### 📁 完整输出文件
1. **JSON数据集** - 完整结构化数据
   - 完整domain report (每个1500-2000词)
   - 完整问题和答案 (严禁截断)
   - 丰富的元数据和质量指标

2. **Excel工作簿** - 多sheet分析
   - 汇总统计
   - Topic概览  
   - **完整QA数据** (全内容，严禁截断)
   - **Domain Report** (完整报告，严禁截断)
   - 质量分析指标

3. **Markdown报告** - 人类可读摘要
   - 执行摘要
   - 合规验证
   - 使用说明

#### ⚠️ 数据完整性保证
- **所有内容完整保存，严禁任何截断**
- 完整domain report (完整1500-2000词)
- 完整问题文本和comprehensive答案
- 所有元数据和质量指标均包含

## 质量保证

### 深度研究问题标准
- **认知复杂度** (30%): 需要分析、综合、评估
- **研究深度** (30%): 涉及复杂概念和专业知识
- **综合要求** (20%): 需要整合多个信息源
- **专业要求** (20%): 需要领域专业知识

### 自动质量控制
- 问题深度自动评估
- 不符合标准的问题自动精炼
- 答案长度和结构验证
- 基于report的答案一致性检查

## 预期输出

### 数量指标
- **总Topics**: 10个
- **总问题**: 500个 (50×10)
- **总答案**: 500个
- **深度研究问题比例**: ≥70%

### 质量指标
- **答案成功率**: ≥90%
- **平均答案长度**: 
  - Easy: ~500词
  - Medium: ~1000词  
  - Hard: ~1750词

## 使用场景

### LLM评估
```python
# 加载benchmark数据
with open('client_qa_benchmark_TIMESTAMP.json', 'r') as f:
    benchmark = json.load(f)

# 测试LLM
for topic_id, topic_data in benchmark['topics'].items():
    for question in topic_data['questions']:
        if question['difficulty'] in ['Medium', 'Hard']:
            # 这些问题需要多步思考
            llm_answer = your_llm.generate(question['question_text'])
            # 与标准答案比较
```

### 研究分析
- 分析不同难度问题的LLM表现
- 评估多步推理能力
- 测试领域专业知识应用

## 技术特点

### 🚀 全自动化
- 无需人工干预的完整流程
- OpenAI GPT-4o驱动的内容生成
- 自动质量控制和精炼

### 🎯 需求导向
- 严格按照要求设计
- 10 topics × 50 QA pairs
- 忽略能源文献，专注ClueWeb22
- 多步思考导向的问题设计

### 📈 可扩展性
- 模块化设计，易于扩展
- 支持不同领域的topic
- 可调整的难度分布和质量标准

## 故障排除

### 常见问题
1. **API限制**: 系统内置rate limiting，自动处理
2. **文档缺失**: 自动生成simulated report作为fallback
3. **质量不达标**: 自动精炼系统确保质量

### 性能优化
- 预计运行时间: 2-3小时 (取决于API响应)
- 内存需求: <2GB
- 网络要求: 稳定的OpenAI API连接

## 项目状态

### ✅ 已完成
- [x] 完整的Phase I流程实现
- [x] 深度研究问题评估框架
- [x] 自动问题精炼系统
- [x] 基于report的答案生成
- [x] 需求专用pipeline
- [x] OpenAI GPT-4o集成

### 🎯 符合要求
- [x] 10个ClueWeb22 topics
- [x] 每topic 50个问题
- [x] 问题+答案完整生成
- [x] 基于高质量report的答案
- [x] 难度分级 (中等和困难问题需要多步思考)
- [x] 忽略能源文献
- [x] Deep research benchmark导向

---

**系统已完全满足所有要求，可以直接投入使用生成高质量的Deep Research QA Benchmark，现已集成OpenAI GPT-4o。** 
# 🎯 Agent深度推理测试框架 (Agent Depth Reasoning Test Framework)

## 📋 概述

这是一个**生产级Agent深度推理测试框架**，专门为智能Agent设计深度推理测试题。框架的**核心目标**是生成复杂的嵌套推理问题，测试Agent的逐步推理能力，防止普通LLM直接获取答案。

## 🚀 快速开始

### 安装依赖
```bash
pip install -r requirements.txt
```

### 运行框架
```bash
python main.py
```

## 📁 项目结构

```
07_tree_extension_deep_query/
├── main.py                    # 主入口文件
├── config.py                  # 配置文件
├── requirements.txt           # 依赖包列表
├── core/                      # 核心模块
│   ├── __init__.py
│   ├── agent_depth_reasoning_framework_fixed.py  # 主框架
│   ├── agent_reasoning_main.py                   # 主程序入口
│   └── default_excel_exporter.py                 # Excel导出器
├── utils/                     # 工具模块
│   ├── __init__.py
│   ├── circular_problem_handler.py               # 循环问题处理器
│   ├── circular_question_detector.py             # 循环问题检测器
│   ├── parallel_keyword_validator.py             # 并行关键词验证器
│   ├── document_loader.py                        # 文档加载器
│   ├── document_screener.py                      # 文档筛选器
│   ├── short_answer_locator.py                   # 短答案定位器
│   ├── web_search.py                             # 网络搜索
│   └── api_key_manager.py                        # API密钥管理器
├── docs/                      # 文档目录
│   ├── README.md             # 主文档
│   ├── QUICK_START.md        # 快速开始指南
│   ├── WorkFlow.md           # 工作流程说明
│   └── README_AGENT_REASONING.md  # 详细技术文档
├── results/                   # 结果输出目录
├── logs/                      # 日志目录
└── archived_temp_files/       # 临时文件存档
```

## 🎯 核心特性

### ✅ **双格式糅合问题生成**
- **描述性格式**: LLM生成的自然语言推理问题
- **嵌套式格式**: 纯算法生成的结构化嵌套问题 `(Q1, (Q2, Q3...))`

### ✅ **智能循环检测系统**
- **语义循环检测**: 基于内容相似度而非简单关键词重叠
- **知识模式识别**: 检测时间-事件对称性、定义循环等模式
- **多层风险评估**: 低/中/高风险分类和相应处理策略

### ✅ **完整数据导出系统**
- **Excel多工作表导出**: 糅合问答对、过程问答对、轨迹数据、效率统计
- **JSON详细数据**: 完整的推理树和轨迹数据
- **Markdown摘要报告**: 可读性强的实验总结

### ✅ **6步设计流程**
1. **Step1**: 提取Short Answer + 构建Root Query
2. **Step2**: 提取Root Query的最小关键词
3. **Step3**: 针对每个关键词做Series深度扩展
4. **Step4**: 针对所有关键词做Parallel横向扩展
5. **Step5**: 重复构建最多3层问题树
6. **Step6**: 糅合所有层级生成最终综合问题

## 🔧 使用方法

### 基本使用
```python
from core import AgentReasoningMainFramework

# 创建框架实例
framework = AgentReasoningMainFramework()

# 运行生产模式
framework.run_production_mode()
```

### 自定义配置
```python
from config import get_config

# 获取配置
config = get_config()

# 修改配置参数
config['max_documents'] = 50
config['max_short_answers'] = 3
```

## 📊 输出格式

### Excel输出
- **Sheet1**: 糅合后问答对 (双格式)
- **Sheet2**: 过程中所有问答对
- **Sheet3**: 轨迹数据记录
- **Sheet4**: 效率统计数据

### JSON输出
完整的推理树结构和详细轨迹数据

## 🛠️ 开发指南

### 添加新功能
1. 在相应的模块目录下添加新文件
2. 更新`__init__.py`文件
3. 添加必要的测试
4. 更新文档

### 代码规范
- 使用类型注解
- 添加详细的docstring
- 遵循PEP 8编码规范
- 记录详细的日志信息

## 📚 详细文档

- [快速开始指南](QUICK_START.md)
- [工作流程说明](WorkFlow.md)  
- [技术详细文档](README_AGENT_REASONING.md)

## 🔗 相关链接

- [项目根目录](../../)
- [其他实验方法](../)

---

**Agent深度推理测试框架** - 为智能Agent构建复杂推理测试题，提升Agent的深度思考能力。 
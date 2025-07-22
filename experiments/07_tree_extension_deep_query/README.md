# 07 Tree Extension Deep Query - 推理树扩展深度查询系统

## 项目概述

基于推理树结构的深度查询生成与分析系统，专门设计用于智能Agent的推理能力测试。

## 核心功能

1. **推理树生成** - 6步设计流程构建多层级问题树
2. **双格式综合问题** - 支持嵌套累积型和LLM整合型问题
3. **Excel多表导出** - 完整的数据分析和结果展示
4. **OpenAI集成** - 使用GPT-4o生成自然语言整合问题

## 快速开始

### 1. 运行主程序
```bash
python main.py
```

### 2. 程序功能
- **自动检测**：扫描results目录中的JSON文件
- **智能导出**：生成包含4个工作表的Excel文件
- **支持生成**：如果没有数据，可选择运行推理生成

### 3. 输出文件
Excel文件包含以下工作表：
- **Sheet1**: 文档处理效率统计
- **Sheet2**: 所有过程中的问答对 
- **Sheet3**: 推理轨迹记录
- **Sheet4**: 糅合后的综合问答（双格式）

## 技术特点

### 嵌套累积型问题
```
(root问题, (中间层问题, 最深层问题))
```

### LLM整合型问题
使用OpenAI GPT-4o生成自然语言流畅的综合问题

### 多层级支持
- 支持最多3层推理树
- 自动识别Layer 0, 1, 2
- 智能去重和层级分组

## 文件结构

```
07_tree_extension_deep_query/
├── main.py                          # 主程序入口
├── default_excel_exporter.py        # Excel导出器
├── agent_reasoning_main.py          # 推理生成主程序
├── agent_depth_reasoning_framework_fixed.py  # 推理框架
├── utils/                           # 工具模块
├── results/                         # 输出结果
└── README.md                        # 项目说明
```

## 依赖要求

```
pandas
openpyxl  
openai
pathlib
```

## API配置

系统内置OpenAI API密钥，用于LLM整合型问题生成。如需修改，请在`default_excel_exporter.py`中更新API密钥。

## 使用说明

1. **有现成数据**：程序自动使用最新的JSON文件导出Excel
2. **无数据**：选择运行推理生成，然后自动导出
3. **查看结果**：打开生成的Excel文件分析数据

## 核心算法

### 6步推理设计
1. 提取Short Answer + 构建最小精确问题
2. 提取Root Query的最小关键词  
3. 针对每个关键词做Series深度扩展
4. 针对所有关键词做Parallel横向扩展
5. 重复构建最多3层问题树
6. 糅合生成最终综合问题

### 问题糅合逻辑
- **嵌套累积型**：纯算法实现，层级包装
- **LLM整合型**：OpenAI GPT-4o自然语言整合

## 注意事项

- 确保有足够的API配额用于LLM整合
- JSON文件较大时处理可能需要时间
- Excel文件包含完整数据，可用于进一步分析 
# 06实验文件结构说明

## 📂 核心文件（必需）

### 🚀 主要脚本
```
main.py                                    # 统一入口程序，交互式菜单
final_optimized_experiment.py             # 核心实验逻辑和算法
topic_based_data_loader.py               # Topic-based数据加载和聚合融合
comprehensive_adaptive_framework.py       # 自适应优化框架
```

### 🔧 支持模块
```
document_content_filter.py               # 文档内容过滤和清洗
excel_export_system.py                   # Excel报告生成系统
answer_compression_optimizer.py          # 答案压缩优化器
gpt4o_qa_quality_evaluator.py           # GPT-4o质量评估器
report_quality_evaluation_system.py      # 报告质量评估系统
```

### 📝 文档
```
README.md                                # 主要使用说明和技术文档
FILE_STRUCTURE.md                       # 本文件，文件结构说明
```

### ⚙️ 配置和数据
```
config/
  └── experiment_config.json             # 实验配置参数
data/                                    # 数据目录（如存在）
logs/                                    # 日志目录（自动生成）
results/                                 # 实验结果目录（自动生成）
```

## 🎯 文件功能说明

### main.py
- **作用**：统一入口点，提供交互式菜单
- **功能**：模式选择、API配置、参数调整
- **推荐**：所有操作都从这里开始

### final_optimized_experiment.py
- **作用**：核心实验引擎
- **功能**：
  - Topic-based多文档融合
  - BrowseComp问题生成
  - 质量验证和统计
  - Excel报告导出

### topic_based_data_loader.py
- **作用**：数据加载和预处理
- **功能**：
  - 加载Topic下所有txt文件
  - 聚合所有文档内容
  - 跨文档去重和价值排序
  - 生成高质量聚合内容

### comprehensive_adaptive_framework.py
- **作用**：自适应优化框架
- **功能**：
  - 参数自动调优
  - 成功率监控
  - 质量反馈循环

## 🗑️ 已清理的文件

以下文件已被删除，不再需要：
- `test_new_fusion_method.py` - 测试文件
- `topic_based_experiment.py` - 旧版本实验文件
- `experimental_fuzzy_query_generator.py` - 实验性文件
- `short_answer_deep_query_experiment.py` - 旧版本核心文件
- `README_FINAL.md` - 旧版本文档
- `PRODUCTION_CONFIG.md` - 旧版本配置文档
- `06实验框架技术详解报告.md` - 旧版本技术报告

## 🚀 快速开始

1. **运行主程序**：
   ```bash
   python main.py
   ```

2. **选择模式**：
   - 选项1：自适应优化实验（推荐先运行）
   - 选项2：完整生产运行

3. **查看结果**：
   - 结果保存在 `results/` 目录
   - Excel报告包含详细分析

## 📊 目录大小

精简后的核心文件总计：
- Python脚本：~200KB
- 文档：~10KB
- 配置：~5KB

**总体**：简洁、完整、功能强大！ 
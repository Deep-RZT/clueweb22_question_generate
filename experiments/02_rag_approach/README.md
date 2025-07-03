# Energy FastText Classification Project

## 项目概述
本项目实现了一个基于FastText的能源领域文档分类器，用于从ClueWeb22语料库中筛选出能源相关文档。

## 核心功能
- 多源学术论文爬取（arXiv、OpenAlex、CrossRef）
- PDF文本提取和处理
- FastText二分类模型训练
- 能源/非能源文档分类

## 项目结构
```
energy_fasttext/
├── config.py                 # 配置文件（73个能源关键词）
├── fresh_start_1000.py       # 主要流程：收集1000篇论文
├── fasttext_trainer.py       # FastText模型训练
├── pdf_text_extractor.py     # PDF文本提取工具
├── crawlers/                 # 爬虫模块
│   ├── base_crawler.py       # 基础爬虫类
│   ├── arxiv_crawler.py      # arXiv爬虫
│   ├── openalex_crawler.py   # OpenAlex爬虫
│   └── crossref_crawler.py   # CrossRef爬虫
├── utils/                    # 工具模块
│   └── logger.py             # 日志工具
├── data/                     # 数据目录
│   ├── metadata/             # 论文元数据
│   ├── raw_papers/           # 原始PDF文件
│   └── processed_text/       # 处理后的文本
├── models/                   # 训练好的模型
└── logs/                     # 日志文件
```

## 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 运行完整流程
```bash
python fresh_start_1000.py
```

这个脚本会：
1. 收集1000篇能源相关论文
2. 下载PDF文件
3. 提取文本内容
4. 创建FastText训练数据集

### 3. 训练FastText模型
```bash
python fasttext_trainer.py
```

## 能源关键词
项目使用73个精心选择的能源关键词，涵盖8个主要类别：
- 通用/综合能源
- 电力系统
- 化石能源
- 可再生能源
- 新兴能源与氢能
- 终端用能与效率
- 排放与环境影响
- 市场与政策

## 技术特点
- **多源数据收集**：整合arXiv、OpenAlex、CrossRef三大学术数据库
- **智能去重**：基于标题相似度和DOI的重复检测
- **错误处理**：完善的异常处理和重试机制
- **进度监控**：详细的日志记录和进度报告
- **模块化设计**：可扩展的爬虫架构

## 数据质量
- 自动文本清理和标准化
- 多语言支持（主要英文）
- 长度过滤（确保文本质量）
- 平衡的正负样本

## 模型性能
- FastText二分类器
- 100维词向量
- 支持n-gram特征
- 快速训练和推理

## 使用场景
- 学术文献筛选
- 能源领域文档分类
- 大规模语料库过滤
- 研究趋势分析

## 注意事项
- 需要稳定的网络连接
- 遵守各API的使用限制
- 建议使用代理以提高下载成功率
- 大量下载时注意存储空间

## 许可证
MIT License 
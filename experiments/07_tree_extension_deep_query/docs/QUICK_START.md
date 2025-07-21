# 🚀 快速开始指南

## 一键运行

```bash
# 1. 设置API密钥
export OPENAI_API_KEY="your-openai-api-key"

# 2. 运行主程序
python agent_reasoning_main.py
```

## 输出文件

运行完成后会生成：
- `results/agent_reasoning_production_*.json` - 原始推理数据
- `results/agent_reasoning_production_*.xlsx` - Excel格式报告

## Excel报告包含

1. **糅合后问答对** - 最终复合推理问题 + 原始推理链
2. **过程问答对** - 每层详细推理 (正确层级 0,1,2)
3. **轨迹数据** - 完整推理过程记录
4. **效率数据** - 性能统计指标

## 核心特性

✅ **GPT-4o模型** + 纯英文prompt  
✅ **正确层级识别** root(0) → series1/parallel1(1) → series2(2)  
✅ **准确分支类型** root/series/parallel  
✅ **原始推理链** 显示完整推理过程  
✅ **自然糅合问题** 倒序拼接逻辑  

## 状态

🎉 **生产就绪** - 所有已知问题已修复！

---
**版本**: v2.0 | **更新**: 2024-07-21 
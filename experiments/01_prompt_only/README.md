# PROMPT-Only Question Generation

## 📋 Overview

This approach uses pure prompt-based generation without external knowledge retrieval. It directly processes documents and generates questions and answers using LLM capabilities.

## 🔧 Methodology

**PROMPT-only approach**: Documents → Domain report → Research questions

- **Phase 1**: Identify domain characteristics using document analysis
- **Phase 2**: Generate comprehensive domain reports (1500-2000 words)
- **Phase 3**: Generate research questions based on domain understanding
- **Advantages**: Simple, fast, self-contained
- **Disadvantages**: Limited by LLM knowledge cutoff, potential hallucination

## 🚀 Usage

```bash
cd experiments/01_prompt_only
python prompt_generator.py
```

## 📊 Configuration

- **Question Count**: 25-50 per topic (adjustable based on document availability)
- **Difficulty Distribution**: Easy (20%), Medium (40%), Hard (40%)
- **Output Format**: JSON + Excel + Markdown

## 📁 Files

- `prompt_generator.py` - Main generator (based on clueweb22_simplified_generator.py)
- `examples/` - Example outputs and configurations

## ✅ Use Cases

- Quick prototyping and validation
- Large-scale batch processing
- Self-contained question generation
- When external knowledge corpus is not available

## 🔗 Dependencies

- OpenAI API or Claude API
- Core components from `../../core/`
- Data sources from `../../data/`

---

*This approach is suitable for rapid question generation when external knowledge integration is not required.* 
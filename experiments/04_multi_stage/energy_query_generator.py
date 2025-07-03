# energy_query_generator.py - 主要生成器类
import anthropic
import json
import time
import os
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
from config import Config

class Difficulty(Enum):
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"

class Category(Enum):
    GENERAL = "General"
    CROSS_SUBDOMAIN = "Cross_Subdomain"

@dataclass
class QueryRequirement:
    difficulty: Difficulty
    category: Category
    primary_subdomain: str
    secondary_subdomains: Optional[List[str]] = None
    count: int = 1

class QualityAssessor:
    """查询质量评估器"""
    
    def __init__(self):
        self.clear_indicators = ['analyze', 'evaluate', 'compare', 'assess', 'examine', 'develop', 'design']
        self.vague_indicators = ['discuss', 'talk about', 'consider', 'what is', 'define']
        self.depth_indicators = ['framework', 'implications', 'trade-offs', 'integrated', 'systemic', 'comprehensive']
        self.complexity_words = ['considering', 'including', 'while', 'however', 'furthermore']
    
    def assess_clarity(self, query: str) -> float:
        """评估问题的清晰度"""
        query_lower = query.lower()
        clarity_score = 0.5
        
        for indicator in self.clear_indicators:
            if indicator in query_lower:
                clarity_score += 0.1
                
        for indicator in self.vague_indicators:
            if indicator in query_lower:
                clarity_score -= 0.1
                
        return max(0.0, min(1.0, clarity_score))
    
    def assess_depth(self, query: str) -> float:
        """评估问题的深度"""
        query_lower = query.lower()
        depth_score = 0.5
        
        for indicator in self.depth_indicators:
            if indicator in query_lower:
                depth_score += 0.1
                
        # 检查复杂性指标
        complexity_count = sum(1 for word in self.complexity_words if word in query_lower)
        depth_score += min(0.3, complexity_count * 0.1)
        
        return max(0.0, min(1.0, depth_score))
    
    def assess_structure(self, query: str) -> float:
        """评估问题的结构性"""
        word_count = len(query.split())
        sentence_count = len([s for s in re.split(r'[.!?]', query) if s.strip()])
        
        # 理想长度评分
        if Config.MIN_WORD_COUNT <= word_count <= Config.MAX_WORD_COUNT:
            length_score = 1.0
        elif word_count < Config.MIN_WORD_COUNT:
            length_score = word_count / Config.MIN_WORD_COUNT
        else:
            length_score = Config.MAX_WORD_COUNT / word_count
            
        # 句子结构评分
        structure_score = min(1.0, sentence_count / 3) if sentence_count > 0 else 0.0
        
        return (length_score + structure_score) / 2
    
    def assess_novelty(self, query: str) -> float:
        """评估问题的新颖性（简化版本）"""
        # 检查是否包含创新性关键词
        innovation_words = ['novel', 'emerging', 'future', 'next-generation', 'breakthrough', 'innovative']
        novelty_score = 0.5
        
        for word in innovation_words:
            if word in query.lower():
                novelty_score += 0.1
                
        return min(1.0, novelty_score)
    
    def comprehensive_evaluation(self, query_dict: Dict[str, Any]) -> Dict[str, float]:
        """综合评估查询质量"""
        query_text = query_dict["query_text"]
        
        scores = {
            "clarity": self.assess_clarity(query_text),
            "depth": self.assess_depth(query_text),
            "structure": self.assess_structure(query_text),
            "novelty": self.assess_novelty(query_text)
        }
        
        # 计算权重平均分
        weights = {"clarity": 0.3, "depth": 0.3, "structure": 0.2, "novelty": 0.2}
        scores["overall"] = sum(score * weights[criterion] for criterion, score in scores.items())
        
        return scores

class EnergyQueryGenerator:
    """能源领域查询生成器"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or Config.CLAUDE_API_KEY
        if not self.api_key:
            raise ValueError("API key is required. Set CLAUDE_API_KEY environment variable or pass it directly.")
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.generated_queries = []
        self.quality_assessor = QualityAssessor()
        
        # 创建输出目录
        os.makedirs(Config.OUTPUT_DIR, exist_ok=True)
    
    def create_optimized_prompt(self, requirement: QueryRequirement) -> str:
        """Create an optimized prompt in English"""
        
        # Difficulty level guidelines
        difficulty_guidelines = {
            Difficulty.EASY: """
## Easy Level Guidelines:
- Focus on fundamental concepts, basic comparisons, or straightforward explanations
- Require understanding of key principles but not complex synthesis
- Should be answerable with direct knowledge recall and basic analysis
- Word count: 15-40 words
- Examples: "What are the main advantages of solar PV vs wind power?" or "Explain the basic process of nuclear fission"
""",
            Difficulty.MEDIUM: """
## Medium Level Guidelines:
- Require multi-factor analysis, trade-off evaluations, or moderate synthesis
- Involve connecting concepts across 2-3 related areas
- Need systematic thinking and structured argumentation
- Word count: 30-70 words
- Examples: "Analyze the challenges of integrating renewable energy into existing grids" or "Compare nuclear vs renewable energy for energy security"
""",
            Difficulty.HARD: """
## Hard Level Guidelines:
- Demand complex system thinking, comprehensive frameworks, or novel solution design
- Require synthesis across multiple subdomains and consideration of various perspectives
- Need deep critical analysis, scenario planning, or creative problem-solving
- Word count: 50-100 words
- Examples: "Design a comprehensive energy transition strategy for a developing nation" or "Develop a framework for evaluating intergenerational energy justice"
"""
        }
        
        # Category guidelines
        category_guidelines = {
            Category.GENERAL: """
## General Energy Questions:
- Focus primarily on one subdomain or broad energy topics
- Can touch on other areas but maintain clear primary focus
- Should explore depth within the specific domain
""",
            Category.CROSS_SUBDOMAIN: """
## Cross-Subdomain Questions:
- Must meaningfully integrate multiple subdomains
- Explore interdependencies and interactions between different areas
- Require understanding of how different energy systems/aspects influence each other
"""
        }
        
        # Build base prompt
        subdomains_str = f"{requirement.primary_subdomain}"
        if requirement.secondary_subdomains:
            subdomains_str += f" + {', '.join(requirement.secondary_subdomains)}"
        
        prompt = f"""You are an expert in energy systems research with deep knowledge across renewable energy, fossil fuels, nuclear power, grid technologies, energy policy, economics, and environmental impacts.

Your task is to generate {requirement.count} high-quality research {"question" if requirement.count == 1 else "questions"} for evaluating large language models' deep research capabilities in the energy domain.

## Current Requirements:
- **Difficulty Level**: {requirement.difficulty.value}
- **Category**: {requirement.category.value}
- **Primary Subdomain**: {requirement.primary_subdomain}
{"- **Secondary Subdomains**: " + ", ".join(requirement.secondary_subdomains) if requirement.secondary_subdomains else ""}

{difficulty_guidelines[requirement.difficulty]}
{category_guidelines[requirement.category]}

## Quality Standards:
1. **Clarity**: Questions should be precisely worded with clear research direction
2. **Relevance**: Address current real-world energy challenges or important theoretical considerations
3. **Depth**: Favor questions requiring analysis, synthesis, or explanation over factual recall
4. **Specificity**: Provide enough context and constraints to make questions answerable
5. **Originality**: Avoid trivial or commonly asked questions

## Context (2024-2025 Energy Landscape):
- Rapid renewable energy deployment and cost reductions
- Growing importance of energy storage and grid flexibility
- Geopolitical tensions affecting energy security
- AI and digitalization transforming energy systems
- Climate commitments driving ambitious policy changes
- Critical mineral supply chain challenges for energy transition

## Output Instructions:
- Generate exactly {requirement.count} {"question" if requirement.count == 1 else "questions"}
- Each question should be a complete, standalone research query
- If generating multiple questions, number them clearly (1., 2., etc.)
- Focus on current and emerging challenges in the energy sector
- Ensure questions test deep understanding rather than superficial knowledge

Generate the {"question" if requirement.count == 1 else "questions"} now:"""
        
        return prompt
    
    def parse_generated_queries(self, content: str, requirement: QueryRequirement) -> List[Dict[str, Any]]:
        """解析生成的查询内容"""
        queries = []
        
        if requirement.count == 1:
            # 单个问题
            query_text = content.strip()
            # 清理可能的编号
            query_text = re.sub(r'^\d+\.\s*', '', query_text)
            query_text = re.sub(r'^\*\*\d+\.\*\*\s*', '', query_text)
            
            if query_text:
                queries.append(self.create_query_dict(query_text, requirement))
        else:
            # 多个问题 - 按行分割并查找编号
            lines = content.split('\n')
            current_query = ""
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # 检查是否是新问题的开始（以数字开头）
                if re.match(r'^\d+\.', line) or re.match(r'^\*\*\d+\.', line):
                    # 保存前一个问题
                    if current_query:
                        clean_query = re.sub(r'^\d+\.\s*', '', current_query.strip())
                        clean_query = re.sub(r'^\*\*\d+\.\*\*\s*', '', clean_query)
                        if clean_query:
                            queries.append(self.create_query_dict(clean_query, requirement))
                    
                    # 开始新问题
                    current_query = line
                else:
                    # 继续当前问题
                    current_query += " " + line
            
            # 处理最后一个问题
            if current_query:
                clean_query = re.sub(r'^\d+\.\s*', '', current_query.strip())
                clean_query = re.sub(r'^\*\*\d+\.\*\*\s*', '', clean_query)
                if clean_query:
                    queries.append(self.create_query_dict(clean_query, requirement))
        
        return queries
    
    def create_query_dict(self, query_text: str, requirement: QueryRequirement) -> Dict[str, Any]:
        """创建查询字典"""
        # 确定子领域
        subdomains = [requirement.primary_subdomain]
        if requirement.secondary_subdomains:
            subdomains.extend(requirement.secondary_subdomains)
        
        return {
            "id": f"AQ{len(self.generated_queries) + 1:03d}",
            "query_text": query_text.strip(),
            "category": requirement.category.value,
            "subdomains": subdomains,
            "difficulty": requirement.difficulty.value,
            "source": "AI_generated",
            "timestamp": datetime.now().isoformat()
        }
    
    def generate_query(self, requirement: QueryRequirement) -> List[Dict[str, Any]]:
        """生成查询问题"""
        prompt = self.create_optimized_prompt(requirement)
        
        try:
            print(f"  Calling Claude API for {requirement.count} {requirement.difficulty.value} question(s)...")
            
            response = self.client.messages.create(
                model=Config.MODEL_NAME,
                max_tokens=Config.MAX_TOKENS,
                temperature=Config.TEMPERATURE,
                system="You are an expert energy researcher designing evaluation benchmarks for AI systems. Generate high-quality, thought-provoking research questions.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            content = response.content[0].text
            
            # 保存原始响应（如果配置启用）
            if Config.SAVE_RAW_RESPONSES:
                self.save_raw_response(content, requirement)
            
            # 解析生成的查询
            queries = self.parse_generated_queries(content, requirement)
            
            # 添加到已生成列表
            self.generated_queries.extend(queries)
            
            print(f"  Successfully generated {len(queries)} queries")
            return queries
            
        except Exception as e:
            print(f"  Error generating query: {e}")
            return []
    
    def save_raw_response(self, content: str, requirement: QueryRequirement):
        """保存原始API响应"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{Config.OUTPUT_DIR}/raw_response_{requirement.difficulty.value}_{requirement.category.value}_{timestamp}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"Requirement: {requirement}\n")
            f.write(f"Timestamp: {datetime.now().isoformat()}\n")
            f.write("=" * 50 + "\n")
            f.write(content)
    
    def batch_generate(self, requirements: List[QueryRequirement]) -> List[Dict[str, Any]]:
        """批量生成查询问题"""
        all_queries = []
        
        print(f"Starting batch generation of {len(requirements)} requirements...")
        
        for i, req in enumerate(requirements, 1):
            print(f"\n[{i}/{len(requirements)}] Processing: {req.difficulty.value} {req.category.value} ({req.primary_subdomain})")
            
            # 重试机制
            for attempt in range(Config.MAX_RETRIES):
                queries = self.generate_query(req)
                
                if queries:
                    all_queries.extend(queries)
                    break
                else:
                    if attempt < Config.MAX_RETRIES - 1:
                        print(f"  Attempt {attempt + 1} failed, retrying...")
                        time.sleep(Config.DELAY_BETWEEN_CALLS)
                    else:
                        print(f"  All attempts failed for this requirement")
            
            # API调用间隔
            if i < len(requirements):
                time.sleep(Config.DELAY_BETWEEN_CALLS)
        
        print(f"\nBatch generation completed. Total queries generated: {len(all_queries)}")
        return all_queries
    
    def filter_high_quality_queries(self, queries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """过滤高质量查询"""
        high_quality_queries = []
        
        print("\nEvaluating query quality...")
        
        for query in queries:
            quality_scores = self.quality_assessor.comprehensive_evaluation(query)
            
            if Config.INCLUDE_QUALITY_SCORES:
                query["quality_scores"] = quality_scores
            
            if quality_scores["overall"] >= Config.QUALITY_THRESHOLD:
                high_quality_queries.append(query)
            else:
                print(f"  Filtered out: {query['id']} (Score: {quality_scores['overall']:.2f})")
        
        print(f"Quality filtering completed. {len(high_quality_queries)}/{len(queries)} queries passed.")
        return high_quality_queries
    
    def save_queries_json(self, queries: List[Dict[str, Any]], filename: str = None):
        """保存查询为JSON格式"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{Config.OUTPUT_DIR}/energy_queries_{timestamp}.json"
        
        output_data = {
            "metadata": {
                "total_queries": len(queries),
                "generation_timestamp": datetime.now().isoformat(),
                "source": "AI_generated",
                "generator": "Claude-3.7-Sonnet",
                "configuration": {
                    "model": Config.MODEL_NAME,
                    "temperature": Config.TEMPERATURE,
                    "quality_threshold": Config.QUALITY_THRESHOLD
                }
            },
            "queries": queries
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"Saved {len(queries)} queries to {filename}")
        return filename
    
    def save_queries_excel(self, queries: List[Dict[str, Any]], filename: str = None):
        """保存查询为Excel格式"""
        try:
            import pandas as pd
            
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{Config.OUTPUT_DIR}/energy_queries_{timestamp}.xlsx"
            
            # 准备数据
            rows = []
            for query in queries:
                row = {
                    'ID': query['id'],
                    'Query Text': query['query_text'],
                    'Category': query['category'],
                    'Subdomains': ', '.join(query['subdomains']),
                    'Difficulty': query['difficulty'],
                    'Source': query['source']
                }
                
                # 添加质量分数（如果存在）
                if 'quality_scores' in query:
                    row['Overall Quality Score'] = f"{query['quality_scores']['overall']:.3f}"
                    row['Clarity'] = f"{query['quality_scores']['clarity']:.3f}"
                    row['Depth'] = f"{query['quality_scores']['depth']:.3f}"
                    row['Structure'] = f"{query['quality_scores']['structure']:.3f}"
                    row['Novelty'] = f"{query['quality_scores']['novelty']:.3f}"
                
                rows.append(row)
            
            # 创建DataFrame并保存
            df = pd.DataFrame(rows)
            df.to_excel(filename, index=False, engine='openpyxl')
            
            print(f"Saved {len(queries)} queries to {filename}")
            return filename
            
        except ImportError:
            print("pandas or openpyxl not installed. Skipping Excel export.")
            return None
    
    def generate_statistics_report(self, queries: List[Dict[str, Any]]):
        """生成统计报告"""
        print("\n" + "=" * 50)
        print("GENERATION STATISTICS REPORT")
        print("=" * 50)
        
        # 基本统计
        print(f"Total queries generated: {len(queries)}")
        
        # 难度分布
        difficulty_counts = {}
        for query in queries:
            diff = query['difficulty']
            difficulty_counts[diff] = difficulty_counts.get(diff, 0) + 1
        
        print("\nDifficulty Distribution:")
        for diff, count in difficulty_counts.items():
            percentage = (count / len(queries)) * 100
            print(f"  {diff}: {count} ({percentage:.1f}%)")
        
        # 类别分布
        category_counts = {}
        for query in queries:
            cat = query['category']
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        print("\nCategory Distribution:")
        for cat, count in category_counts.items():
            percentage = (count / len(queries)) * 100
            print(f"  {cat}: {count} ({percentage:.1f}%)")
        
        # 子领域分布
        subdomain_counts = {}
        for query in queries:
            for subdomain in query['subdomains']:
                subdomain_counts[subdomain] = subdomain_counts.get(subdomain, 0) + 1
        
        print("\nSubdomain Distribution:")
        for subdomain, count in sorted(subdomain_counts.items()):
            print(f"  {subdomain}: {count}")
        
        # 质量分数统计（如果存在）
        if queries and 'quality_scores' in queries[0]:
            quality_scores = [q['quality_scores']['overall'] for q in queries]
            avg_quality = sum(quality_scores) / len(quality_scores)
            min_quality = min(quality_scores)
            max_quality = max(quality_scores)
            
            print(f"\nQuality Scores:")
            print(f"  Average: {avg_quality:.3f}")
            print(f"  Range: {min_quality:.3f} - {max_quality:.3f}")
        
        print("=" * 50)
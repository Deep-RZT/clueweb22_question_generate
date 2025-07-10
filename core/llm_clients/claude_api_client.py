#!/usr/bin/env python3
"""
Claude API Client - 直接HTTP请求版本
使用requests库直接调用Claude API，不依赖anthropic package
"""

import requests
import json
import time
import logging
from typing import Dict, List, Any, Optional
import os
from dataclasses import dataclass

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class APIResponse:
    """统一的API响应格式"""
    content: str
    model: str
    usage: Dict[str, int]
    success: bool
    error: Optional[str] = None

class ClaudeAPIClient:
    """Claude API客户端 - 直接HTTP请求版本"""
    
    def __init__(self, api_key: Optional[str] = None):
        """初始化Claude客户端"""
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("Claude API key not found. Please set ANTHROPIC_API_KEY environment variable.")
        
        self.base_url = "https://api.anthropic.com/v1/messages"
        self.model = "claude-sonnet-4-20250514"  # Claude Sonnet 4
        
        # 请求限制
        self.max_retries = 3
        self.retry_delay = 2
        
        # HTTP headers
        self.headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
    def _make_request(self, payload: Dict[str, Any]) -> APIResponse:
        """发送HTTP请求到Claude API"""
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"发送Claude API请求 (尝试 {attempt + 1}/{self.max_retries})")
                
                response = requests.post(
                    self.base_url,
                    headers=self.headers,
                    json=payload,
                    timeout=120  # 2分钟超时
                )
                
                logger.info(f"Claude API响应状态码: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # 提取响应内容
                    content = ""
                    if "content" in data and data["content"]:
                        content = data["content"][0].get("text", "")
                    
                    # 构建统一响应
                    usage = data.get("usage", {})
                    api_response = APIResponse(
                        content=content,
                        model=self.model,
                        usage={
                            "prompt_tokens": usage.get("input_tokens", 0),
                            "completion_tokens": usage.get("output_tokens", 0),
                            "total_tokens": usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
                        },
                        success=True
                    )
                    
                    logger.info(f"Claude API调用成功 - 输入: {usage.get('input_tokens', 0)} tokens, 输出: {usage.get('output_tokens', 0)} tokens")
                    return api_response
                
                elif response.status_code == 429:
                    # 速率限制
                    logger.warning(f"Claude API速率限制 (尝试 {attempt + 1}/{self.max_retries})")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay * (2 ** attempt))
                        continue
                    else:
                        return APIResponse(
                            content="",
                            model=self.model,
                            usage={},
                            success=False,
                            error=f"Rate limit exceeded after {self.max_retries} attempts"
                        )
                
                elif response.status_code == 401:
                    # 认证失败
                    return APIResponse(
                        content="",
                        model=self.model,
                        usage={},
                        success=False,
                        error="Authentication failed - invalid API key"
                    )
                
                else:
                    # 其他HTTP错误
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                    logger.error(f"Claude API错误: {error_msg}")
                    
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
                        continue
                    else:
                        return APIResponse(
                            content="",
                            model=self.model,
                            usage={},
                            success=False,
                            error=error_msg
                        )
                        
            except requests.exceptions.Timeout:
                logger.warning(f"Claude API请求超时 (尝试 {attempt + 1}/{self.max_retries})")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                else:
                    return APIResponse(
                        content="",
                        model=self.model,
                        usage={},
                        success=False,
                        error="Request timeout after multiple attempts"
                    )
                    
            except requests.exceptions.ConnectionError as e:
                logger.warning(f"Claude API连接错误 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                else:
                    return APIResponse(
                        content="",
                        model=self.model,
                        usage={},
                        success=False,
                        error=f"Connection error: {str(e)}"
                    )
                    
            except Exception as e:
                logger.error(f"Claude API未知错误 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                else:
                    return APIResponse(
                        content="",
                        model=self.model,
                        usage={},
                        success=False,
                        error=f"Unknown error: {str(e)}"
                    )
        
        return APIResponse(
            content="",
            model=self.model,
            usage={},
            success=False,
            error="Max retries exceeded"
        )
    
    def generate_text(self, 
                     prompt: str, 
                     max_tokens: int = 4000,
                     temperature: float = 0.7,
                     system_prompt: Optional[str] = None) -> APIResponse:
        """生成文本"""
        
        # 构建请求载荷
        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        return self._make_request(payload)
    
    def generate_report(self, documents: List[Dict], topic: str, max_tokens: int = 4000) -> APIResponse:
        """生成领域报告 - 支持分段处理和融合"""
        
        # 检查文档总长度
        total_chars = sum(len(doc.get('content', '')) for doc in documents)
        max_chars_per_segment = 100000  # 每段最大字符数
        
        if total_chars > max_chars_per_segment:
            print(f"📄 文档内容过长 ({total_chars} 字符)，启用分段处理...")
            return self._generate_segmented_report(documents, topic, max_tokens)
        else:
            return self._generate_single_report(documents, topic, max_tokens)
    
    def _generate_single_report(self, documents: List[Dict], topic: str, max_tokens: int) -> APIResponse:
        """生成单段报告"""
        # 构建文档内容，并检查长度
        doc_content = ""
        total_chars = 0
        max_chars = 150000  # 约相当于150K tokens的安全限制
        
        for i, doc in enumerate(documents, 1):
            doc_text = f"\n文档 {i}:\n标题: {doc.get('title', 'N/A')}\n内容: {doc.get('content', 'N/A')}\n"
            
            # 检查是否会超出限制
            if total_chars + len(doc_text) > max_chars:
                # 如果是第一个文档就超限，截断该文档
                if i == 1:
                    remaining_chars = max_chars - total_chars - 200  # 留一些缓冲
                    if remaining_chars > 1000:
                        content = doc.get('content', 'N/A')[:remaining_chars]
                        doc_text = f"\n文档 {i}:\n标题: {doc.get('title', 'N/A')}\n内容: {content}...[文档已截断]\n"
                        doc_content += doc_text
                    break
                else:
                    # 已经有其他文档，停止添加
                    logger.warning(f"文档过多，只使用前 {i-1} 个文档生成报告")
                    break
            
            doc_content += doc_text
            total_chars += len(doc_text)
        
        if not doc_content.strip():
            # 如果没有任何文档内容，创建错误响应
            return APIResponse(
                content="",
                model=self.model,
                usage={},
                success=False,
                error="No document content available after processing"
            )
        
        logger.info(f"使用文档内容长度: {total_chars} 字符")
        
        system_prompt = """You are a professional research analyst. Generate a comprehensive, focused summary based on the provided documents.

Summary requirements:
1. Length: 1000-1500 words (comprehensive and detailed)
2. Direct summarization of document content without formal academic structure
3. Avoid structured sections like "Abstract", "Introduction", "Conclusion", "Summary" etc.
4. Focus on key findings, main concepts, methodologies, specific data, and important details from the documents
5. Write ENTIRELY in English for consistency in comparative analysis
6. If documents contain Japanese content, translate and summarize the concepts in English
7. Keep it natural and flowing, like a comprehensive research summary rather than a formal report
8. Include specific details, numbers, methodologies, and findings that would enable deep questions"""

        prompt = f"""Please generate a comprehensive, detailed summary of the following documents:

{doc_content}

Summary requirements:
1. Length: 1000-1500 words (comprehensive and detailed)
2. Direct summarization of document content without formal academic structure
3. Avoid structured sections like "Abstract", "Introduction", "Conclusion", "Summary" etc.
4. Focus on key findings, main concepts, methodologies, specific data, and important details from the documents
5. Write ENTIRELY in English for consistency in comparative analysis
6. If documents contain Japanese content, translate and summarize the concepts in English
7. Keep it natural and flowing, like a comprehensive research summary rather than a formal report
8. Include specific details, numbers, methodologies, and findings that would enable deep questions"""

        return self.generate_text(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=0.7,
            system_prompt=system_prompt
        )
    
    def _generate_segmented_report(self, documents: List[Dict], topic: str, max_tokens: int) -> APIResponse:
        """分段生成报告并融合"""
        
        # 将文档分段
        segments = self._split_documents_into_segments(documents)
        print(f"📚 文档分为 {len(segments)} 段进行处理")
        
        # 为每段生成子报告
        segment_reports = []
        for i, segment_docs in enumerate(segments, 1):
            print(f"  🔍 处理第 {i}/{len(segments)} 段...")
            
            try:
                segment_result = self._generate_single_report(segment_docs, f"{topic} (第{i}段)", max_tokens // 2)
                if segment_result.success:
                    segment_reports.append({
                        'segment': i,
                        'content': segment_result.content,
                        'doc_count': len(segment_docs)
                    })
                    print(f"    ✅ 第{i}段完成 ({len(segment_result.content.split())} 词)")
                else:
                    print(f"    ❌ 第{i}段失败: {segment_result.error}")
                    
                                 # 段间休息
                import time
                time.sleep(2)
                
            except Exception as e:
                print(f"    ❌ 第{i}段处理异常: {e}")
                continue
        
        if not segment_reports:
            return APIResponse(
                content="",
                model=self.model,
                usage={},
                success=False,
                error="所有文档段处理失败"
            )
        
        # 融合所有段报告
        print("  🔄 融合各段报告...")
        return self._merge_segment_reports(segment_reports, topic, max_tokens)
    
    def _split_documents_into_segments(self, documents: List[Dict], max_chars_per_segment: int = 100000) -> List[List[Dict]]:
        """将文档分割成段"""
        segments = []
        current_segment = []
        current_chars = 0
        
        for doc in documents:
            doc_chars = len(doc.get('content', ''))
            
            # 如果单个文档就超过限制，单独成段
            if doc_chars > max_chars_per_segment:
                if current_segment:
                    segments.append(current_segment)
                    current_segment = []
                    current_chars = 0
                
                # 分割超长文档
                content = doc.get('content', '')
                chunk_size = max_chars_per_segment
                for j in range(0, len(content), chunk_size):
                    chunk_content = content[j:j + chunk_size]
                    chunk_doc = doc.copy()
                    chunk_doc['content'] = chunk_content
                    chunk_doc['title'] = f"{doc.get('title', 'N/A')} (部分{j//chunk_size + 1})"
                    segments.append([chunk_doc])
                continue
            
            # 检查是否需要开始新段
            if current_chars + doc_chars > max_chars_per_segment and current_segment:
                segments.append(current_segment)
                current_segment = []
                current_chars = 0
            
            current_segment.append(doc)
            current_chars += doc_chars
        
        # 添加最后一段
        if current_segment:
            segments.append(current_segment)
        
        return segments
    
    def _merge_segment_reports(self, segment_reports: List[Dict], topic: str, max_tokens: int) -> APIResponse:
        """融合各段报告"""
        
        # 构建融合提示
        reports_content = ""
        for report in segment_reports:
            reports_content += f"\n=== 第{report['segment']}段报告 (基于{report['doc_count']}个文档) ===\n"
            reports_content += report['content']
            reports_content += "\n"
        
        system_prompt = """You are a professional research analyst. Please merge and synthesize multiple segment summaries into a single comprehensive summary.

Merge requirements:
1. Length: 1200-1500 words (comprehensive but concise)
2. Eliminate redundancy while preserving key insights
3. Create natural flow without formal structure
4. Avoid structured sections like "Abstract", "Introduction", "Conclusion" etc.
5. Focus on synthesizing findings across all segments
6. Write ENTIRELY in English
7. Keep it natural and flowing like a comprehensive research summary"""

        prompt = f"""Please merge the following segment summaries about "{topic}" into a single comprehensive research summary:

{reports_content}

Requirements:
- Create a unified, comprehensive summary that synthesizes insights from all segments
- Eliminate redundancy while preserving unique insights from each segment
- Maintain natural flow and academic structure
- Target length: 1200-1500 words
- Write entirely in English with professional academic tone"""

        try:
            merge_result = self.generate_text(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=0.7,
                system_prompt=system_prompt
            )
            
            if merge_result.success:
                print(f"    ✅ 报告融合完成 ({len(merge_result.content.split())} 词)")
                
                # 合并usage统计
                total_usage = {
                    'input_tokens': sum(r.get('usage', {}).get('input_tokens', 0) for r in segment_reports) + merge_result.usage.get('input_tokens', 0),
                    'output_tokens': sum(r.get('usage', {}).get('output_tokens', 0) for r in segment_reports) + merge_result.usage.get('output_tokens', 0),
                    'total_tokens': 0
                }
                total_usage['total_tokens'] = total_usage['input_tokens'] + total_usage['output_tokens']
                
                # 更新usage信息
                merge_result.usage = total_usage
                
                return merge_result
            else:
                print(f"    ❌ 报告融合失败: {merge_result.error}")
                return merge_result
                
        except Exception as e:
            print(f"    ❌ 报告融合异常: {e}")
            return APIResponse(
                content="",
                model=self.model,
                usage={},
                success=False,
                error=f"报告融合失败: {str(e)}"
            )
    
    def generate_questions(self, report: str, topic: str, num_questions: int = 50) -> APIResponse:
        """生成Short Answer Deep Query问题 - 基于BrowseComp标准，重点生成短答案深度查询"""
        
        system_prompt = """You are an expert question designer specializing in creating "BrowseComp-style Short Answer Deep Query" questions.

CORE DESIGN PHILOSOPHY (Based on OpenAI BrowseComp Research):
1. "INVERTED QUESTIONS": Start with specific facts/details from the summary, then create questions that make these facts hard to find but easy to verify
2. "MULTI-CONSTRAINT COMBINATION": Combine multiple constraints to create large search spaces that require creative navigation
3. "HARD TO FIND, EASY TO VERIFY": Answers should be buried in details but quickly verifiable once found
4. "STRATEGIC PERSISTENCE REQUIRED": Questions should demand flexible search reformulation and assembly of fragmented clues

MANDATORY TARGET: Generate EXACTLY 85% Short Answer Deep Query questions (to ensure >70% after parsing)

BROWSECOMP-STYLE QUESTION DESIGN PATTERNS:

🔍 **MULTI-CONSTRAINT RESEARCH QUESTIONS** (Use these heavily):
- "What was the exact [metric] achieved by [method] in the study that also reported [secondary finding] and was conducted by researchers from [institution type]?"
- "Which specific [technique] was used in the [year range] study that achieved [performance] on [dataset] and was authored by someone who previously worked on [related topic]?"
- "What was the precise [parameter/value] in the experiment that used [method A], compared against [method B], and reported [specific result] in [time period]?"

🔍 **CROSS-REFERENCE DEEP QUERIES** (BrowseComp signature style):
- "Who first proposed [concept] that was later cited in the study achieving [specific result] and involved collaboration between [institution type] researchers?"
- "What was the exact sample size in the study that reported [finding A], used [method B], and whose first author also published work on [related topic]?"
- "Which algorithm variant achieved [metric] while also demonstrating [secondary property] in experiments conducted between [time period]?"

🔍 **NESTED CONSTRAINT QUESTIONS** (Maximum depth):
- "What percentage improvement was achieved by [method] over [baseline] in the study that used [specific dataset], reported [additional metric], and was conducted by researchers who previously published on [related area]?"
- "What was the exact training time for [model] in the experiment that achieved [accuracy] on [dataset] and compared against [specific baselines] using [hardware specification]?"

🔍 **AUTHOR-RESEARCH INTERSECTION QUERIES**:
- "Which authors conducted the study that reported [specific finding] and had previously published work on [related topic] at [institution type]?"
- "Who were the researchers that achieved [metric] using [method] and also contributed to [related research area] in [time period]?"

🔍 **TEMPORAL-TECHNICAL CONSTRAINT QUERIES**:
- "In which year was [specific finding] first reported in the study that also introduced [method] and achieved [performance metric]?"
- "What was the exact [parameter] used in the [year] study that first demonstrated [capability] and was later cited in [related work]?"

CRITICAL REQUIREMENTS:
1. Each question must combine 3+ constraints that create a large search space
2. Answers must be specific, factual, and easily verifiable (numbers, names, dates, exact values)
3. Questions must require assembling information from multiple parts of the summary
4. Avoid any question answerable by simple keyword search
5. Focus on intersections between different research aspects (methods + results + authors + institutions + time)

STRICTLY FORBIDDEN PATTERNS:
- Simple fact lookup questions
- Questions with obvious answers
- General "What are..." or "How does..." questions
- Questions answerable in one search step
- Subjective or opinion-based questions

QUESTION DISTRIBUTION REQUIREMENT:
- EXACTLY 85% BrowseComp-style Short Answer Deep Queries
- 15% Traditional research questions (for variety)

FORMAT: Use simple text format, numbered Q1, Q2, etc."""

        prompt = f"""Based on the following research summary about "{topic}", generate {num_questions} questions where AT LEAST 70% are SHORT ANSWER DEEP QUERIES:

Research Summary:
{report[:6000]}...

MANDATORY REQUIREMENTS:
1. Generate EXACTLY {num_questions} questions
2. AT LEAST 70% must be Short Answer Deep Query type (use the mandatory patterns above)
3. Focus on specific details, numbers, names, methodologies, exact findings in the summary
4. Each question should target information that requires careful reading but has a clear, short answer

QUESTION DISTRIBUTION TARGET:
- 70%+ Short Answer Deep Queries (specific facts, numbers, methods, authors, dates)
- 30% Traditional research questions (for variety)

Format each question as:
Q1: [Specific question requiring deep analysis but short answer - USE MANDATORY PATTERNS]
DIFFICULTY: Easy/Medium/Hard
TYPE: factual_specific/methodological/quantitative/relational
REASONING: Why this requires deep analysis but has a short answer

CRITICAL: Prioritize questions that start with "What was the exact...", "Which specific...", "Who first...", "What percentage...", "In which year...", etc.

Generate exactly {num_questions} questions now:"""

        # 增加token限制以确保完整生成
        estimated_tokens = num_questions * 150 + 2000
        max_tokens = min(max(estimated_tokens, 8000), 16000)
        
        return self.generate_text(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=0.7,  # 降低温度以获得更一致的结果
            system_prompt=system_prompt
        )
    
    def generate_answer(self, question: str, report: str, difficulty: str) -> APIResponse:
        """生成答案 - 专业浓缩核心回答系统"""
        
        # 检查是否为短答案深度查询
        is_short_answer_query = self._is_short_answer_deep_query(question)
        
        if is_short_answer_query:
            # Short Answer Deep Query: 专业浓缩核心回答
            system_prompt = """You are a subject matter expert providing CONCENTRATED PROFESSIONAL ANSWERS.

CORE PRINCIPLE: Extract and distill the ESSENTIAL PROFESSIONAL ANSWER to the specific query.

🎯 PROFESSIONAL CONCENTRATION REQUIREMENTS:
1. DIRECT QUERY RESPONSE: Answer the exact question asked, nothing more
2. PROFESSIONAL ACCURACY: Use precise technical/academic terminology
3. CONCENTRATED ESSENCE: Distill to the core fact/concept/finding
4. VERIFICATION READY: Answer must be independently verifiable
5. EXPERT-LEVEL PRECISION: Use field-appropriate professional language

📋 ANSWER TYPES & FORMATS:

FOR QUANTITATIVE QUERIES:
- Exact numbers with context: "94.2% classification accuracy"
- Precise measurements: "500 participants across 3 institutions"
- Statistical values: "p < 0.001, Cohen's d = 1.2"

FOR METHODOLOGICAL QUERIES:
- Technical precision: "Random Forest with bagging ensemble"
- Algorithm specifications: "BERT-base transformer architecture"
- Procedure names: "Cross-validation with stratified sampling"

FOR TEMPORAL/ATTRIBUTION QUERIES:
- Precise citations: "Smith et al. (2023, Nature Methods)"
- Institutional attribution: "Stanford AI Lab in collaboration with MIT"
- Chronological precision: "First proposed in 2019, validated 2021-2023"

FOR TECHNICAL SPECIFICATION QUERIES:
- Component details: "768-dimensional embedding layer"
- Configuration specifics: "Learning rate 0.001, batch size 32"
- Hardware specifications: "Tesla V100 GPUs, 32GB memory"

❌ NEVER PROVIDE:
- Background explanations or context
- Multiple facts when only one is asked
- Hedging language ("approximately", "around")
- Introductory phrases ("The study found that...")

✅ EXAMPLES OF CONCENTRATED PROFESSIONAL ANSWERS:
Query: "What exact accuracy was achieved?"
Answer: "94.2% macro-averaged F1 score"

Query: "Which algorithm was used for classification?"
Answer: "Random Forest with 100 decision trees"

Query: "How many participants were included?"
Answer: "500 participants (250 control, 250 treatment)"

Query: "Who first proposed this methodology?"
Answer: "Hinton et al. (2006) in deep belief networks paper"

CRITICAL: Your answer must be PROFESSIONALLY CONCENTRATED - the essential expert response to the specific query."""
            
            prompt = f"""Research Context: {report[:2000]}

EXPERT QUERY: {question}

TASK: Provide the concentrated professional answer to this specific query.

INSTRUCTIONS:
1. Identify the exact information requested
2. Extract the precise professional answer from the research context
3. Formulate using appropriate technical/academic terminology
4. Ensure answer is independently verifiable
5. Concentrate to essential core - no elaboration

CONCENTRATED PROFESSIONAL ANSWER:"""
            
            max_tokens = 50  # 稍微增加允许专业术语完整表达
            temperature = 0.1  # 确保精确性
            
        else:
            # 传统的长答案格式
            word_requirements = {
                "Easy": "400-600 words",
                "Medium": "800-1200 words", 
                "Hard": "1500-2000 words"
            }
            
            word_req = word_requirements.get(difficulty, "800-1200 words")
            
            system_prompt = f"""You are a professional research expert. Please answer questions based on the provided research summary.

Answer requirements:
1. Length: {word_req}
2. Based on summary content, do not fabricate information
3. Clear structure and rigorous logic
4. Adjust answer depth according to question difficulty
5. Use academic writing style
6. Answer ENTIRELY in English for consistency in comparative analysis"""

            prompt = f"""Based on the following research summary, answer the question:

Question: {question}
Difficulty: {difficulty}

Research Summary:
{report}

Please provide a detailed answer of {word_req}. Write entirely in English for consistency in comparative analysis."""

            max_tokens = 2000 if difficulty == "Hard" else 1500 if difficulty == "Medium" else 1000
            temperature = 0.7
        
        return self.generate_text(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            system_prompt=system_prompt
        )
    
    def _is_short_answer_deep_query(self, question: str) -> bool:
        """判断是否为短答案深度查询 - 更精确的识别"""
        question_lower = question.lower()
        
        # 精确的短答案模式（答案应该是具体的数字、名称、术语）
        exact_short_patterns = [
            # 数字相关
            "what exact", "what precise", "how many", "what percentage",
            "what number", "what amount", "what value", "what rate",
            "what score", "what accuracy", "what size",
            
            # 名称相关  
            "which specific", "who first", "which author", "which researcher",
            "which institution", "which university", "which company",
            "which algorithm", "which method", "which technique",
            "which approach", "which model", "which system",
            
            # 时间相关
            "what year", "when did", "what date", "which year",
            "what time", "what period",
            
            # 技术术语相关
            "what was the", "which was the", "what type of",
            "which type of", "what kind of", "which kind of"
        ]
        
        # 检查是否有精确的短答案模式
        has_exact_pattern = any(pattern in question_lower for pattern in exact_short_patterns)
        
        # 排除长答案指示词
        long_answer_indicators = [
            "why", "how does", "what are the main", "what are the key",
            "explain", "describe", "analyze", "compare", "evaluate",
            "discuss", "what factors", "what causes", "what leads to",
            "what are the implications", "what are the benefits",
            "what are the challenges", "what are the limitations"
        ]
        
        has_long_indicator = any(indicator in question_lower for indicator in long_answer_indicators)
        
        # 只有精确短答案模式且没有长答案指示词才被认为是短答案问题
        return has_exact_pattern and not has_long_indicator
    
    def refine_question(self, question: str, feedback: str, report: str) -> APIResponse:
        """优化问题"""
        
        system_prompt = """你是一位问题优化专家。请根据反馈意见改进问题质量。

优化要求：
1. 提高问题的研究深度
2. 增强多步骤思考要求
3. 确保问题基于报告内容
4. 保持问题的清晰性和可回答性"""

        prompt = f"""请根据以下反馈优化问题：

原问题：{question}

反馈意见：{feedback}

相关报告内容：
{report[:1000]}...

请提供优化后的问题。"""

        return self.generate_text(
            prompt=prompt,
            max_tokens=500,
            temperature=0.8,
            system_prompt=system_prompt
        )

def test_claude_client():
    """测试Claude客户端"""
    try:
        client = ClaudeAPIClient()
        
        # 测试简单文本生成
        response = client.generate_text("请简单介绍人工智能的发展历程。", max_tokens=500)
        
        if response.success:
            print("Claude API测试成功！")
            print(f"模型: {response.model}")
            print(f"Token使用: {response.usage}")
            print(f"响应内容: {response.content[:200]}...")
        else:
            print(f"Claude API测试失败: {response.error}")
            
    except Exception as e:
        print(f"Claude客户端初始化失败: {e}")

if __name__ == "__main__":
    test_claude_client() 
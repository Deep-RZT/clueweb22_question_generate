#!/usr/bin/env python3
"""
OpenAI API Client for Deep Research QA Benchmark
Replaces Claude API with OpenAI GPT-4o for all content generation
"""

import json
import requests
import time
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# 设置日志
logger = logging.getLogger(__name__)

@dataclass
class APIResponse:
    """统一的API响应格式"""
    content: str
    model: str
    usage: Dict[str, int]
    success: bool
    error: Optional[str] = None

class OpenAIClient:
    """OpenAI API client for content generation"""
    
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.api_key = api_key
        self.model = model
        self.api_url = "https://api.openai.com/v1/chat/completions"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
    def generate_content(self, prompt: str, system_prompt: str = None, 
                        max_tokens: int = 6000, temperature: float = 0.7,
                        max_retries: int = 3, retry_delay: float = 2.0) -> Optional[str]:
        """
        Generate content using OpenAI API with optimized parameters for longer responses
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate (increased for longer responses)
            temperature: Sampling temperature
            max_retries: Maximum number of retry attempts
            retry_delay: Delay between retries in seconds
            
        Returns:
            Generated content or None if failed
        """
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        data = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": 0.9,
            "frequency_penalty": 0.1,
            "presence_penalty": 0.1
        }
        
        for attempt in range(max_retries):
            try:
                print(f"  🔄 OpenAI API调用 (尝试 {attempt + 1}/{max_retries})")
                
                response = requests.post(self.api_url, headers=self.headers, json=data, timeout=30)
                response.raise_for_status()
                
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    content = result['choices'][0]['message']['content'].strip()
                    print(f"  ✅ API调用成功 (内容长度: {len(content)}字符)")
                    return content
                else:
                    if attempt < max_retries - 1:
                        print(f"  ⚠️ 响应无内容，{retry_delay}秒后重试...")
                        time.sleep(retry_delay)
                        continue
                    else:
                        print(f"❌ No choices in OpenAI response after {max_retries} attempts: {result}")
                        return None
                        
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:  # Rate limit
                    if attempt < max_retries - 1:
                        # 尝试从响应头中读取建议的等待时间
                        retry_after = e.response.headers.get('Retry-After')
                        if retry_after:
                            wait_time = int(retry_after)
                        else:
                            # 更保守的指数退避
                            wait_time = min(retry_delay * (2 ** attempt), 60)  # 最大60秒
                        
                        print(f"  🚦 API速率限制，{wait_time}秒后重试...")
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"❌ Rate limit exceeded after {max_retries} attempts")
                        return None
                elif e.response.status_code >= 500:  # Server errors
                    if attempt < max_retries - 1:
                        print(f"  🔧 服务器错误 ({e.response.status_code})，{retry_delay}秒后重试...")
                        time.sleep(retry_delay)
                        continue
                    else:
                        print(f"❌ Server error {e.response.status_code} after {max_retries} attempts")
                        return None
                else:
                    print(f"❌ HTTP error: {e}")
                    return None
                    
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    print(f"  🔌 网络错误，{retry_delay}秒后重试...")
                    time.sleep(retry_delay)
                    continue
                else:
                    print(f"❌ OpenAI API request failed after {max_retries} attempts: {e}")
                    return None
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"  ❌ 未知错误，{retry_delay}秒后重试...")
                    time.sleep(retry_delay)
                    continue
                else:
                    print(f"❌ OpenAI API error after {max_retries} attempts: {e}")
                    return None
        
        return None
    
    def generate_response(self, prompt: str, system_prompt: str = None, 
                         max_tokens: int = 2000, temperature: float = 0.3,
                         max_retries: int = 10) -> str:
        """
        Alias for generate_content method to maintain compatibility with existing code
        """
        result = self.generate_content(prompt, system_prompt, max_tokens, temperature, max_retries)
        return result if result is not None else ""
    
    def generate_text(self, 
                     prompt: str, 
                     max_tokens: int = 4000,
                     temperature: float = 0.7,
                     system_prompt: Optional[str] = None,
                     max_retries: int = 3,
                     retry_delay: float = 2.0) -> APIResponse:
        """生成文本 - 与Claude API兼容的接口，增加重试机制"""
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        data = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": 0.9,
            "frequency_penalty": 0.1,
            "presence_penalty": 0.1
        }
        
        for attempt in range(max_retries):
            try:
                print(f"  🔄 OpenAI API调用 (尝试 {attempt + 1}/{max_retries})")
                
                response = requests.post(self.api_url, headers=self.headers, json=data, timeout=30)
                response.raise_for_status()
                
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    content = result['choices'][0]['message']['content'].strip()
                    usage = result.get('usage', {})
                    
                    print(f"  ✅ API调用成功 (tokens: {usage.get('total_tokens', 0)})")
                    return APIResponse(
                        content=content,
                        model=self.model,
                        usage={
                            "prompt_tokens": usage.get('prompt_tokens', 0),
                            "completion_tokens": usage.get('completion_tokens', 0),
                            "total_tokens": usage.get('total_tokens', 0)
                        },
                        success=True
                    )
                else:
                    if attempt < max_retries - 1:
                        print(f"  ⚠️ 响应无内容，{retry_delay}秒后重试...")
                        time.sleep(retry_delay)
                        continue
                    else:
                        return APIResponse(
                            content="",
                            model=self.model,
                            usage={},
                            success=False,
                            error="No choices in response after all retries"
                        )
                        
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:  # Rate limit
                    if attempt < max_retries - 1:
                        # 尝试从响应头中读取建议的等待时间
                        retry_after = e.response.headers.get('Retry-After')
                        if retry_after:
                            wait_time = int(retry_after)
                        else:
                            # 更保守的指数退避
                            wait_time = min(retry_delay * (2 ** attempt), 60)  # 最大60秒
                        
                        print(f"  🚦 API速率限制，{wait_time}秒后重试...")
                        time.sleep(wait_time)
                        continue
                    else:
                        return APIResponse(
                            content="",
                            model=self.model,
                            usage={},
                            success=False,
                            error=f"Rate limit exceeded after {max_retries} attempts"
                        )
                elif e.response.status_code >= 500:  # Server errors
                    if attempt < max_retries - 1:
                        print(f"  🔧 服务器错误 ({e.response.status_code})，{retry_delay}秒后重试...")
                        time.sleep(retry_delay)
                        continue
                    else:
                        return APIResponse(
                            content="",
                            model=self.model,
                            usage={},
                            success=False,
                            error=f"Server error {e.response.status_code} after {max_retries} attempts"
                        )
                else:
                    return APIResponse(
                        content="",
                        model=self.model,
                        usage={},
                        success=False,
                        error=f"HTTP error: {str(e)}"
                    )
                    
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    print(f"  🔌 网络错误，{retry_delay}秒后重试...")
                    time.sleep(retry_delay)
                    continue
                else:
                    return APIResponse(
                        content="",
                        model=self.model,
                        usage={},
                        success=False,
                        error=f"Request failed after {max_retries} attempts: {str(e)}"
                    )
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"  ❌ 未知错误，{retry_delay}秒后重试...")
                    time.sleep(retry_delay)
                    continue
                else:
                    return APIResponse(
                        content="",
                        model=self.model,
                        usage={},
                        success=False,
                        error=f"API error after {max_retries} attempts: {str(e)}"
                    )
        
        return APIResponse(
            content="",
            model=self.model,
            usage={},
            success=False,
            error="Max retries exceeded"
        )
    
    def generate_report(self, documents: List[Dict], topic: str, max_tokens: int = 4000) -> APIResponse:
        """生成领域报告 - 支持分段处理和融合"""
        
        # 检查文档总长度
        total_chars = sum(len(doc.get('content', '')) for doc in documents)
        max_chars_per_segment = 80000  # OpenAI使用更保守的限制
        
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
        max_chars = 120000  # 约相当于120K tokens的安全限制，为OpenAI留更多余地
        
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
                    print(f"⚠️ 文档过多，只使用前 {i-1} 个文档生成报告")
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
        
        print(f"📊 使用文档内容长度: {total_chars} 字符")
        
        system_prompt = """You are an expert research synthesizer. Create a flowing narrative that naturally weaves together all document content into a cohesive research landscape overview.

Requirements for natural narrative synthesis:
1. Length: 1200-1800 words (comprehensive coverage - MUST reach at least 1200 words)
2. Write as a continuous research narrative that flows naturally from topic to topic
3. COMPLETELY AVOID any structural markers like "Abstract", "Introduction", "Methods", "Results", "Conclusion", "Summary", section numbers, bullet points, or formal organization
4. Instead of categorizing information, tell the story of the research field as revealed through these documents
5. Weave together ALL specific details naturally: exact numbers, percentages, sample sizes, parameter settings, performance metrics, researcher names, dates, institutions, methodologies
6. Create natural transitions between different research threads and findings
7. Write ENTIRELY in English for consistency
8. If documents contain Japanese content, seamlessly integrate the translated concepts into the English narrative
9. Make it read like an expert's comprehensive knowledge synthesis rather than a formal academic summary
10. CRITICAL: Ensure every factual detail is preserved in the narrative flow to enable complex multi-document reasoning questions"""

        prompt = f"""Create a comprehensive research narrative that weaves together all the information from these documents into a flowing story of the research landscape. YOU MUST WRITE AT LEAST 1200 WORDS:

{doc_content}

CRITICAL NARRATIVE REQUIREMENTS:
1. Length: MINIMUM 1200 words, target 1500-1800 words (this is MANDATORY)
2. Write as a continuous narrative that tells the story of the research field - how different studies connect, build upon each other, and reveal patterns
3. COMPLETELY ELIMINATE any formal structure: no sections, no "Abstract/Introduction/Conclusion", no numbered points, no bullet lists, no headers
4. Naturally integrate EVERY factual detail into the flowing narrative: exact numbers, percentages, sample sizes, parameter values, performance metrics, researcher names, publication dates, institutional affiliations, technical specifications
5. Show the connections and relationships between different research efforts, methodologies, and findings as they naturally emerge in the narrative
6. Create seamless transitions that show how one research finding leads to or relates to another
7. Write ENTIRELY in English - if documents contain Japanese content, smoothly integrate translated concepts
8. Make it read like an expert researcher explaining the comprehensive state of the field to a colleague, not like a formal academic summary
9. Preserve every numerical result, methodology detail, and technical specification within the natural flow of the narrative
10. CRITICAL: The narrative must contain enough interconnected factual details to support complex questions requiring multi-document reasoning and cross-referencing

IMPORTANT: Write as if you're telling the complete story of this research area. Count your words as you write. You MUST reach at least 1200 words by expanding on the relationships between studies, detailed explanations of methodologies, and comprehensive coverage of all findings and technical details."""

        return self.generate_text(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=0.7,
            system_prompt=system_prompt
        )
    
    def _generate_segmented_report(self, documents, topic_id=None):
        """分段生成报告"""
        try:
            # 分段处理
            segments = self._split_documents(documents)
            segment_reports = []
            
            for i, segment in enumerate(segments):
                logger.info(f"  🔍 处理第 {i+1}/{len(segments)} 段...")
                logger.info(f"📊 使用文档内容长度: {len(segment)} 字符")
                
                # 每段目标字数更高
                target_words = max(1000, min(1500, len(segment) // 40))
                
                prompt = f"""Based on the following document content, generate a detailed segment report.

CRITICAL REQUIREMENTS:
1. Word count: MANDATORY minimum {target_words} words - count your words as you write
2. Content requirements:
   - Detailed description of ALL information, data, methods and findings
   - Include EVERY specific number, percentage, statistical data found
   - Mention ALL research methods, experimental parameters, sample information
   - Cover ALL authors, institutions, time, location and specific information
   - Include ALL detailed cases, examples and technical details
   - Elaborate extensively on every finding and methodology
3. Writing requirements:
   - Maximum information density, avoid any empty descriptions
   - Use extremely rich details and specific data
   - Ensure comprehensive and extremely in-depth content
   - NEVER use section headers or markdown formatting
   - Write as continuous flowing narrative

IMPORTANT: If you haven't reached {target_words} words, continue adding more detail until you reach the minimum word count.

Document content:
{segment}

Generate a detailed segment report (minimum {target_words} words):"""

                response = self.generate_text(
                    prompt=prompt,
                    max_tokens=2500,  # 增加token限制
                    temperature=0.3,
                    system_prompt="You are a professional academic report writing expert, skilled at generating detailed, information-rich segment reports."
                )
                
                if response.success:
                    segment_report = response.content
                    word_count = len(segment_report.split())
                    segment_reports.append(segment_report)
                    logger.info(f"    ✅ 第{i+1}段完成 ({word_count} 词)")
                else:
                    logger.error(f"    ❌ 第{i+1}段生成失败: {response.error}")
                    return None
            
            # 融合各段报告 - 关键优化
            logger.info("  🔄 融合各段报告...")
            merged_report = self._merge_segment_reports(segment_reports)
            
            return merged_report
            
        except Exception as e:
            logger.error(f"分段生成报告失败: {str(e)}")
            return None

    def _split_documents(self, documents, max_chars_per_segment=80000):
        """分割文档为多个段落"""
        try:
            # 如果documents是字符串，直接分割
            if isinstance(documents, str):
                text = documents
            else:
                # 如果是列表，合并为字符串
                text = " ".join(str(doc) for doc in documents)
            
            segments = []
            current_segment = ""
            
            # 按句子分割
            sentences = text.split('.')
            
            for sentence in sentences:
                if len(current_segment) + len(sentence) + 1 <= max_chars_per_segment:
                    current_segment += sentence + "."
                else:
                    if current_segment:
                        segments.append(current_segment)
                    current_segment = sentence + "."
            
            # 添加最后一段
            if current_segment:
                segments.append(current_segment)
            
            return segments
            
        except Exception as e:
            logger.error(f"分割文档失败: {str(e)}")
            return [documents]  # 返回原始文档

    def _merge_segment_reports(self, segment_reports):
        """融合分段报告 - 关键优化"""
        try:
            # 计算目标字数 - 避免过长
            total_segment_words = sum(len(report.split()) for report in segment_reports)
            target_words = max(1000, min(1500, total_segment_words // 3))
            
            # 构建融合prompt
            segments_text = "\n\n".join([f"Segment Report {i+1}:\n{report}" for i, report in enumerate(segment_reports)])
            
            prompt = f"""Please merge the following multiple segment reports into a complete comprehensive report.

CRITICAL REQUIREMENTS:
1. Word count: MANDATORY minimum {target_words} words - count your words as you write
2. Merging requirements:
   - Integrate ALL information from ALL segments, avoid any omissions
   - Merge similar topics while avoiding repetition
   - Retain ALL specific data, numbers, methods, findings
   - Retain ALL authors, institutions, time and other information
   - Maintain logical coherence and fluency
3. Content requirements:
   - Detailed description of ALL research findings and data
   - Include ALL specific numbers, percentages, statistical information
   - Mention ALL detailed research methods and technical details
   - Cover ALL cases and application scenarios
   - Elaborate extensively on every finding and methodology
4. Structure requirements:
   - NEVER use section headers like "Abstract", "Introduction", "Conclusion", "Summary"
   - NEVER use markdown headers (##, ###) or numbered sections
   - Write as continuous flowing narrative without formal structure
   - Naturally organize content by topic importance
   - Ensure maximum information density and rich content

IMPORTANT: If you haven't reached {target_words} words, continue adding more detail about methodologies, experimental procedures, results analysis, and technical specifications until you reach the minimum word count.

Segment report content:
{segments_text}

Generate a detailed merged report (minimum {target_words} words):"""

            response = self.generate_text(
                prompt=prompt,
                max_tokens=3000,  # 大幅增加token限制
                temperature=0.2,   # 降低温度确保一致性
                system_prompt="You are a professional academic report merging expert, skilled at integrating multiple segment reports into information-rich comprehensive reports."
            )
            
            if response.success:
                merged_report = response.content
                word_count = len(merged_report.split())
                logger.info(f"    ✅ 报告融合完成 ({word_count} 词)")
                return merged_report
            else:
                logger.error(f"    ❌ 报告融合失败: {response.error}")
                return None
            
        except Exception as e:
            logger.error(f"融合报告失败: {str(e)}")
            return None

    def generate_deep_short_answer_questions(self, report: str, topic: str, num_questions: int = 50) -> APIResponse:
        """生成Deep Short Answer Questions - 基于您的要求优化"""
        
        system_prompt = f"""You are an expert in creating "Deep Short-Answer Queries" that require sophisticated multi-document reasoning but have concise, verifiable answers.

CORE DESIGN PHILOSOPHY (Based on Research Requirements):
1. **DEEP**: Cannot be answered by simple RAG - requires multi-step reasoning across document sections
2. **SHORT ANSWER**: 1-10 words, objectively verifiable (correct/incorrect can be directly judged)
3. **MULTI-DOCUMENT SYNTHESIS**: Requires combining information from different parts of the narrative
4. **HIDDEN CONNECTIONS**: Tests understanding of implicit relationships rather than explicit statements

DEEP QUERY DESIGN PATTERNS:

🔍 **CROSS-SECTION SYNTHESIS QUERIES**:
"What exact [metric] was achieved by [method] that also demonstrated [secondary property] in studies using [constraint]?"
→ Requires finding method, locating its metrics, and cross-referencing secondary properties

🔍 **IMPLICIT RELATIONSHIP DISCOVERY**:
"Which [entity] appears in both [context A] and [context B] research but with different [characteristic]?"
→ Requires scanning multiple research contexts and identifying cross-appearances

🔍 **DETAIL INTEGRATION QUERIES**:
"What [specific parameter] was used in experiments that achieved [result A] but not [result B]?"
→ Requires comparing different experimental setups and identifying distinguishing factors

🔍 **TEMPORAL/CAUSAL REASONING**:
"Who first [action] before later [related action] that influenced [outcome]?"
→ Requires understanding chronological relationships and causal connections

🔍 **HIDDEN PATTERN DISCOVERY**:
"What characteristic is shared by all studies that achieved [threshold] but absent in those below [threshold]?"
→ Requires pattern analysis across multiple research examples

CRITICAL REQUIREMENTS:
1. **Multi-step reasoning required**: Simple search should fail
2. **Short, factual answers**: Names, numbers, exact terms, dates
3. **Objectively verifiable**: Clear right/wrong determination possible
4. **Based on narrative content**: Only use information from the provided research narrative
5. **Reasonable difficulty**: Challenging but solvable with careful analysis

STRICTLY AVOID:
- Simple fact lookup questions ("What is X?")
- Questions answerable by keyword search
- Subjective or opinion-based questions
- Questions requiring external knowledge

TARGET: Generate exactly {num_questions} deep short-answer questions."""

        prompt = f"""Based on the following research narrative about "{topic}", create {num_questions} Deep Short-Answer Queries that require multi-document reasoning:

Research Narrative:
{report[:8000]}...

REQUIREMENTS:
1. Generate EXACTLY {num_questions} questions
2. Each question must require 2-3 reasoning steps across different parts of the narrative
3. Answers must be 1-10 words and objectively verifiable
4. Test understanding of connections, patterns, and relationships rather than simple facts
5. Focus on information synthesis rather than information retrieval

Question Format:
Q1: [Deep question requiring multi-step reasoning]
Q2: [Deep question requiring multi-step reasoning]
...

CRITICAL: Ensure each question tests deep understanding of the research landscape while maintaining short, verifiable answers."""

        return self.generate_text(
            prompt=prompt,
            max_tokens=min(max(num_questions * 100, 4000), 12000),
            temperature=0.6,
            system_prompt=system_prompt
        )

    def generate_questions(self, report: str, topic: str, num_questions: int = 50) -> APIResponse:
        """生成Short Answer Deep Query问题 - 基于BrowseComp标准，重点生成短答案深度查询"""
        
        system_prompt = """You are an expert question designer specializing in creating "Academic-Grade BrowseComp-style Deep Query" questions that meet high scholarly standards.

CRITICAL MISSION: Generate questions that achieve 3.0+/4 depth score and 2.0+/4 academic rigor score to reach 70%+ Good+ rating.

PROVEN SUCCESSFUL PATTERNS (BASED ON BEST RESULTS):

🎯 **PATTERN 1 - Multi-Constraint Academic Chain** (Target: 3.5+/4 depth):
"What was the exact [metric] achieved by [method] in the peer-reviewed study that also reported [secondary finding], was conducted by researchers who previously worked on [related topic] at [institution], and used [experimental design] with [dataset] between [time period]?"

🎯 **PATTERN 2 - Temporal Academic Lineage** (Target: 3.5+/4 depth):
"Which specific [technique] was first proposed by [author] who later collaborated with [institution] researchers in the controlled experiment that achieved [performance], was peer-reviewed by [venue], and whose methodology was subsequently validated in [follow-up study]?"

🎯 **PATTERN 3 - Cross-Institutional Research** (Target: 3.0+/4 academic):
"Who first proposed [concept] that was later cited in the peer-reviewed study achieving [metric], involved collaboration between [institution A] and [institution B], was published in [venue/year], and whose methodology became the standard for [field]?"

🎯 **PATTERN 4 - Methodological Validation** (Target: 2.5+/4 academic):
"What was the precise [parameter] in the [year] empirical study that compared [method A] against [method B] using [experimental design], reported statistical significance of [p-value], was conducted by [institution] researchers, and whose results were later replicated by [follow-up team]?"

BALANCED ACADEMIC RIGOR REQUIREMENTS (EVERY QUESTION MUST INCLUDE 3+):
✅ Methodological terms: "controlled experiment", "peer-reviewed", "empirical validation", "statistical significance"
✅ Experimental design: "randomized trial", "cross-validation", "baseline comparison", "ablation study"
✅ Precise metrics: "exact accuracy", "statistical significance", "confidence interval", "effect size"
✅ Publication context: "published in", "peer-reviewed by", "conference proceedings"
✅ Validation evidence: "results replicated", "methodology validated", "findings confirmed"
✅ Temporal progression: "first proposed", "later cited", "subsequently validated"
✅ Cross-institutional: "collaboration between", "joint research", "multi-site study"

OPTIMAL DEPTH REQUIREMENTS (EVERY QUESTION MUST ACHIEVE):
1. Chain 4+ constraints per question (proven effective)
2. Require 2+ temporal reasoning steps
3. Demand 1+ cross-institutional connections
4. Need 1+ methodological validation steps
5. Include literature impact assessment
6. Require replication/adoption evidence

ACADEMIC VOCABULARY (USE STRATEGICALLY):
- High-impact terms: "peer-reviewed", "controlled experiment", "statistical significance"
- Methodological terms: "empirical validation", "cross-validation", "baseline comparison"
- Impact terms: "cited in studies", "became standard", "methodology adopted"
- Collaboration terms: "multi-institutional", "joint research", "collaboration between"

BALANCED SUCCESS CRITERIA (ACHIEVABLE TARGETS):
- Depth Score Target: 3.0+/4 (Deep level with 4+ constraints)
- Academic Score Target: 2.0+/4 (Solid academic rigor)
- Constraint Count: 4+ per question minimum
- Academic Terms: 3+ per question minimum
- Cross-references: 2+ per question minimum
- Temporal Steps: 2+ per question minimum

MANDATORY TARGET: Generate EXACTLY 90% Academic-Grade BrowseComp questions (proven ratio)

FORMAT: Use simple text format, numbered Q1, Q2, etc."""

        prompt = f"""Based on the following research summary about "{topic}", generate {num_questions} questions where EXACTLY 90% MUST BE Academic-Grade BrowseComp-style Deep Query type:

Research Summary:
{report[:6000]}...

ABSOLUTE MANDATORY REQUIREMENTS FOR ACADEMIC EXCELLENCE:
1. Generate EXACTLY {num_questions} questions
2. EXACTLY 90% MUST be Academic-Grade BrowseComp-style questions (use the mandatory patterns below)
3. Each question MUST achieve 3.0+/4 depth score and 2.0+/4 academic rigor score
4. EVERY question must include methodological terminology and experimental design elements

QUESTION DISTRIBUTION REQUIREMENT:
- EXACTLY {int(num_questions * 0.90)} Academic-Grade BrowseComp Deep Queries
- EXACTLY {int(num_questions * 0.10)} Methodologically rigorous traditional questions

MANDATORY ACADEMIC-GRADE PATTERNS (NO EXCEPTIONS - EVERY QUESTION MUST USE THESE):

PATTERN 1 - Multi-Layer Constraint (4+ constraints):
"What was the exact [metric] achieved by [method] in the peer-reviewed study that also reported [secondary finding], was conducted by researchers who previously worked on [related topic] at [institution], and used [experimental design] with [dataset] between [time period]?"

PATTERN 2 - Cross-Institutional Validation:
"Which specific [technique] was first proposed by [author] who later collaborated with [institution] researchers in the controlled experiment that achieved [performance], was peer-reviewed by [venue], and whose methodology was subsequently validated in [follow-up study]?"

PATTERN 3 - Temporal-Methodological Chain:
"What was the precise [parameter] in the [year] empirical study that compared [method A] against [method B] using [experimental design], reported statistical significance of [p-value], was conducted by [institution] researchers, and whose results were later replicated by [follow-up team]?"

PATTERN 4 - Academic Literature Integration:
"Who first proposed [concept] that was later cited in the peer-reviewed study achieving [metric], involved collaboration between [institution A] and [institution B], was published in [venue/year], and whose methodology became the standard for [field]?"

CRITICAL ACADEMIC REQUIREMENTS (EVERY QUESTION MUST INCLUDE):
✅ Methodological terms: "controlled experiment", "peer-reviewed", "empirical validation", "statistical significance"
✅ Experimental design: "randomized trial", "cross-validation", "ablation study", "baseline comparison"  
✅ Precise metrics: "exact accuracy", "confidence interval", "effect size", "p-value"
✅ Publication context: "published in", "peer-reviewed by", "conference proceedings"
✅ Replication/validation: "results replicated", "methodology validated", "findings confirmed"
✅ Temporal chains: "first proposed", "later cited", "subsequently validated"
✅ Cross-institutional: "collaboration between", "joint research", "multi-site study"

Format each question as:
Q1: [MUST use Academic-Grade patterns with 4+ constraints and methodological terms]
DEPTH ELEMENTS: [List the constraint count and reasoning steps]
ACADEMIC ELEMENTS: [List methodological and experimental design terms used]
VERIFICATION: [Confirm answer is specific, quantitative, and easily verifiable]

CRITICAL SUCCESS CRITERIA:
- Depth Score Target: 3.0+/4 (Deep level with 4+ constraints)
- Academic Score Target: 2.0+/4 (Solid academic rigor)
- Constraint Count: 4+ per question minimum
- Methodological Terms: 3+ per question minimum
- Cross-references: 2+ per question minimum

Generate exactly {num_questions} questions now with MAXIMUM academic rigor:"""

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
            # Short Answer Deep Query: 极致浓缩专业回答系统
            system_prompt = """You are an ULTRA-PRECISE answer extraction specialist for BrowseComp-style academic queries.

🚨 CRITICAL MISSION: Extract ONLY the CORE FACTUAL ANSWER - Maximum 10 words, 80 characters.

⚡ ULTRA-CONCENTRATION PROTOCOL:
1. EXTRACT ONLY: The specific fact/number/name being asked for
2. ZERO CONTEXT: No explanations, no background, no elaboration
3. PURE PRECISION: Use exact technical terminology only when essential
4. FACTUAL CORE: The verifiable answer element only
5. MAXIMUM BREVITY: Absolute minimum words to convey the fact

📊 EXTRACTION PATTERNS:

QUANTITATIVE EXTRACTION:
Query: "What exact accuracy...?" → "94.2%"
Query: "How many participants...?" → "500"
Query: "What batch size...?" → "128"

NAME/ATTRIBUTION EXTRACTION:
Query: "Who first proposed...?" → "Smith et al."
Query: "Which institution...?" → "Stanford"
Query: "Which algorithm...?" → "Random Forest"

TECHNICAL SPECIFICATION EXTRACTION:
Query: "What learning rate...?" → "0.001"
Query: "Which model...?" → "BERT-base"
Query: "What architecture...?" → "CNN-Transformer"

TEMPORAL EXTRACTION:
Query: "What year...?" → "2023"
Query: "When did...?" → "March 2023"

🚫 ABSOLUTE PROHIBITIONS:
- ANY explanatory text ("The study found that...")
- ANY context ("In the context of...")
- ANY qualifiers ("approximately", "around", "about")
- ANY full sentences with subjects and verbs
- ANY background information
- ANY multiple facts when only one is requested

✅ PERFECT EXTRACTION EXAMPLES:
❌ Wrong: "The study achieved an accuracy of 94.2% which was significantly higher than baseline"
✅ Correct: "94.2%"

❌ Wrong: "Random Forest algorithm with 100 decision trees was used for classification"
✅ Correct: "Random Forest"

❌ Wrong: "Smith and Brown first proposed this methodology in their 2022 paper"
✅ Correct: "Smith and Brown"

🎯 ULTIMATE GOAL: One precise fact, maximum brevity, zero elaboration."""
            
            prompt = f"""Research Context: {report[:1500]}

QUERY: {question}

EXTRACTION TASK: Extract ONLY the core factual answer.

CRITICAL CONSTRAINTS:
- Maximum 10 words
- Maximum 80 characters
- ZERO explanatory text
- ONLY the requested fact/number/name
- NO sentences or elaboration

ULTRA-CONCENTRATED ANSWER:"""
            
            max_tokens = 30  # 严格限制token数量
            temperature = 0.05  # 最低温度确保精确性
            
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
        """判断是否为短答案深度查询 - 增强的BrowseComp风格识别"""
        question_lower = question.lower()
        
        # BrowseComp风格指示器 - 基于实际测试数据优化
        browsecomp_indicators = [
            "depth elements:", "academic elements:", "verification:",
            "constraints", "peer-reviewed", "controlled experiment",
            "statistical significance", "randomized", "empirical study"
        ]
        
        # 检查是否为BrowseComp风格问题
        is_browsecomp_style = any(indicator in question_lower for indicator in browsecomp_indicators)
        
        # 精确的短答案模式（答案应该是具体的数字、名称、术语）
        exact_short_patterns = [
            # 数字相关 - 更精确的模式
            "what exact", "what precise", "how many", "what percentage",
            "what number", "what amount", "what value", "what rate",
            "what score", "what accuracy", "what size", "what batch size",
            "what learning rate", "what parameter count", "what training time",
            
            # 名称相关 - 扩展学术查询模式
            "which specific", "who first", "which author", "which researcher",
            "which institution", "which university", "which company",
            "which algorithm", "which method", "which technique",
            "which approach", "which model", "which system",
            "who developed", "who proposed", "who created",
            
            # 时间相关
            "what year", "when did", "what date", "which year",
            "what time", "what period", "when was",
            
            # 技术术语相关 - 更精确的学术查询
            "what was the", "which was the", "what type of",
            "which type of", "what kind of", "which kind of",
            "what is the name of", "what is called"
        ]
        
        # 检查是否有精确的短答案模式
        has_exact_pattern = any(pattern in question_lower for pattern in exact_short_patterns)
        
        # 排除长答案指示词
        long_answer_indicators = [
            "why", "how does", "what are the main", "what are the key",
            "explain", "describe", "analyze", "compare", "evaluate",
            "discuss", "what factors", "what causes", "what leads to",
            "what are the implications", "what are the benefits",
            "what are the challenges", "what are the limitations",
            "how can", "what should", "what would"
        ]
        
        has_long_indicator = any(indicator in question_lower for indicator in long_answer_indicators)
        
        # 增强的判断逻辑
        # 1. 如果明确是BrowseComp风格 + 有短答案模式 = 短答案查询
        if is_browsecomp_style and has_exact_pattern:
            return True
        
        # 2. 有精确短答案模式且没有长答案指示词
        if has_exact_pattern and not has_long_indicator:
            return True
        
        # 3. 特殊模式：包含约束要求的问题通常是BrowseComp短答案
        constraint_patterns = [
            "that also", "was conducted by", "published in", "achieved",
            "using", "with", "between", "reported", "involved"
        ]
        has_constraints = sum(1 for pattern in constraint_patterns if pattern in question_lower) >= 2
        
        if has_constraints and has_exact_pattern:
            return True
        
        return False
    
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

    def generate_with_retry(self, prompt: str, system_prompt: str = None,
                           max_tokens: int = 4000, temperature: float = 0.7,
                           max_retries: int = 3, retry_delay: float = 2.0) -> Optional[str]:
        """
        Generate content with retry logic
        
        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation
            max_retries: Maximum number of retries
            retry_delay: Delay between retries in seconds
            
        Returns:
            Generated content or None if all retries failed
        """
        
        for attempt in range(max_retries + 1):
            result = self.generate_content(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            if result is not None:
                return result
            
            if attempt < max_retries:
                print(f"   🔄 Retrying in {retry_delay} seconds... (attempt {attempt + 1}/{max_retries})")
                time.sleep(retry_delay)
        
        print(f"   ❌ All {max_retries + 1} attempts failed")
        return None

    def generate_simplified_report(self, documents, topic_id=None):
        """生成简化报告 - 智能分层处理，确保高质量输出"""
        try:
            # 计算总内容长度
            if isinstance(documents, str):
                total_length = len(documents)
                documents_text = documents
            else:
                # 如果是文档列表，先进行智能整合
                return self._generate_layered_report(documents, topic_id)
            
            # 如果内容过长，使用分段处理
            if total_length > 70000:
                return self._generate_segmented_report(documents_text, topic_id)
            
            # 计算目标字数（根据内容长度自适应）
            target_words = max(1200, min(2000, total_length // 40))
            
            prompt = f"""Based on the following documents, create a comprehensive narrative summary that integrates all the factual information into a flowing report.

REQUIREMENTS:
1. Target length: {target_words}-{target_words + 200} words 
2. AVOID ALL structured academic writing patterns:
   - No Abstract, Introduction, Methods, Results, Discussion, Conclusion sections
   - No "Summary:", "Overview:", "Background:" headers
   - No numbered/bulleted lists or formal subdivisions
   - No phrases like "This report examines", "In summary", "To conclude"
3. Write as a continuous factual narrative that naturally weaves together:
   - All specific research findings and numerical data
   - Methodological details and experimental approaches  
   - Author names, institutions, and collaborative relationships
   - Temporal sequences and research developments
   - Technical specifications and parameters
   - Statistical results and performance metrics

NARRATIVE APPROACH:
- Begin immediately with substantive content (no meta-commentary)
- Create natural topic transitions without formal organization
- Maintain dense information content throughout
- Use precise technical terminology
- Integrate cross-references and connections organically
- Focus purely on factual content extraction and synthesis

CRITICAL FOR BROWSECOMP: Include specific, verifiable facts that can support short-answer deep queries:
- Exact numerical values and percentages
- Specific author names and institutional affiliations
- Precise dates and timeframes
- Technical specifications and parameters
- Performance metrics and statistical results
- Methodological details and experimental conditions

Document content:
{documents_text}

Generate a comprehensive {target_words}-word factual narrative optimized for BrowseComp question generation:"""

            response = self.generate_text(
                prompt=prompt,
                max_tokens=3500,  # 增加token限制
                temperature=0.15,  # 更低温度确保精确性
                system_prompt="You are an expert at creating comprehensive factual narratives optimized for BrowseComp question generation. Transform document collections into flowing, information-dense reports that avoid academic structure while capturing all verifiable facts, numbers, names, dates, and technical specifications."
            )
            
            if response.success:
                return response.content
            else:
                logger.error(f"简化报告生成失败: {response.error}")
                return None
            
        except Exception as e:
            logger.error(f"生成简化报告失败: {str(e)}")
            return None

    def _generate_layered_report(self, documents, topic_id=None):
        """分层报告生成 - 处理文档列表"""
        try:
            # 第一层：整合文档内容
            logger.info(f"开始分层报告生成，文档数量: {len(documents)}")
            
            # 将文档按重要性分组
            high_value_docs = [doc for doc in documents if doc.get('combined_score', 0) > 0.7]
            medium_value_docs = [doc for doc in documents if 0.4 <= doc.get('combined_score', 0) <= 0.7]
            
            logger.info(f"高价值文档: {len(high_value_docs)}, 中等价值文档: {len(medium_value_docs)}")
            
            # 优先整合高价值内容
            priority_content = []
            total_length = 0
            
            # 添加高价值文档
            for doc in high_value_docs:
                if total_length + doc['char_count'] < 40000:  # 控制总长度
                    priority_content.append(f"Document {doc.get('doc_id', 'unknown')}: {doc['content']}")
                    total_length += doc['char_count']
            
            # 添加部分中等价值文档
            for doc in medium_value_docs:
                if total_length + doc['char_count'] < 50000:
                    priority_content.append(f"Document {doc.get('doc_id', 'unknown')}: {doc['content']}")
                    total_length += doc['char_count']
                else:
                    break
            
            integrated_content = "\n\n".join(priority_content)
            
            logger.info(f"整合后内容长度: {len(integrated_content)} 字符")
            
            # 第二层：生成高质量报告
            return self.generate_simplified_report(integrated_content, topic_id)
            
        except Exception as e:
            logger.error(f"分层报告生成失败: {str(e)}")
            return None

    def generate_short_answer_deep_questions(self, report, topic_id=None):
        """生成短答案深度问题 - 激进模板强制方法"""
        try:
            # 基于BrowseComp "Inverted Questions" 方法论的问题生成
            prompt = f"""Create 30 BrowseComp-style "Inverted Questions" following OpenAI's methodology from arXiv:2504.12516v1.

CORE BROWSECOMP PRINCIPLE: Start with specific facts from the report → Create questions that are "hard to find but easy to verify"

METHODOLOGY (from OpenAI paper):
1. Identify a "seed" (person, event, artifact) from the report
2. Find multiple characteristics with large search spaces  
3. Create intersection queries requiring "strategic persistence and creativity"
4. Ensure answers are easily verifiable but hard to find without guidance

TARGET DISTRIBUTION:
- 8 "What exact" questions (precision queries)
- 6 "Which specific" questions (identification queries)  
- 4 "Who first" questions (attribution queries)
- 4 "When did" questions (temporal queries)
- 4 "Where was" questions (location queries)
- 4 "How many" questions (quantitative queries)

BROWSECOMP QUESTION PATTERNS:

🔎 **Multi-Constraint Intersection**: "What exact [METRIC] did [METHOD] achieve in the study that also involved [CONSTRAINT_1], was conducted by [RESEARCHER] at [INSTITUTION], and used [TECHNIQUE] during [TIMEFRAME]?"

🔎 **Cross-Reference Chains**: "Which specific [ITEM] was first developed by [ENTITY_A] who later collaborated with [ENTITY_B] on [PROJECT] that achieved [OUTCOME] in [LOCATION]?"

🔎 **Temporal-Technical Intersections**: "In which [YEAR/MONTH] did [ENTITY] first [ACTION] while also [CONSTRAINT_1] and [CONSTRAINT_2] using [METHOD]?"

ANSWER REQUIREMENTS (OpenAI Standard):
- 1-15 words (balanced for precision and completeness)
- Easy to verify once found
- Buried in technical details but extractable
- Examples: "94.2% accuracy", "Stanford University", "Transformer architecture", "March 2019", "500 participants"

CONSTRAINT REQUIREMENTS (Each question needs 3+ intersecting constraints):
✓ FACTUAL: Exact numbers, percentages, measurements
✓ TEMPORAL: Specific dates, periods, sequences  
✓ INSTITUTIONAL: Universities, companies, research labs
✓ METHODOLOGICAL: Techniques, algorithms, experimental designs
✓ ATTRIBUTION: Author names, collaborations, citations

CRITICAL: Generate questions ONLY based on the specific facts, data, and information contained in the report below. Do NOT use external knowledge or topic information.

Report content (your ONLY source of information):
{report}

Generate exactly 30 "Inverted Questions" that exemplify BrowseComp's "easy to verify but hard to find" principle. Each question must be answerable ONLY from the information provided in the above report:"""

            response = self.generate_text(
                prompt=prompt,
                max_tokens=5000,  # Increase token limit for comprehensive generation
                temperature=0.05,  # Very low temperature for consistency
                system_prompt="You are an expert in OpenAI's BrowseComp methodology (arXiv:2504.12516v1). You create 'Inverted Questions' that start with specific facts and build multi-constraint intersection queries requiring 'strategic persistence and creativity' to solve. Your questions are designed to be 'easy to verify but hard to find' - a core principle where answers are short and verifiable but buried in complex constraint intersections that demand sophisticated browsing strategies."
            )
            
            if not response.success:
                logger.error(f"问题生成失败: {response.error}")
                return []
            
            questions_text = response.content
            
            # 解析问题
            questions = []
            lines = questions_text.split('\n')
            
            for line in lines:
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('Q')):
                    # 移除编号
                    if '. ' in line:
                        question = line.split('. ', 1)[1].strip()
                    elif ') ' in line:
                        question = line.split(') ', 1)[1].strip()
                    else:
                        question = line.strip()
                    
                    if question and len(question) > 20:  # Ensure substantial questions
                        # Validate that question follows BrowseComp patterns
                        if self._validate_browsecomp_question(question):
                            questions.append({
                                'question': question,
                                'topic_id': topic_id,
                                'type': 'short_answer_deep_query',
                                'difficulty': 'Hard',  # All BrowseComp questions are inherently hard
                                'constraints_detected': self._count_question_constraints(question)
                            })
            
            logger.info(f"BrowseComp问题生成成功: {len(questions)} 个有效问题")
            return questions
            
        except Exception as e:
            logger.error(f"生成短答案深度问题失败: {str(e)}")
            return []

    def _validate_browsecomp_question(self, question: str) -> bool:
        """验证问题是否符合BrowseComp标准"""
        question_lower = question.lower()
        
        # 检查短答案指示词（更宽泛的匹配）
        short_answer_indicators = [
            "what exact", "what precise", "which specific", "who first",
            "what was the", "how many", "what percentage", "in which year",
            "what amount", "which author", "which institution", "which method",
            "what year", "what is the", "how large", "how long", "what specific",
            "which", "what", "who", "when", "where"
        ]
        
        has_short_indicator = any(indicator in question_lower for indicator in short_answer_indicators)
        
        # 检查约束复杂性（降低要求）
        constraint_connectors = [
            "that also", "who also", "which also", "and", "while", "during", 
            "between", "involving", "conducted by", "reported", "achieved",
            "used", "in", "at", "by", "with", "using", "on"
        ]
        
        constraint_count = sum(1 for connector in constraint_connectors if connector in question_lower)
        
        # 排除明显的长答案问题
        long_answer_patterns = [
            "why", "how does", "explain how", "describe how", "analyze",
            "compare and contrast", "discuss the implications", "evaluate"
        ]
        
        has_long_pattern = any(pattern in question_lower for pattern in long_answer_patterns)
        
        # 更宽松的验证：有短答案指示词且不是明显的长答案问题
        return has_short_indicator and not has_long_pattern

    def _count_question_constraints(self, question: str) -> int:
        """计算问题中的约束数量 - 基于BrowseComp方法论优化"""
        question_lower = question.lower()
        
        # 更全面的约束指示词，基于BrowseComp的多约束交集理念
        constraint_categories = {
            'precision': ['exact', 'precise', 'specific'],
            'temporal': ['first', 'during', 'between', 'when', 'before', 'after', 'while', 'in which year', 'in which month'],
            'logical': ['also', 'and', 'both', 'either', 'that also', 'who also', 'which also'],
            'attribution': ['conducted by', 'published by', 'developed by', 'created by', 'authored by', 'reported by'],
            'institutional': ['at', 'from', 'university', 'institute', 'lab', 'company', 'organization'],
            'methodological': ['using', 'with', 'based on', 'through', 'via', 'by means of'],
            'achievement': ['achieved', 'reported', 'demonstrated', 'showed', 'resulted in'],
            'collaboration': ['collaborated', 'partnered', 'worked with', 'joint'],
            'validation': ['validated', 'confirmed', 'verified', 'replicated', 'cited'],
            'comparison': ['compared to', 'versus', 'against', 'relative to', 'better than'],
            'location': ['where', 'located', 'based in', 'situated'],
            'quantification': ['how many', 'how much', 'number of', 'amount of', 'percentage']
        }
        
        constraints_found = 0
        categories_used = set()
        
        # 计算每个类别的约束
        for category, indicators in constraint_categories.items():
            for indicator in indicators:
                if indicator in question_lower:
                    categories_used.add(category)
                    break  # 每个类别最多计算一次
        
        # 约束数量 = 使用的类别数量
        constraints_found = len(categories_used)
        
        # 额外的复杂性指标
        complexity_indicators = [
            ('nested clauses', len([x for x in ['that', 'which', 'who', 'where', 'when'] if x in question_lower])),
            ('multiple entities', len([x for x in ['and', 'both', 'either'] if x in question_lower])),
            ('time sequences', len([x for x in ['first', 'then', 'later', 'subsequently'] if x in question_lower]))
        ]
        
        # 为复杂结构添加额外约束
        for name, count in complexity_indicators:
            if count > 0:
                constraints_found += min(count, 2)  # 最多添加2个额外约束
        
        return constraints_found

# Compatibility functions for easy migration from Claude API
def call_openai_api(prompt: str, api_key: str, system_prompt: str = None,
                   max_tokens: int = 4000, temperature: float = 0.7) -> Optional[str]:
    """
    Compatibility function for easy migration from Claude API calls
    
    Args:
        prompt: User prompt
        api_key: OpenAI API key
        system_prompt: System prompt (optional)
        max_tokens: Maximum tokens to generate
        temperature: Temperature for generation
        
    Returns:
        Generated content or None if failed
    """
    client = OpenAIClient(api_key)
    return client.generate_content(
        prompt=prompt,
        system_prompt=system_prompt,
        max_tokens=max_tokens,
        temperature=temperature
    )

def call_openai_with_messages(api_key: str, messages: List[Dict[str, str]], 
                             model: str = "gpt-4o", max_tokens: int = 6000, 
                             temperature: float = 0.7) -> Optional[str]:
    """
    Call OpenAI API with messages format - optimized for longer responses
    
    Args:
        api_key: OpenAI API key
        messages: List of message dictionaries
        model: Model to use
        max_tokens: Maximum tokens (increased default)
        temperature: Sampling temperature
        
    Returns:
        Generated content or None if failed
    """
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    data = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": 0.9,
        "frequency_penalty": 0.1,
        "presence_penalty": 0.1
    }
    
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions", 
            headers=headers, 
            json=data, 
            timeout=120
        )
        response.raise_for_status()
        
        result = response.json()
        if 'choices' in result and len(result['choices']) > 0:
            return result['choices'][0]['message']['content'].strip()
        else:
            print(f"❌ No choices in OpenAI response: {result}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ OpenAI API request failed: {e}")
        return None
    except Exception as e:
        print(f"❌ OpenAI API error: {e}")
        return None

def get_difficulty_specific_system_prompt(difficulty: str) -> str:
    """
    Get system prompt optimized for specific difficulty levels
    
    Args:
        difficulty: Question difficulty (Easy, Medium, Hard)
        
    Returns:
        Optimized system prompt for the difficulty level
    """
    
    base_prompt = """You are an expert researcher providing comprehensive, evidence-based analysis. Your responses must be:

- Structured with clear sections (Introduction, Analysis, Synthesis, Conclusion)
- Well-cited with references to the domain report
- Academically rigorous and detailed
- Written in a formal, analytical style"""

    if difficulty == "Hard":
        return base_prompt + """

CRITICAL REQUIREMENTS FOR HARD QUESTIONS:
- Minimum 1500-2000 words
- Multi-dimensional analysis with interdisciplinary perspectives
- Deep synthesis of complex relationships and patterns
- Critical evaluation of methodological considerations
- Exploration of systemic implications and future developments
- Comprehensive evidence integration from multiple angles
- Sophisticated argumentation with nuanced conclusions

Focus on depth, complexity, and comprehensive coverage of all aspects."""

    elif difficulty == "Medium":
        return base_prompt + """

REQUIREMENTS FOR MEDIUM QUESTIONS:
- Target 800-1200 words
- Multi-step analytical thinking
- Synthesis of different aspects from the domain report
- Critical evaluation of evidence and limitations
- Clear pattern identification and relationship mapping
- Integration of theoretical and practical perspectives

Provide thorough analysis with moderate complexity."""

    else:  # Easy
        return base_prompt + """

REQUIREMENTS FOR EASY QUESTIONS:
- Target 400-600 words
- Clear, direct analysis
- Evidence-based reasoning
- Logical structure and flow
- Accessible but comprehensive coverage

Provide complete but concise analysis.""" 
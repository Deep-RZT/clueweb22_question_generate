#!/usr/bin/env python3
"""
OpenAI API Client for Deep Research QA Benchmark
Replaces Claude API with OpenAI GPT-4o for all content generation
"""

import json
import requests
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

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
                        max_tokens: int = 6000, temperature: float = 0.7) -> Optional[str]:
        """
        Generate content using OpenAI API with optimized parameters for longer responses
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate (increased for longer responses)
            temperature: Sampling temperature
            
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
        
        try:
            response = requests.post(self.api_url, headers=self.headers, json=data, timeout=120)
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
    
    def generate_text(self, 
                     prompt: str, 
                     max_tokens: int = 4000,
                     temperature: float = 0.7,
                     system_prompt: Optional[str] = None) -> APIResponse:
        """生成文本 - 与Claude API兼容的接口"""
        
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
        
        try:
            response = requests.post(self.api_url, headers=self.headers, json=data, timeout=120)
            response.raise_for_status()
            
            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0]['message']['content'].strip()
                usage = result.get('usage', {})
                
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
                return APIResponse(
                    content="",
                    model=self.model,
                    usage={},
                    success=False,
                    error="No choices in response"
                )
                
        except requests.exceptions.RequestException as e:
            return APIResponse(
                content="",
                model=self.model,
                usage={},
                success=False,
                error=f"Request failed: {str(e)}"
            )
        except Exception as e:
            return APIResponse(
                content="",
                model=self.model,
                usage={},
                success=False,
                error=f"API error: {str(e)}"
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
        
        system_prompt = """You are a professional research analyst. Please generate a high-quality domain report based on the provided documents.

Report requirements:
1. Length: 1500-2000 words
2. Clear structure with introduction, main findings, analysis, and conclusion
3. Deep analysis and synthesis based on document content
4. Use academic writing style
5. Write ENTIRELY in English for consistency in comparative analysis
6. If documents contain Japanese content, translate and analyze the concepts in English
7. Maintain academic rigor while ensuring all output is in English"""

        prompt = f"""Please generate a professional research report on "{topic}" based on the following documents:

{doc_content}

Generate a comprehensive 1500-2000 word research report that deeply analyzes the current state, trends, and key findings in this field. Write entirely in English. If the documents contain Japanese content, translate the key concepts and analyze them in English to ensure consistency for comparative analysis."""

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
                        'doc_count': len(segment_docs),
                        'usage': segment_result.usage
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
    
    def _split_documents_into_segments(self, documents: List[Dict], max_chars_per_segment: int = 80000) -> List[List[Dict]]:
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
        
        system_prompt = """You are a professional research analyst. Please merge and synthesize multiple segment reports into a single comprehensive report.

Merge requirements:
1. Length: 2000-2500 words (comprehensive synthesis)
2. Eliminate redundancy while preserving key insights
3. Create coherent flow and logical structure
4. Synthesize findings across all segments
5. Maintain academic writing style
6. Write ENTIRELY in English
7. Ensure the final report is well-structured with clear sections"""

        prompt = f"""Please merge the following segment reports about "{topic}" into a single comprehensive research report:

{reports_content}

Requirements:
- Create a unified, comprehensive report that synthesizes insights from all segments
- Eliminate redundancy while preserving unique insights from each segment
- Maintain logical flow and academic structure
- Target length: 2000-2500 words
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
                    'prompt_tokens': sum(r.get('usage', {}).get('prompt_tokens', 0) for r in segment_reports) + merge_result.usage.get('prompt_tokens', 0),
                    'completion_tokens': sum(r.get('usage', {}).get('completion_tokens', 0) for r in segment_reports) + merge_result.usage.get('completion_tokens', 0),
                    'total_tokens': 0
                }
                total_usage['total_tokens'] = total_usage['prompt_tokens'] + total_usage['completion_tokens']
                
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
        """生成问题 - 使用简单文本格式"""
        
        system_prompt = """You are a professional question design expert. Generate high-quality research questions based on the research report.

Question requirements:
1. Cover different difficulty levels: Easy (30%), Medium (40%), Hard (30%)
2. Diverse question types: fact lookup, analytical reasoning, comprehensive evaluation, critical thinking
3. Each question should be based on report content
4. Questions should evaluate deep research capabilities
5. Generate ALL questions in English for consistency in comparative analysis

IMPORTANT: Use simple text format, not JSON. Format each question as:
Q1: [Question text here]
DIFFICULTY: Easy/Medium/Hard
TYPE: Question type
REASONING: Why this question is valuable

Q2: [Next question]
DIFFICULTY: Easy/Medium/Hard
TYPE: Question type  
REASONING: Why this question is valuable"""

        prompt = f"""Based on the following research report about "{topic}", generate {num_questions} high-quality research questions:

Report content:
{report[:3000]}...

CRITICAL REQUIREMENTS:
1. Generate EXACTLY {num_questions} questions - THIS IS MANDATORY
2. Use the simple text format shown above
3. Difficulty distribution: ~{int(num_questions*0.3)} Easy, ~{int(num_questions*0.4)} Medium, ~{int(num_questions*0.3)} Hard
4. All content in English
5. Each question should be numbered Q1, Q2, Q3, ..., Q{num_questions}

DO NOT STOP until you have generated all {num_questions} questions. Count them to ensure you have exactly {num_questions}.

Generate the questions now:"""

        # 计算需要的token数量: 每个问题大约80-100 tokens
        estimated_tokens = num_questions * 100 + 500  # 加上缓冲
        max_tokens = min(max(estimated_tokens, 6000), 8000)  # 最少6000，最多8000
        
        return self.generate_text(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=0.8,
            system_prompt=system_prompt
        )
    
    def generate_answer(self, question: str, report: str, difficulty: str) -> APIResponse:
        """生成答案"""
        
        # 根据难度设置字数要求
        word_requirements = {
            "Easy": "400-600字",
            "Medium": "800-1200字", 
            "Hard": "1500-2000字"
        }
        
        word_req = word_requirements.get(difficulty, "800-1200字")
        
        system_prompt = f"""You are a professional research expert. Please answer questions based on the provided research report.

Answer requirements:
1. Length: {word_req}
2. Based on report content, do not fabricate information
3. Clear structure and rigorous logic
4. Adjust answer depth according to question difficulty
5. Use academic writing style
6. Answer ENTIRELY in English for consistency in comparative analysis"""

        prompt = f"""Based on the following research report, answer the question:

Question: {question}
Difficulty: {difficulty}

Research Report:
{report}

Please provide a detailed answer of {word_req}. Write entirely in English for consistency in comparative analysis."""

        max_tokens = 2000 if difficulty == "Hard" else 1500 if difficulty == "Medium" else 1000
        
        return self.generate_text(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=0.7,
            system_prompt=system_prompt
        )
    
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
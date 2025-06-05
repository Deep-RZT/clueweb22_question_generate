#!/usr/bin/env python3
"""
Claude API Client
重新集成Claude Sonnet 4 API支持
"""

import anthropic
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
    """Claude API客户端"""
    
    def __init__(self, api_key: Optional[str] = None):
        """初始化Claude客户端"""
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("Claude API key not found. Please set ANTHROPIC_API_KEY environment variable.")
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = "claude-3-5-sonnet-20241022"  # Claude Sonnet 4
        
        # 请求限制
        self.max_retries = 3
        self.retry_delay = 2
        
    def generate_text(self, 
                     prompt: str, 
                     max_tokens: int = 4000,
                     temperature: float = 0.7,
                     system_prompt: Optional[str] = None) -> APIResponse:
        """生成文本"""
        
        for attempt in range(self.max_retries):
            try:
                # 构建消息
                messages = [{"role": "user", "content": prompt}]
                
                # 调用Claude API
                kwargs = {
                    "model": self.model,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "messages": messages
                }
                
                if system_prompt:
                    kwargs["system"] = system_prompt
                
                response = self.client.messages.create(**kwargs)
                
                # 提取响应内容
                content = response.content[0].text if response.content else ""
                
                # 构建统一响应
                api_response = APIResponse(
                    content=content,
                    model=self.model,
                    usage={
                        "prompt_tokens": response.usage.input_tokens,
                        "completion_tokens": response.usage.output_tokens,
                        "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                    },
                    success=True
                )
                
                logger.info(f"Claude API调用成功 - 输入: {response.usage.input_tokens} tokens, 输出: {response.usage.output_tokens} tokens")
                return api_response
                
            except anthropic.RateLimitError as e:
                logger.warning(f"Claude API速率限制 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2 ** attempt))
                else:
                    return APIResponse(
                        content="",
                        model=self.model,
                        usage={},
                        success=False,
                        error=f"Rate limit exceeded: {str(e)}"
                    )
                    
            except anthropic.APIError as e:
                logger.error(f"Claude API错误 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    return APIResponse(
                        content="",
                        model=self.model,
                        usage={},
                        success=False,
                        error=f"API error: {str(e)}"
                    )
                    
            except Exception as e:
                logger.error(f"Claude API未知错误 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
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
    
    def generate_report(self, documents: List[Dict], topic: str, max_tokens: int = 4000) -> APIResponse:
        """生成领域报告"""
        
        # 构建文档内容
        doc_content = ""
        for i, doc in enumerate(documents, 1):
            doc_content += f"\n文档 {i}:\n标题: {doc.get('title', 'N/A')}\n内容: {doc.get('content', 'N/A')}\n"
        
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
    
    def generate_questions(self, report: str, topic: str, num_questions: int = 50) -> APIResponse:
        """生成问题"""
        
        system_prompt = """You are a professional question design expert. Please generate high-quality research questions based on the research report.

Question requirements:
1. Cover different difficulty levels: Easy (30%), Medium (40%), Hard (30%)
2. Diverse question types: fact lookup, analytical reasoning, comprehensive evaluation, critical thinking
3. Each question should be based on report content
4. Questions should evaluate deep research capabilities
5. Generate ALL questions in English for consistency in comparative analysis

Output format: JSON array, each question contains:
- question: Question content (in English only)
- difficulty: Easy/Medium/Hard
- type: Question type
- reasoning: Question design rationale (in English)"""

        prompt = f"""Based on the following research report about "{topic}", generate {num_questions} high-quality research questions:

Report content:
{report}

Please generate {num_questions} questions with reasonable difficulty distribution and diverse types. Generate ALL questions in English only for consistency in comparative analysis."""

        return self.generate_text(
            prompt=prompt,
            max_tokens=4000,
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
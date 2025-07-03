#!/usr/bin/env python3
"""
Dynamic LLM Manager
动态LLM调用管理器，支持OpenAI和Claude API的统一调用
"""

import os
import json
import logging
import re
from typing import Dict, List, Any, Optional, Union
from enum import Enum
from dataclasses import dataclass

# 导入API客户端
from .openai_api_client import OpenAIClient
from .claude_api_client import ClaudeAPIClient, APIResponse

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMProvider(Enum):
    """LLM提供商枚举"""
    OPENAI = "openai"
    CLAUDE = "claude"

@dataclass
class LLMConfig:
    """LLM配置"""
    provider: LLMProvider
    model_name: str
    api_key: Optional[str] = None
    max_tokens: int = 4000
    temperature: float = 0.7

class DynamicLLMManager:
    """动态LLM管理器"""
    
    def __init__(self):
        """初始化管理器"""
        self.clients = {}
        self.current_provider = None
        self.configs = {}
        
        # 默认配置
        self.default_configs = {
            LLMProvider.OPENAI: LLMConfig(
                provider=LLMProvider.OPENAI,
                model_name="gpt-4o",
                api_key=os.getenv('OPENAI_API_KEY'),
                max_tokens=4000,
                temperature=0.7
            ),
            LLMProvider.CLAUDE: LLMConfig(
                provider=LLMProvider.CLAUDE,
                model_name="claude-3-5-sonnet-20241022",
                api_key=os.getenv('ANTHROPIC_API_KEY'),
                max_tokens=4000,
                temperature=0.7
            )
        }
        
        # 初始化可用的客户端
        self._initialize_clients()
    
    def _initialize_clients(self):
        """初始化API客户端"""
        # 初始化OpenAI客户端
        try:
            if self.default_configs[LLMProvider.OPENAI].api_key:
                self.clients[LLMProvider.OPENAI] = OpenAIClient(
                    api_key=self.default_configs[LLMProvider.OPENAI].api_key
                )
                logger.info("OpenAI客户端初始化成功")
            else:
                logger.warning("OpenAI API key未找到，跳过初始化")
        except Exception as e:
            logger.error(f"OpenAI客户端初始化失败: {e}")
        
        # 初始化Claude客户端
        try:
            if self.default_configs[LLMProvider.CLAUDE].api_key:
                self.clients[LLMProvider.CLAUDE] = ClaudeAPIClient(
                    api_key=self.default_configs[LLMProvider.CLAUDE].api_key
                )
                logger.info("Claude客户端初始化成功")
            else:
                logger.warning("Claude API key未找到，跳过初始化")
        except Exception as e:
            logger.error(f"Claude客户端初始化失败: {e}")
        
        # 设置默认提供商
        if LLMProvider.OPENAI in self.clients:
            self.current_provider = LLMProvider.OPENAI
        elif LLMProvider.CLAUDE in self.clients:
            self.current_provider = LLMProvider.CLAUDE
        else:
            logger.error("没有可用的LLM客户端")
    
    def set_provider(self, provider: Union[LLMProvider, str]):
        """设置当前LLM提供商"""
        if isinstance(provider, str):
            provider = LLMProvider(provider.lower())
        
        if provider not in self.clients:
            raise ValueError(f"LLM提供商 {provider.value} 不可用")
        
        self.current_provider = provider
        logger.info(f"切换到LLM提供商: {provider.value}")
    
    def get_current_provider(self) -> Optional[LLMProvider]:
        """获取当前LLM提供商"""
        return self.current_provider
    
    def get_available_providers(self) -> List[LLMProvider]:
        """获取可用的LLM提供商"""
        return list(self.clients.keys())
    
    def generate_text(self, 
                     prompt: str, 
                     provider: Optional[Union[LLMProvider, str]] = None,
                     max_tokens: Optional[int] = None,
                     temperature: Optional[float] = None,
                     system_prompt: Optional[str] = None) -> APIResponse:
        """生成文本"""
        
        # 确定使用的提供商
        if provider:
            if isinstance(provider, str):
                provider = LLMProvider(provider.lower())
            target_provider = provider
        else:
            target_provider = self.current_provider
        
        if not target_provider or target_provider not in self.clients:
            raise ValueError(f"LLM提供商 {target_provider} 不可用")
        
        # 获取配置
        config = self.default_configs[target_provider]
        max_tokens = max_tokens or config.max_tokens
        temperature = temperature or config.temperature
        
        # 调用相应的客户端
        client = self.clients[target_provider]
        
        try:
            if target_provider == LLMProvider.OPENAI:
                return client.generate_text(
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system_prompt=system_prompt
                )
            elif target_provider == LLMProvider.CLAUDE:
                return client.generate_text(
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system_prompt=system_prompt
                )
        except Exception as e:
            logger.error(f"文本生成失败 ({target_provider.value}): {e}")
            return APIResponse(
                content="",
                model=config.model_name,
                usage={},
                success=False,
                error=str(e)
            )
    
    def generate_report(self, 
                       documents: List[Dict], 
                       topic: str,
                       provider: Optional[Union[LLMProvider, str]] = None,
                       max_tokens: int = 4000) -> APIResponse:
        """生成领域报告"""
        
        # 确定使用的提供商
        if provider:
            if isinstance(provider, str):
                provider = LLMProvider(provider.lower())
            target_provider = provider
        else:
            target_provider = self.current_provider
        
        if not target_provider or target_provider not in self.clients:
            raise ValueError(f"LLM提供商 {target_provider} 不可用")
        
        # 调用相应的客户端
        client = self.clients[target_provider]
        
        try:
            return client.generate_report(documents, topic, max_tokens)
        except Exception as e:
            logger.error(f"报告生成失败 ({target_provider.value}): {e}")
            config = self.default_configs[target_provider]
            return APIResponse(
                content="",
                model=config.model_name,
                usage={},
                success=False,
                error=str(e)
            )
    
    def generate_questions(self, 
                          report: str, 
                          topic: str,
                          num_questions: int = 50,
                          provider: Optional[Union[LLMProvider, str]] = None) -> APIResponse:
        """生成问题"""
        
        # 确定使用的提供商
        if provider:
            if isinstance(provider, str):
                provider = LLMProvider(provider.lower())
            target_provider = provider
        else:
            target_provider = self.current_provider
        
        if not target_provider or target_provider not in self.clients:
            raise ValueError(f"LLM提供商 {target_provider} 不可用")
        
        # 调用相应的客户端
        client = self.clients[target_provider]
        
        try:
            api_response = client.generate_questions(report, topic, num_questions)
            
            if api_response.success and api_response.content:
                # 直接解析文本格式
                content = api_response.content.strip()
                questions_data = self._parse_text_questions(content)
                
                # 构建成功响应
                result = APIResponse(
                    content=api_response.content,
                    model=api_response.model,
                    usage=api_response.usage,
                    success=True
                )
                
                # 添加解析后的问题数据
                result.questions = questions_data
                result.count = len(questions_data)
                
                logger.info(f"问题生成成功: {len(questions_data)} 个有效问题")
                return result
            else:
                # API调用失败
                result = APIResponse(
                    content="",
                    model=api_response.model,
                    usage=api_response.usage,
                    success=False,
                    error=api_response.error
                )
                result.questions = []
                result.count = 0
                return result
                
        except Exception as e:
            logger.error(f"问题生成失败 ({target_provider.value}): {e}")
            config = self.default_configs[target_provider]
            result = APIResponse(
                content="",
                model=config.model_name,
                usage={},
                success=False,
                error=str(e)
            )
            result.questions = []
            result.count = 0
            return result
    
    def _extract_questions_from_text(self, text: str) -> List[Dict[str, Any]]:
        """从文本中提取问题的备用方法"""
        questions = []
        
        # 尝试按行分割查找问题
        lines = text.split('\n')
        question_patterns = [
            r'^\s*\d+\.\s*(.+)\?',  # 1. 问题?
            r'^\s*[Qq]uestion:\s*(.+)\?',  # Question: 问题?
            r'^\s*-\s*(.+)\?',  # - 问题?
        ]
        
        for i, line in enumerate(lines):
            line = line.strip()
            if line and '?' in line:
                for pattern in question_patterns:
                    import re
                    match = re.match(pattern, line)
                    if match:
                        question = match.group(1).strip()
                        if len(question) > 10:  # 过滤过短的问题
                            questions.append({
                                'question': question + '?',
                                'difficulty': 'Medium',
                                'type': 'general',
                                'reasoning': 'Extracted from text'
                            })
                        break
        
        # 如果还是没有找到问题，生成一些基础问题
        if not questions:
            default_questions = [
                {
                    'question': 'What are the main findings presented in this research?',
                    'difficulty': 'Easy',
                    'type': 'factual',
                    'reasoning': 'Basic comprehension question'
                },
                {
                    'question': 'How do these findings relate to current developments in the field?',
                    'difficulty': 'Medium',
                    'type': 'analytical',
                    'reasoning': 'Analytical thinking question'
                },
                {
                    'question': 'What are the potential implications and future directions based on this research?',
                    'difficulty': 'Hard',
                    'type': 'evaluative',
                    'reasoning': 'Critical evaluation question'
                }
            ]
            questions = default_questions
        
        return questions[:10]  # 最多返回10个问题
    
    def _clean_json_content(self, content: str) -> str:
        """清理JSON内容中的控制字符和格式问题"""
        import re
        
        # 1. 移除所有不可见控制字符
        content = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', content)
        
        # 2. 规范化引号
        content = content.replace('"', '"').replace('"', '"')
        content = content.replace(''', "'").replace(''', "'")
        
        # 3. 处理JSON字符串中的换行符
        # 在JSON字符串值中，换行符需要转义
        lines = content.split('\n')
        cleaned_lines = []
        in_string = False
        escape_next = False
        
        for line in lines:
            cleaned_line = ""
            for i, char in enumerate(line):
                if escape_next:
                    cleaned_line += char
                    escape_next = False
                    continue
                    
                if char == '\\':
                    escape_next = True
                    cleaned_line += char
                    continue
                    
                if char == '"' and not escape_next:
                    in_string = not in_string
                    
                cleaned_line += char
            
            cleaned_lines.append(cleaned_line)
        
        # 4. 重新组合，确保JSON结构正确
        content = '\n'.join(cleaned_lines)
        
        # 5. 修复常见的JSON格式问题
        content = re.sub(r',\s*}', '}', content)  # 移除对象末尾多余的逗号
        content = re.sub(r',\s*]', ']', content)  # 移除数组末尾多余的逗号
        
        return content.strip()
    
    def _parse_text_questions(self, content: str) -> List[Dict[str, Any]]:
        """解析文本格式的问题"""
        import re
        
        questions = []
        
        # 按问题分割 (Q1:, Q2:, Q3:, 等)
        question_blocks = re.split(r'\bQ\d+:', content)
        
        for i, block in enumerate(question_blocks):
            if i == 0:  # 跳过第一个空块
                continue
                
            block = block.strip()
            if not block:
                continue
            
            # 解析每个问题块
            question_text = ""
            difficulty = "Medium"
            question_type = "general"
            reasoning = "Generated research question"
            
            lines = block.split('\n')
            current_section = "question"
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                if line.upper().startswith('DIFFICULTY:'):
                    difficulty = line.split(':', 1)[1].strip()
                    current_section = "difficulty"
                elif line.upper().startswith('TYPE:'):
                    question_type = line.split(':', 1)[1].strip()
                    current_section = "type"
                elif line.upper().startswith('REASONING:'):
                    reasoning = line.split(':', 1)[1].strip()
                    current_section = "reasoning"
                else:
                    if current_section == "question":
                        question_text += " " + line if question_text else line
                    elif current_section == "reasoning":
                        reasoning += " " + line
            
            # 清理问题文本
            question_text = question_text.strip()
            if question_text:
                questions.append({
                    'question': question_text,
                    'difficulty': difficulty,
                    'type': question_type,
                    'reasoning': reasoning
                })
        
        # 如果没有解析到足够的问题，使用备用方法
        if len(questions) < 3:
            logger.warning(f"文本解析只得到 {len(questions)} 个问题，使用备用解析")
            backup_questions = self._extract_questions_from_text(content)
            questions.extend(backup_questions)
        
        return questions
    
    def generate_answer(self, 
                       question: str, 
                       report: str, 
                       difficulty: str,
                       provider: Optional[Union[LLMProvider, str]] = None) -> APIResponse:
        """生成答案"""
        
        # 确定使用的提供商
        if provider:
            if isinstance(provider, str):
                provider = LLMProvider(provider.lower())
            target_provider = provider
        else:
            target_provider = self.current_provider
        
        if not target_provider or target_provider not in self.clients:
            raise ValueError(f"LLM提供商 {target_provider} 不可用")
        
        # 调用相应的客户端
        client = self.clients[target_provider]
        
        try:
            return client.generate_answer(question, report, difficulty)
        except Exception as e:
            logger.error(f"答案生成失败 ({target_provider.value}): {e}")
            config = self.default_configs[target_provider]
            return APIResponse(
                content="",
                model=config.model_name,
                usage={},
                success=False,
                error=str(e)
            )
    
    def generate_answers(self, 
                        questions_data: List[Dict[str, Any]], 
                        report: str,
                        provider: Optional[Union[LLMProvider, str]] = None,
                        max_answers: int = 5) -> Dict[str, Any]:
        """批量生成答案"""
        
        # 确定使用的提供商
        if provider:
            if isinstance(provider, str):
                provider = LLMProvider(provider.lower())
            target_provider = provider
        else:
            target_provider = self.current_provider
        
        if not target_provider or target_provider not in self.clients:
            raise ValueError(f"LLM提供商 {target_provider} 不可用")
        
        # 限制答案数量
        questions_to_answer = questions_data[:max_answers] if len(questions_data) > max_answers else questions_data
        
        qa_pairs = []
        total_answer_length = 0
        successful_answers = 0
        
        for i, question_data in enumerate(questions_to_answer):
            try:
                question = question_data.get('question', '')
                difficulty = question_data.get('difficulty', 'Medium')
                question_type = question_data.get('type', 'general')
                
                logger.info(f"生成答案 {i+1}/{len(questions_to_answer)}: {question[:50]}...")
                
                # 生成答案
                answer_response = self.generate_answer(question, report, difficulty, provider)
                
                if answer_response.success and answer_response.content:
                    answer = answer_response.content
                    answer_length = len(answer)
                    answer_word_count = len(answer.split())
                    
                    qa_pair = {
                        'question_id': f"q_{i+1:03d}",
                        'question': question,
                        'answer': answer,
                        'difficulty': difficulty,
                        'type': question_type,
                        'answer_length': answer_length,
                        'answer_word_count': answer_word_count,
                        'success': True
                    }
                    
                    qa_pairs.append(qa_pair)
                    total_answer_length += answer_length
                    successful_answers += 1
                    
                    logger.info(f"  ✅ 答案生成成功 ({answer_word_count} 词)")
                    
                else:
                    logger.warning(f"  ❌ 答案生成失败: {answer_response.error}")
                    # 记录失败的QA对
                    qa_pair = {
                        'question_id': f"q_{i+1:03d}",
                        'question': question,
                        'answer': "",
                        'difficulty': difficulty,
                        'type': question_type,
                        'answer_length': 0,
                        'answer_word_count': 0,
                        'success': False,
                        'error': answer_response.error
                    }
                    qa_pairs.append(qa_pair)
                
                # 短暂休息避免API限制
                import time
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"处理问题 {i+1} 失败: {e}")
                qa_pair = {
                    'question_id': f"q_{i+1:03d}",
                    'question': question_data.get('question', ''),
                    'answer': "",
                    'difficulty': question_data.get('difficulty', 'Medium'),
                    'type': question_data.get('type', 'general'),
                    'answer_length': 0,
                    'answer_word_count': 0,
                    'success': False,
                    'error': str(e)
                }
                qa_pairs.append(qa_pair)
                continue
        
        # 构建结果
        result = {
            'success': len(qa_pairs) > 0,
            'count': successful_answers,
            'total_questions': len(questions_to_answer),
            'qa_pairs': qa_pairs,
            'total_answer_length': total_answer_length,
            'average_answer_length': total_answer_length / max(successful_answers, 1)
        }
        
        if successful_answers == 0:
            result['success'] = False
            result['error'] = "没有成功生成的答案"
        
        logger.info(f"批量答案生成完成: {successful_answers}/{len(questions_to_answer)} 成功")
        
        return result
    
    def refine_question(self, 
                       question: str, 
                       feedback: str, 
                       report: str,
                       provider: Optional[Union[LLMProvider, str]] = None) -> APIResponse:
        """优化问题"""
        
        # 确定使用的提供商
        if provider:
            if isinstance(provider, str):
                provider = LLMProvider(provider.lower())
            target_provider = provider
        else:
            target_provider = self.current_provider
        
        if not target_provider or target_provider not in self.clients:
            raise ValueError(f"LLM提供商 {target_provider} 不可用")
        
        # 调用相应的客户端
        client = self.clients[target_provider]
        
        try:
            return client.refine_question(question, feedback, report)
        except Exception as e:
            logger.error(f"问题优化失败 ({target_provider.value}): {e}")
            config = self.default_configs[target_provider]
            return APIResponse(
                content="",
                model=config.model_name,
                usage={},
                success=False,
                error=str(e)
            )
    
    def compare_providers(self, 
                         prompt: str, 
                         providers: Optional[List[Union[LLMProvider, str]]] = None) -> Dict[str, APIResponse]:
        """比较不同提供商的响应"""
        
        if not providers:
            providers = self.get_available_providers()
        
        # 转换字符串为枚举
        provider_list = []
        for p in providers:
            if isinstance(p, str):
                provider_list.append(LLMProvider(p.lower()))
            else:
                provider_list.append(p)
        
        results = {}
        
        for provider in provider_list:
            if provider in self.clients:
                logger.info(f"使用 {provider.value} 生成响应...")
                response = self.generate_text(prompt, provider=provider)
                results[provider.value] = response
            else:
                logger.warning(f"提供商 {provider.value} 不可用")
        
        return results
    
    def get_provider_info(self) -> Dict[str, Any]:
        """获取提供商信息"""
        info = {
            "current_provider": self.current_provider.value if self.current_provider else None,
            "available_providers": [p.value for p in self.get_available_providers()],
            "provider_configs": {}
        }
        
        for provider, config in self.default_configs.items():
            if provider in self.clients:
                info["provider_configs"][provider.value] = {
                    "model_name": config.model_name,
                    "max_tokens": config.max_tokens,
                    "temperature": config.temperature,
                    "api_key_configured": bool(config.api_key)
                }
        
        return info

# 全局管理器实例
llm_manager = DynamicLLMManager()

def test_dynamic_llm_manager():
    """测试动态LLM管理器"""
    manager = DynamicLLMManager()
    
    print("=== 动态LLM管理器测试 ===")
    
    # 显示提供商信息
    info = manager.get_provider_info()
    print(f"当前提供商: {info['current_provider']}")
    print(f"可用提供商: {info['available_providers']}")
    
    # 测试文本生成
    test_prompt = "请简单介绍机器学习的基本概念。"
    
    for provider in manager.get_available_providers():
        print(f"\n--- 测试 {provider.value} ---")
        response = manager.generate_text(test_prompt, provider=provider, max_tokens=200)
        
        if response.success:
            print(f"成功: {response.content[:100]}...")
            print(f"Token使用: {response.usage}")
        else:
            print(f"失败: {response.error}")
    
    # 测试比较功能
    print("\n--- 提供商比较测试 ---")
    comparison = manager.compare_providers(test_prompt)
    
    for provider, response in comparison.items():
        print(f"{provider}: {'成功' if response.success else '失败'}")

if __name__ == "__main__":
    test_dynamic_llm_manager() 
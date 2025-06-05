#!/usr/bin/env python3
"""
Dynamic LLM Manager
动态LLM调用管理器，支持OpenAI和Claude API的统一调用
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Union
from enum import Enum
from dataclasses import dataclass

# 导入API客户端
from openai_api_client import OpenAIClient
from claude_api_client import ClaudeAPIClient, APIResponse

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
            return client.generate_questions(report, topic, num_questions)
        except Exception as e:
            logger.error(f"问题生成失败 ({target_provider.value}): {e}")
            config = self.default_configs[target_provider]
            return APIResponse(
                content="",
                model=config.model_name,
                usage={},
                success=False,
                error=str(e)
            )
    
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
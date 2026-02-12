"""
DeepSeek LLM 实现
"""
from typing import List, Optional
from .base import BaseLLM, Message
from config.settings import get_settings


class DeepSeekLLM(BaseLLM):
    """DeepSeek LLM"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化 DeepSeek
        
        Args:
            api_key: DeepSeek API Key
        """
        settings = get_settings()
        api_key = api_key or settings.deepseek_api_key
        super().__init__(api_key=api_key, model_name="deepseek-chat")
        
        self._client = None
        self._check_availability()
    
    def _check_availability(self):
        """检查 API 是否可用"""
        if not self.api_key or self.api_key == "your_deepseek_key_here":
            self._is_available = False
            return
        
        try:
            from openai import OpenAI
            self._client = OpenAI(
                api_key=self.api_key,
                base_url="https://api.deepseek.com/v1"
            )
            self._is_available = True
        except ImportError:
            self._is_available = False
    
    def is_available(self) -> bool:
        return self._is_available
    
    def chat(self, messages: List[Message], **kwargs) -> str:
        """
        发送对话请求
        
        Args:
            messages: 消息列表
            **kwargs: 额外参数
            
        Returns:
            模型回复内容
        """
        if not self._is_available:
            raise RuntimeError("DeepSeek API 不可用，请检查 API Key 配置")
        
        # 转换消息格式
        formatted_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", 2000)
        
        response = self._client.chat.completions.create(
            model=self.model_name,
            messages=formatted_messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return response.choices[0].message.content

"""
智谱 GLM LLM 实现
"""
from typing import List, Optional
from .base import BaseLLM, Message
from config.settings import get_settings


class ZhipuLLM(BaseLLM):
    """智谱 GLM LLM"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化智谱 GLM
        
        Args:
            api_key: 智谱 API Key
        """
        settings = get_settings()
        api_key = api_key or settings.zhipu_api_key
        super().__init__(api_key=api_key, model_name="glm-4")
        
        self._client = None
        self._check_availability()
    
    def _check_availability(self):
        """检查 API 是否可用"""
        if not self.api_key or self.api_key == "your_zhipu_key_here":
            self._is_available = False
            return
        
        try:
            from zhipuai import ZhipuAI
            self._client = ZhipuAI(api_key=self.api_key)
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
            raise RuntimeError("智谱 API 不可用，请检查 API Key 配置")
        
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

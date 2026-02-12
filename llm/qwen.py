"""
通义千问 LLM 实现
"""
from typing import List, Optional
from .base import BaseLLM, Message
from config.settings import get_settings


class QwenLLM(BaseLLM):
    """通义千问 LLM"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化通义千问
        
        Args:
            api_key: DashScope API Key
        """
        settings = get_settings()
        api_key = api_key or settings.dashscope_api_key
        super().__init__(api_key=api_key, model_name="qwen-turbo")
        
        self._client = None
        self._check_availability()
    
    def _check_availability(self):
        """检查 API 是否可用"""
        if not self.api_key or self.api_key == "your_dashscope_key_here":
            self._is_available = False
            return
        
        try:
            import dashscope
            dashscope.api_key = self.api_key
            self._client = dashscope
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
            **kwargs: 额外参数（temperature, max_tokens 等）
            
        Returns:
            模型回复内容
        """
        if not self._is_available:
            raise RuntimeError("通义千问 API 不可用，请检查 API Key 配置")
        
        from dashscope import Generation
        
        # 转换消息格式
        formatted_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        # 设置默认参数
        temperature = kwargs.get("temperature", 0.7)
        max_tokens = kwargs.get("max_tokens", 2000)
        
        response = Generation.call(
            model=self.model_name,
            messages=formatted_messages,
            temperature=temperature,
            max_tokens=max_tokens,
            result_format="message"
        )
        
        if response.status_code == 200:
            return response.output.choices[0].message.content
        else:
            raise RuntimeError(f"通义千问 API 调用失败: {response.code} - {response.message}")

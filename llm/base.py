"""
LLM 抽象基类
定义所有 LLM 后端必须实现的接口
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from dataclasses import dataclass


@dataclass
class Message:
    """消息结构"""
    role: str  # system / user / assistant
    content: str


class BaseLLM(ABC):
    """LLM 抽象基类"""
    
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        """
        初始化 LLM
        
        Args:
            api_key: API 密钥
            model_name: 模型名称
        """
        self.api_key = api_key
        self.model_name = model_name
        self._is_available = False
    
    @abstractmethod
    def chat(self, messages: List[Message], **kwargs) -> str:
        """
        发送对话请求
        
        Args:
            messages: 消息列表
            **kwargs: 额外参数
            
        Returns:
            模型回复内容
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        检查 LLM 是否可用
        
        Returns:
            是否可用
        """
        pass
    
    def build_messages(
        self, 
        user_input: str, 
        system_prompt: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None
    ) -> List[Message]:
        """
        构建消息列表
        
        Args:
            user_input: 用户输入
            system_prompt: 系统提示词
            history: 历史对话
            
        Returns:
            消息列表
        """
        messages = []
        
        if system_prompt:
            messages.append(Message(role="system", content=system_prompt))
        
        if history:
            for msg in history:
                messages.append(Message(role=msg["role"], content=msg["content"]))
        
        messages.append(Message(role="user", content=user_input))
        
        return messages
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} model={self.model_name} available={self._is_available}>"

"""
LLM 模块
提供统一的 LLM 接口和多模型切换能力
"""
from typing import Optional, List
from .base import BaseLLM, Message
from .qwen import QwenLLM
from .zhipu import ZhipuLLM
from .deepseek import DeepSeekLLM
from config.settings import get_settings


# 支持的 LLM 类型
LLM_REGISTRY = {
    "qwen": QwenLLM,
    "zhipu": ZhipuLLM,
    "deepseek": DeepSeekLLM,
}


class LLMFactory:
    """LLM 工厂类"""
    
    _instances: dict = {}
    
    @classmethod
    def get_llm(cls, llm_type: Optional[str] = None) -> BaseLLM:
        """
        获取 LLM 实例
        
        Args:
            llm_type: LLM 类型（qwen / zhipu / deepseek）
            
        Returns:
            LLM 实例
            
        Raises:
            ValueError: 没有可用的 LLM
        """
        settings = get_settings()
        llm_type = llm_type or settings.default_llm
        
        # 如果已有实例，直接返回
        if llm_type in cls._instances:
            return cls._instances[llm_type]
        
        # 创建新实例
        if llm_type not in LLM_REGISTRY:
            raise ValueError(f"不支持的 LLM 类型: {llm_type}")
        
        llm_class = LLM_REGISTRY[llm_type]
        instance = llm_class()
        cls._instances[llm_type] = instance
        
        return instance
    
    @classmethod
    def get_available_llms(cls) -> List[str]:
        """
        获取所有可用的 LLM 类型
        
        Returns:
            可用的 LLM 类型列表
        """
        available = []
        for llm_type, llm_class in LLM_REGISTRY.items():
            instance = llm_class()
            if instance.is_available():
                available.append(llm_type)
        return available
    
    @classmethod
    def get_first_available(cls) -> BaseLLM:
        """
        获取第一个可用的 LLM
        
        Returns:
            LLM 实例
            
        Raises:
            RuntimeError: 没有可用的 LLM
        """
        for llm_type in LLM_REGISTRY:
            instance = cls.get_llm(llm_type)
            if instance.is_available():
                return instance
        
        raise RuntimeError("没有可用的 LLM，请检查 API Key 配置")


__all__ = [
    "BaseLLM",
    "Message",
    "QwenLLM",
    "ZhipuLLM",
    "DeepSeekLLM",
    "LLMFactory",
]

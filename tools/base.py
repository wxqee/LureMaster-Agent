"""
工具基类
"""
from abc import ABC, abstractmethod
from typing import Any, Optional
from dataclasses import dataclass


@dataclass
class ToolResult:
    """工具执行结果"""
    success: bool
    data: Any
    message: str = ""
    error: Optional[str] = None


class BaseTool(ABC):
    """工具抽象基类"""
    
    name: str = "base_tool"
    description: str = "基础工具"
    
    def __init__(self, mock_mode: bool = False):
        """
        初始化工具
        
        Args:
            mock_mode: 是否使用模拟模式
        """
        self.mock_mode = mock_mode
    
    @abstractmethod
    def run(self, *args, **kwargs) -> ToolResult:
        """
        执行工具
        
        Returns:
            工具执行结果
        """
        pass
    
    def get_mock_data(self, *args, **kwargs) -> Any:
        """
        获取模拟数据
        
        Returns:
            模拟数据
        """
        return None
    
    def __repr__(self) -> str:
        return f"<Tool: {self.name}>"

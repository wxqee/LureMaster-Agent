"""
工具模块
提供天气、地理、知识检索等工具
"""
from .base import BaseTool, ToolResult
from .weather import WeatherTool
from .location import LocationTool
from .knowledge import KnowledgeTool


class ToolManager:
    """工具管理器"""
    
    def __init__(self):
        """初始化工具管理器"""
        self._tools = {
            "weather": WeatherTool(),
            "location": LocationTool(),
            "knowledge": KnowledgeTool(),
        }
    
    def get_tool(self, name: str) -> BaseTool:
        """
        获取工具实例
        
        Args:
            name: 工具名称
            
        Returns:
            工具实例
        """
        if name not in self._tools:
            raise ValueError(f"未知工具: {name}")
        return self._tools[name]
    
    def list_tools(self) -> list:
        """列出所有可用工具"""
        return list(self._tools.keys())
    
    def run_tool(self, name: str, *args, **kwargs) -> ToolResult:
        """
        执行工具
        
        Args:
            name: 工具名称
            *args: 位置参数
            **kwargs: 关键字参数
            
        Returns:
            工具执行结果
        """
        tool = self.get_tool(name)
        return tool.run(*args, **kwargs)


__all__ = [
    "BaseTool",
    "ToolResult",
    "WeatherTool",
    "LocationTool",
    "KnowledgeTool",
    "ToolManager",
]

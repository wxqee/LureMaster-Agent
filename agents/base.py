"""
Agent 基类
定义 Agent 的基本结构和接口
"""
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ConversationState:
    """对话状态"""
    messages: List[Dict[str, str]] = field(default_factory=list)
    collected_info: Dict[str, Any] = field(default_factory=dict)
    current_stage: str = "greeting"  # greeting / collecting / analyzing / advising
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    generated_knowledge: Dict[str, Any] = field(default_factory=dict)  # 存储LLM生成的知识
    
    def add_message(self, role: str, content: str):
        """添加消息"""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        self.updated_at = datetime.now()
    
    def update_info(self, key: str, value: Any):
        """更新收集的信息"""
        self.collected_info[key] = value
        self.updated_at = datetime.now()
    
    def add_generated_knowledge(self, knowledge_type: str, name: str, data: Dict[str, Any]):
        """添加生成的知识"""
        key = f"{knowledge_type}:{name}"
        self.generated_knowledge[key] = {
            "type": knowledge_type,
            "name": name,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        self.updated_at = datetime.now()
    
    def get_generated_knowledge(self, knowledge_type: str, name: str) -> Optional[Dict[str, Any]]:
        """获取生成的知识"""
        key = f"{knowledge_type}:{name}"
        return self.generated_knowledge.get(key)
    
    def get_last_user_message(self) -> Optional[str]:
        """获取最后一条用户消息"""
        for msg in reversed(self.messages):
            if msg["role"] == "user":
                return msg["content"]
        return None
    
    def get_history(self, limit: int = 10) -> List[Dict[str, str]]:
        """获取对话历史"""
        return self.messages[-limit:]


class BaseAgent(ABC):
    """Agent 抽象基类"""
    
    name: str = "base_agent"
    description: str = "基础 Agent"
    
    def __init__(self):
        """初始化 Agent"""
        self.state = ConversationState()
    
    @abstractmethod
    def chat(self, user_input: str) -> str:
        """
        与 Agent 对话
        
        Args:
            user_input: 用户输入
            
        Returns:
            Agent 回复
        """
        pass
    
    @abstractmethod
    def reset(self):
        """重置对话状态"""
        pass
    
    def get_state(self) -> ConversationState:
        """获取当前状态"""
        return self.state
    
    def get_collected_info(self) -> Dict[str, Any]:
        """获取已收集的信息"""
        return self.state.collected_info

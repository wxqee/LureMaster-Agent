"""
知识收集 Skill

从原始文本中提取结构化钓鱼知识
"""
import json
import re
from typing import Dict, Any, Optional, List
from llm import LLMFactory, BaseLLM, Message
from config.schemas import (
    get_schema_description,
    get_knowledge_key,
    validate_data,
    DataType
)


COLLECT_PROMPT = """你是一个钓鱼知识提取专家。请从以下文本中提取{data_type}相关的结构化信息。

## 原始文本
{raw_text}

## 数据结构
{schema}

## 提取要求
1. 只提取文本中明确提到的信息，不要编造
2. 如果某个字段没有提到，设为 null
3. 保持数据准确性
4. 只返回 JSON 格式，不要有其他内容

请直接返回 JSON："""


class KnowledgeCollector:
    """知识收集器"""
    
    SUPPORTED_TYPES = ["fish", "lure", "rig", "spot_type"]
    
    TYPE_NAMES = {
        "fish": "鱼种",
        "lure": "路亚饵",
        "rig": "钓组",
        "spot_type": "标点类型"
    }
    
    def __init__(self, llm: Optional[BaseLLM] = None):
        """
        初始化知识收集器
        
        Args:
            llm: LLM 实例，如果不提供则自动创建
        """
        if llm:
            self.llm = llm
        else:
            self.llm = LLMFactory.get_first_available()
    
    def collect(self, text: str, data_type: str) -> Dict[str, Any]:
        """
        从文本中收集知识
        
        Args:
            text: 原始文本
            data_type: 数据类型 (fish/lure/rig/spot_type)
            
        Returns:
            提取的结构化数据
        """
        if data_type not in self.SUPPORTED_TYPES:
            raise ValueError(f"不支持的数据类型: {data_type}，支持的类型: {self.SUPPORTED_TYPES}")
        
        schema = get_schema_description(data_type)
        prompt = COLLECT_PROMPT.format(
            data_type=self.TYPE_NAMES.get(data_type, data_type),
            raw_text=text,
            schema=schema
        )
        
        response = self.llm.chat([Message(role="user", content=prompt)])
        
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            try:
                data = json.loads(json_match.group())
                return data
            except json.JSONDecodeError:
                pass
        
        return {}
    
    def collect_batch(self, text: str, data_type: str) -> List[Dict[str, Any]]:
        """
        从文本中批量收集知识（支持多个条目）
        
        Args:
            text: 原始文本
            data_type: 数据类型
            
        Returns:
            提取的结构化数据列表
        """
        BATCH_PROMPT = """你是一个钓鱼知识提取专家。请从以下文本中提取所有{data_type}相关的结构化信息。

## 原始文本
{raw_text}

## 数据结构（每个条目）
{schema}

## 提取要求
1. 提取文本中提到的所有{data_type}信息
2. 只提取文本中明确提到的信息，不要编造
3. 如果某个字段没有提到，设为 null
4. 返回 JSON 数组格式

请返回 JSON 数组："""
        
        if data_type not in self.SUPPORTED_TYPES:
            raise ValueError(f"不支持的数据类型: {data_type}")
        
        schema = get_schema_description(data_type)
        prompt = BATCH_PROMPT.format(
            data_type=self.TYPE_NAMES.get(data_type, data_type),
            raw_text=text,
            schema=schema
        )
        
        response = self.llm.chat([Message(role="user", content=prompt)])
        
        json_match = re.search(r'\[[\s\S]*\]', response)
        if json_match:
            try:
                data_list = json.loads(json_match.group())
                if isinstance(data_list, list):
                    return data_list
            except json.JSONDecodeError:
                pass
        
        return []
    
    def validate(self, data: Dict[str, Any], data_type: str) -> bool:
        """
        验证数据是否符合 Schema
        
        Args:
            data: 待验证的数据
            data_type: 数据类型
            
        Returns:
            是否有效
        """
        return validate_data(data, data_type)
    
    def format_output(self, data: Dict[str, Any], data_type: str) -> str:
        """
        格式化输出数据
        
        Args:
            data: 数据
            data_type: 数据类型
            
        Returns:
            格式化的字符串
        """
        type_name = self.TYPE_NAMES.get(data_type, data_type)
        lines = [f"\n📋 提取的{type_name}信息："]
        lines.append("─" * 40)
        
        for key, value in data.items():
            if value is not None:
                if isinstance(value, list):
                    value_str = "、".join(str(v) for v in value) if value else "无"
                elif isinstance(value, dict):
                    value_str = json.dumps(value, ensure_ascii=False)
                else:
                    value_str = str(value)
                lines.append(f"  {key}: {value_str}")
        
        lines.append("─" * 40)
        return "\n".join(lines)

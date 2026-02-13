"""
知识生成器
当知识库缺失时，使用 LLM 生成相关知识
"""
import json
import re
from typing import Optional, Dict, Any
from llm import LLMFactory, BaseLLM, Message
from config.prompts import (
    FISH_KNOWLEDGE_GENERATION_PROMPT,
    LURE_KNOWLEDGE_GENERATION_PROMPT,
    SPOT_TYPE_KNOWLEDGE_GENERATION_PROMPT,
)


class KnowledgeGenerator:
    """知识生成器 - 使用 LLM 生成缺失的知识"""
    
    SUPPORTED_TYPES = {
        "fish": {
            "name": "鱼种",
            "prompt": FISH_KNOWLEDGE_GENERATION_PROMPT,
            "key_field": "fish_name",
        },
        "lure": {
            "name": "路亚饵",
            "prompt": LURE_KNOWLEDGE_GENERATION_PROMPT,
            "key_field": "lure_name",
        },
        "spot_type": {
            "name": "标点类型",
            "prompt": SPOT_TYPE_KNOWLEDGE_GENERATION_PROMPT,
            "key_field": "spot_type_name",
        },
    }
    
    def __init__(self, llm: Optional[BaseLLM] = None):
        """
        初始化知识生成器
        
        Args:
            llm: LLM 实例，如果不提供则自动创建
        """
        if llm:
            self.llm = llm
        else:
            self.llm = LLMFactory.get_first_available()
    
    def generate_fish_knowledge(self, fish_name: str) -> Optional[Dict[str, Any]]:
        """
        生成鱼种知识
        
        Args:
            fish_name: 鱼种名称
            
        Returns:
            生成的知识字典，失败返回 None
        """
        return self.generate("fish", fish_name)
    
    def generate_lure_knowledge(self, lure_name: str) -> Optional[Dict[str, Any]]:
        """
        生成路亚饵知识
        
        Args:
            lure_name: 路亚饵名称
            
        Returns:
            生成的知识字典，失败返回 None
        """
        return self.generate("lure", lure_name)
    
    def generate_spot_type_knowledge(self, spot_type_name: str) -> Optional[Dict[str, Any]]:
        """
        生成标点类型知识
        
        Args:
            spot_type_name: 标点类型名称
            
        Returns:
            生成的知识字典，失败返回 None
        """
        return self.generate("spot_type", spot_type_name)
    
    def generate(self, data_type: str, name: str) -> Optional[Dict[str, Any]]:
        """
        生成知识
        
        Args:
            data_type: 数据类型 (fish/lure/spot_type)
            name: 名称
            
        Returns:
            生成的知识字典，失败返回 None
        """
        if data_type not in self.SUPPORTED_TYPES:
            raise ValueError(f"不支持的数据类型: {data_type}，支持的类型: {list(self.SUPPORTED_TYPES.keys())}")
        
        type_config = self.SUPPORTED_TYPES[data_type]
        prompt = type_config["prompt"].format(**{type_config["key_field"]: name})
        
        try:
            response = self.llm.chat([Message(role="user", content=prompt)])
            
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
                data["_generated"] = True
                data["_source"] = "llm_generated"
                return data
        except Exception as e:
            print(f"生成知识失败: {e}")
        
        return None
    
    def format_output(self, data: Dict[str, Any], data_type: str) -> str:
        """
        格式化输出知识
        
        Args:
            data: 知识数据
            data_type: 数据类型
            
        Returns:
            格式化后的字符串
        """
        if data_type == "fish":
            return self._format_fish(data)
        elif data_type == "lure":
            return self._format_lure(data)
        elif data_type == "spot_type":
            return self._format_spot_type(data)
        else:
            return json.dumps(data, ensure_ascii=False, indent=2)
    
    def _format_fish(self, data: Dict[str, Any]) -> str:
        """格式化鱼种知识"""
        lines = [
            f"🐟 鱼种：{data.get('name', '未知')}",
            f"   别名：{', '.join(data.get('aliases', []))}",
            f"   习性：{data.get('habits', '未知')}",
            f"   最佳季节：{', '.join(data.get('best_season', []))}",
            f"   最佳时段：{', '.join(data.get('best_time', []))}",
            f"   推荐路亚饵：{', '.join(data.get('lures', []))}",
            f"   推荐钓法：{', '.join(data.get('techniques', []))}",
            f"   活动水层：{data.get('water_layer', '未知')}",
            f"   作钓难度：{data.get('difficulty', '未知')}",
        ]
        if data.get('tips'):
            lines.append(f"   💡 小技巧：{data.get('tips')}")
        if data.get('_generated'):
            lines.append("   ⚠️ 此知识由 AI 生成，建议验证后保存")
        return "\n".join(lines)
    
    def _format_lure(self, data: Dict[str, Any]) -> str:
        """格式化路亚饵知识"""
        lines = [
            f"🎣 路亚饵：{data.get('name', '未知')}",
            f"   分类：{data.get('category', '未知')}",
            f"   描述：{data.get('description', '未知')}",
            f"   目标鱼种：{', '.join(data.get('target_fish', []))}",
            f"   使用手法：{', '.join(data.get('techniques', []))}",
            f"   常用克重：{data.get('weight_range', '未知')}",
            f"   适合季节：{', '.join(data.get('best_season', []))}",
            f"   适合时段：{', '.join(data.get('best_time', []))}",
            f"   使用难度：{data.get('difficulty', '未知')}",
        ]
        if data.get('tips'):
            lines.append(f"   💡 使用技巧：{data.get('tips')}")
        if data.get('_generated'):
            lines.append("   ⚠️ 此知识由 AI 生成，建议验证后保存")
        return "\n".join(lines)
    
    def _format_spot_type(self, data: Dict[str, Any]) -> str:
        """格式化标点类型知识"""
        lines = [
            f"📍 标点类型：{data.get('name', '未知')}",
            f"   描述：{data.get('description', '未知')}",
            f"   常见鱼种：{', '.join(data.get('target_fish', []))}",
            f"   作钓方式：{', '.join(data.get('techniques', []))}",
            f"   推荐路亚饵：{', '.join(data.get('lures', []))}",
            f"   作钓难度：{data.get('difficulty', '未知')}",
        ]
        if data.get('tips'):
            lines.append(f"   💡 寻找技巧：{data.get('tips')}")
        if data.get('_generated'):
            lines.append("   ⚠️ 此知识由 AI 生成，建议验证后保存")
        return "\n".join(lines)

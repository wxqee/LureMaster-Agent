"""
知识库数据 Schema 定义

定义各类钓鱼知识的结构化字段，用于：
1. 数据验证
2. LLM 提取时的模板
3. 知识合并时的校验
"""

from typing import Dict, List, Any
from dataclasses import dataclass, field, asdict
from enum import Enum


class DataType(Enum):
    """数据类型枚举"""
    FISH = "fish"
    LURE = "lure"
    RIG = "rig"
    SPOT_TYPE = "spot_type"
    SPOT = "spot"
    EQUIPMENT = "equipment"
    TECHNIQUE = "technique"


@dataclass
class FishSchema:
    """鱼种数据 Schema"""
    name: str = ""
    aliases: List[str] = field(default_factory=list)
    habits: str = ""
    best_season: List[str] = field(default_factory=list)
    best_time: List[str] = field(default_factory=list)
    lures: List[str] = field(default_factory=list)
    techniques: List[str] = field(default_factory=list)
    water_layer: str = ""
    difficulty: str = ""
    tips: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def get_schema_description(cls) -> str:
        return """
{
    "name": "鱼种名称（如：鳜鱼）",
    "aliases": ["别名列表（如：桂鱼、季花鱼）"],
    "habits": "生活习性描述",
    "best_season": ["最佳季节（春/夏/秋/冬）"],
    "best_time": ["最佳时段（清晨/傍晚/夜间/白天）"],
    "lures": ["推荐路亚饵"],
    "techniques": ["推荐钓法"],
    "water_layer": "活动水层（底层/中层/上层/全水层）",
    "difficulty": "作钓难度（简单/中等/困难）",
    "tips": "实用技巧"
}
"""


@dataclass
class LureSchema:
    """路亚饵数据 Schema"""
    name: str = ""
    category: str = ""
    subtypes: List[str] = field(default_factory=list)
    weights: List[str] = field(default_factory=list)
    colors: Dict[str, str] = field(default_factory=dict)
    target_fish: List[str] = field(default_factory=list)
    techniques: List[str] = field(default_factory=list)
    price_range: str = ""
    tips: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def get_schema_description(cls) -> str:
        return """
{
    "name": "路亚饵名称（如：软虫）",
    "category": "分类（软饵/硬饵/金属饵/水面系）",
    "subtypes": ["子类型列表（如：面条虫、虾型软虫）"],
    "weights": ["克重规格（如：3g、5g、7g）"],
    "colors": {
        "推荐": "推荐颜色",
        "浑水": "浑水用颜色",
        "清水": "清水用颜色"
    },
    "target_fish": ["目标鱼种"],
    "techniques": ["适用钓法"],
    "price_range": "价格区间（如：5-30元/包）",
    "tips": "使用技巧"
}
"""


@dataclass
class RigSchema:
    """钓组数据 Schema"""
    name: str = ""
    components: List[str] = field(default_factory=list)
    suitable_fish: List[str] = field(default_factory=list)
    suitable_environment: List[str] = field(default_factory=list)
    advantages: str = ""
    disadvantages: str = ""
    difficulty: str = ""
    setup_tips: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def get_schema_description(cls) -> str:
        return """
{
    "name": "钓组名称（如：德州钓组）",
    "components": ["组成部件（如：软虫、防挂铅、曲柄钩）"],
    "suitable_fish": ["适合鱼种"],
    "suitable_environment": ["适合环境（如：障碍区、石缝）"],
    "advantages": "优点说明",
    "disadvantages": "缺点说明",
    "difficulty": "使用难度（简单/中等/困难）",
    "setup_tips": "组装技巧"
}
"""


@dataclass
class SpotTypeSchema:
    """标点类型数据 Schema"""
    name: str = ""
    category: str = ""
    description: str = ""
    how_to_find: str = ""
    target_fish: List[str] = field(default_factory=list)
    techniques: List[str] = field(default_factory=list)
    seasonal_tips: Dict[str, str] = field(default_factory=dict)
    tips: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def get_schema_description(cls) -> str:
        return """
{
    "name": "标点名称（如：桥墩）",
    "category": "分类（结构标点/地形标点/植被标点）",
    "description": "标点描述",
    "how_to_find": "寻找方法",
    "target_fish": ["目标鱼种"],
    "techniques": ["适用钓法"],
    "seasonal_tips": {
        "春": "春季技巧",
        "夏": "夏季技巧",
        "秋": "秋季技巧",
        "冬": "冬季技巧"
    },
    "tips": "实用技巧"
}
"""


SCHEMA_MAP: Dict[str, type] = {
    "fish": FishSchema,
    "lure": LureSchema,
    "rig": RigSchema,
    "spot_type": SpotTypeSchema,
}

DATA_TYPE_TO_KEY: Dict[str, str] = {
    "fish": "fish_species",
    "lure": "lures",
    "rig": "rigs",
    "spot_type": "spot_types",
    "spot": "fishing_spots",
    "equipment": "equipment",
    "technique": "techniques",
}


def get_schema(data_type: str) -> type:
    """获取指定类型的 Schema 类"""
    return SCHEMA_MAP.get(data_type)


def get_schema_description(data_type: str) -> str:
    """获取指定类型的 Schema 描述"""
    schema_class = SCHEMA_MAP.get(data_type)
    if schema_class:
        return schema_class.get_schema_description()
    return ""


def get_knowledge_key(data_type: str) -> str:
    """获取数据类型对应的知识库 key"""
    return DATA_TYPE_TO_KEY.get(data_type, data_type)


def validate_data(data: Dict[str, Any], data_type: str) -> bool:
    """验证数据是否符合 Schema"""
    schema_class = SCHEMA_MAP.get(data_type)
    if not schema_class:
        return False
    
    required_fields = ["name"]
    for field_name in required_fields:
        if field_name not in data or not data[field_name]:
            return False
    
    return True

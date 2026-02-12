"""
知识检索工具
从内置知识库中检索钓鱼相关知识
"""
import json
from typing import Optional, List
from pathlib import Path
from .base import BaseTool, ToolResult


class KnowledgeTool(BaseTool):
    """知识检索工具"""
    
    name = "knowledge"
    description = "从知识库中检索钓鱼相关知识"
    
    def __init__(self, knowledge_file: Optional[str] = None):
        """
        初始化知识检索工具
        
        Args:
            knowledge_file: 知识库文件路径
        """
        super().__init__(mock_mode=False)
        
        if knowledge_file:
            self.knowledge_file = Path(knowledge_file)
        else:
            self.knowledge_file = Path(__file__).parent.parent / "data" / "fishing_knowledge.json"
        
        self._knowledge_base = None
    
    def _load_knowledge(self) -> dict:
        """加载知识库"""
        if self._knowledge_base is not None:
            return self._knowledge_base
        
        try:
            if self.knowledge_file.exists():
                with open(self.knowledge_file, "r", encoding="utf-8") as f:
                    self._knowledge_base = json.load(f)
            else:
                self._knowledge_base = self._get_default_knowledge()
        except Exception as e:
            print(f"加载知识库失败: {e}")
            self._knowledge_base = self._get_default_knowledge()
        
        return self._knowledge_base
    
    def run(self, query: str, category: Optional[str] = None) -> ToolResult:
        """
        检索知识
        
        Args:
            query: 查询关键词
            category: 知识类别（fish_species / fishing_spots / equipment / techniques）
            
        Returns:
            相关知识
        """
        knowledge = self._load_knowledge()
        results = []
        
        # 搜索鱼种信息
        if category in [None, "fish_species"]:
            for fish in knowledge.get("fish_species", []):
                if self._match_query(query, fish):
                    results.append({
                        "category": "fish_species",
                        "data": fish
                    })
        
        # 搜索钓点信息
        if category in [None, "fishing_spots"]:
            for spot in knowledge.get("fishing_spots", []):
                if self._match_query(query, spot):
                    results.append({
                        "category": "fishing_spots",
                        "data": spot
                    })
        
        # 搜索装备信息
        if category in [None, "equipment"]:
            for equip in knowledge.get("equipment", []):
                if self._match_query(query, equip):
                    results.append({
                        "category": "equipment",
                        "data": equip
                    })
        
        # 搜索技巧信息
        if category in [None, "techniques"]:
            for tech in knowledge.get("techniques", []):
                if self._match_query(query, tech):
                    results.append({
                        "category": "techniques",
                        "data": tech
                    })
        
        return ToolResult(
            success=True,
            data=results,
            message=f"找到 {len(results)} 条相关知识"
        )
    
    def _match_query(self, query: str, item: dict) -> bool:
        """检查是否匹配查询"""
        query_lower = query.lower()
        
        # 搜索所有字符串字段
        for value in item.values():
            if isinstance(value, str) and query_lower in value.lower():
                return True
            if isinstance(value, list):
                for v in value:
                    if isinstance(v, str) and query_lower in v.lower():
                        return True
        
        return False
    
    def get_fish_info(self, fish_name: str) -> Optional[dict]:
        """
        获取特定鱼种的信息
        
        Args:
            fish_name: 鱼种名称
            
        Returns:
            鱼种信息
        """
        knowledge = self._load_knowledge()
        
        for fish in knowledge.get("fish_species", []):
            if fish_name in fish.get("name", "") or fish_name in fish.get("aliases", []):
                return fish
        
        return None
    
    def get_spot_info(self, spot_name: str) -> Optional[dict]:
        """
        获取特定钓点的信息
        
        Args:
            spot_name: 钓点名称
            
        Returns:
            钓点信息
        """
        knowledge = self._load_knowledge()
        
        for spot in knowledge.get("fishing_spots", []):
            if spot_name in spot.get("name", ""):
                return spot
        
        return None
    
    def get_all_fish_species(self) -> List[dict]:
        """获取所有鱼种列表"""
        knowledge = self._load_knowledge()
        return knowledge.get("fish_species", [])
    
    def get_all_spots(self) -> List[dict]:
        """获取所有钓点列表"""
        knowledge = self._load_knowledge()
        return knowledge.get("fishing_spots", [])
    
    def _get_default_knowledge(self) -> dict:
        """获取默认知识库"""
        return {
            "fish_species": [
                {
                    "name": "鳜鱼",
                    "aliases": ["桂鱼", "季花鱼", "鳌花鱼"],
                    "habits": "底层肉食性鱼类，喜欢清澈水质，常藏身于石缝、树桩、桥墩等障碍物附近",
                    "best_season": ["春", "秋"],
                    "best_time": ["清晨", "傍晚", "夜间"],
                    "lures": ["软虫", "亮片", "VIB", "米诺"],
                    "techniques": ["跳底", "慢速收线", "定点搜索"],
                    "water_layer": "底层",
                    "difficulty": "中等"
                },
                {
                    "name": "鲈鱼",
                    "aliases": ["大口鲈", "加州鲈", "淡水鲈"],
                    "habits": "凶猛肉食性鱼类，喜欢有障碍物的水域，攻击性强",
                    "best_season": ["春", "夏", "秋"],
                    "best_time": ["清晨", "傍晚"],
                    "lures": ["软虫", "复合亮片", "摇摆饵", "波趴"],
                    "techniques": ["德州钓组", "倒钓钓组", "水面系"],
                    "water_layer": "全水层",
                    "difficulty": "简单"
                },
                {
                    "name": "翘嘴",
                    "aliases": ["翘嘴鲌", "白鱼", "大白鱼"],
                    "habits": "中上层肉食性鱼类，喜欢追逐小鱼，常在开阔水域活动",
                    "best_season": ["夏", "秋"],
                    "best_time": ["清晨", "傍晚", "夜间"],
                    "lures": ["米诺", "铁板", "亮片", "铅笔"],
                    "techniques": ["远投搜索", "快速收线", "水面系"],
                    "water_layer": "中上层",
                    "difficulty": "中等"
                },
                {
                    "name": "黑鱼",
                    "aliases": ["乌鱼", "生鱼", "财鱼"],
                    "habits": "底层肉食性鱼类，喜欢水草茂密的静水区域，耐低氧",
                    "best_season": ["夏"],
                    "best_time": ["白天"],
                    "lures": ["雷蛙", "软虫", "复合亮片"],
                    "techniques": ["水面系", "草洞搜索", "慢速收线"],
                    "water_layer": "表层/底层",
                    "difficulty": "简单"
                },
                {
                    "name": "军鱼",
                    "aliases": ["光倒刺鲃", "青棍", "光眼鱼"],
                    "habits": "中下层杂食性鱼类，喜欢流水环境，力量大",
                    "best_season": ["春", "夏", "秋"],
                    "best_time": ["白天"],
                    "lures": ["米诺", "亮片", "VIB", "小克重铁板"],
                    "techniques": ["流水搜索", "中速收线"],
                    "water_layer": "中下层",
                    "difficulty": "中等"
                }
            ],
            "fishing_spots": [
                {
                    "name": "太湖",
                    "location": "江苏省苏州市",
                    "fish_types": ["鳜鱼", "鲈鱼", "翘嘴", "军鱼"],
                    "tips": "西岸区域鳜鱼较多，东岸翘嘴活跃，建议使用船钓",
                    "difficulty": "中等",
                    "recommended_lures": ["软虫", "米诺", "亮片"]
                },
                {
                    "name": "阳澄湖",
                    "location": "江苏省苏州市",
                    "fish_types": ["鳜鱼", "翘嘴", "黑鱼"],
                    "tips": "水草区域黑鱼较多，深水区有鳜鱼",
                    "difficulty": "中等",
                    "recommended_lures": ["雷蛙", "软虫", "VIB"]
                },
                {
                    "name": "千岛湖",
                    "location": "浙江省杭州市",
                    "fish_types": ["鲈鱼", "翘嘴", "鳜鱼", "军鱼"],
                    "tips": "水质清澈，适合路亚，翘嘴资源丰富",
                    "difficulty": "简单",
                    "recommended_lures": ["米诺", "铁板", "亮片"]
                },
                {
                    "name": "洞庭湖",
                    "location": "湖南省岳阳市",
                    "fish_types": ["翘嘴", "鳜鱼", "黑鱼", "军鱼"],
                    "tips": "水面开阔，适合远投搜索翘嘴",
                    "difficulty": "中等",
                    "recommended_lures": ["铁板", "米诺", "铅笔"]
                }
            ],
            "equipment": [
                {
                    "type": "路亚竿",
                    "spec": "L调性（轻调）",
                    "suitable_for": ["小型鱼类", "精细作钓"],
                    "description": "适合软虫、小型米诺，手感灵敏"
                },
                {
                    "type": "路亚竿",
                    "spec": "ML调性（中轻调）",
                    "suitable_for": ["翘嘴", "军鱼"],
                    "description": "通用性强，适合大多数路亚饵"
                },
                {
                    "type": "路亚竿",
                    "spec": "M调性（中调）",
                    "suitable_for": ["鲈鱼", "翘嘴"],
                    "description": "适合硬饵、复合亮片，抛投距离远"
                },
                {
                    "type": "路亚竿",
                    "spec": "MH调性（中硬调）",
                    "suitable_for": ["鳜鱼", "鲈鱼"],
                    "description": "适合跳底、德州钓组，刺鱼有力"
                },
                {
                    "type": "路亚竿",
                    "spec": "H调性（硬调）",
                    "suitable_for": ["黑鱼", "重障碍区"],
                    "description": "适合雷蛙、重铅，强力刺鱼"
                },
                {
                    "type": "渔轮",
                    "spec": "纺车轮 2500型",
                    "suitable_for": ["通用"],
                    "description": "适合新手，操作简单，适合轻型饵"
                },
                {
                    "type": "渔轮",
                    "spec": "水滴轮",
                    "suitable_for": ["精准抛投", "重型饵"],
                    "description": "抛投精准，适合有经验的钓友"
                }
            ],
            "techniques": [
                {
                    "name": "跳底",
                    "description": "让饵在底部跳动，模拟受伤的小鱼",
                    "suitable_fish": ["鳜鱼", "鲈鱼"],
                    "suitable_lures": ["软虫", "VIB"],
                    "difficulty": "中等"
                },
                {
                    "name": "德州钓组",
                    "description": "软虫配防挂铅，适合障碍区搜索",
                    "suitable_fish": ["鲈鱼", "鳜鱼"],
                    "suitable_lures": ["软虫"],
                    "difficulty": "中等"
                },
                {
                    "name": "水面系",
                    "description": "在水面制造动静，诱鱼攻击",
                    "suitable_fish": ["黑鱼", "鲈鱼", "翘嘴"],
                    "suitable_lures": ["波趴", "雷蛙", "铅笔"],
                    "difficulty": "简单"
                },
                {
                    "name": "匀速收线",
                    "description": "保持均匀速度收线，简单有效",
                    "suitable_fish": ["翘嘴", "军鱼"],
                    "suitable_lures": ["米诺", "亮片", "铁板"],
                    "difficulty": "简单"
                }
            ]
        }

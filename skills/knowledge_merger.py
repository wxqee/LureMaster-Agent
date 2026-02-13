"""
知识合并 Skill

智能合并新数据到知识库
"""
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from config.schemas import get_knowledge_key, validate_data


class KnowledgeMerger:
    """知识合并器"""
    
    def __init__(self, knowledge_path: Optional[str] = None):
        """
        初始化知识合并器
        
        Args:
            knowledge_path: 知识库文件路径，默认为 data/fishing_knowledge.json
        """
        if knowledge_path:
            self.knowledge_path = Path(knowledge_path)
        else:
            self.knowledge_path = Path(__file__).parent.parent / "data" / "fishing_knowledge.json"
    
    def load_knowledge(self) -> Dict[str, Any]:
        """加载知识库"""
        if not self.knowledge_path.exists():
            return {}
        
        with open(self.knowledge_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def save_knowledge(self, knowledge: Dict[str, Any]) -> None:
        """保存知识库"""
        self.knowledge_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.knowledge_path, "w", encoding="utf-8") as f:
            json.dump(knowledge, f, ensure_ascii=False, indent=2)
    
    def backup(self) -> str:
        """
        备份知识库
        
        Returns:
            备份文件路径
        """
        if not self.knowledge_path.exists():
            return ""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.knowledge_path.with_suffix(f".backup_{timestamp}.json")
        shutil.copy(self.knowledge_path, backup_path)
        return str(backup_path)
    
    def check_duplicates(self, new_data: Dict[str, Any], existing: List[Dict], data_type: str) -> List[Dict[str, Any]]:
        """
        检查重复数据
        
        Args:
            new_data: 新数据
            existing: 现有数据列表
            data_type: 数据类型
            
        Returns:
            重复的数据列表
        """
        duplicates = []
        new_name = new_data.get("name", "").lower()
        
        for item in existing:
            item_name = item.get("name", "").lower()
            if item_name == new_name:
                duplicates.append(item)
                continue
            
            aliases = item.get("aliases", [])
            if isinstance(aliases, list):
                for alias in aliases:
                    if alias.lower() == new_name:
                        duplicates.append(item)
                        break
        
        return duplicates
    
    def merge(
        self, 
        new_data: Dict[str, Any], 
        data_type: str,
        strategy: str = "skip"
    ) -> Tuple[bool, str]:
        """
        合并新数据到知识库
        
        Args:
            new_data: 新数据
            data_type: 数据类型
            strategy: 合并策略 (skip/overwrite/merge)
                - skip: 跳过重复数据
                - overwrite: 覆盖重复数据
                - merge: 合并重复数据
                
        Returns:
            (是否成功, 消息)
        """
        if not validate_data(new_data, data_type):
            return False, f"数据验证失败：缺少必要字段"
        
        knowledge = self.load_knowledge()
        key = get_knowledge_key(data_type)
        
        if key not in knowledge:
            knowledge[key] = []
        
        existing = knowledge[key]
        duplicates = self.check_duplicates(new_data, existing, data_type)
        
        if duplicates:
            if strategy == "skip":
                return False, f"发现重复数据：{new_data.get('name')}，已跳过"
            elif strategy == "overwrite":
                for dup in duplicates:
                    existing.remove(dup)
                existing.append(new_data)
                self.save_knowledge(knowledge)
                return True, f"已覆盖重复数据：{new_data.get('name')}"
            elif strategy == "merge":
                merged = self._merge_data(duplicates[0], new_data)
                existing.remove(duplicates[0])
                existing.append(merged)
                self.save_knowledge(knowledge)
                return True, f"已合并重复数据：{new_data.get('name')}"
        else:
            existing.append(new_data)
            self.save_knowledge(knowledge)
            return True, f"已添加新数据：{new_data.get('name')}"
    
    def merge_batch(
        self, 
        data_list: List[Dict[str, Any]], 
        data_type: str,
        strategy: str = "skip"
    ) -> Tuple[int, List[str]]:
        """
        批量合并数据
        
        Args:
            data_list: 数据列表
            data_type: 数据类型
            strategy: 合并策略
            
        Returns:
            (成功数量, 消息列表)
        """
        success_count = 0
        messages = []
        
        for data in data_list:
            success, msg = self.merge(data, data_type, strategy)
            if success:
                success_count += 1
            messages.append(msg)
        
        return success_count, messages
    
    def _merge_data(self, existing: Dict[str, Any], new_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        合并两条数据
        
        Args:
            existing: 现有数据
            new_data: 新数据
            
        Returns:
            合并后的数据
        """
        merged = existing.copy()
        
        for key, value in new_data.items():
            if value is None:
                continue
            
            if key not in merged or merged[key] is None:
                merged[key] = value
            elif isinstance(merged[key], list) and isinstance(value, list):
                existing_items = set(str(item) for item in merged[key])
                for item in value:
                    if str(item) not in existing_items:
                        merged[key].append(item)
            elif isinstance(merged[key], str) and isinstance(value, str):
                if merged[key] != value:
                    merged[key] = f"{merged[key]}；{value}"
            else:
                merged[key] = value
        
        return merged
    
    def get_stats(self) -> Dict[str, int]:
        """
        获取知识库统计
        
        Returns:
            各类型数据数量
        """
        knowledge = self.load_knowledge()
        stats = {}
        
        for key, value in knowledge.items():
            if isinstance(value, list):
                stats[key] = len(value)
        
        return stats
    
    def format_stats(self) -> str:
        """格式化统计信息"""
        stats = self.get_stats()
        
        type_names = {
            "fish_species": "鱼种",
            "lures": "路亚饵",
            "rigs": "钓组",
            "spot_types": "标点类型",
            "fishing_spots": "钓点",
            "equipment": "装备",
            "techniques": "钓法技巧",
            "weather_tips": "天气建议"
        }
        
        lines = ["\n📊 知识库统计", "═" * 40]
        
        for key, count in stats.items():
            name = type_names.get(key, key)
            lines.append(f"  {name}: {count} 条")
        
        total = sum(stats.values())
        lines.append("─" * 40)
        lines.append(f"  总计: {total} 条数据")
        lines.append("═" * 40)
        
        return "\n".join(lines)

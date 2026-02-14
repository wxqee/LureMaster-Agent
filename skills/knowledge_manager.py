"""
知识库管理器

提供知识库的完整生命周期管理，包括：
- 元数据管理（来源、置信度、版本）
- 向量检索（语义搜索）
- 版本控制
- 反馈收集
"""
import json
import hashlib
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum


class KnowledgeSource(Enum):
    """知识来源"""
    EXPERT = "expert"              # 专家录入
    MANUAL = "manual"              # 手动录入
    COLLECTED = "collected"        # 网页采集
    LLM_GENERATED = "llm_generated"  # LLM 生成
    USER_FEEDBACK = "user_feedback"  # 用户反馈
    IMPORTED = "imported"          # 外部导入


class KnowledgeStatus(Enum):
    """知识状态"""
    DRAFT = "draft"          # 草稿
    PENDING = "pending"      # 待审核
    ACTIVE = "active"        # 已发布
    DEPRECATED = "deprecated"  # 已废弃
    ARCHIVED = "archived"    # 已归档


@dataclass
class KnowledgeMeta:
    """知识元数据"""
    version: int = 1
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    source: str = KnowledgeSource.MANUAL.value
    confidence: float = 1.0
    verified: bool = False
    verified_by: Optional[str] = None
    verified_at: Optional[str] = None
    feedback_count: int = 0
    positive_feedback: int = 0
    negative_feedback: int = 0
    status: str = KnowledgeStatus.ACTIVE.value
    parent_version: Optional[int] = None
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "KnowledgeMeta":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class KnowledgeVersion:
    """知识版本记录"""
    version: int
    data: Dict[str, Any]
    meta: KnowledgeMeta
    changes: str = ""
    changed_at: str = field(default_factory=lambda: datetime.now().isoformat())
    changed_by: str = "system"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "data": self.data,
            "meta": self.meta.to_dict(),
            "changes": self.changes,
            "changed_at": self.changed_at,
            "changed_by": self.changed_by
        }


class KnowledgeManager:
    """知识库管理器"""
    
    TYPE_MAPPING = {
        "fish": "fish_species",
        "lure": "lures",
        "rig": "rigs",
        "spot_type": "spot_types",
        "fish_species": "fish_species",
        "lures": "lures",
        "rigs": "rigs",
        "spot_types": "spot_types",
    }
    
    TYPE_NAMES = {
        "fish_species": "鱼种",
        "lures": "路亚饵",
        "rigs": "钓组",
        "spot_types": "标点类型",
        "fishing_spots": "钓点",
        "equipment": "装备",
        "techniques": "钓法技巧",
    }
    
    DEFAULT_CONFIDENCE = {
        KnowledgeSource.EXPERT.value: 1.0,
        KnowledgeSource.MANUAL.value: 0.9,
        KnowledgeSource.COLLECTED.value: 0.7,
        KnowledgeSource.LLM_GENERATED.value: 0.6,
        KnowledgeSource.USER_FEEDBACK.value: 0.8,
        KnowledgeSource.IMPORTED.value: 0.7,
    }
    
    def __init__(self, knowledge_path: Optional[str] = None, versions_path: Optional[str] = None):
        if knowledge_path:
            self.knowledge_path = Path(knowledge_path)
        else:
            self.knowledge_path = Path(__file__).parent.parent / "data" / "fishing_knowledge.json"
        
        if versions_path:
            self.versions_path = Path(versions_path)
        else:
            self.versions_path = Path(__file__).parent.parent / "data" / "knowledge_versions.json"
        
        self._knowledge = None
        self._versions = None
    
    def load_knowledge(self) -> Dict[str, Any]:
        """加载知识库"""
        if self._knowledge is not None:
            return self._knowledge
        
        if not self.knowledge_path.exists():
            self._knowledge = {}
        else:
            with open(self.knowledge_path, "r", encoding="utf-8") as f:
                self._knowledge = json.load(f)
        
        return self._knowledge
    
    def save_knowledge(self, knowledge: Dict[str, Any]) -> None:
        """保存知识库"""
        self.knowledge_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.knowledge_path, "w", encoding="utf-8") as f:
            json.dump(knowledge, f, ensure_ascii=False, indent=2)
        self._knowledge = knowledge
    
    def load_versions(self) -> Dict[str, Any]:
        """加载版本记录"""
        if self._versions is not None:
            return self._versions
        
        if not self.versions_path.exists():
            self._versions = {}
        else:
            with open(self.versions_path, "r", encoding="utf-8") as f:
                self._versions = json.load(f)
        
        return self._versions
    
    def save_versions(self, versions: Dict[str, Any]) -> None:
        """保存版本记录"""
        self.versions_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.versions_path, "w", encoding="utf-8") as f:
            json.dump(versions, f, ensure_ascii=False, indent=2)
        self._versions = versions
    
    def get_type_key(self, data_type: str) -> str:
        """获取知识库键名"""
        return self.TYPE_MAPPING.get(data_type, data_type)
    
    def add_knowledge(
        self,
        data: Dict[str, Any],
        data_type: str,
        source: str = KnowledgeSource.MANUAL.value,
        confidence: Optional[float] = None,
        verified: bool = False,
        changes: str = ""
    ) -> Tuple[bool, str]:
        """
        添加知识（带完整元数据）
        
        Args:
            data: 知识数据
            data_type: 数据类型
            source: 知识来源
            confidence: 置信度（不传则根据来源自动设置）
            verified: 是否已验证
            changes: 变更说明
            
        Returns:
            (是否成功, 消息)
        """
        knowledge = self.load_knowledge()
        versions = self.load_versions()
        key = self.get_type_key(data_type)
        
        if key not in knowledge:
            knowledge[key] = []
        
        if confidence is None:
            confidence = self.DEFAULT_CONFIDENCE.get(source, 0.7)
        
        existing, existing_idx = self._find_existing(data, knowledge[key])
        
        if existing:
            return self._update_existing(
                knowledge, versions, key, existing_idx, data, 
                source, confidence, verified, changes
            )
        else:
            return self._add_new(
                knowledge, versions, key, data, 
                source, confidence, verified
            )
    
    def _find_existing(self, data: Dict[str, Any], items: List[Dict]) -> Tuple[Optional[Dict], int]:
        """查找已存在的数据"""
        name = data.get("name", "").lower()
        
        for idx, item in enumerate(items):
            item_name = item.get("name", "").lower()
            if item_name == name:
                return item, idx
            
            aliases = item.get("aliases", [])
            if isinstance(aliases, list):
                for alias in aliases:
                    if alias.lower() == name:
                        return item, idx
        
        return None, -1
    
    def _add_new(
        self,
        knowledge: Dict[str, Any],
        versions: Dict[str, Any],
        key: str,
        data: Dict[str, Any],
        source: str,
        confidence: float,
        verified: bool
    ) -> Tuple[bool, str]:
        """添加新知识"""
        meta = KnowledgeMeta(
            source=source,
            confidence=confidence,
            verified=verified,
            status=KnowledgeStatus.ACTIVE.value
        )
        
        data_with_meta = {**data, "_meta": meta.to_dict()}
        knowledge[key].append(data_with_meta)
        
        version_key = f"{key}:{data.get('name')}"
        if version_key not in versions:
            versions[version_key] = []
        
        version_record = KnowledgeVersion(
            version=1,
            data=data,
            meta=meta,
            changes="初始版本"
        )
        versions[version_key].append(version_record.to_dict())
        
        self.save_knowledge(knowledge)
        self.save_versions(versions)
        
        return True, f"已添加新数据：{data.get('name')}（置信度: {confidence:.0%}）"
    
    def _update_existing(
        self,
        knowledge: Dict[str, Any],
        versions: Dict[str, Any],
        key: str,
        idx: int,
        data: Dict[str, Any],
        source: str,
        confidence: float,
        verified: bool,
        changes: str
    ) -> Tuple[bool, str]:
        """更新已存在的知识"""
        existing = knowledge[key][idx]
        old_meta = existing.get("_meta", {})
        old_version = old_meta.get("version", 1)
        
        new_meta = KnowledgeMeta(
            version=old_version + 1,
            source=source,
            confidence=max(old_meta.get("confidence", 0.7), confidence),
            verified=verified or old_meta.get("verified", False),
            status=KnowledgeStatus.ACTIVE.value,
            parent_version=old_version
        )
        
        merged_data = self._merge_data(existing, data)
        merged_data["_meta"] = new_meta.to_dict()
        knowledge[key][idx] = merged_data
        
        version_key = f"{key}:{data.get('name')}"
        if version_key not in versions:
            versions[version_key] = []
        
        version_record = KnowledgeVersion(
            version=new_meta.version,
            data=merged_data,
            meta=new_meta,
            changes=changes or "数据更新"
        )
        versions[version_key].append(version_record.to_dict())
        
        self.save_knowledge(knowledge)
        self.save_versions(versions)
        
        return True, f"已更新数据：{data.get('name')}（版本: {new_meta.version}）"
    
    def _merge_data(self, existing: Dict[str, Any], new_data: Dict[str, Any]) -> Dict[str, Any]:
        """合并数据"""
        merged = {}
        
        for key in set(list(existing.keys()) + list(new_data.keys())):
            if key == "_meta":
                continue
            
            old_val = existing.get(key)
            new_val = new_data.get(key)
            
            if new_val is None:
                merged[key] = old_val
            elif old_val is None:
                merged[key] = new_val
            elif isinstance(old_val, list) and isinstance(new_val, list):
                merged[key] = list(set(str(x) for x in old_val) | set(str(x) for x in new_val))
                merged[key] = list(merged[key])
            elif isinstance(old_val, str) and isinstance(new_val, str):
                if old_val != new_val and len(new_val) > len(old_val):
                    merged[key] = new_val
                else:
                    merged[key] = old_val
            else:
                merged[key] = new_val
        
        return merged
    
    def add_feedback(
        self,
        data_type: str,
        name: str,
        is_positive: bool,
        comment: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        添加用户反馈
        
        Args:
            data_type: 数据类型
            name: 知识名称
            is_positive: 是否正面反馈
            comment: 反馈评论
            
        Returns:
            (是否成功, 消息)
        """
        knowledge = self.load_knowledge()
        key = self.get_type_key(data_type)
        
        if key not in knowledge:
            return False, f"未找到类型: {data_type}"
        
        for item in knowledge[key]:
            if item.get("name") == name:
                meta = item.get("_meta", {})
                meta["feedback_count"] = meta.get("feedback_count", 0) + 1
                
                if is_positive:
                    meta["positive_feedback"] = meta.get("positive_feedback", 0) + 1
                else:
                    meta["negative_feedback"] = meta.get("negative_feedback", 0) + 1
                
                total = meta["positive_feedback"] + meta["negative_feedback"]
                if total > 0:
                    positive_rate = meta["positive_feedback"] / total
                    if positive_rate < 0.3 and total >= 5:
                        meta["status"] = KnowledgeStatus.DEPRECATED.value
                    elif positive_rate < 0.5 and total >= 3:
                        meta["status"] = KnowledgeStatus.PENDING.value
                
                item["_meta"] = meta
                self.save_knowledge(knowledge)
                
                return True, f"已记录反馈：{name}"
        
        return False, f"未找到知识：{name}"
    
    def verify_knowledge(
        self,
        data_type: str,
        name: str,
        verified_by: str
    ) -> Tuple[bool, str]:
        """
        验证知识
        
        Args:
            data_type: 数据类型
            name: 知识名称
            verified_by: 验证者
            
        Returns:
            (是否成功, 消息)
        """
        knowledge = self.load_knowledge()
        key = self.get_type_key(data_type)
        
        if key not in knowledge:
            return False, f"未找到类型: {data_type}"
        
        for item in knowledge[key]:
            if item.get("name") == name:
                meta = item.get("_meta", {})
                meta["verified"] = True
                meta["verified_by"] = verified_by
                meta["verified_at"] = datetime.now().isoformat()
                meta["confidence"] = 1.0
                meta["status"] = KnowledgeStatus.ACTIVE.value
                item["_meta"] = meta
                
                self.save_knowledge(knowledge)
                return True, f"已验证知识：{name}"
        
        return False, f"未找到知识：{name}"
    
    def get_knowledge_versions(self, data_type: str, name: str) -> List[Dict[str, Any]]:
        """获取知识版本历史"""
        versions = self.load_versions()
        key = f"{self.get_type_key(data_type)}:{name}"
        return versions.get(key, [])
    
    def get_low_confidence_knowledge(self, threshold: float = 0.7) -> List[Dict[str, Any]]:
        """获取低置信度知识（需要审核）"""
        knowledge = self.load_knowledge()
        result = []
        
        for type_key, items in knowledge.items():
            if not isinstance(items, list):
                continue
            
            for item in items:
                meta = item.get("_meta", {})
                confidence = meta.get("confidence", 1.0)
                
                if confidence < threshold or not meta.get("verified", False):
                    result.append({
                        "type": type_key,
                        "name": item.get("name"),
                        "confidence": confidence,
                        "source": meta.get("source", "unknown"),
                        "verified": meta.get("verified", False),
                        "feedback": {
                            "positive": meta.get("positive_feedback", 0),
                            "negative": meta.get("negative_feedback", 0)
                        }
                    })
        
        return result
    
    def get_stats(self) -> Dict[str, Any]:
        """获取知识库统计"""
        knowledge = self.load_knowledge()
        stats = {
            "by_type": {},
            "by_source": {},
            "by_status": {},
            "verified_count": 0,
            "total_confidence": 0,
            "total_count": 0
        }
        
        for type_key, items in knowledge.items():
            if not isinstance(items, list):
                continue
            
            stats["by_type"][type_key] = len(items)
            stats["total_count"] += len(items)
            
            for item in items:
                meta = item.get("_meta", {})
                source = meta.get("source", "unknown")
                status = meta.get("status", "active")
                
                stats["by_source"][source] = stats["by_source"].get(source, 0) + 1
                stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
                
                if meta.get("verified", False):
                    stats["verified_count"] += 1
                
                stats["total_confidence"] += meta.get("confidence", 1.0)
        
        if stats["total_count"] > 0:
            stats["avg_confidence"] = stats["total_confidence"] / stats["total_count"]
        
        return stats
    
    def format_stats(self) -> str:
        """格式化统计信息"""
        stats = self.get_stats()
        
        lines = [
            "\n📊 知识库统计",
            "═" * 50,
            "\n【按类型】"
        ]
        
        for key, count in stats["by_type"].items():
            name = self.TYPE_NAMES.get(key, key)
            lines.append(f"  {name}: {count} 条")
        
        lines.append("\n【按来源】")
        source_names = {
            "expert": "专家录入",
            "manual": "手动录入",
            "collected": "网页采集",
            "llm_generated": "AI 生成",
            "user_feedback": "用户反馈",
            "imported": "外部导入",
        }
        for source, count in stats["by_source"].items():
            name = source_names.get(source, source)
            lines.append(f"  {name}: {count} 条")
        
        lines.append("\n【质量指标】")
        lines.append(f"  已验证: {stats['verified_count']}/{stats['total_count']} 条")
        lines.append(f"  平均置信度: {stats.get('avg_confidence', 0):.0%}")
        
        lines.extend([
            "─" * 50,
            f"  总计: {stats['total_count']} 条数据",
            "═" * 50
        ])
        
        return "\n".join(lines)
    
    def backup(self) -> str:
        """备份知识库"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if self.knowledge_path.exists():
            backup_path = self.knowledge_path.with_suffix(f".backup_{timestamp}.json")
            shutil.copy(self.knowledge_path, backup_path)
        
        if self.versions_path.exists():
            backup_path = self.versions_path.with_suffix(f".backup_{timestamp}.json")
            shutil.copy(self.versions_path, backup_path)
        
        return timestamp

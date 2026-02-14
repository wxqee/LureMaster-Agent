#!/usr/bin/env python3
"""
知识库数据迁移脚本

为现有知识添加元数据
"""
import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from skills.knowledge_manager import KnowledgeManager, KnowledgeMeta, KnowledgeSource, KnowledgeStatus


def migrate_knowledge():
    """迁移知识库数据，添加元数据"""
    manager = KnowledgeManager()
    knowledge = manager.load_knowledge()
    
    migrated_count = 0
    
    for type_key, items in knowledge.items():
        if not isinstance(items, list):
            continue
        
        for item in items:
            if "_meta" in item:
                continue
            
            meta = KnowledgeMeta(
                source=KnowledgeSource.MANUAL.value,
                confidence=0.9,
                verified=False,
                status=KnowledgeStatus.ACTIVE.value
            )
            
            item["_meta"] = meta.to_dict()
            migrated_count += 1
            print(f"  已迁移: {type_key}/{item.get('name', '未知')}")
    
    if migrated_count > 0:
        manager.backup()
        manager.save_knowledge(knowledge)
        print(f"\n✓ 共迁移 {migrated_count} 条数据")
    else:
        print("无需迁移，所有数据已有元数据")
    
    return migrated_count


if __name__ == "__main__":
    print("开始迁移知识库数据...")
    print("=" * 50)
    migrate_knowledge()
    print("=" * 50)
    print("迁移完成！")

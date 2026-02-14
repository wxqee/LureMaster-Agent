"""
向量检索模块

提供基于语义的知识检索功能
"""
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    VECTOR_SEARCH_AVAILABLE = True
except ImportError:
    VECTOR_SEARCH_AVAILABLE = False


@dataclass
class SearchResult:
    """检索结果"""
    data: Dict[str, Any]
    score: float
    data_type: str
    search_type: str  # "semantic" or "keyword"


class VectorStore:
    """向量存储"""
    
    EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
    
    def __init__(self, knowledge_path: Optional[str] = None, index_path: Optional[str] = None):
        if knowledge_path:
            self.knowledge_path = Path(knowledge_path)
        else:
            self.knowledge_path = Path(__file__).parent.parent / "data" / "fishing_knowledge.json"
        
        if index_path:
            self.index_path = Path(index_path)
        else:
            self.index_path = Path(__file__).parent.parent / "data" / "vector_index.json"
        
        self.encoder = None
        self.embeddings = {}
        self.documents = {}
        self._initialized = False
    
    def _init_encoder(self):
        """初始化编码器"""
        if self.encoder is not None:
            return True
        
        if not VECTOR_SEARCH_AVAILABLE:
            return False
        
        try:
            self.encoder = SentenceTransformer(self.EMBEDDING_MODEL)
            return True
        except Exception as e:
            print(f"初始化编码器失败: {e}")
            return False
    
    def _load_knowledge(self) -> Dict[str, Any]:
        """加载知识库"""
        if not self.knowledge_path.exists():
            return {}
        
        with open(self.knowledge_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def _load_index(self) -> Dict[str, Any]:
        """加载向量索引"""
        if not self.index_path.exists():
            return {}
        
        with open(self.index_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def _save_index(self, index: Dict[str, Any]):
        """保存向量索引"""
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.index_path, "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False)
    
    def _text_to_embedding(self, text: str) -> Optional[List[float]]:
        """文本转向量"""
        if not self._init_encoder():
            return None
        
        try:
            embedding = self.encoder.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            print(f"编码失败: {e}")
            return None
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        if not VECTOR_SEARCH_AVAILABLE:
            return 0.0
        
        arr1 = np.array(vec1)
        arr2 = np.array(vec2)
        
        dot_product = np.dot(arr1, arr2)
        norm1 = np.linalg.norm(arr1)
        norm2 = np.linalg.norm(arr2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
    
    def _create_document_text(self, item: Dict[str, Any], data_type: str) -> str:
        """创建用于向量化的文档文本"""
        parts = []
        
        if data_type == "fish_species":
            parts.append(f"鱼种: {item.get('name', '')}")
            if item.get('aliases'):
                parts.append(f"别名: {', '.join(item['aliases'])}")
            parts.append(f"习性: {item.get('habits', '')}")
            parts.append(f"推荐路亚饵: {', '.join(item.get('lures', []))}")
            parts.append(f"推荐钓法: {', '.join(item.get('techniques', []))}")
            parts.append(f"活动水层: {item.get('water_layer', '')}")
            parts.append(f"最佳季节: {', '.join(item.get('best_season', []))}")
            parts.append(f"最佳时段: {', '.join(item.get('best_time', []))}")
            if item.get('tips'):
                parts.append(f"技巧: {item['tips']}")
        
        elif data_type == "lures":
            parts.append(f"路亚饵: {item.get('name', '')}")
            parts.append(f"分类: {item.get('category', '')}")
            parts.append(f"目标鱼种: {', '.join(item.get('target_fish', []))}")
            parts.append(f"使用手法: {', '.join(item.get('techniques', []))}")
            if item.get('tips'):
                parts.append(f"技巧: {item['tips']}")
        
        elif data_type == "rigs":
            parts.append(f"钓组: {item.get('name', '')}")
            parts.append(f"组件: {', '.join(item.get('components', []))}")
            parts.append(f"适合鱼种: {', '.join(item.get('suitable_fish', []))}")
            parts.append(f"适合环境: {', '.join(item.get('suitable_environment', []))}")
            parts.append(f"优点: {item.get('advantages', '')}")
            if item.get('setup_tips'):
                parts.append(f"组装技巧: {item['setup_tips']}")
        
        else:
            for key, value in item.items():
                if key.startswith("_"):
                    continue
                if isinstance(value, list):
                    parts.append(f"{key}: {', '.join(str(v) for v in value)}")
                elif isinstance(value, dict):
                    parts.append(f"{key}: {json.dumps(value, ensure_ascii=False)}")
                else:
                    parts.append(f"{key}: {value}")
        
        return "\n".join(parts)
    
    def build_index(self, force: bool = False) -> Tuple[int, str]:
        """
        构建向量索引
        
        Args:
            force: 是否强制重建
            
        Returns:
            (索引数量, 消息)
        """
        if not self._init_encoder():
            return 0, "向量检索不可用，请安装 sentence-transformers: pip install sentence-transformers"
        
        knowledge = self._load_knowledge()
        existing_index = self._load_index() if not force else {}
        
        indexed_count = 0
        
        for type_key, items in knowledge.items():
            if not isinstance(items, list):
                continue
            
            for item in items:
                name = item.get("name", "")
                if not name:
                    continue
                
                doc_id = f"{type_key}:{name}"
                
                if doc_id in existing_index.get("embeddings", {}) and not force:
                    continue
                
                text = self._create_document_text(item, type_key)
                embedding = self._text_to_embedding(text)
                
                if embedding:
                    if "embeddings" not in existing_index:
                        existing_index["embeddings"] = {}
                    if "documents" not in existing_index:
                        existing_index["documents"] = {}
                    
                    existing_index["embeddings"][doc_id] = embedding
                    existing_index["documents"][doc_id] = {
                        "type": type_key,
                        "name": name,
                        "text": text[:500]
                    }
                    indexed_count += 1
        
        if indexed_count > 0:
            existing_index["model"] = self.EMBEDDING_MODEL
            existing_index["updated_at"] = str(Path(__file__).stat().st_mtime)
            self._save_index(existing_index)
        
        total = len(existing_index.get("embeddings", {}))
        return indexed_count, f"已索引 {indexed_count} 条新数据，总计 {total} 条"
    
    def search(
        self,
        query: str,
        top_k: int = 5,
        data_type: Optional[str] = None,
        threshold: float = 0.3
    ) -> List[SearchResult]:
        """
        语义搜索
        
        Args:
            query: 查询文本
            top_k: 返回数量
            data_type: 限制数据类型
            threshold: 相似度阈值
            
        Returns:
            搜索结果列表
        """
        if not self._init_encoder():
            return []
        
        index = self._load_index()
        embeddings = index.get("embeddings", {})
        documents = index.get("documents", {})
        
        if not embeddings:
            self.build_index()
            index = self._load_index()
            embeddings = index.get("embeddings", {})
            documents = index.get("documents", {})
        
        query_embedding = self._text_to_embedding(query)
        if not query_embedding:
            return []
        
        results = []
        
        for doc_id, doc_embedding in embeddings.items():
            doc_info = documents.get(doc_id, {})
            
            if data_type and doc_info.get("type") != data_type:
                continue
            
            score = self._cosine_similarity(query_embedding, doc_embedding)
            
            if score >= threshold:
                knowledge = self._load_knowledge()
                doc_type = doc_info.get("type")
                doc_name = doc_info.get("name")
                
                doc_data = None
                for item in knowledge.get(doc_type, []):
                    if item.get("name") == doc_name:
                        doc_data = item
                        break
                
                if doc_data:
                    results.append(SearchResult(
                        data=doc_data,
                        score=score,
                        data_type=doc_type,
                        search_type="semantic"
                    ))
        
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]
    
    def hybrid_search(
        self,
        query: str,
        top_k: int = 5,
        data_type: Optional[str] = None,
        semantic_weight: float = 0.7
    ) -> List[SearchResult]:
        """
        混合检索（语义 + 关键词）
        
        Args:
            query: 查询文本
            top_k: 返回数量
            data_type: 限制数据类型
            semantic_weight: 语义搜索权重（0-1）
            
        Returns:
            搜索结果列表
        """
        knowledge = self._load_knowledge()
        keyword_results = self._keyword_search(knowledge, query, data_type, top_k * 2)
        
        semantic_results = self.search(query, top_k * 2, data_type)
        
        combined = {}
        
        for result in semantic_results:
            key = f"{result.data_type}:{result.data.get('name')}"
            combined[key] = SearchResult(
                data=result.data,
                score=result.score * semantic_weight,
                data_type=result.data_type,
                search_type="semantic"
            )
        
        keyword_weight = 1 - semantic_weight
        for result in keyword_results:
            key = f"{result.data_type}:{result.data.get('name')}"
            if key in combined:
                combined[key].score += result.score * keyword_weight
                combined[key].search_type = "hybrid"
            else:
                combined[key] = SearchResult(
                    data=result.data,
                    score=result.score * keyword_weight,
                    data_type=result.data_type,
                    search_type="keyword"
                )
        
        results = sorted(combined.values(), key=lambda x: x.score, reverse=True)
        return results[:top_k]
    
    def _keyword_search(
        self,
        knowledge: Dict[str, Any],
        query: str,
        data_type: Optional[str],
        top_k: int
    ) -> List[SearchResult]:
        """关键词搜索"""
        query_lower = query.lower()
        results = []
        
        type_keys = [data_type] if data_type else list(knowledge.keys())
        
        for type_key in type_keys:
            items = knowledge.get(type_key, [])
            if not isinstance(items, list):
                continue
            
            for item in items:
                score = 0.0
                
                name = item.get("name", "").lower()
                if query_lower in name or name in query_lower:
                    score += 0.8
                
                aliases = item.get("aliases", [])
                for alias in aliases:
                    if query_lower in alias.lower():
                        score += 0.6
                        break
                
                for key, value in item.items():
                    if key.startswith("_"):
                        continue
                    if isinstance(value, str) and query_lower in value.lower():
                        score += 0.3
                    elif isinstance(value, list):
                        for v in value:
                            if isinstance(v, str) and query_lower in v.lower():
                                score += 0.2
                                break
                
                if score > 0:
                    results.append(SearchResult(
                        data=item,
                        score=score,
                        data_type=type_key,
                        search_type="keyword"
                    ))
        
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]


def check_vector_search_available() -> Tuple[bool, str]:
    """检查向量检索是否可用"""
    if VECTOR_SEARCH_AVAILABLE:
        return True, "向量检索可用"
    else:
        return False, "向量检索不可用，请安装: pip install sentence-transformers"

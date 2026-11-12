"""分类路径的 ChromaDB 存储封装。单 Collection，每条记录独立。"""

import logging
import time
from typing import Any

import chromadb

from ..models import CategoryRecord

logger = logging.getLogger(__name__)


class CategoryStore:
    """分类路径的 ChromaDB 存储封装。单 Collection，每条记录独立。

    ChromaDB 记录映射：
        id           → record.id (UUID)
        document     → record.document (类别说明)
        embedding    → record.embedding (向量)
        metadata:
            category_path    → record.category_path
            ValidCount       → record.valid_count
            LastUpdateTime   → record.last_update_time
    """

    def __init__(self, chroma_client: chromadb.PersistentClient, collection_name: str, dimension: int):
        """初始化。获取或创建 ChromaDB Collection。

        Args:
            chroma_client: ChromaDB 持久化客户端
            collection_name: Collection 名称
            dimension: 向量维度
        """
        self._client = chroma_client
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        self._dimension = dimension

    def _record_from_chroma(self, id_: str, document: str, embedding: list[float],
                            metadata: dict[str, Any]) -> CategoryRecord:
        """将 ChromaDB 返回的单条数据转换为 CategoryRecord。"""
        return CategoryRecord(
            id=id_,
            category_path=metadata.get("category_path", ""),
            document=document,
            embedding=embedding,
            valid_count=float(metadata.get("ValidCount", 1.0)),
            last_update_time=float(metadata.get("LastUpdateTime", time.time())),
        )

    def add(self, record: CategoryRecord) -> str:
        """添加一条分类记录。返回记录 UUID。

        Args:
            record: 分类记录

        Returns:
            记录 UUID
        """
        self._collection.add(
            ids=[record.id],
            documents=[record.document],
            embeddings=[record.embedding],
            metadatas=[{
                "category_path": record.category_path,
                "ValidCount": record.valid_count,
                "LastUpdateTime": record.last_update_time,
            }],
        )
        return record.id

    def get(self, record_id: str) -> CategoryRecord | None:
        """按 UUID 获取单条记录。

        Args:
            record_id: 记录 UUID

        Returns:
            分类记录，不存在返回 None
        """
        result = self._collection.get(
            ids=[record_id],
            include=["embeddings", "documents", "metadatas"],
        )
        if not result["ids"]:
            return None
        return self._record_from_chroma(
            id_=result["ids"][0],
            document=result["documents"][0],
            embedding=result["embeddings"][0],
            metadata=result["metadatas"][0],
        )

    def update_heat(self, record_id: str, valid_count: float) -> None:
        """更新单条记录的 ValidCount 和 LastUpdateTime。

        Args:
            record_id: 记录 UUID
            valid_count: 新的有效计数
        """
        self._collection.update(
            ids=[record_id],
            metadatas=[{
                "ValidCount": valid_count,
                "LastUpdateTime": time.time(),
            }],
        )

    def delete(self, record_ids: list[str]) -> None:
        """删除指定记录。

        Args:
            record_ids: 记录 UUID 列表
        """
        if record_ids:
            self._collection.delete(ids=record_ids)

    def query_by_embedding(self, embedding: list[float], top_k: int = 7) -> list[tuple[CategoryRecord, float]]:
        """向量检索。按 cosine distance 排序返回 TopK。

        Args:
            embedding: 查询向量
            top_k: 返回数量

        Returns:
            [(CategoryRecord, distance), ...] 按距离排序
        """
        result = self._collection.query(
            query_embeddings=[embedding],
            n_results=top_k,
            include=["embeddings", "documents", "metadatas", "distances"],
        )

        if not result["ids"] or not result["ids"][0]:
            return []

        records = []
        ids = result["ids"][0]
        documents = result["documents"][0]
        embeddings = result["embeddings"][0]
        metadatas = result["metadatas"][0]
        distances = result["distances"][0]

        for i in range(len(ids)):
            record = self._record_from_chroma(
                id_=ids[i],
                document=documents[i],
                embedding=embeddings[i],
                metadata=metadatas[i],
            )
            records.append((record, distances[i]))

        return records

    def query_by_path(self, category_path: str) -> list[CategoryRecord]:
        """按精确路径查询。同一路径可能有多条记录。

        Args:
            category_path: 分类路径

        Returns:
            匹配的记录列表
        """
        result = self._collection.get(
            where={"category_path": category_path},
            include=["embeddings", "documents", "metadatas"],
        )

        if not result["ids"]:
            return []

        return [
            self._record_from_chroma(
                id_=result["ids"][i],
                document=result["documents"][i],
                embedding=result["embeddings"][i],
                metadata=result["metadatas"][i],
            )
            for i in range(len(result["ids"]))
        ]
    def get_all_records(self) -> list[CategoryRecord]:
        """获取所有记录。用于全量衰减。

        Returns:
            所有分类记录列表
        """
        result = self._collection.get(
            include=["embeddings", "documents", "metadatas"],
        )

        if not result["ids"]:
            return []

        return [
            self._record_from_chroma(
                id_=result["ids"][i],
                document=result["documents"][i],
                embedding=result["embeddings"][i],
                metadata=result["metadatas"][i],
            )
            for i in range(len(result["ids"]))
        ]

    def export_tree(self) -> dict:
        """导出分类为嵌套 JSON 结构（路径节点自然合并成树样展示）。

        从扁平的 category_path 记录按路径前缀自然合并成嵌套结构。同一路径可能
        有多条记录（不同描述），全部挂在该路径节点下。中间路径（无直接记录）
        也作为节点出现，以保持结构完整。子节点按名称排序。

        Returns:
            嵌套 dict，根节点路径为 "/"。每个节点结构：
            {
                "name": 节点名称（根为 "/"，其余为路径最后一段）,
                "path": 完整路径,
                "records": 该路径下的记录列表 [{"id", "document", "valid_count"}],
                "children": [子节点, ...]
            }
        """
        records = self.get_all_records()

        # 路径 → 记录列表
        path_records: dict[str, list[CategoryRecord]] = {}
        for r in records:
            path_records.setdefault(r.category_path, []).append(r)

        # 收集所有需要存在的路径（含中间路径）
        all_paths: set[str] = set()
        for path in path_records:
            if path == "/":
                all_paths.add("/")
                continue
            segments = path.strip("/").split("/")
            for i in range(1, len(segments) + 1):
                all_paths.add("/" + "/".join(segments[:i]))

        # 构建树：按路径深度排序，保证父节点先于子节点创建
        root = {"name": "/", "path": "/", "records": [], "children": []}
        nodes: dict[str, dict] = {"/": root}

        for path in sorted(all_paths, key=lambda p: p.count("/")):
            if path == "/":
                continue
            parent = self._parent_path(path)
            name = path.rsplit("/", 1)[-1]
            node = {"name": name, "path": path, "records": [], "children": []}
            nodes[path] = node
            nodes[parent]["children"].append(node)

        # 挂载记录到对应路径节点
        for path, recs in path_records.items():
            if path in nodes:
                nodes[path]["records"] = [
                    {"id": r.id, "document": r.document, "valid_count": r.valid_count}
                    for r in recs
                ]

        # 子节点按名称排序（便于稳定输出）
        self._sort_children(root)
        return root

    @staticmethod
    def _parent_path(path: str) -> str:
        """获取父路径。根路径 / 返回 /。"""
        if path == "/" or "/" not in path[1:]:
            return "/"
        return path.rsplit("/", 1)[0] or "/"

    @staticmethod
    def _sort_children(node: dict) -> None:
        """递归对子节点按名称排序。"""
        node["children"].sort(key=lambda c: c["name"])
        for child in node["children"]:
            CategoryStore._sort_children(child)

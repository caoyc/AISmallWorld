"""共现表服务（供 CL-05 buffer 调用）。"""
from __future__ import annotations
from .cooccurrence_store import CooccurrenceStore, CooccurrenceRecord


class CooccurrenceService:
    def __init__(self, store: CooccurrenceStore):
        self._store = store
        # 当前共现 validcount 缓存：increment 写入时顺手缓存（pair → new_count），
        # get_co_validcount 命中即返（刚写入的精确值，免再查库二次衰减）。
        # 生命周期=一个入库批次：flush 清空（跨批次时间跨度大，缓存值让位给库的衰减读）。
        self._vc_cache: dict[tuple[str, str], float] = {}

    @staticmethod
    def _pair_key(a: str, b: str) -> tuple[str, str]:
        """对称归一 key（与 store._pair_id 同序，保证 (a,b)==(b,a) 同缓存项）。"""
        return (a, b) if a <= b else (b, a)

    def increment(self, pairs: list[tuple[str, str]]) -> None:
        """批量共现 +1.0（当前 category 与缓冲内前 K 条 category 两两配对，概要 §4.1）。

        入库同时缓存当前共现 validcount（upsert 返回 new_count → _vc_cache），
        供紧随其后的 PMI.compute 取用精确值（免查库二次衰减）。

        Args:
            pairs: 两两配对的 category 列表 [(a, b), ...]。
        """
        for a, b in pairs:
            if a and b and a != b:              # 跳过空 category（概要 §4.4）+ 自对
                new_vc = self._store.upsert(a, b, delta=1.0)
                if new_vc is not None:
                    self._vc_cache[self._pair_key(a, b)] = new_vc

    def get_co_validcount(self, a: str, b: str) -> float:
        """取共对衰减后 count（PMI 用，概要 §3.1）。

        命中 _vc_cache 返缓存（最新鲜，刚 increment 写入）；否则查库（衰减读）。

        Args:
            a: category 之一。
            b: category 之二。

        Returns:
            衰减后 count；不存在返回 0.0。
        """
        key = self._pair_key(a, b)
        if key in self._vc_cache:
            return self._vc_cache[key]
        rec = self._store.get_pair(a, b)
        return rec.count if rec else 0.0

    def clear_validcount_cache(self) -> None:
        """清空 validcount 缓存（ClusterService.flush 调；跨批次让位给库的衰减读）。"""
        self._vc_cache.clear()

    def scan(self) -> list[CooccurrenceRecord]:
        return self._store.scan()

    def cleanup(self, threshold: float = 0.5) -> int:
        return self._store.cleanup(threshold)

"""category 共现表存储（sqlite 版，CL-11 优化：chromadb→sqlite）。

pair(category_a, category_b) → co_validcount + last_update，牛顿冷却衰减（bmcc_v2 范式）。
对称去重：pair_id = "|".join(sorted([a, b]))，保证 (a,b)==(b,a) 同记录。
不记自对 (c,c)（同 category 摘要边权在 MST 层处理，概要 §4.3）。

CL-11：存储后端由 chromadb 换 sqlite（纯 KV 错配 HNSW + 占位 embedding，从不向量检索），
对外四方法（upsert/get_pair/scan/cleanup）签名与 CooccurrenceRecord 结构不变，
CooccurrenceService / cluster buffer / pmi 零改。范式对齐 CL-09 DoneTracker。
"""
from __future__ import annotations
import time
import sqlite3
import threading
import logging
from pathlib import Path
from dataclasses import dataclass

from ..config import CoolingRate                       # 已交付 Enum
from ...forgetting.cooling import NewtonCooling

logger = logging.getLogger(__name__)


@dataclass
class CooccurrenceRecord:
    id: str                 # "min|max"
    category_a: str         # 字典序较小
    category_b: str         # 字典序较大
    count: float            # co_validcount（衰减后）
    last_updated: float     # unix 时间戳


class CooccurrenceStore:
    """category 共现表（sqlite，纯 KV 用法）。CL-11：chromadb→sqlite。

    对外四方法（upsert/get_pair/scan/cleanup）签名与语义与 chromadb 版逐一对齐。
    """

    def __init__(self, db_path: str, cooling_rate: CoolingRate = CoolingRate.DAYS_31):
        self._path = Path(db_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self._path), check_same_thread=False)
        self._lock = threading.Lock()
        self._cooling_rate = cooling_rate
        with self._conn:
            self._conn.execute(
                "CREATE TABLE IF NOT EXISTS cooccurrence ("
                "pair_id TEXT PRIMARY KEY, category_a TEXT, category_b TEXT, "
                "count REAL, last_updated REAL)"
            )

    @staticmethod
    def _pair_id(a: str, b: str) -> tuple[str, str, str]:
        """对称归一：返回 (id, min_cat, max_cat)。"""
        lo, hi = (a, b) if a <= b else (b, a)
        return f"{lo}|{hi}", lo, hi

    def _apply_decay(self, count: float, last_updated: float) -> float:
        """牛顿冷却：count × exp(-α × dt)（bmcc_v2 范式）。"""
        if not last_updated:
            return count
        return NewtonCooling.newton_cooling(count, time.time() - last_updated, self._cooling_rate)

    def upsert(self, category_a: str, category_b: str, delta: float = 1.0) -> float | None:
        """共现 +delta（先衰后 +delta，同 CL-02/03/04 upsert 范式）。

        Args:
            category_a: category 之一。
            category_b: category 之二。
            delta: 增量，默认 1.0。

        Returns:
            当前共现 validcount（new_count，衰减后）；自对 (a==b) 返回 None。供调用方缓存，
            使 PMI 紧随 increment 即取刚写入的精确值，免再查库二次衰减。入参签名不变（CL-11 四方法契约）。
        """
        if category_a == category_b:
            return None                         # 不记自对（概要 §2.2）
        pid, lo, hi = self._pair_id(category_a, category_b)
        now = time.time()
        with self._lock:
            cur = self._conn.execute(
                "SELECT count, last_updated FROM cooccurrence WHERE pair_id=?", (pid,)
            )
            row = cur.fetchone()
            new_count = delta if row is None else self._apply_decay(row[0], row[1]) + delta
            with self._conn:
                self._conn.execute(
                    "INSERT INTO cooccurrence(pair_id, category_a, category_b, count, last_updated) "
                    "VALUES(?, ?, ?, ?, ?) "
                    "ON CONFLICT(pair_id) DO UPDATE SET count=excluded.count, last_updated=excluded.last_updated",
                    (pid, lo, hi, new_count, now),
                )
        return new_count

    def get_pair(self, category_a: str, category_b: str) -> CooccurrenceRecord | None:
        """取对称对记录（衰减后 count）。

        Args:
            category_a: category 之一。
            category_b: category 之二。

        Returns:
            对称对记录（count 已衰减）；自对 (a==b) 或不存在返回 None。
        """
        if category_a == category_b:
            return None
        pid, lo, hi = self._pair_id(category_a, category_b)
        with self._lock:
            cur = self._conn.execute(
                "SELECT category_a, category_b, count, last_updated FROM cooccurrence WHERE pair_id=?",
                (pid,),
            )
            row = cur.fetchone()
        if row is None:
            return None
        return CooccurrenceRecord(
            id=pid, category_a=row[0], category_b=row[1],
            count=self._apply_decay(row[2], row[3]),
            last_updated=row[3],
        )

    def scan(self) -> list[CooccurrenceRecord]:
        """全表扫描（供 CL-07 cleanup + 调试）。

        Returns:
            全表记录列表（count 均已衰减）。
        """
        with self._lock:
            cur = self._conn.execute(
                "SELECT pair_id, category_a, category_b, count, last_updated FROM cooccurrence"
            )
            rows = cur.fetchall()
        return [CooccurrenceRecord(id=r[0], category_a=r[1], category_b=r[2],
                                   count=self._apply_decay(r[3], r[4]),
                                   last_updated=r[4])
                for r in rows]

    def cleanup(self, threshold: float = 0.5) -> int:
        """删除衰减低于 threshold 的共现对（供 CL-07 调度）。

        Args:
            threshold: 衰减后 count 低于此值则删除，默认 0.5。

        Returns:
            删除的共现对数量。
        """
        with self._lock:
            cur = self._conn.execute(
                "SELECT pair_id, count, last_updated FROM cooccurrence"
            )
            rows = cur.fetchall()
            ids_to_delete = [r[0] for r in rows
                             if self._apply_decay(r[1], r[2]) < threshold]
            if ids_to_delete:
                placeholders = ",".join("?" * len(ids_to_delete))
                with self._conn:
                    self._conn.execute(
                        f"DELETE FROM cooccurrence WHERE pair_id IN ({placeholders})",
                        ids_to_delete,
                    )
        return len(ids_to_delete)

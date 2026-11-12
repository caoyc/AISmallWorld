"""PMI 计算（原话 14-3）。单元=category 节点，marginal=category 自身 validcount（牛顿冷却折现）。
PMI(cat_a,cat_b) = log(co_vc) + log(N) - log(vc_a) - log(vc_b)（概要 §3.1）。

归属（CL PMI 回归）：PMI 的两输入——共现表（P(AB)）与 category 边际（P(A)/P(B)）——皆 category_system
资产，共现表本就是为 PMI 而生，故 PMI 类归此（原误落 cluster_system/cluster/pmi.py，其 import 全指
category_system 即为铁证）。构造收显式标量 log_N/cooling_rate（由 CategorySystemConfig 的 cooling_rate+
delta_t 推导，见 service/factory.build_category_system），不再寄生 cluster_system 的 ClusterConfig。
"""
from __future__ import annotations
import math
import time
import logging

from ..config import CoolingRate
from ..storage.cooccurrence_service import CooccurrenceService
from ..storage.category_store import CategoryStore        # query_by_path 取 validcount
from ...forgetting.cooling import NewtonCooling

logger = logging.getLogger(__name__)


class PMICalculator:
    def __init__(self, log_N: float, cooling_rate: CoolingRate,
                 cooccurrence: CooccurrenceService, category_store: CategoryStore):
        """装配 PMI 计算器（显式标量，解耦 ClusterConfig）。

        Args:
            log_N: PMI 归一化常数 log(N)（N=系统稳态记忆总数 = 1/(1-e^(-α·dt))；预算，不随对变化）。
            cooling_rate: 牛顿冷却档位（把存量 validcount 折现到当下，概要 §3.1 vc 来源）。
            cooccurrence: 共现表服务（取 P(AB) = co_vc）。
            category_store: 分类库（取 P(A)/P(B) 边际；与分类加热同一个库，根除两库漂移）。
        """
        self._log_N = log_N          # 预算（不随对变化）
        self._cooling_rate = cooling_rate
        self._cooc = cooccurrence
        self._cat_store = category_store

    def _category_validcount(self, category_path: str) -> float:
        """取 category 衰减后 validcount（牛顿冷却，概要 §3.1 vc 来源）。

        CategoryStore.query_by_path 返回 CategoryRecord（valid_count/last_update_time）。

        Args:
            category_path: 分类完整路径。

        Returns:
            衰减后的 valid_count；路径为空或不存在返回 0.0。
        """
        if not category_path:
            return 0.0
        records = self._cat_store.query_by_path(category_path)
        if not records:
            return 0.0
        rec = records[0]                     # 精确匹配首条
        return NewtonCooling.newton_cooling(rec.valid_count, time.time() - rec.last_update_time,
                                            self._cooling_rate)

    def compute(self, cat_a: str, cat_b: str) -> float:
        """算 category 对 PMI（概要 §3.1）。

        Args:
            cat_a: category 之一。
            cat_b: category 之二。

        Returns:
            PMI = log(co_vc) + log(N) - log(vc_a) - log(vc_b)；co_vc=0 或边际=0 时返回 -inf（不入边）。
        """
        co_vc = self._cooc.get_co_validcount(cat_a, cat_b)
        if co_vc <= 0.0:
            return float("-inf")             # 无共现，不入边
        vc_a = self._category_validcount(cat_a)
        vc_b = self._category_validcount(cat_b)
        if vc_a <= 0.0 or vc_b <= 0.0:
            return float("-inf")             # category 不存在/未加热
        return math.log(co_vc) + self._log_N - math.log(vc_a) - math.log(vc_b)

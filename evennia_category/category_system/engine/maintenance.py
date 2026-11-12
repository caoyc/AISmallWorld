"""后台维护服务。全量衰减 + 清理。对用户透明。"""

import logging
import time

from ..config import CategorySystemConfig, CoolingRate
from ..storage.category_store import CategoryStore
from ...forgetting.cooling import NewtonCooling

logger = logging.getLogger(__name__)


class MaintenanceService:
    """后台维护。全量衰减 + 清理。对用户透明。"""

    def __init__(self, store: CategoryStore, config: CategorySystemConfig):
        """初始化。

        Args:
            store: 分类存储
            config: 系统配置
        """
        self._store = store
        self._config = config
        self._cooling_rate = CoolingRate[config.cooling_rate]

    def decay_all(self) -> int:
        """全量衰减。返回衰减的记录数。

        Returns:
            衰减处理的记录数。
        """
        now = time.time()
        records = self._store.get_all_records()
        count = 0

        for record in records:
            decayed = NewtonCooling.newton_cooling(
                record.valid_count, now - record.last_update_time, self._cooling_rate
            )
            self._store.update_heat(record.id, decayed)
            count += 1

        return count

    def cleanup(self) -> int:
        """清理低于阈值的记录。返回清理的记录数。

        Returns:
            清理掉的记录数。
        """
        now = time.time()
        threshold = self._cooling_rate.final_ratio
        records = self._store.get_all_records()
        to_delete = []

        for record in records:
            decayed = NewtonCooling.newton_cooling(
                record.valid_count, now - record.last_update_time, self._cooling_rate
            )
            if decayed < threshold:
                to_delete.append(record.id)

        if to_delete:
            self._store.delete(to_delete)
            logger.info("清理了 %d 条冷记录（阈值=%.4f）", len(to_delete), threshold)

        return len(to_delete)

    def run_maintenance(self) -> tuple[int, int]:
        """执行一轮完整维护：衰减 → 清理。返回 (衰减数, 清理数)。

        衰减和清理分两轮遍历，不可合并为一轮。
        cleanup 依赖 decay_all 更新后的最新 valid_count。

        Returns:
            (衰减的记录数, 清理的记录数)
        """
        decayed_count = self.decay_all()
        deleted_count = self.cleanup()
        logger.info("维护完成：衰减 %d 条，清理 %d 条", decayed_count, deleted_count)
        return (decayed_count, deleted_count)

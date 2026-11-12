"""牛顿冷却遗忘算法层。
 
- CoolingRate（衰减档位枚举）
- NewtonCooling（牛顿冷却衰减静态方法）
"""
from __future__ import annotations

import math
import os
from enum import Enum

try:
    import tomllib  # 3.11+ 内置
except ModuleNotFoundError:
    import tomli as tomllib  # 3.10 fallback（tomli 2.2.1）


class CoolingRate(Enum):
    """冷却速率档位。

    每个档位存储 ``(final_ratio, interval_seconds)`` 二元组，``alpha`` 由二者自动计算：
    ``alpha = -ln(final_ratio) / interval_seconds``。

    Attributes:
        final_ratio (float): 经 interval_seconds 后 ValidCount 衰减到初始值的比例。
        interval_seconds (int): 衰减周期（秒）。
    """

    MINUTES_20 = (0.582, 20 * 60)
    HOURS_1 = (0.442, 1 * 60 * 60)
    HOURS_9 = (0.358, 9 * 60 * 60)
    DAYS_1 = (0.337, 86400)
    DAYS_2 = (0.278, 172800)
    DAYS_6 = (0.254, 518400)
    DAYS_31 = (0.211, 2678400)

    @property
    def final_ratio(self) -> float:
        """经一个周期后 ValidCount 衰减到初始值的比例。"""
        return self.value[0]

    @property
    def interval_seconds(self) -> int:
        """衰减周期（秒）。"""
        return self.value[1]

    def alpha(self) -> float:
        """衰减系数（1/秒）。

        公式：``alpha = -ln(final_ratio) / interval_seconds``。

        Returns:
            float: 衰减系数。
        """
        return -math.log(self.final_ratio) / self.interval_seconds


def _load_local() -> dict:
    """读本目录 config.toml（forgetting/ 包源头默认配置；加载代码与配置同目录）。"""
    cfg_path = os.path.join(os.path.dirname(__file__), "config.toml")
    if os.path.exists(cfg_path):
        with open(cfg_path, "rb") as f:  # tomllib 要二进制模式
            return tomllib.load(f)
    return {}


_LOCAL = _load_local()

#: 硬编码最终默认（config.toml 也缺失时的兜底）。
_HARD_DEFAULT: CoolingRate = CoolingRate.DAYS_31


def _resolve_cooling_rate(cooling_rate: CoolingRate | None) -> CoolingRate:
    """cooling_rate 三级解析（分层覆盖；见 memory config-layered-override-principle）。

    1. 参数非 None → 用参数（上层显式覆盖，最高优先）；
    2. 参数 None → 本目录 config.toml 的 ``cooling_rate``（包源头默认）；
    3. 配置也缺 → :data:`_HARD_DEFAULT`（DAYS_31）。
    """
    if cooling_rate is not None:
        return cooling_rate
    name = _LOCAL.get("cooling_rate")
    if name is not None:
        return CoolingRate[name]
    return _HARD_DEFAULT


class NewtonCooling:
    """牛顿冷却定律静态工具集。

    提供有效计数衰减、稳态总量两类纯函数计算，无实例状态。
    """

    @staticmethod
    def newton_cooling(valid_count: float, interval: float, cooling_rate: CoolingRate | None = None) -> float:
        """牛顿冷却定律计算衰减后的有效计数（按冷却档位 + 时间间隔）。

        入参为 ``CoolingRate``（自动推导 α）与时间间隔 ``interval``，
        适用于已知档位与固定间隔的场景。

        公式：``valid_count' = valid_count × e^(-α × interval)``，其中 ``α = cooling_rate.alpha()``。

        Args:
            valid_count (float): 当前有效计数（热度）。
            interval (float): 时间间隔（秒），即自上次更新以来经过的时长。
            cooling_rate (CoolingRate | None): 冷却速率档位，决定衰减系数 α。
                None 时三级回退：本包 config.toml → 硬默认 DAYS_31（见 :func:`_resolve_cooling_rate`）。

        Returns:
            float: 衰减后的有效计数。
        """
        cooling_rate = _resolve_cooling_rate(cooling_rate)
        if interval <= 0:
            return valid_count
        alpha = cooling_rate.alpha()
        return valid_count * math.exp(-alpha * interval)

    @staticmethod
    def steady_state_total(cooling_rate: CoolingRate | None = None, delta_t: float = 1.0 / 7) -> float:
        """计算系统记忆总量（稳态值）。

        以固定频率 delta_t 秒添加一条记忆，每条记忆按牛顿冷却衰减后，
        全系统所有记忆的 ValidCount 之和收敛到此稳态值。
        这是一个几何级数求和的结果，只取决于冷却速率和添加频率，
        是数学定值，不需要遍历全表逐条累计。

        应用场景：PMI 计算中的总记忆数 N，归一化等。

        公式：``N = 1 / (1 - e^(-α × delta_t))``。

        Args:
            cooling_rate (CoolingRate | None): 冷却速率档位。None 时三级回退
                （本包 config.toml → 硬默认 DAYS_31，见 :func:`_resolve_cooling_rate`）。
            delta_t (float): 连续两次记忆添加的时间间隔（秒），默认 1/7 秒。
                物理含义为人阅读文字的速度约每秒 7 个单元；采用此超参的目的是
                保持记忆和遗忘的速度与人类大脑量级相仿。DAYS_6 下稳态总数约
                265 万，DAYS_31 下约 1204 万。

        Returns:
            float: 系统稳态记忆总量。
        """
        cooling_rate = _resolve_cooling_rate(cooling_rate)
        alpha = cooling_rate.alpha()
        return 1.0 / (1.0 - math.exp(-alpha * delta_t))

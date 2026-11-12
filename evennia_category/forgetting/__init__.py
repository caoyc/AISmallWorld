"""bionic_agent_v4 公共遗忘算法层。

原样迁入自 bionic_agent_v2/forgetting/cooling.py（CL-15 去引用化）：
- cooling.CoolingRate（衰减档位枚举）
- cooling.NewtonCooling（牛顿冷却衰减静态方法）

保持版本间绝对独立（v3 自持副本，零 bionic_agent_v2 import）。
"""
from .cooling import CoolingRate, NewtonCooling

__all__ = ["CoolingRate", "NewtonCooling"]

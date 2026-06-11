"""
新鲜材料时间干燥脚本。

附属 fresh_grass / fresh_moss 对象，到达干燥时间后
自动替换为干燥材料（dry_grass / dry_moss）。

注意：prototype 的 exec 字段无法在 spawner 事务内持久化脚本，
因此改为 spawn 后手动调用 attach_drying_timer()。
"""
from evennia import DefaultScript, spawn

# ── 常量 ──────────────────────────────────────────
DRYING_TIME = 300  # 干燥时间（秒），5 分钟

# 干燥映射表
DRYING_MAP = {
    "fresh_grass": "dry_grass",
    "fresh_moss": "dry_moss",
}


class DryingTimer(DefaultScript):
    """新鲜材料干燥计时器。附属材料对象运行。"""

    key = "drying_timer"
    description = "材料干燥计时"

    def at_script_creation(self):
        """脚本创建时设定参数。"""
        self.interval = DRYING_TIME
        self.persistent = True
        self.repeats = 1  # 执行一次
        self.start_delay = True  # 等待 interval 后再触发，否则立即触发

    def at_repeat(self):
        """到达干燥时间，替换为干燥材料。"""
        obj = self.obj
        if not obj:
            return

        # 获取 prototype_key（通过 property 访问 tag）
        proto_key = obj.tags.get(category="from_prototype")

        # DR-01/DR-02：确定干燥目标
        target_key = DRYING_MAP.get(proto_key)
        if not target_key:
            # 无法确定干燥目标，静默停止
            return

        # 记录位置
        location = obj.location

        # spawn 干燥材料
        obj_list = spawn(target_key)
        if obj_list:
            dried = obj_list[0]
            # 放到同一位置
            if location:
                dried.move_to(location, quiet=True)
                # 如果在玩家背包中，发送通知
                if hasattr(location, 'has_account') and location.has_account:
                    location.msg(f"你的{obj.key}已经变干了，变成了{dried.key}。")

        # 删除原对象
        obj.delete()


def attach_drying_timer(obj):
    """给新鲜材料对象附加干燥计时器脚本。

    检查对象的 prototype_key，如果在 DRYING_MAP 中则添加脚本。
    安全调用：对非干燥对象无副作用。

    Args:
        obj: 刚 spawn 的对象。
    """
    proto_key = obj.tags.get(category="from_prototype")
    if proto_key in DRYING_MAP:
        obj.scripts.add(DryingTimer)

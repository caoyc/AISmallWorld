"""
帐篷对象级指令（sleep）

sleep 定义在帐篷对象上的对象级指令，参照 FishTrap（fish.py）模式。
rest 保持全局指令（不需要帐篷即可使用）。
"""
import time

from evennia import Command, CmdSet


# ── 对象级 CmdSet ──

class TentCmdSet(CmdSet):
    """帐篷对象级指令集。"""
    key = "tent_cmdset"
    priority = 0
    mergetype = "Union"

    def at_cmdset_creation(self):
        self.add(CmdSleep())


# ── 睡觉 ──

class CmdSleep(Command):
    """
    睡觉，持续恢复耐力

    用法：
      sleep

    在帐篷里躺下睡觉，持续恢复耐力。
    帐篷内有床时效率进一步提升。
    对象级指令，定义在帐篷对象上。
    """
    key = "sleep"
    help_category = "行动"
    locks = "cmd:all()"

    def func(self):
        caller = self.caller
        tent = self.obj
        room = caller.location

        if not room:
            caller.msg("你不在任何地方。")
            return

        if caller.db.resting:
            caller.msg("你已经在休息了。")
            return

        # ── 计算加成 ──
        bonus = tent.attributes.get("stamina_bonus", 0.0)
        has_bed = False
        for inner in tent.contents:
            inner_key = inner.tags.get(category="from_prototype")
            if inner_key == "leaf_bed":
                bonus += inner.attributes.get("stamina_bonus", 0.0)
                has_bed = True

        # ── 设置休息状态（与 CmdRest 共用属性格式） ──
        now = time.time()
        caller.db.resting = True
        caller.db.rest_start_time = now
        caller.db.rest_bonus = bonus
        caller.db.rest_last_settle = now

        # ── 提示消息 ──
        if has_bed:
            caller.msg("你躺在帐篷里的床上，进入深度休息。")
        else:
            caller.msg("你在帐篷里躺下休息，体力恢复得很快。")

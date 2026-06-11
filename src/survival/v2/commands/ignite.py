"""
篝火对象级指令（LC-01a 重构）

ignite/addfuel/extinguish 定义在篝火对象上的对象级指令，
参照 FishTrap（fish.py）的对象级 CmdSet 模式。
"""
from evennia import Command, CmdSet

from .burn_timer import INITIAL_BURN_DURATION, BurnTimer
from .addfuel import CmdAddfuel
from .extinguish import CmdExtinguish


# ── 对象级 CmdSet ──

class CampfireCmdSet(CmdSet):
    """篝火对象级指令集。"""
    key = "campfire_cmdset"
    priority = 0
    mergetype = "Union"

    def at_cmdset_creation(self):
        self.add(CmdIgnite())
        self.add(CmdAddfuel())
        self.add(CmdExtinguish())


# ── 点火 ──

class CmdIgnite(Command):
    """
    对未点燃的篝火进行点火。

    用法：
        ignite

    需要手钻（工具）和火绒（干草/干苔藓，消耗）。
    对象级指令，定义在篝火对象上。
    """
    key = "ignite"
    help_category = "行动"
    locks = "cmd:all()"

    def func(self):
        caller = self.caller
        fire = self.obj
        room = caller.location
        if not room:
            caller.msg("你不在任何地方。")
            return

        # ── 1. 检查篝火状态 ───────────────────────────
        fire_state = fire.db.fire_state
        if fire_state == "burning":
            caller.msg("篝火已经在燃烧了。")
            return
        if fire_state == "burnt_out":
            # 营火（persistent）可从 burnt_out 重新点燃
            if not fire.attributes.get("persistent"):
                caller.msg("篝火已经熄灭了，无法再次点燃。")
                return
        elif fire_state == "extinguished":
            caller.msg("篝火已经熄灭了，无法再次点燃。")
            return
        elif fire_state != "unlit":
            caller.msg("篝火当前无法点燃。")
            return

        # ── 2. 检查手钻 ──────────────────────────────
        hand_drill = None
        for obj in caller.contents:
            if obj.attributes.get("tool_type") == "fire_starting":
                hand_drill = obj
                break
        if not hand_drill:
            caller.msg("你需要一个手钻来点火。")
            return

        # ── 3. 检查火绒 ──────────────────────────────
        tinder = None
        for obj in caller.contents:
            if obj.attributes.get("tinder"):
                tinder = obj
                break
        if not tinder:
            caller.msg("你需要火绒（干草或干苔藓）来点火。")
            return

        # ── 4. 执行点火 ──────────────────────────────
        tinder_name = tinder.key
        tinder.delete()

        fire.db.fire_state = "burning"
        # 保留已添加的燃料时间，叠加初始燃烧时长
        fire.db.burn_duration = min(
            fire.db.burn_duration + INITIAL_BURN_DURATION,
            fire.db.max_burn_duration
        )

        # 更新描述
        if fire_state == "burnt_out":
            desc = fire.db.desc_burning or "石圈内的火焰重新跳动起来。"
        else:
            desc = fire.db.desc_burning or "一堆燃烧的篝火，火焰跳动着。"
        fire.db.desc_look = desc

        # 启动燃烧计时器
        fire.scripts.add(BurnTimer)

        caller.msg(f"你用{tinder_name}点燃了篝火。")
        room.msg_contents(
            f"{caller.key}用{tinder_name}点燃了篝火。",
            exclude=caller
        )

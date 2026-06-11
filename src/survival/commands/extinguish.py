"""
灭火指令。将燃烧中的篝火熄灭。

对象级指令，定义在篝火对象上。
普通篝火：主动灭火等同燃尽（销毁+草木灰）。
营火（persistent）：灭火转为 burnt_out 状态，不销毁。
"""
from evennia import Command, spawn

from .burn_timer import extinguish_cleanup, WOOD_ASH_COUNT_PERSISTENT


class CmdExtinguish(Command):
    """
    将燃烧中的篝火熄灭。

    用法：
        extinguish

    对象级指令，定义在篝火对象上。
    """
    key = "extinguish"
    help_category = "行动"
    locks = "cmd:all()"

    def func(self):
        caller = self.caller
        fire = self.obj
        room = caller.location
        if not room:
            caller.msg("你不在任何地方。")
            return

        # ── 1. 检查篝火状态 ──────────────────────────
        if fire.db.fire_state != "burning":
            caller.msg("篝火未在燃烧。")
            return

        # ── 2. 停止燃烧计时器 ────────────────────────
        for script in fire.scripts.all():
            if script.key == "burn_timer":
                script.stop()
                break

        # ── 3. 执行灭火 ──────────────────────────────
        if fire.attributes.get("persistent"):
            # 营火：转为 burnt_out 状态，生成草木灰×8，不销毁
            caller.msg("你熄灭了营火。")
            room.msg_contents(
                f"{caller.key}熄灭了营火，只剩下灰烬。",
                exclude=caller
            )
            for obj in list(fire.contents):
                obj.move_to(room, quiet=True)
            for _ in range(WOOD_ASH_COUNT_PERSISTENT):
                ash_list = spawn("wood_ash")
                if ash_list:
                    ash_list[0].move_to(room, quiet=True)
            fire.db.fire_state = "burnt_out"
            fire.db.burn_duration = 0
            fire.db.desc_look = fire.db.desc_burnt_out or "一堆灰烬残留在石块围成的火塘中。"
            fire.db.desc_smell = fire.db.desc_smell_burnt_out or fire.db.desc_smell_extinguished
        else:
            # 普通篝火：销毁+草木灰
            caller.msg("你熄灭了篝火。")
            extinguish_cleanup(fire, reason=f"{caller.key}熄灭了篝火，只剩下灰烬。")

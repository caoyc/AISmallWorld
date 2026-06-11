"""
添柴指令。向篝火添加可燃物。

允许在未点燃（unlit）和燃烧中（burning）两种状态下添柴。
对象级指令，定义在篝火对象上。
"""
from evennia import Command

from .burn_timer import FUEL_TIME_PER_VALUE


class CmdAddfuel(Command):
    """
    向燃烧中的篝火添加可燃物。

    用法：
        addfuel <燃料名>

    可燃物：树枝、木棍、长木棍、原木、竹枝、长竹棍。
    火绒（干草/干苔藓）不能作为燃料。
    对象级指令，定义在篝火对象上。
    """
    key = "addfuel"
    help_category = "行动"
    locks = "cmd:all()"

    def func(self):
        caller = self.caller
        fire = self.obj
        room = caller.location
        if not room:
            caller.msg("你不在任何地方。")
            return

        # ── 1. 检查参数 ──────────────────────────────
        args = self.args.strip() if self.args else ""
        if not args:
            caller.msg("请指定要添加的燃料。用法：addfuel <燃料名>")
            return

        # ── 2. 检查篝火状态 ──────────────────────────
        fire_state = fire.db.fire_state
        if fire_state == "burnt_out":
            # 营火（persistent）可向 burnt_out 添柴
            if not fire.attributes.get("persistent"):
                caller.msg("篝火已经熄灭，无法添加燃料。")
                return
        elif fire_state not in ("unlit", "burning"):
            caller.msg("篝火已经熄灭，无法添加燃料。")
            return

        # ── 3. 查找指定燃料（从背包）──────────────────
        fuel = caller.search(args)
        if not fuel:
            return

        # ── 4. 验证燃料 ──────────────────────────────
        fuel_value = fuel.attributes.get("fuel_value")
        if fuel_value is None:
            caller.msg(f"{fuel.key}不能作为燃料。")
            return

        if fuel.attributes.get("tinder"):
            caller.msg("火绒不能作为燃料，请使用树枝、木棍等可燃物。")
            return

        # ── 5. 检查燃烧时间上限 ──────────────────────
        if fire.db.burn_duration >= fire.db.max_burn_duration:
            caller.msg("篝火燃烧时间已满，不需要添加燃料。")
            return

        # ── 6. 执行添柴 ──────────────────────────────
        fuel_name = fuel.key
        additional = fuel_value * FUEL_TIME_PER_VALUE
        fire.db.burn_duration = min(
            fire.db.burn_duration + additional,
            fire.db.max_burn_duration
        )
        fuel.delete()

        caller.msg(f"你向篝火中添加了{fuel_name}，燃烧时间增加了。")
        room.msg_contents(
            f"{caller.key}向篝火中添加了{fuel_name}。",
            exclude=caller
        )

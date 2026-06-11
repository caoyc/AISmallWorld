"""
进食指令

详见：docs/设计文档/解决饥饿/详细设计/指令系统详细设计.md
"""

from evennia.commands.command import Command

from .resources import FoodItem


def _find_eat_target(caller, target):
    """搜索可吃目标（FoodItem），搜房间 + 背包。"""
    room = caller.location
    candidates = (
        [obj for obj in room.contents if isinstance(obj, FoodItem)]
        + [obj for obj in caller.contents if isinstance(obj, FoodItem)]
    )
    if not target:
        return candidates
    return [obj for obj in candidates if target in obj.key]


class CmdEat(Command):
    """吃食物物品。

    key = "eat"
    aliases = ["吃", "ea"]

    无参数时取第一个可吃物品，有参数时按名称查找。
    搜索范围：房间 + 背包。
    """

    key = "eat"
    aliases = ["吃", "ea"]
    locks = "cmd:all()"

    def func(self):
        caller = self.caller
        target = self.args.strip() if self.args else ""

        items = _find_eat_target(caller, target)
        if not items:
            caller.msg("附近没有可以吃的东西。")
            return

        item = items[0]

        if not item.db.can_eat or item.db.hunger_restore <= 0:
            caller.msg(f"{item.key}已经不能吃了。")
            return

        hunger = item.db.hunger_restore
        caller.restore_hunger(hunger)

        food_desc = item.db.food_desc or item.key
        caller.msg(f"你吃了{item.key}。{food_desc}饥饿感缓解了一些。")

        item.db.can_eat = False
        item.db.hunger_restore = 0
        item.db.times_used += 1

        if item.is_fully_consumed():
            caller.msg(f"{item.key}已经吃完了。")
            item.delete()

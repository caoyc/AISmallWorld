"""
饮水指令

详见：docs/设计文档/解决饥饿/详细设计/指令系统详细设计.md
"""

from evennia.commands.command import Command

from .resources import FoodItem, WaterSource, find_water_sources


def _find_drink_target(caller, target):
    """搜索可喝目标（WaterSource 或可喝 FoodItem），优先房间再背包。"""
    room = caller.location

    if not target:
        # 无参数：房间内水源
        return find_water_sources(room) or []

    # 有参数：先搜房间 WaterSource
    for obj in room.contents:
        if isinstance(obj, WaterSource) and target in obj.key:
            return [obj]

    # 搜房间 + 背包中的 FoodItem
    candidates = (
        [obj for obj in room.contents if isinstance(obj, FoodItem)]
        + [obj for obj in caller.contents if isinstance(obj, FoodItem)]
    )
    return [obj for obj in candidates if target in obj.key]


class CmdDrink(Command):
    """喝水。

    key = "drink"
    aliases = ["喝", "dr"]

    无参数时查找房间内水源，有参数时按名称查找水源或可喝物品。
    搜索范围：房间 + 背包。
    """

    key = "drink"
    aliases = ["喝", "dr"]
    locks = "cmd:all()"

    def func(self):
        caller = self.caller
        target = self.args.strip() if self.args else ""

        results = _find_drink_target(caller, target)
        if not results:
            caller.msg("没有可以喝的东西。" if target else "附近没有水源。")
            return

        obj = results[0]

        if isinstance(obj, WaterSource):
            water_type = obj.db.water_type
            if water_type == "fresh":
                caller.restore_thirst(30)
                caller.msg("你俯身喝了一些清凉的淡水，甘甜的滋味让精神为之一振。")
            else:
                caller.increase_thirst(20)
                caller.msg("你喝了一口咸涩的海水，喉咙反而更加干渴了。")
            return

        # FoodItem
        if not obj.db.can_drink or obj.db.thirst_restore <= 0:
            caller.msg(f"{obj.key}不能喝。")
            return

        caller.restore_thirst(obj.db.thirst_restore)
        caller.msg(f"你喝了{obj.key}，解了些渴。")

        obj.db.can_drink = False
        obj.db.thirst_restore = 0
        obj.db.times_used += 1

        if obj.is_fully_consumed():
            caller.msg(f"{obj.key}已经没有了。")
            obj.delete()

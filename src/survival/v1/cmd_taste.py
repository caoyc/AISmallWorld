"""
品尝指令

详见：docs/设计文档/五感系统/详细设计/感官指令详细设计.md
"""

from evennia.commands.command import Command

from .resources import FoodItem, WaterSource
from .rooms import SurvivalRoom
from .sense_utils import _find_sense_target


class CmdTaste(Command):
    """安全地品尝水源或食物，不扣除任何属性值。

    key = "taste"
    aliases = ["尝", "ta"]

    无参数时尝当前房间，有参数时按名称查找。
    搜索范围：房间 + 背包。
    """

    key = "taste"
    aliases = ["尝", "ta"]
    locks = "cmd:all()"

    def func(self):
        caller = self.caller
        target = self.args.strip() if self.args else ""

        results = _find_sense_target(caller, target)
        if not results:
            caller.msg("这里没有什么可以尝的。")
            return

        obj = results[0]

        if isinstance(obj, WaterSource):
            if obj.db.water_type == "fresh":
                caller.msg("你用手指蘸了点水放在舌尖——清甜甘冽，是淡水。")
            else:
                caller.msg("你用手指蘸了点水放在舌尖——咸涩苦腥，是咸水。")
        elif isinstance(obj, FoodItem):
            desc = obj.db.desc_taste
            if desc:
                caller.msg(f"你小心翼翼地尝了一点{obj.key}——{desc}")
            else:
                caller.msg(f"你小心翼翼地尝了一点{obj.key}——看起来可以食用。")
        elif isinstance(obj, SurvivalRoom):
            caller.msg(obj.get_sense_description("taste"))
        else:
            desc = obj.db.desc_taste
            if desc:
                caller.msg(desc)
            else:
                caller.msg("你尝了尝，没有什么特别的味道。")

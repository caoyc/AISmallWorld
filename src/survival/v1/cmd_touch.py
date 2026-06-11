"""
触摸指令
"""

from evennia.commands.command import Command

from .rooms import SurvivalRoom
from .sense_utils import _find_sense_target


class CmdTouch(Command):
    """触摸周围的东西。

    key = "touch"
    aliases = ["摸", "to"]

    无参数时触摸当前环境，有参数时触摸指定对象。
    """

    key = "touch"
    aliases = ["摸", "to"]
    locks = "cmd:all()"

    def func(self):
        caller = self.caller
        target = self.args.strip() if self.args else ""

        targets = _find_sense_target(caller, target)
        if not targets:
            caller.msg("这里没有什么可以触摸的东西。")
            return

        obj = targets[0]

        if isinstance(obj, SurvivalRoom):
            caller.msg(obj.get_sense_description("touch"))
        else:
            desc = obj.db.desc_touch or "你摸了摸，没有什么特别的触感。"
            caller.msg(desc)
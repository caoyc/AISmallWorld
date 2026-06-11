"""
闻嗅指令
"""

from evennia.commands.command import Command

from .rooms import SurvivalRoom
from .sense_utils import _find_sense_target


class CmdSmell(Command):
    """闻一闻周围的气味。

    key = "smell"
    aliases = ["闻", "sm"]

    无参数时闻当前房间，有参数时闻指定对象。
    """

    key = "smell"
    aliases = ["闻", "sm"]
    locks = "cmd:all()"

    def func(self):
        caller = self.caller
        target = self.args.strip() if self.args else ""

        targets = _find_sense_target(caller, target)
        if not targets:
            caller.msg("这里没有什么可以闻的东西。")
            return

        obj = targets[0]

        if isinstance(obj, SurvivalRoom):
            caller.msg(obj.get_sense_description("smell"))
        else:
            desc = obj.db.desc_smell or "你仔细闻了闻，没有发现什么特别的气味。"
            caller.msg(desc)
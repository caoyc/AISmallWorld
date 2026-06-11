"""
聆听指令
"""

from evennia.commands.command import Command

from .rooms import SurvivalRoom
from .sense_utils import _find_sense_target


class CmdListen(Command):
    """聆听周围的声音。

    key = "listen"
    aliases = ["听", "li"]

    无参数时聆听当前房间，有参数时聆听指定对象。
    """

    key = "listen"
    aliases = ["听", "li"]
    locks = "cmd:all()"

    def func(self):
        caller = self.caller
        target = self.args.strip() if self.args else ""

        targets = _find_sense_target(caller, target)
        if not targets:
            caller.msg("这里没有什么可以听的东西。")
            return

        obj = targets[0]

        if isinstance(obj, SurvivalRoom):
            caller.msg(obj.get_sense_description("listen"))
        else:
            desc = obj.db.desc_listen or "你仔细听了听，没有发现什么特别的声音。"
            caller.msg(desc)
"""
状态查看指令

详见：docs/设计文档/解决饥饿/详细设计/指令系统详细设计.md
"""

from evennia.commands.command import Command


class CmdStatus(Command):
    """查看当前饥渴状态。

    key = "status"
    aliases = ["状态", "st"]
    locks = "cmd:all()"

    无参数，无条件限制。
    """

    key = "status"
    aliases = ["状态", "st"]
    locks = "cmd:all()"

    def func(self):
        """输出角色当前状态。"""
        self.caller.msg(self.caller.get_status_display())

"""
生存指令集

独立 CmdSet，与 Evennia 默认指令集合并使用。
角色通过 at_object_creation 挂载此指令集。

详见：docs/设计文档/五感系统/详细设计/感官指令详细设计.md
"""

from evennia.commands.cmdset import CmdSet

from .cmd_drink import CmdDrink
from .cmd_eat import CmdEat
from .cmd_listen import CmdListen
from .cmd_notebook import CmdNotebook
from .cmd_search import CmdSearch
from .cmd_smell import CmdSmell
from .cmd_status import CmdStatus
from .cmd_taste import CmdTaste
from .cmd_touch import CmdTouch


class SurvivalCmdSet(CmdSet):
    """生存指令集，添加生存相关指令。

    作为独立 CmdSet 与 Evennia 默认角色指令集合并。
    角色 at_object_creation 时通过 cmdset.add 挂载。

    key = "survival"
    priority = 1
    """

    key = "survival"
    priority = 1

    def at_cmdset_creation(self):
        """注册所有生存指令。"""
        self.add(CmdStatus())
        self.add(CmdSearch())
        self.add(CmdTaste())
        self.add(CmdDrink())
        self.add(CmdEat())
        self.add(CmdNotebook())
        self.add(CmdListen())
        self.add(CmdSmell())
        self.add(CmdTouch())

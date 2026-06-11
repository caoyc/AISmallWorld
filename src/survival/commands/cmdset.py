"""
v2 生存指令集 — SurvivalV2CmdSet

priority=2（高于 v1 的 priority=1），覆盖 v1 指令集。
所有自定义指令只设 key，不设 aliases。

详见：docs/设计文档/解决饥渴_v2/详细设计/指令实现.md
详见：docs/设计文档/热带环礁岛基础生存闭环/详细设计/v1/基础生存闭环详细设计.md
"""

from evennia.commands.cmdset import CmdSet

from .help import CmdHelp
from .search import CmdSearch
from .eat import CmdEat
from .drink import CmdDrink
from .senses import CmdLook, CmdSmell, CmdListen, CmdTouch, CmdTaste
from .status import CmdStatus
from .rest import CmdRest
from .move import CmdMove
from .get import CmdGet
from .drop import CmdDrop
from .follow import CmdFollow
from .cut import CmdCut
from .make import CmdMake
from .cancel import CmdCancel
from .research import CmdResearch
from .chop import CmdChop
from .build import CmdBuild
from .fill import CmdFill
from .empty import CmdEmpty
from .cook import CmdCook
from .map import CmdMap
from .inventory import CmdInventory
from .recipes import CmdRecipes
from .repair import CmdRepair


class SurvivalV2CmdSet(CmdSet):
    """v2 生存指令集，priority=2（高于 v1）。"""

    key = "survival_v2"
    priority = 2

    def at_cmdset_creation(self):
        """注册所有 v2 指令。help 覆写 Evennia 内置。"""
        self.add(CmdHelp())
        self.add(CmdSearch())
        self.add(CmdEat())
        self.add(CmdDrink())
        self.add(CmdLook())
        self.add(CmdSmell())
        self.add(CmdListen())
        self.add(CmdTouch())
        self.add(CmdTaste())
        self.add(CmdStatus())
        self.add(CmdRest())
        self.add(CmdMove())
        self.add(CmdGet())
        self.add(CmdDrop())
        self.add(CmdFollow())
        self.add(CmdCut())
        self.add(CmdMake())
        self.add(CmdCancel())
        self.add(CmdResearch())
        # 基础生存闭环新增
        self.add(CmdChop())
        self.add(CmdBuild())
        self.add(CmdFill())
        self.add(CmdEmpty())
        self.add(CmdCook())
        self.add(CmdMap())
        self.add(CmdInventory())
        self.add(CmdRecipes())
        self.add(CmdRepair())

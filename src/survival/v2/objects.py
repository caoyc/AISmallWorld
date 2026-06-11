"""
v2 对象 Typeclass — Organism / NonLiving

typeclass 按 prototype 分类层级映射：
- organism 及所有后代 → Organism
- non_living 及所有后代 → NonLiving

覆写 get_display_desc 返回 v2 的 desc_look 描述内容。
玩法信息（配方、耐久等）由专门指令查看，不在描述中泄露。

详见：docs/设计文档/解决饥渴_v2/详细设计/typeclass实现.md
详见：docs/设计文档/石刃业务闭环/详细设计/指令修改.md § objects.py
"""

from evennia.objects.objects import DefaultObject


# 延迟导入，避免循环引用
def _get_fish_trap_cmdset():
    from .commands.fish import FishTrapCmdSet
    return FishTrapCmdSet


def _get_campfire_cmdset():
    from .commands.ignite import CampfireCmdSet
    return CampfireCmdSet


def _get_tent_cmdset():
    from .commands.sleep import TentCmdSet
    return TentCmdSet


class NonLiving(DefaultObject):
    """非生物基类。

    覆写 get_display_desc 返回 v2 的 desc_look 描述内容。
    行为由 prototype 属性驱动。
    """

    def get_display_desc(self, looker, **kwargs):
        """返回 desc_look 描述文本。

        Args:
            looker: 查看者。
            **kwargs: 透传参数。

        Returns:
            str: 描述文本。
        """
        return self.db.desc_look or super().get_display_desc(looker, **kwargs)


class Organism(DefaultObject):
    """生物基类。

    覆写 get_display_desc 返回 v2 的 desc_look 描述内容。
    行为由 prototype 属性驱动。

    多重继承的部件 prototype（如 coconut）同时继承物种链和部件链，
    Evennia 自动合并属性，右侧覆盖左侧同名属性。
    """

    def get_display_desc(self, looker, **kwargs):
        """返回 desc_look 描述文本。

        Args:
            looker: 查看者。
            **kwargs: 透传参数。

        Returns:
            str: 描述文本。
        """
        return self.db.desc_look or super().get_display_desc(looker, **kwargs)


class FishTrap(NonLiving):
    """捕鱼笼对象，持有 settrap/collect 对象级指令。"""

    def at_object_creation(self):
        super().at_object_creation()
        FishTrapCmdSet = _get_fish_trap_cmdset()
        self.cmdset.add(FishTrapCmdSet, persistent=True)


class Campfire(NonLiving):
    """篝火对象，持有 ignite/addfuel/extinguish 对象级指令。"""

    def at_object_creation(self):
        super().at_object_creation()
        CampfireCmdSet = _get_campfire_cmdset()
        self.cmdset.add(CampfireCmdSet, persistent=True)


class Tent(NonLiving):
    """帐篷对象，持有 sleep 对象级指令。"""

    def at_object_creation(self):
        super().at_object_creation()
        TentCmdSet = _get_tent_cmdset()
        self.cmdset.add(TentCmdSet, persistent=True)


class CoconutTree(Organism):
    """椰子树对象。

    椰子定时掉落脚本由 build_island.py spawn 后手动挂载，
    不在此处 at_object_creation 中自动挂载。
    参照 drying_timer 的鲁棒模式。
    """

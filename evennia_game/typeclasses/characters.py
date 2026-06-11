"""
Characters

Characters are (by default) Objects setup to be puppeted by Accounts.
They are what you "see" in game.

默认角色使用 survival.characters.SurvivalCharacterV2，
此文件保留兼容层，如需覆盖可在此处修改。

"""

from survival.characters import SurvivalCharacterV2


class Character(SurvivalCharacterV2):
    """
    游戏默认角色类型。

    继承自 SurvivalCharacterV2，包含饥渴系统、耐力系统和生存指令集。
    如需添加额外的角色行为，可在此处覆盖。
    """

    pass

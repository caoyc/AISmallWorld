"""
v2 生存指令基类 — SurvivalCommand

mixin 耐力检查和扣减。所有 v2 生存指令继承此类。

详见：docs/设计文档/解决饥渴_v2/详细设计/指令实现.md
"""

from evennia.commands.command import Command


class SurvivalCommand(Command):
    """v2 生存指令基类。mixin 耐力检查和扣减。

    Attributes:
        stamina_cost (int): 正数=恢复，负数=消耗，0=不影响。子类覆写。
    """

    stamina_cost = 0
    rest_interrupt = True  # 是否打断休息状态。查询类指令覆写为 False

    def pre_check(self):
        """前置检查：休息打断结算 + 耐力是否足够。

        Returns:
            bool: True 继续，False 中止。
        """
        caller = self.caller
        # 休息打断：rest_interrupt=True 的指令结算恢复值并打断休息
        if caller.attributes.get("resting") and self.rest_interrupt:
            caller._settle_recovery()
            caller.db.resting = False
            caller.db.rest_start_time = None
            caller.db.rest_bonus = 0.0
            caller.db.rest_last_settle = None
            caller.msg("你结束了休息。")
            # 澄清3：结算完成后提示一次当前耐力状态
            stamina = caller.db.stamina
            label = caller._get_stamina_label()
            caller.msg(f"你的耐力：{stamina} [{label}]")
        # 耐力检查（只有消耗型需要）
        if self.stamina_cost < 0 and caller.db.stamina < abs(self.stamina_cost):
            caller.msg("你太累了，没有力气做这件事。")
            return False
        return True

    def apply_stamina(self):
        """应用耐力变化，钳制 0~100。"""
        if self.stamina_cost != 0:
            caller = self.caller
            caller.db.stamina = max(
                0, min(100, caller.db.stamina + self.stamina_cost)
            )

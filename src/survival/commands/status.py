"""
v2 status 指令 — 显示角色状态（含耐力）

详见：docs/设计文档/解决饥渴_v2/详细设计/指令实现.md
"""

from .base import SurvivalCommand


class CmdStatus(SurvivalCommand):
    """
    查看角色状态

    用法：
      status

    显示饥饿、口渴、耐力三项状态值。
    """

    key = "status"
    help_category = "生存"
    stamina_cost = 0
    rest_interrupt = False

    def func(self):
        """显示饥饿、口渴、耐力三属性。"""
        if not self.pre_check():
            return

        caller = self.caller
        # 澄清1：status 查看时结算恢复值并重置计时，不打断休息
        if caller.db.resting:
            caller._settle_recovery()
        # SurvivalCharacterV2 有 get_status_display
        if hasattr(caller, "get_status_display"):
            caller.msg(caller.get_status_display())
        else:
            # 回退到 v1 显示
            caller.msg(
                f"--- 状态 ---\n"
                f"饥饿: {caller.db.hunger}\n"
                f"口渴: {caller.db.thirst}"
            )

"""
v2 move 指令 — 移动覆写，添加耐力消耗

覆写 Evennia 默认移动指令，在移动前检查耐力，移动后扣减。
移动时自动解除休息状态。

详见：docs/设计文档/解决饥渴_v2/详细设计/指令实现.md
详见：docs/设计文档/热带环礁岛基础生存闭环/详细设计/v6/LC-03a/LC-03a详细设计.md
"""

from evennia.commands.default.general import CmdLook as DefaultCmdLook

from .base import SurvivalCommand


class CmdMove(SurvivalCommand):
    """
    移动到其他地点

    用法：
      move <方向>

    向指定方向移动，消耗耐力。
    """

    key = "move"
    help_category = "行动"
    stamina_cost = -1

    def func(self):
        """移动前检查耐力，移动后扣减。

        流程：
            mermaid:
            TD
                A[pre_check] --> B{耐力足够?}
                B -->|否| C[提示]
                B -->|是| D[调用 Evennia 内置移动]
                D --> E[apply_stamina]
        """
        if not self.pre_check():
            return

        # 委托给 Evennia 内置移动逻辑
        # 使用 caller.search 查找出口，然后触发移动
        if not self.args:
            self.caller.msg("你要去哪里？")
            return

        # 查找出口
        results = self.caller.search(self.args.strip(), location=self.caller.location,
                                     quiet=True, exact=True)
        if not results:
            self.caller.msg("那个方向走不通。")
            return
        target = results[0]

        # AC-11：auto-action 期间移动限制
        if self.caller.db.auto_action:
            action_type = self.caller.db.auto_action_type or "操作"
            action_verb = "切割" if action_type == "cut" else "砍伐" if action_type == "chop" else "操作"
            self.caller.msg(f"你正在{action_verb}，无法移动。")
            return

        # 执行移动
        # 主动移动时取消跟随（主动移动意味着放弃跟随）
        if self.caller.db.following:
            old_target = self.caller.db.following
            if old_target.db.followers and self.caller in old_target.db.followers:
                old_target.db.followers.remove(self.caller)
            self.caller.db.following = None

        self.caller.move_to(target)
        self.apply_stamina()

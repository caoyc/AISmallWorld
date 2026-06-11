"""
v2 cancel 指令 — 终止制作/操作

终止当前制作或自动连续操作（cut/chop），按 destroy_chance 消耗材料，无产出。
cancel 与制造失败同一套损毁机制。

详见：docs/设计文档/石刃业务闭环/详细设计/make指令.md
详见：docs/设计文档/热带环礁岛基础生存闭环/详细设计/v6/LC-03a/LC-03a详细设计.md
"""

from .base import SurvivalCommand
from .recipe_utils import consume_materials_cancel
from .auto_action import cancel_auto_action


class CmdCancel(SurvivalCommand):
    """
    终止当前制作（材料按概率损毁）

    用法：
      cancel

    取消正在进行的配方制作，材料按概率损毁。
    """

    key = "cancel"
    help_category = "制作"
    stamina_cost = 0

    def func(self):
        """执行取消。

        流程：
            mermaid:
            TD
                A{auto_action?} -->|是| B[cancel_auto_action]
                A -->|否| C{busy?}
                C -->|否| D[没有正在进行的操作]
                C -->|是| E[清除 task_id]
                E --> F[按 destroy_chance 消耗材料]
                F --> G[清除制作数据]
                G --> H[提示终止]
        """
        caller = self.caller

        # 优先检查 auto-action（cut/chop 自动连续执行）
        if caller.db.auto_action:
            cancel_auto_action(caller)
            return

        if not caller.db.busy:
            caller.msg("你没有正在进行的操作。")
            return

        # 清除 task_id，使 delay 链自然中断
        caller.db.craft_task_id = None
        caller.db.busy = False

        # cancel 时按同一套 destroy_chance 消耗材料
        materials = caller.db.craft_materials or []
        consume_materials_cancel(caller, materials)

        # 清除暂存的制作数据
        caller.db.craft_recipe = None
        caller.db.craft_materials = None
        caller.db.craft_output = None
        caller.db.craft_byproduct = None
        caller.db.craft_build_location = None
        caller.db.craft_env_obj = None
        caller.db.craft_environment = None

        caller.msg("你终止了当前操作。")

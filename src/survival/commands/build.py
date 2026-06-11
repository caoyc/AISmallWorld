"""
v2 build 指令 — 建造设施

prototype 驱动的建造指令，配方查找、检查、消耗、产出统一走 recipe_utils 公共方法。
建造配方 recipe_type="build"，产出位置 build_location="room"。
支持延迟建造（D5-4）、制作中禁止移动（D5-2）、条件变更视为取消（D5-3）。

用法：build <配方名称>

详见：docs/设计文档/配方修正/详细设计/v2/MF-02/MF-02详细设计.md
"""

import uuid

from evennia.utils import delay

from .base import SurvivalCommand
from .recipe_utils import (
    autocomplete_recipe_name,
    find_recipe,
    check_environment,
    check_requires,
    consume_environment,
    create_output,
    check_materials,
    consume_materials_full,
    consume_materials_cancel,
    find_tool_by_type,
)

DELAY_PER_MSG = 1  # 每条过程消息间隔（秒）


class CmdBuild(SurvivalCommand):
    """
    建造设施

    用法：
      build               — 列出可建造的配方
      build <配方名称>    — 按配方建造设施

    配方名称可省略"配方"后缀，程序自动补全。
    在当前房间建造设施。消耗材料，设施出现在房间中。
    """

    key = "build"
    help_category = "行动"
    stamina_cost = -2

    def func(self):
        """执行建造。

        流程：
            mermaid:
            TD
                A[pre_check: busy?] --> B{busy?}
                B -->|是| C[你正在忙]
                B -->|否| D{有参数?}
                D -->|否| E[可建造配方列表]
                D -->|是| F[自动补全+查找配方]
                F --> G{找到?}
                G -->|否| H[未找到配方]
                G -->|是| I{recipe_type=build?}
                I -->|否| J[不是建造配方]
                I -->|是| K[lock 检查]
                K --> L{access use?}
                L -->|否| M[条件不满足]
                L -->|是| N[环境检查]
                N --> O{通过?}
                O -->|否| P[环境不满足]
                O -->|是| Q[前置条件检查]
                Q --> R{通过?}
                R -->|否| S[前置不满足]
                R -->|是| T[材料检查]
                T --> U{材料齐全?}
                U -->|否| V[缺少材料]
                U -->|是| W[设置 busy + 展开消息]
                W --> X[delay → _send_next_msg]
        """
        caller = self.caller

        if not self.pre_check():
            return

        # 检查 busy（D5-2）
        if caller.db.busy:
            caller.msg("你正在忙，无法执行其他操作。")
            return

        # 参数解析
        args = self.args.strip() if self.args else ""
        if not args:
            # 显示可建造的配方列表
            self._list_build_recipes(caller)
            return

        # 自动补全"配方"后缀
        recipe_name = autocomplete_recipe_name(args)

        # 查找配方
        recipe = find_recipe(caller, recipe_name)
        if not recipe:
            caller.msg(f"你没有找到'{recipe_name}'。")
            self.apply_stamina()
            return

        # 验证配方类型
        recipe_type = recipe.attributes.get("recipe_type")
        if recipe_type != "build":
            if recipe_type == "make":
                caller.msg("该配方是制作配方，请使用 make 指令。")
            elif recipe_type == "cook":
                caller.msg("该配方是烹饪配方，请使用 cook 指令。")
            else:
                caller.msg("该配方不是建造配方。")
            self.apply_stamina()
            return

        # 权限检查
        if not recipe.access(caller, "use"):
            caller.msg("你不具备使用这个配方的条件。")
            self.apply_stamina()
            return

        # 读取配方属性
        materials = recipe.attributes.get("materials", [])
        output_key = recipe.attributes.get("output")
        build_location = recipe.attributes.get("build_location", "room")
        build_container = recipe.attributes.get("build_container")
        environment = recipe.attributes.get("environment")
        requires = recipe.attributes.get("requires", [])
        process_descs = recipe.attributes.get("process_descs", [])

        # 环境检查
        env_passed, env_msg, env_obj = check_environment(caller, environment)
        if not env_passed:
            caller.msg(env_msg)
            self.apply_stamina()
            return

        # 前置条件检查
        req_passed, req_msg = check_requires(caller, requires)
        if not req_passed:
            caller.msg(req_msg)
            self.apply_stamina()
            return

        # 材料检查
        if not check_materials(caller, materials):
            self.apply_stamina()
            return

        # ── 展开过程消息（支持嵌套 group）──
        msgs = []
        for entry in process_descs:
            if "group" in entry:
                group = entry["group"]
                group_repeat = entry.get("repeat", 1)
                for _ in range(group_repeat):
                    for sub in group:
                        desc = sub.get("desc", "")
                        sub_repeat = sub.get("repeat", 1)
                        for _ in range(sub_repeat):
                            if desc:
                                msgs.append(desc)
            else:
                desc = entry.get("desc", "")
                repeat = entry.get("repeat", 1)
                for _ in range(repeat):
                    if desc:
                        msgs.append(desc)

        # ── 设置 busy 状态 + 保存制作数据（D5-2）──
        task_id = str(uuid.uuid4())
        caller.db.busy = True
        caller.db.craft_task_id = task_id
        caller.db.craft_recipe = recipe
        caller.db.craft_materials = materials
        caller.db.craft_output = output_key
        caller.db.craft_build_location = build_location
        caller.db.craft_build_container = build_container
        caller.db.craft_env_obj = env_obj
        caller.db.craft_environment = environment
        caller.db.craft_requires = requires  # D5-3：保存 requires 用于延迟期间检查

        # ── 启动延迟链（D5-4：统一走 delay，无论 msgs 是否为空）──
        if msgs:
            caller.msg(msgs[0])
            if len(msgs) > 1:
                delay(DELAY_PER_MSG, self._send_next_msg, caller, msgs, 1, task_id)
            else:
                delay(DELAY_PER_MSG, self._complete_craft_delayed, caller, task_id)
        else:
            # 无过程消息：仍走 delay 流程，立即完成（D5-4）
            delay(DELAY_PER_MSG, self._complete_craft_delayed, caller, task_id)

        self.apply_stamina()

    @staticmethod
    def _send_next_msg(caller, msgs, index, task_id):
        """延迟发送下一条过程消息，发送前检查 requires 条件（D5-3）。

        每次发送消息前检查前置条件（如 room_has:tent），条件不满足则视为取消。

        Args:
            caller: 玩家角色。
            msgs: 过程消息列表。
            index: 当前消息索引。
            task_id: 制作任务 ID（cancel 时清除）。
        """
        # 检查是否被 cancel
        if caller.db.craft_task_id != task_id:
            return

        # D5-3：检查 requires 条件是否仍满足
        requires = caller.db.craft_requires
        if requires:
            req_passed, req_msg = check_requires(caller, requires)
            if not req_passed:
                # 条件不满足 → 视为取消
                caller.db.busy = False
                caller.db.craft_task_id = None
                materials = caller.db.craft_materials or []
                consume_materials_cancel(caller, materials)
                # 清除制作数据
                caller.db.craft_recipe = None
                caller.db.craft_materials = None
                caller.db.craft_output = None
                caller.db.craft_build_location = None
                caller.db.craft_env_obj = None
                caller.db.craft_environment = None
                caller.db.craft_requires = None
                caller.msg("建造条件已不满足，建造失败。")
                return

        if index >= len(msgs):
            # 消息发送完毕，延迟后完成建造
            delay(DELAY_PER_MSG, CmdBuild._complete_craft_delayed, caller, task_id)
            return

        caller.msg(msgs[index])
        delay(DELAY_PER_MSG, CmdBuild._send_next_msg, caller, msgs, index + 1, task_id)

    @staticmethod
    def _complete_craft_delayed(caller, task_id):
        """延迟完成建造（delay 链末端回调）。

        Args:
            caller: 玩家角色。
            task_id: 制作任务 ID。
        """
        if caller.db.craft_task_id != task_id:
            return  # 已 cancel

        recipe = caller.db.craft_recipe
        materials = caller.db.craft_materials
        output_key = caller.db.craft_output
        build_location = caller.db.craft_build_location
        build_container = caller.db.craft_build_container
        env_obj = caller.db.craft_env_obj
        environment = caller.db.craft_environment

        # 清除制作状态
        caller.db.busy = False
        caller.db.craft_task_id = None
        caller.db.craft_recipe = None
        caller.db.craft_materials = None
        caller.db.craft_output = None
        caller.db.craft_build_location = None
        caller.db.craft_build_container = None
        caller.db.craft_env_obj = None
        caller.db.craft_environment = None
        caller.db.craft_requires = None

        CmdBuild._complete_craft(caller, recipe, materials, output_key,
                                 build_location, build_container, env_obj, environment)

    @staticmethod
    def _complete_craft(caller, recipe, materials, output_key,
                        build_location, build_container, env_obj, environment):
        """完成建造：消耗材料 + 创建产出 + 扣减环境。

        正常完成时原料全部销毁，不走 destroy_chance 概率。

        Args:
            caller: 玩家角色。
            recipe: 配方对象。
            materials: 材料列表。
            output_key: 产出 prototype 标识。
            build_location: 产出位置。
            build_container: 产出容器 prototype 标识（如 "tent"）。
            env_obj: 环境对象（如篝火）。
            environment: 环境依赖字典。
        """
        # 消耗材料（正常完成，全部销毁）
        consume_materials_full(caller, materials)

        # 创建产出物
        if build_container and build_location == "container":
            # 放入指定容器（如树叶床→帐篷）
            room = caller.location
            container_obj = None
            for obj in room.contents:
                if obj.tags.get(category="from_prototype") == build_container:
                    container_obj = obj
                    break
            if container_obj:
                create_output(caller, output_key, "container", source_containers={"container": container_obj})
            else:
                create_output(caller, output_key, "room")
        else:
            create_output(caller, output_key, build_location)

        # 扣减环境资源
        consume_environment(env_obj, environment)

        # 提示
        from .recipe_utils import _proto_display_name
        output_label = _proto_display_name(output_key) if output_key else "设施"
        caller.msg(f"建造完成！{output_label}已出现在当前房间。")

    @staticmethod
    def _list_build_recipes(caller):
        """显示当前可建造的配方列表（从收藏夹中列出）。

        Args:
            caller: 玩家对象。
        """
        from .recipe_utils import get_or_create_recipe_book

        book = get_or_create_recipe_book(caller)
        if not book:
            caller.msg("你没有可建造的配方。")
            return

        build_recipes = [obj.key for obj in book.contents
                         if obj.attributes.get("recipe_type") == "build"]

        if build_recipes:
            names = "、".join(build_recipes)
            caller.msg(f"可建造设施：{names}\n用法：\n  look <配方名称>：查看配方详情\n  build <配方名称>：建造设施")
        else:
            caller.msg("你没有可建造的配方。")

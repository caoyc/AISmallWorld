"""
v2 make 指令 — 配方制作

执行配方制作，支持延迟过程消息和 busy 状态。
正常完成时原料全部销毁，工具按设定掉耐久。
cancel/失败时按 destroy_chance 概率损毁材料。

新增能力：
  - alternatives 可替换材料组（任选一种满足即可）
  - craft_tool 制作工具检查（不消耗）
  - output_overrides 材料到产出属性的映射（如石刃根据燧石/黑曜石获得不同属性）
  - build_location 产出位置驱动（inventory/room/container）

用法：make <配方名称>

详见：docs/设计文档/配方修正/详细设计/v1/详细设计.md
"""

import uuid

from evennia.prototypes.spawner import spawn
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


def _expand_process_descs(process_descs):
    """展开过程消息列表，支持嵌套 group 穿插格式。

    简单条目：{"desc": "...", "repeat": N}
    嵌套条目：{"group": [子条目列表], "repeat": M}
      → 将子条目序列重复 M 次，实现穿插效果。

    示例：
        [
            {"desc": "选址", "repeat": 1},
            {"group": [
                {"desc": "铺设叶片", "repeat": 3},
                {"desc": "藤条固定", "repeat": 1},
            ], "repeat": 4},
            {"desc": "完成", "repeat": 1},
        ]
        → 选址, 铺设×3, 固定×1, 铺设×3, 固定×1, ... ×4, 完成

    Args:
        process_descs: 过程消息列表。

    Returns:
        list: 展开后的消息字符串列表。
    """
    msgs = []
    for entry in process_descs:
        if "group" in entry:
            # 嵌套组：将子条目序列重复 N 次
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
            # 简单条目
            desc = entry.get("desc", "")
            repeat = entry.get("repeat", 1)
            for _ in range(repeat):
                if desc:
                    msgs.append(desc)
    return msgs


class CmdMake(SurvivalCommand):
    """
    按配方制作物品

    用法：
      make                — 列出可制作的配方
      make <配方名称>     — 按配方制作物品

    配方名称可省略"配方"后缀，程序自动补全。
    制作过程中处于 busy 状态，可用 cancel 终止。
    """

    key = "make"
    help_category = "制作"
    stamina_cost = -1

    def func(self):
        """执行配方制作。

        流程：
            mermaid:
            TD
                A[pre_check: busy?] --> B{busy?}
                B -->|是| C[你正在忙]
                B -->|否| D[解析参数+自动补全]
                D --> E[查找配方(房间→对象→背包)]
                E --> F{找到?}
                F -->|否| G[你没有这个配方]
                F -->|是| H[配方 lock 检查]
                H --> I{access use?}
                I -->|否| J[条件不满足]
                I -->|是| K[环境检查]
                K --> L{通过?}
                L -->|否| M[环境不满足]
                L -->|是| N[前置条件检查]
                N --> O{通过?}
                O -->|否| P[前置不满足]
                O -->|是| Q[craft_tool 检查]
                Q --> R{craft_tool 满足?}
                R -->|否| S[缺少制作工具]
                R -->|是| T[检查 materials(含 alternatives)]
                T --> U{材料齐全?}
                U -->|否| V[缺少材料]
                U -->|是| W[设置 busy + task_id]
                W --> X[展开 process_descs]
                X --> Y[delay → _send_next_msg]
        """
        caller = self.caller

        if not self.pre_check():
            return

        # 检查 busy
        if caller.db.busy:
            caller.msg("你正在忙，无法执行其他操作。")
            return

        # 参数解析
        args = self.args.strip() if self.args else ""
        if not args:
            self._list_make_recipes(caller)
            return

        # 自动补全"配方"后缀
        recipe_name = autocomplete_recipe_name(args)

        # 查找配方（房间→房间中对象→玩家背包）
        recipe = find_recipe(caller, recipe_name)
        if not recipe:
            caller.msg(f"你没有找到'{recipe_name}'。")
            self.apply_stamina()
            return

        # 配方 lock 检查
        if not recipe.access(caller, "use"):
            caller.msg("你不具备使用这个配方的条件。")
            self.apply_stamina()
            return

        # 验证配方类型
        recipe_type = recipe.attributes.get("recipe_type")
        if recipe_type and recipe_type != "make":
            if recipe_type == "build":
                caller.msg("该配方是建造配方，请使用 build 指令。")
            elif recipe_type == "cook":
                caller.msg("该配方是烹饪配方，请使用 cook 指令。")
            else:
                caller.msg(f"该配方类型为{recipe_type}，不适用于制作。")
            self.apply_stamina()
            return

        # 读取配方属性
        materials = recipe.attributes.get("materials", [])
        process_descs = recipe.attributes.get("process_descs", [])
        output_key = recipe.attributes.get("output")
        byproduct_key = recipe.attributes.get("byproduct")
        craft_tool_type = recipe.attributes.get("craft_tool")
        build_location = recipe.attributes.get("build_location", "inventory")
        environment = recipe.attributes.get("environment")
        requires = recipe.attributes.get("requires", [])

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

        # craft_tool 检查（不消耗工具）
        if craft_tool_type:
            tool = find_tool_by_type(caller, craft_tool_type)
            if not tool:
                caller.msg(f"你需要一件 {craft_tool_type} 类工具才能制作。")
                self.apply_stamina()
                return

        # 材料检查（含 alternatives 支持）
        if not check_materials(caller, materials):
            self.apply_stamina()
            return

        # 展开过程消息（支持嵌套 group 穿插格式）
        msgs = _expand_process_descs(process_descs)

        # ── 设置 busy 状态 + 保存制作数据（D5-2）──
        task_id = str(uuid.uuid4())
        caller.db.busy = True
        caller.db.craft_task_id = task_id
        caller.db.craft_recipe = recipe
        caller.db.craft_materials = materials
        caller.db.craft_output = output_key
        caller.db.craft_byproduct = byproduct_key
        caller.db.craft_build_location = build_location
        caller.db.craft_env_obj = env_obj
        caller.db.craft_environment = environment

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
    def _list_make_recipes(caller):
        """显示当前可制作的配方列表（从收藏夹中列出）。

        Args:
            caller: 玩家对象。
        """
        from .recipe_utils import get_or_create_recipe_book

        book = get_or_create_recipe_book(caller)
        if not book:
            caller.msg("你没有可制作的配方。")
            return

        make_recipes = [obj.key for obj in book.contents
                        if obj.attributes.get("recipe_type") == "make"]

        if make_recipes:
            names = "、".join(make_recipes)
            caller.msg(f"可制作物品：{names}\n用法：\n  look <配方名称>：查看配方详情\n  make <配方名称>：制作物品")
        else:
            caller.msg("你没有可制作的配方。")

    @staticmethod
    def _send_next_msg(caller, msgs, index, task_id):
        """延迟发送下一条过程消息。

        Args:
            caller: 玩家角色。
            msgs: 过程消息列表。
            index: 当前消息索引。
            task_id: 制作任务 ID（cancel 时清除）。
        """
        # 检查是否被 cancel
        if caller.db.craft_task_id != task_id:
            return

        if index >= len(msgs):
            # 消息发送完毕，延迟后完成制作
            delay(DELAY_PER_MSG, CmdMake._complete_craft_delayed, caller, task_id)
            return

        caller.msg(msgs[index])
        delay(DELAY_PER_MSG, CmdMake._send_next_msg, caller, msgs, index + 1, task_id)

    @staticmethod
    def _complete_craft(caller, recipe, materials, output_key, byproduct_key,
                        build_location, env_obj, environment):
        """即时完成制作（无过程消息时使用）。

        正常完成时原料全部销毁，不走 destroy_chance 概率。
        支持 alternatives 可替换组和 output_overrides 属性映射。

        Args:
            caller: 玩家角色。
            recipe: 配方对象。
            materials: 材料列表。
            output_key: 产出 prototype_key。
            byproduct_key: 副产品 prototype_key。
            build_location: 产出位置。
            env_obj: 环境对象（如篝火）。
            environment: 环境依赖字典。
        """
        # 记录每种 alternatives 组中实际消耗了哪种材料（用于 output_overrides）
        result = consume_materials_full(caller, materials)
        consumed_keys = result["consumed_keys"]

        # spawn 产出
        output_obj = None
        if output_key:
            objs = spawn(output_key)
            if objs:
                output_obj = objs[0]
                if build_location == "room":
                    output_obj.move_to(caller.location, quiet=True)
                else:
                    output_obj.move_to(caller, quiet=True)

                # output_overrides：根据消耗的材料设置产出属性
                output_overrides = recipe.attributes.get("output_overrides", [])
                if output_overrides and consumed_keys:
                    for override in output_overrides:
                        mat_key = override.get("material")
                        if mat_key in consumed_keys:
                            for attr_name, attr_value in override.items():
                                if attr_name == "material":
                                    continue
                                if attr_name == "key":
                                    output_obj.key = attr_value
                                elif attr_name == "desc_look":
                                    output_obj.db.desc_look = attr_value
                                else:
                                    output_obj.attributes.add(attr_name, attr_value)
                            break  # 匹配到第一个 override 后退出
            else:
                caller.msg(f"制作失败：无法创建 {output_key}。")

        if byproduct_key:
            objs = spawn(byproduct_key)
            if objs:
                objs[0].move_to(caller, quiet=True)

        # 扣减环境资源
        consume_environment(env_obj, environment)

        # 提示
        from .recipe_utils import _proto_display_name
        output_label = output_obj.key if output_obj else _proto_display_name(output_key) if output_key else "成品"
        byproduct_label = f" + {_proto_display_name(byproduct_key)}" if byproduct_key else ""
        caller.msg(f"制作完成！你获得了 {output_label}{byproduct_label}。")

    @staticmethod
    def _complete_craft_delayed(caller, task_id):
        """延迟完成制作（delay 链末端回调）。

        Args:
            caller: 玩家角色。
            task_id: 制作任务 ID。
        """
        if caller.db.craft_task_id != task_id:
            return  # 已 cancel

        recipe = caller.db.craft_recipe
        materials = caller.db.craft_materials
        output_key = caller.db.craft_output
        byproduct_key = caller.db.craft_byproduct
        build_location = caller.db.craft_build_location
        env_obj = caller.db.craft_env_obj
        environment = caller.db.craft_environment

        # 清除制作状态
        caller.db.busy = False
        caller.db.craft_task_id = None
        caller.db.craft_recipe = None
        caller.db.craft_materials = None
        caller.db.craft_output = None
        caller.db.craft_byproduct = None
        caller.db.craft_build_location = None
        caller.db.craft_env_obj = None
        caller.db.craft_environment = None

        CmdMake._complete_craft(caller, recipe, materials, output_key, byproduct_key,
                                build_location, env_obj, environment)

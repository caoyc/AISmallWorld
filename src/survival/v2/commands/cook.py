"""
v2 cook 指令 — 烹饪全局指令

映射表驱动：cook <菜肴名称>，通过 cook_recipe_map 映射表将菜肴名
解析为配方模板和具体食材。

支持延迟烹饪（D5-4）、制作中禁止移动（D5-2）、环境条件变更视为取消（D5-3）。
支持 in_container 材料（容器内容物作为材料）和 vessel_content 产出。

用法：cook <菜肴名称>

详见：docs/设计文档/热带环礁岛基础生存闭环/详细设计/v5/LC-01d/LC-01d详细设计.md
"""

import uuid

from evennia.prototypes.spawner import spawn
from evennia.utils import delay

from .base import SurvivalCommand
from .recipe_utils import (
    resolve_cook_dish,
    get_cook_map,
    get_or_create_recipe_book,
    check_environment,
    check_requires,
    consume_environment,
    create_output,
    check_materials,
    consume_materials_full,
    consume_materials_cancel,
    find_tool_by_type,
)

# 配方分支：延迟链每条消息间隔（秒）
DELAY_PER_MSG = 1

# 水产 prototype_key 集合（用于材料缩窄时识别水产组）
_AQUATIC_KEYS = {
    "mudskipper", "mangrove_shrimp", "mud_crab", "mangrove_clam", "sea_slug",
    "grouper", "spiny_lobster", "reef_crab", "oyster", "sea_snail",
    "tilapia", "river_shrimp", "stream_crab", "freshwater_mussel", "pond_snail",
}


def _narrow_materials(materials, aquatic_key):
    """将模板配方的材料列表缩窄到指定水产。

    遍历 materials，找到包含水产的 alternatives 组，
    将其替换为仅包含指定水产的单项材料。
    非水产材料（签子、盐、椰壳等）保持不变。

    Args:
        materials: 原始材料列表。
        aquatic_key: 指定水产的 prototype_key，None 时不缩窄。

    Returns:
        list: 缩窄后的材料列表。
    """
    if not aquatic_key or not materials:
        return materials

    narrowed = []
    for entry in materials:
        if "alternatives" in entry:
            alts = entry["alternatives"]
            has_aquatic = any(alt.get("prototype") in _AQUATIC_KEYS for alt in alts)
            if has_aquatic:
                narrowed.append({"prototype": aquatic_key, "count": 1, "destroy_chance": 0})
            else:
                narrowed.append(entry)
        else:
            proto = entry.get("prototype", "")
            if proto in _AQUATIC_KEYS:
                narrowed.append({"prototype": aquatic_key, "count": 1, "destroy_chance": 0})
            else:
                narrowed.append(entry)

    return narrowed


class CmdCook(SurvivalCommand):
    """
    烹饪

    用法：
      cook                — 列出可烹饪的配方和菜肴
      cook <菜肴名称>     — 烹饪（如：烤龙虾、鲜美的烤龙虾、烤肉）

    需要房间内有燃烧中的篝火。
    """

    key = "cook"
    help_category = "行动"
    stamina_cost = -1

    def func(self):
        """执行烹饪。

        流程：
            mermaid:
            TD
                A[pre_check] --> B{有参数?}
                B -->|否| C[列出可烹饪配方+菜肴]
                B -->|是| D[映射表查找菜肴名]
                D --> E{找到?}
                E -->|否| F[未知菜肴]
                E -->|是| G[收藏夹查找配方对象]
                G --> H{有配方?}
                H -->|否| I[没有该配方]
                H -->|是| J[缩窄材料+lock+busy+环境+前置+材料+工具检查]
                J --> K{全部通过?}
                K -->|否| L[对应错误提示]
                K -->|是| M[预查找源容器+设置busy+启动delay链]
        """
        if not self.pre_check():
            return

        caller = self.caller
        args = self.args.strip() if self.args else ""

        if not args:
            self._list_cook_recipes(caller)
            return

        # ── 映射表查找菜肴名 ──
        recipe, aquatic_key = resolve_cook_dish(caller, args)

        if not recipe:
            caller.msg(f"你不知道怎么制作'{args}'。")
            self.apply_stamina()
            return

        # 验证配方类型
        recipe_type = recipe.attributes.get("recipe_type")
        if recipe_type != "cook":
            if recipe_type == "make":
                caller.msg("该配方是制作配方，请使用 make 指令。")
            elif recipe_type == "build":
                caller.msg("该配方是建造配方，请使用 build 指令。")
            else:
                caller.msg("该配方不是烹饪配方。")
            self.apply_stamina()
            return

        # 权限检查
        if not recipe.access(caller, "use"):
            caller.msg("你不具备使用这个配方的条件。")
            self.apply_stamina()
            return

        # 忙碌检查（D5-2）
        if caller.db.busy:
            caller.msg("你正在忙，无法执行其他操作。")
            return

        # 读取配方属性 + 缩窄材料
        template_materials = recipe.attributes.get("materials", [])
        materials = _narrow_materials(template_materials, aquatic_key)
        output_key = recipe.attributes.get("output")
        build_location = recipe.attributes.get("build_location", "inventory")
        environment = recipe.attributes.get("environment")
        requires = recipe.attributes.get("requires", [])
        craft_tool_type = recipe.attributes.get("craft_tool")
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

        # 预查找 in_container 材料的源容器
        source_containers = {}
        for entry in (materials or []):
            entries = entry.get("alternatives", [entry]) if "alternatives" in entry else [entry]
            for mat in entries:
                if mat.get("in_container"):
                    proto_key = mat.get("prototype")
                    container_proto = mat.get("container_prototype")
                    for obj in caller.contents:
                        if obj.attributes.get("is_container"):
                            if obj.attributes.get("vessel_content") == proto_key:
                                if container_proto:
                                    p = obj.tags.get(category="from_prototype")
                                    if p != container_proto:
                                        continue
                                source_containers[proto_key] = obj
                                break

        # 工具检查
        if craft_tool_type:
            tool = find_tool_by_type(caller, craft_tool_type)
            if not tool:
                caller.msg(f"你需要{craft_tool_type}类工具。")
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
        caller.db.craft_env_obj = env_obj
        caller.db.craft_environment = environment
        caller.db.craft_requires = requires  # D5-3：保存 requires
        caller.db.craft_source_containers = source_containers if source_containers else None

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
    def _list_cook_recipes(caller):
        """显示当前可烹饪的配方列表和菜肴列表。

        Args:
            caller: 玩家对象。
        """
        book = get_or_create_recipe_book(caller)
        if not book:
            caller.msg("你没有可烹饪的配方。")
            return

        cook_recipes = [obj for obj in book.contents
                        if obj.attributes.get("recipe_type") == "cook"]

        if not cook_recipes:
            caller.msg("你没有可烹饪的配方。")
            return

        # 列出配方名
        recipe_names = "、".join(obj.key for obj in cook_recipes)

        # 列出可烹饪的菜肴名（只列当前拥有配方的菜肴）
        cook_map = get_cook_map()
        owned_recipe_keys = {obj.tags.get(category="from_prototype") for obj in cook_recipes}
        available_dishes = sorted(
            name for name, entry in cook_map.items()
            if entry["recipe"] in owned_recipe_keys
        )
        dishes_str = "、".join(available_dishes) if available_dishes else "无"

        caller.msg(
            f"可烹饪配方：{recipe_names}\n"
            f"可烹饪菜肴：{dishes_str}\n"
            f"用法：\n"
            f"  look <配方名称>：查看配方详情\n"
            f"  cook <菜肴名称>：烹饪食物"
        )

    # ── 配方分支延迟链方法 ──

    @staticmethod
    def _send_next_msg(caller, msgs, index, task_id):
        """延迟发送下一条过程消息，发送前检查 environment 和 requires 条件（D5-3）。

        cook 独有：environment（篝火燃烧状态）可能因 burn_duration 耗尽而变化。
        每次发送消息前同时检查 environment 和 requires，任一不满足则视为取消。

        取消/条件变更时不扣减篝火燃烧值（consume_environment 不调用）。

        Args:
            caller: 玩家角色。
            msgs: 过程消息列表。
            index: 当前消息索引。
            task_id: 制作任务 ID（cancel 时清除）。
        """
        # 检查是否被 cancel
        if caller.db.craft_task_id != task_id:
            return

        # D5-3：检查 environment 条件是否仍满足（篝火是否仍燃烧）
        environment = caller.db.craft_environment
        if environment:
            env_passed, env_msg, _ = check_environment(caller, environment)
            if not env_passed:
                # 环境不满足（篝火熄灭等）→ 视为取消
                CmdCook._cancel_craft(caller, materials=caller.db.craft_materials or [])
                caller.msg("篝火熄灭了，烹饪失败。")
                return

        # D5-3：检查 requires 条件是否仍满足
        requires = caller.db.craft_requires
        if requires:
            req_passed, req_msg = check_requires(caller, requires)
            if not req_passed:
                # 条件不满足 → 视为取消
                CmdCook._cancel_craft(caller, materials=caller.db.craft_materials or [])
                caller.msg("烹饪条件已不满足，烹饪失败。")
                return

        if index >= len(msgs):
            # 消息发送完毕，延迟后完成烹饪
            delay(DELAY_PER_MSG, CmdCook._complete_craft_delayed, caller, task_id)
            return

        caller.msg(msgs[index])
        delay(DELAY_PER_MSG, CmdCook._send_next_msg, caller, msgs, index + 1, task_id)

    @staticmethod
    def _cancel_craft(caller, materials):
        """取消制作：清理 busy 状态 + 清除制作数据 + 按概率损毁材料。

        Args:
            caller: 玩家角色。
            materials: 材料需求列表。
        """
        caller.db.busy = False
        caller.db.craft_task_id = None
        consume_materials_cancel(caller, materials)
        for attr in ("craft_recipe", "craft_materials", "craft_output",
                     "craft_build_location", "craft_env_obj", "craft_environment",
                     "craft_requires", "craft_source_containers"):
            caller.attributes.remove(attr)

    @staticmethod
    def _complete_craft_delayed(caller, task_id):
        """延迟完成烹饪（delay 链末端回调）。

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
        env_obj = caller.db.craft_env_obj
        environment = caller.db.craft_environment
        source_containers = caller.db.craft_source_containers

        # 清除制作状态
        caller.db.busy = False
        caller.db.craft_task_id = None
        for attr in ("craft_recipe", "craft_materials", "craft_output",
                     "craft_build_location", "craft_env_obj", "craft_environment",
                     "craft_requires", "craft_source_containers"):
            caller.attributes.remove(attr)

        CmdCook._complete_craft(caller, recipe, materials, output_key,
                                build_location, env_obj, environment,
                                source_containers=source_containers)

    @staticmethod
    def _complete_craft(caller, recipe, materials, output_key,
                        build_location, env_obj, environment,
                        source_containers=None):
        """完成烹饪：消耗材料 + 创建产出 + 扣减环境。"""
        # 消耗材料
        result = consume_materials_full(caller, materials, recipe=recipe)
        # 如果配方有 in_container 材料，使用实际消耗返回的 source_containers
        actual_sources = result.get("source_containers", {})
        if not source_containers:
            source_containers = actual_sources

        # 获取被消耗的水产 prototype_key（动态配方用）
        consumed_aquatic_key = result.get("consumed_aquatic_key")

        # 创建产出物
        output_obj = None
        if output_key:
            if build_location == "vessel_content":
                create_output(caller, output_key, build_location, source_containers=source_containers)
            else:
                # 检测动态产出
                dynamic_output = recipe.attributes.get("dynamic_output", False) if recipe else False
                if dynamic_output and consumed_aquatic_key:
                    output_obj = _create_dynamic_output(
                        output_key, consumed_aquatic_key, recipe
                    )
                else:
                    objs = spawn(output_key)
                    output_obj = objs[0] if objs else None

                if output_obj:
                    if env_obj:
                        output_obj.move_to(env_obj, quiet=True)
                    else:
                        output_obj.move_to(caller, quiet=True)

        # 扣减环境资源
        consume_environment(env_obj, environment)

        # 提示（动态产出物显示实际名称，普通产出用中文名）
        dynamic_output = recipe.attributes.get("dynamic_output", False) if recipe else False
        if dynamic_output and output_obj:
            caller.msg(f"烹饪完成！你获得了 {output_obj.key}。")
        elif output_obj:
            caller.msg(f"烹饪完成！你获得了 {output_obj.key}。")
        else:
            from .recipe_utils import _proto_display_name
            label = _proto_display_name(output_key) if output_key else "成品"
            caller.msg(f"烹饪完成！你获得了 {label}。")

    @staticmethod
    def _find_burning_fire(caller):
        """查找房间内燃烧中的篝火。

        Args:
            caller: 玩家角色。

        Returns:
            篝火对象或 None。
        """
        room = caller.location
        if not room:
            return None
        for obj in room.contents:
            if obj.attributes.get("fire_state") == "burning":
                return obj
        return None


def _create_dynamic_output(output_base, aquatic_key, recipe):
    """创建动态产出物：基于 output_base prototype，覆盖 key/desc_look。

    Args:
        output_base: 产出物基础 prototype_key
        aquatic_key: 被消耗的水产 prototype_key
        recipe: 配方对象

    Returns:
        产出物对象，或 None
    """
    from evennia.prototypes.prototypes import search_prototype

    # 查找水产的 dishes_name
    aquatic_protos = search_prototype(key=aquatic_key)
    dishes_name = aquatic_key  # fallback
    if aquatic_protos:
        for attr_tuple in aquatic_protos[0].get("attrs", []):
            if attr_tuple[0] == "dishes_name":
                dishes_name = attr_tuple[1]
                break

    # 按 output_template 生成产出物名称
    output_template = recipe.attributes.get("output_template", "")
    output_name = output_template.format(dishes_name=dishes_name)

    # spawn 产出物（基于 output_base）
    objs = spawn(output_base)
    if not objs:
        return None

    output_obj = objs[0]
    output_obj.key = output_name
    # 更新描述以体现具体水产
    output_obj.db.desc_look = f"{output_name}，散发着诱人的香气。"

    return output_obj

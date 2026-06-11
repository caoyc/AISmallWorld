"""
v2 配方类指令公共方法

被 make.py、build.py、cook.py 共同调用的配方查找、检查、消耗、产出方法。
从 make.py 和 build.py 抽取的共享逻辑，统一配方类指令族的执行流程。

详见：docs/设计文档/配方修正/详细设计/v1/详细设计.md
"""

import random

from evennia.prototypes.spawner import spawn


# ── 配方名自动补全 ──


def autocomplete_recipe_name(name):
    """配方名自动补全：若名称不以'配方'结尾，追加'配方'后缀。

    Args:
        name: 玩家输入的配方名称

    Returns:
        str: 补全后的配方名称
    """
    if name.endswith("配方"):
        return name
    return name + "配方"


# ── 配方收藏夹 ──


def get_or_create_recipe_book(caller):
    """获取或创建角色的配方收藏夹。

    查找角色 contents 中 tag="recipe_book" 的对象，
    不存在则从 prototype 创建并 move_to 角色。

    Args:
        caller: 玩家角色。

    Returns:
        配方收藏夹对象。
    """
    for obj in caller.contents:
        if obj.tags.has("recipe_book", category="system"):
            return obj
    objs = spawn("recipe_book")
    if objs:
        book = objs[0]
        book.move_to(caller, quiet=True)
        return book
    return None


# ── 配方查找 ──


def find_recipe(caller, recipe_name):
    """在四层级中查找配方对象。

    查找顺序：房间 → 房间中对象 → 配方收藏夹 → 玩家背包（排除收藏夹）

    Args:
        caller: 玩家对象
        recipe_name: 配方名称（已补全"配方"后缀）

    Returns:
        配方对象，未找到返回 None
    """
    # 第一层：房间
    results = caller.location.search(recipe_name, quiet=True, exact=True)
    if results:
        return results[0] if isinstance(results, list) else results

    # 第二层：房间中对象的内容物
    for obj in caller.location.contents:
        inner_results = obj.search(recipe_name, quiet=True, exact=True)
        if inner_results:
            return inner_results[0] if isinstance(inner_results, list) else inner_results

    # 第三层：配方收藏夹
    book = get_or_create_recipe_book(caller)
    if book:
        results = book.search(recipe_name, quiet=True, exact=True)
        if results:
            return results[0] if isinstance(results, list) else results

    # 第四层：玩家背包（排除收藏夹本身）
    for obj in caller.contents:
        if obj.tags.has("recipe_book", category="system"):
            continue
        if obj.key == recipe_name or recipe_name in obj.aliases.all():
            return obj

    return None


# ── 配方动态描述 ──

# prototype 显示名缓存（从 prototype 定义的 key 字段读取）
_proto_name_cache = {}


def _proto_display_name(proto_key):
    """将 prototype_key 转换为中文显示名（从 prototype 定义的 key 字段读取）。

    优先查缓存，未命中则从 prototype 定义读取并缓存。
    找不到 prototype 定义时返回 proto_key 原值。
    """
    if proto_key in _proto_name_cache:
        return _proto_name_cache[proto_key]

    from evennia.prototypes.prototypes import search_prototype
    protos = search_prototype(key=proto_key)
    if protos:
        name = protos[0].get("key", proto_key)
    else:
        name = proto_key

    _proto_name_cache[proto_key] = name
    return name


def generate_recipe_desc(caller, recipe):
    """动态生成配方的结构化描述。

    实时检查玩家当前状态（材料、工具、条件），生成带 ✓/✗ 的配方详情。
    没有内容的段落整段不显示。

    Args:
        caller: 玩家角色。
        recipe: 配方对象。

    Returns:
        str: 格式化的配方描述文本。
    """
    lines = []
    sep = "=" * 24

    # ── 标题行 ──
    key = recipe.key or ""
    desc = recipe.attributes.get("desc", "")
    title = f" {key}：{desc}" if desc else f" {key}"
    lines.append(sep)
    lines.append(title)
    lines.append(sep)

    # ── 背景 ──
    background = recipe.attributes.get("background", "")
    if background:
        lines.append(f"【背景】{background}")

    # ── 预计用时 ──
    duration = recipe.attributes.get("duration", 0)
    if duration:
        lines.append(f"【预计用时】{duration}秒")

    # ── 条件 ──
    environment = recipe.attributes.get("environment")
    requires = recipe.attributes.get("requires", [])
    cond_lines = []
    cond_idx = 1
    if environment and environment.get("fire") == "burning":
        has_fire = False
        room = caller.location
        if room:
            for obj in room.contents:
                if obj.attributes.get("fire_state") == "burning":
                    has_fire = True
                    break
        mark = "v" if has_fire else "x"
        cond_lines.append(f"  {cond_idx}. [{mark}]【必选】燃烧中的篝火")
        cond_idx += 1
    for req in requires:
        req_type = req.get("type")
        if req_type == "room_has":
            proto_key = req.get("prototype")
            proto_names = {"tent": "帐篷", "small_fire": "篝火"}
            name = proto_names.get(proto_key, proto_key)
            room = caller.location
            has_it = False
            if room:
                for obj in room.contents:
                    if obj.tags.get(category="from_prototype") == proto_key:
                        has_it = True
                        break
            mark = "v" if has_it else "x"
            cond_lines.append(f"  {cond_idx}. [{mark}]【必选】{name}")
            cond_idx += 1
    if cond_lines:
        lines.append("【条件】")
        lines.extend(cond_lines)

    # ── 原材料 ──
    materials = recipe.attributes.get("materials", [])
    mat_lines = []
    mat_idx = 1
    for entry in materials:
        if "alternatives" in entry:
            alts = entry["alternatives"]
            alt_names = [_proto_display_name(alt.get("prototype")) for alt in alts]
            total_available = sum(
                count_material(caller, alt.get("prototype"),
                               in_container=alt.get("in_container", False),
                               container_prototype=alt.get("container_prototype"),
                               search_scope=alt.get("search_scope", "inventory"))
                for alt in alts
            )
            required_count = alts[0].get("count", 1)
            mark = "v" if total_available >= required_count else "x"
            names_str = entry.get("display_name") or "/".join(alt_names)
            mat_lines.append(f"  {mat_idx}. [{mark}]【必选】{names_str} ×{required_count}")
        else:
            proto_key = entry.get("prototype")
            count = entry.get("count", 1)
            display_name = _proto_display_name(proto_key)
            found = count_material(caller, proto_key,
                                   in_container=entry.get("in_container", False),
                                   container_prototype=entry.get("container_prototype"),
                                   search_scope=entry.get("search_scope", "inventory"))
            mark = "v" if found >= count else "x"
            mat_lines.append(f"  {mat_idx}. [{mark}]【必选】{display_name} ×{count}")
        mat_idx += 1
    if mat_lines:
        lines.append("【原材料】")
        lines.extend(mat_lines)

    # ── 工具 ──
    craft_tool = recipe.attributes.get("craft_tool")
    if craft_tool:
        tool = find_tool_by_type(caller, craft_tool)
        mark = "v" if tool else "x"
        lines.append("【工具】")
        lines.append(f"  1. [{mark}]【必选】{_proto_display_name(craft_tool)}")

    # ── 主产品 ──
    output_key = recipe.attributes.get("output")
    if output_key:
        lines.append("【主产品】")
        lines.append(f"  1. {_proto_display_name(output_key)} ×1")

    # ── 副产品 ──
    byproduct_key = recipe.attributes.get("byproduct")
    if byproduct_key:
        lines.append("【副产品】")
        destroy_chance = recipe.attributes.get("byproduct_chance", 1.0)
        lines.append(f"  1. {_proto_display_name(byproduct_key)} ×1，获取概率：{destroy_chance}")

    return "\n".join(lines)


# ── 环境检查 ──


def check_environment(caller, environment):
    """检查环境依赖（如篝火）。

    Args:
        caller: 玩家对象
        environment: 环境依赖字典，如 {"fire": "burning", "burn_cost": 30}

    Returns:
        tuple: (是否通过, 错误消息, 环境对象) 三元组
    """
    if environment is None:
        return True, "", None

    # 篝火环境检查
    if environment.get("fire") == "burning":
        room = caller.location
        if not room:
            return False, "你不在任何地方。", None
        for obj in room.contents:
            if obj.attributes.get("fire_state") == "burning":
                burn_duration = obj.attributes.get("burn_duration", 0)
                burn_cost = environment.get("burn_cost", 0)
                if burn_duration < burn_cost:
                    return False, "篝火快灭了，火力不够。", None
                return True, "", obj
        return False, "这里没有燃烧中的篝火。", None

    return True, "", None


# ── 前置条件检查 ──


def check_requires(caller, requires):
    """检查前置条件列表。

    Args:
        caller: 玩家对象
        requires: 前置条件列表，如 [{"type": "room_has", "prototype": "tent"}]

    Returns:
        tuple: (是否通过, 错误消息) 二元组
    """
    if not requires:
        return True, ""

    for req in requires:
        req_type = req.get("type")

        if req_type == "room_has":
            proto_key = req.get("prototype")
            room = caller.location
            if not room:
                return False, "你不在任何地方。"
            found = False
            for obj in room.contents:
                obj_proto = obj.tags.get(category="from_prototype")
                if obj_proto == proto_key:
                    found = True
                    break
            if not found:
                proto_names = {
                    "tent": "帐篷",
                    "small_fire": "篝火",
                }
                name = proto_names.get(proto_key, proto_key)
                return False, f"这里没有{name}。"

        elif req_type == "room_not_has":
            proto_key = req.get("prototype")
            room = caller.location
            if not room:
                return False, "你不在任何地方。"
            for obj in room.contents:
                obj_proto = obj.tags.get(category="from_prototype")
                if obj_proto == proto_key:
                    proto_names = {
                        "tent": "帐篷",
                        "leaf_bed": "床",
                    }
                    name = proto_names.get(proto_key, proto_key)
                    return False, f"这里已经有{name}了。"

    return True, ""


# ── 环境资源消耗 ──


def consume_environment(env_obj, environment):
    """扣减环境资源（如篝火燃烧时长）。

    Args:
        env_obj: 环境对象（如篝火）
        environment: 环境依赖字典
    """
    if env_obj is None or environment is None:
        return

    burn_cost = environment.get("burn_cost")
    if burn_cost:
        burn_duration = env_obj.attributes.get("burn_duration", 0)
        env_obj.attributes.add("burn_duration", max(0, burn_duration - burn_cost))


# ── 产出物创建 ──


def create_output(caller, output_key, build_location, source_containers=None):
    """在指定位置创建产出物。

    Args:
        caller: 玩家对象
        output_key: 产出物 prototype_key
        build_location: 产出位置 "inventory"/"room"/"vessel_content"
        source_containers: 源容器字典（in_container 材料对应的容器）
    """
    if not output_key:
        return

    if build_location == "vessel_content":
        # 产出物写入源容器的 vessel_content（不 spawn 对象）
        if source_containers:
            container = list(source_containers.values())[0]
            container.attributes.add("vessel_content", output_key)
        return

    # 原有逻辑
    objs = spawn(output_key)
    if not objs:
        caller.msg("制作失败了。")
        return

    output_obj = objs[0]
    if build_location == "container" and source_containers:
        # 放入指定容器（如树叶床→帐篷）
        container = list(source_containers.values())[0]
        output_obj.move_to(container, quiet=True)
    elif build_location == "room":
        output_obj.move_to(caller.location, quiet=True)
    else:
        output_obj.move_to(caller, quiet=True)


# ── 材料搜索范围 ──


def _get_material_candidates(caller, search_scope="inventory"):
    """获取材料搜索候选列表。

    Args:
        caller: 玩家角色。
        search_scope: 搜索范围。
            "inventory" — 仅背包（默认，向后兼容）
            "room" — 背包 + 房间（不含房间对象内容物）
            "room_contents" — 背包 + 房间 + 房间对象内容物

    Returns:
        list: 候选对象列表。
    """
    candidates = list(caller.contents)
    if search_scope in ("room", "room_contents"):
        room = caller.location
        if room:
            for obj in room.contents:
                if obj != caller:
                    candidates.append(obj)
                    if search_scope == "room_contents" and hasattr(obj, 'contents'):
                        candidates.extend(obj.contents)
    return candidates


# ── 材料统计 ──


def count_material(caller, required_key, in_container=False,
                   container_prototype=None, search_scope="inventory"):
    """统计材料数量。

    支持 prototype_key 和 cut_from 属性匹配。
    当 in_container=True 时，改为检查容器 vessel_content。

    Args:
        caller: 玩家角色。
        required_key: prototype_key 或 cut_from 值。
        in_container: 是否检查容器 vessel_content。
        container_prototype: 限定容器 prototype_key（可选）。
        search_scope: 搜索范围（"inventory"/"room"/"room_contents"）。

    Returns:
        int: 匹配的数量。
    """
    if in_container:
        found = 0
        for obj in caller.contents:
            if obj.attributes.get("is_container"):
                if obj.attributes.get("vessel_content") == required_key:
                    if container_prototype:
                        proto = obj.tags.get(category="from_prototype")
                        if proto != container_prototype:
                            continue
                    found += 1
        return found

    candidates = _get_material_candidates(caller, search_scope)
    found = 0
    for obj in candidates:
        proto_key = obj.tags.get(category="from_prototype")
        cut_from = obj.attributes.get("cut_from")
        if proto_key == required_key or cut_from == required_key:
            found += 1
    return found


# ── 材料检查 ──


def check_materials(caller, materials):
    """检查玩家是否有配方所需材料（含 in_container 支持）。

    Args:
        caller: 玩家角色。
        materials: 材料需求列表。

    Returns:
        bool: 材料是否齐全。
    """
    if not materials:
        return True
    for entry in materials:
        if "alternatives" in entry:
            total_available = 0
            for alt in entry["alternatives"]:
                required_key = alt.get("prototype")
                in_container = alt.get("in_container", False)
                container_prototype = alt.get("container_prototype")
                search_scope = alt.get("search_scope", "inventory")
                found = count_material(caller, required_key, in_container=in_container,
                                       container_prototype=container_prototype,
                                       search_scope=search_scope)
                total_available += found
            required_count = entry["alternatives"][0].get("count", 1)
            if total_available < required_count:
                caller.msg("你缺少所需的材料。")
                return False
        else:
            required_key = entry.get("prototype")
            required_count = entry.get("count", 1)
            in_container = entry.get("in_container", False)
            container_prototype = entry.get("container_prototype")
            search_scope = entry.get("search_scope", "inventory")
            found = count_material(caller, required_key, in_container=in_container,
                                   container_prototype=container_prototype,
                                   search_scope=search_scope)
            if found < required_count:
                caller.msg("你缺少所需的材料。")
                return False
    return True


# ── 材料消耗（正常完成，全部销毁）──


def consume_materials_full(caller, materials, recipe=None):
    """正常完成时消耗全部材料，返回消耗信息和源容器。

    对于 in_container 材料：清除容器 vessel_content，记录源容器。
    对于普通材料：删除背包物品（原有逻辑）。

    Args:
        caller: 玩家角色。
        materials: 材料需求列表。
        recipe: 配方对象（可选，用于动态配方识别）。

    Returns:
        dict: {"consumed_keys": set, "source_containers": {...}, "consumed_aquatic_key": str or None}
    """
    consumed_keys = set()
    source_containers = {}  # {prototype_key: container_obj}
    consumed_aquatic_key = None
    dynamic_output = recipe.attributes.get("dynamic_output", False) if recipe else False

    # 水产 prototype_key 集合（用于识别被消耗的水产）
    AQUATIC_KEYS = {
        "mudskipper", "mangrove_shrimp", "mud_crab", "mangrove_clam", "sea_slug",
        "grouper", "spiny_lobster", "reef_crab", "oyster", "sea_snail",
        "tilapia", "river_shrimp", "stream_crab", "freshwater_mussel", "pond_snail",
    }

    for entry in materials:
        if "alternatives" in entry:
            required_count = entry["alternatives"][0].get("count", 1)
            destroyed = 0
            for alt in entry["alternatives"]:
                proto_key = alt.get("prototype")
                in_container = alt.get("in_container", False)
                container_prototype = alt.get("container_prototype")
                if in_container:
                    for obj in list(caller.contents):
                        if destroyed >= required_count:
                            break
                        if obj.attributes.get("is_container"):
                            if obj.attributes.get("vessel_content") == proto_key:
                                if container_prototype:
                                    p = obj.tags.get(category="from_prototype")
                                    if p != container_prototype:
                                        continue
                                source_containers[proto_key] = obj
                                obj.attributes.add("vessel_content", None)
                                consumed_keys.add(proto_key)
                                if dynamic_output and (proto_key in AQUATIC_KEYS):
                                    consumed_aquatic_key = proto_key
                                destroyed += 1
                else:
                    s_scope = alt.get("search_scope", "inventory")
                    d_chance = alt.get("destroy_chance", 1.0)
                    for obj in list(_get_material_candidates(caller, s_scope)):
                        if destroyed >= required_count:
                            break
                        obj_proto = obj.tags.get(category="from_prototype")
                        cut_from = obj.attributes.get("cut_from")
                        if obj_proto == proto_key or cut_from == proto_key:
                            if d_chance > 0:
                                obj.delete()
                            consumed_keys.add(proto_key)
                            if dynamic_output and (proto_key in AQUATIC_KEYS):
                                consumed_aquatic_key = proto_key
                            destroyed += 1
                if destroyed >= required_count:
                    break
        else:
            required_key = entry.get("prototype")
            count = entry.get("count", 1)
            in_container = entry.get("in_container", False)
            container_prototype = entry.get("container_prototype")
            destroyed = 0
            if in_container:
                for obj in list(caller.contents):
                    if destroyed >= count:
                        break
                    if obj.attributes.get("is_container"):
                        if obj.attributes.get("vessel_content") == required_key:
                            if container_prototype:
                                p = obj.tags.get(category="from_prototype")
                                if p != container_prototype:
                                    continue
                            source_containers[required_key] = obj
                            obj.attributes.add("vessel_content", None)
                            consumed_keys.add(required_key)
                            if dynamic_output and (required_key in AQUATIC_KEYS):
                                consumed_aquatic_key = required_key
                            destroyed += 1
            else:
                s_scope = entry.get("search_scope", "inventory")
                d_chance = entry.get("destroy_chance", 1.0)
                for obj in list(_get_material_candidates(caller, s_scope)):
                    if destroyed >= count:
                        break
                    proto_key = obj.tags.get(category="from_prototype")
                    cut_from = obj.attributes.get("cut_from")
                    if proto_key == required_key or cut_from == required_key:
                        if d_chance > 0:
                            obj.delete()
                        consumed_keys.add(required_key)
                        if dynamic_output and (proto_key in AQUATIC_KEYS):
                            consumed_aquatic_key = proto_key
                        destroyed += 1

    return {"consumed_keys": consumed_keys, "source_containers": source_containers,
            "consumed_aquatic_key": consumed_aquatic_key}


# ── 材料消耗（取消/失败，按 destroy_chance 概率损毁）──


def consume_materials_cancel(caller, materials):
    """按 destroy_chance 消耗材料（cancel/失败时使用）。

    支持 alternatives 可替换组。

    Args:
        caller: 玩家角色。
        materials: 材料需求列表。
    """
    for entry in materials:
        if "alternatives" in entry:
            # 可替换组：按顺序优先消耗
            required_count = entry["alternatives"][0].get("count", 1)
            consumed = 0
            for alt in entry["alternatives"]:
                proto_key = alt.get("prototype")
                destroy_chance = alt.get("destroy_chance", 1.0)
                s_scope = alt.get("search_scope", "inventory")
                for obj in list(_get_material_candidates(caller, s_scope)):
                    if consumed >= required_count:
                        break
                    obj_proto = obj.tags.get(category="from_prototype")
                    cut_from = obj.attributes.get("cut_from")
                    if obj_proto == proto_key or cut_from == proto_key:
                        if random.random() < destroy_chance:
                            obj.delete()
                        consumed += 1
                if consumed >= required_count:
                    break
        else:
            required_key = entry.get("prototype")
            destroy_chance = entry.get("destroy_chance", 1.0)
            count = entry.get("count", 1)
            s_scope = entry.get("search_scope", "inventory")
            consumed = 0
            for obj in list(_get_material_candidates(caller, s_scope)):
                if consumed >= count:
                    break
                proto_key = obj.tags.get(category="from_prototype")
                cut_from = obj.attributes.get("cut_from")
                if proto_key == required_key or cut_from == required_key:
                    if random.random() < destroy_chance:
                        obj.delete()
                    consumed += 1


# ── 工具查找 ──


def find_tool_by_type(caller, tool_type):
    """在背包和房间中查找指定类型的可用工具（dur>0）。

    Args:
        caller: 玩家角色。
        tool_type: 工具类型字符串。

    Returns:
        工具对象或 None。
    """
    candidates = list(caller.contents) + list(caller.location.contents)
    for obj in candidates:
        if obj.attributes.get("tool_type") == tool_type:
            dur = obj.attributes.get("dur", 0)
            if dur > 0:
                return obj
    return None


# ── cook 配方映射表 ──

# 模块级缓存：菜肴名 → {"recipe": prototype_key, "aquatic": prototype_key or None}
_cook_map_cache = None


def get_cook_map():
    """获取 cook 菜肴映射表（带缓存）。

    从 cook_recipe_map prototype 读取配置，展开模板 × 水产列表
    为完整的菜肴名 → 配方映射 dict。

    Returns:
        dict: {菜肴名: {"recipe": str, "aquatic": str or None}}
    """
    global _cook_map_cache
    if _cook_map_cache is not None:
        return _cook_map_cache

    from evennia.prototypes.prototypes import search_prototype

    protos = search_prototype(key="cook_recipe_map")
    if not protos:
        _cook_map_cache = {}
        return _cook_map_cache

    proto = protos[0]
    attrs = {t[0]: t[1] for t in proto.get("attrs", [])}

    static = attrs.get("static_recipes", {})
    templates = attrs.get("templates", [])
    aquatics = attrs.get("aquatics", [])

    # 查找所有水产的 dishes_name
    aquatic_names = {}
    for aquatic_key in aquatics:
        a_protos = search_prototype(key=aquatic_key)
        if a_protos:
            a_attrs = {t[0]: t[1] for t in a_protos[0].get("attrs", [])}
            aquatic_names[aquatic_key] = a_attrs.get("dishes_name", aquatic_key)

    # 展开模板 × 水产列表
    cook_map = {}
    for tmpl in templates:
        recipe_key = tmpl["recipe"]
        pattern = tmpl["pattern"]
        for aquatic_key in aquatics:
            dname = aquatic_names.get(aquatic_key, aquatic_key)
            dish_name = pattern.format(dishes_name=dname)
            cook_map[dish_name] = {"recipe": recipe_key, "aquatic": aquatic_key}

    # 合并静态映射（非模板配方）
    for dish_name, recipe_key in static.items():
        cook_map[dish_name] = {"recipe": recipe_key, "aquatic": None}

    _cook_map_cache = cook_map
    return _cook_map_cache


def resolve_cook_dish(caller, dish_name):
    """将菜肴名解析为配方对象和具体水产。

    查找映射表 → 在玩家收藏夹中找配方对象 → 返回配方和水产信息。

    Args:
        caller: 玩家角色。
        dish_name: 菜肴名称（如"烤龙虾"）。

    Returns:
        tuple: (recipe_obj, aquatic_key) 或 (None, None)
            recipe_obj: 配方对象（从收藏夹找到的）
            aquatic_key: 水产 prototype_key（模板配方用），非模板配方为 None
    """
    cook_map = get_cook_map()
    entry = cook_map.get(dish_name)
    if not entry:
        return None, None

    recipe_proto_key = entry["recipe"]
    aquatic_key = entry.get("aquatic")

    # 在玩家收藏夹中查找配方对象
    book = get_or_create_recipe_book(caller)
    if not book:
        return None, None

    for obj in book.contents:
        obj_proto = obj.tags.get(category="from_prototype")
        if obj_proto == recipe_proto_key:
            return obj, aquatic_key

    return None, None

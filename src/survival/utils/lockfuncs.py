"""
v2 自定义锁函数

注册到 settings.LOCK_FUNC_MODULES 后可在 prototype locks 中使用。

锁函数签名：func(accessing_obj, accessed_obj, *args, **kwargs)
- accessing_obj：发起访问的对象（玩家角色）
- accessed_obj：被访问的对象（配方/物品）
- args：锁字符串中括号内的参数
- 返回 True 表示条件满足

has_materials 支持 alternatives 可替换材料组。

详见：docs/设计文档/热带环礁岛基础生存闭环/详细设计/v1/基础生存闭环详细设计.md
"""


def has_tool_type(accessing_obj, accessed_obj, *args, **kwargs):
    """检查玩家拥有指定类型的工具。

    搜索范围：accessing_obj.contents（背包）+ accessing_obj.location.contents（所在房间）。
    条件：obj.db.tool_type == args[0] 且 obj.db.dur > 0（耐久未耗尽）。

    Args:
        accessing_obj: 玩家角色。
        accessed_obj: 配方物品。
        args[0]: tool_type 值（如 "cutting"）。

    Returns:
        bool: 是否拥有符合条件的工具。
    """
    if not args:
        return False
    tool_type = args[0]
    candidates = list(accessing_obj.contents) + list(accessing_obj.location.contents)
    for obj in candidates:
        if obj.attributes.get("tool_type") == tool_type:
            dur = obj.attributes.get("dur", 0)
            if dur > 0:
                return True
    return False


def has_materials(accessing_obj, accessed_obj, *args, **kwargs):
    """检查玩家拥有配方所需的全部材料。

    从 accessed_obj.db.materials 读取材料列表，逐一检查。
    支持 alternatives 可替换材料组、search_scope 搜索范围、
    in_container 容器内容物。

    Args:
        accessing_obj: 玩家角色。
        accessed_obj: 配方物品。

    Returns:
        bool: 是否拥有全部所需材料。
    """
    materials = accessed_obj.attributes.get("materials")
    if not materials:
        return True
    for entry in materials:
        if "alternatives" in entry:
            total_available = 0
            required_count = entry["alternatives"][0].get("count", 1)
            for alt in entry["alternatives"]:
                required_key = alt.get("prototype")
                in_container = alt.get("in_container", False)
                search_scope = alt.get("search_scope", "inventory")
                found = _count_by_key(accessing_obj, required_key,
                                      in_container=in_container,
                                      search_scope=search_scope)
                total_available += found
            if total_available < required_count:
                return False
        else:
            required_key = entry.get("prototype")
            required_count = entry.get("count", 1)
            in_container = entry.get("in_container", False)
            search_scope = entry.get("search_scope", "inventory")
            found = _count_by_key(accessing_obj, required_key,
                                  in_container=in_container,
                                  search_scope=search_scope)
            if found < required_count:
                return False
    return True


def _count_by_key(accessing_obj, required_key, in_container=False,
                   search_scope="inventory"):
    """统计指定材料的数量。

    Args:
        accessing_obj: 玩家角色。
        required_key: prototype_key 或 cut_from 值。
        in_container: 是否检查容器 vessel_content。
        search_scope: 搜索范围（"inventory"/"room"/"room_contents"）。

    Returns:
        int: 匹配的数量。
    """
    if in_container:
        found = 0
        for obj in accessing_obj.contents:
            if obj.attributes.get("is_container"):
                if obj.attributes.get("vessel_content") == required_key:
                    found += 1
        return found

    candidates = _get_candidates(accessing_obj, search_scope)
    found = 0
    for obj in candidates:
        proto_key = _get_prototype_key(obj)
        cut_from = obj.attributes.get("cut_from")
        if proto_key == required_key or cut_from == required_key:
            found += 1
    return found


def _get_candidates(accessing_obj, search_scope="inventory"):
    """获取搜索候选列表。

    Args:
        accessing_obj: 玩家角色。
        search_scope: "inventory" 仅背包，"room" 背包+房间，
                      "room_contents" 背包+房间+房间对象内容物。

    Returns:
        list: 候选对象列表。
    """
    candidates = list(accessing_obj.contents)
    if search_scope in ("room", "room_contents"):
        room = accessing_obj.location
        if room:
            for obj in room.contents:
                if obj != accessing_obj:
                    candidates.append(obj)
                    if search_scope == "room_contents" and hasattr(obj, 'contents'):
                        candidates.extend(obj.contents)
    return candidates


def _get_prototype_key(obj):
    """从对象读取 prototype_key（通过 tag）。

    Evennia spawn 的对象通过 tag（category="from_prototype"）存储 prototype_key。

    Args:
        obj: 游戏对象。

    Returns:
        str or None: prototype_key。
    """
    return obj.tags.get(category="from_prototype")


def in_tent(accessing_obj, accessed_obj, *args, **kwargs):
    """检查当前房间是否有帐篷。用于树叶床建造。

    Args:
        accessing_obj: 玩家角色。

    Returns:
        bool: 房间内是否有帐篷。
    """
    room = accessing_obj.location
    if not room:
        return False
    for obj in room.contents:
        if _get_prototype_key(obj) == "tent":
            return True
    return False


def has_fire_burning(accessing_obj, accessed_obj, *args, **kwargs):
    """检查当前房间是否有燃烧中的篝火。用于 cook 指令。

    Args:
        accessing_obj: 玩家角色。

    Returns:
        bool: 房间内是否有燃烧中的篝火。
    """
    room = accessing_obj.location
    if not room:
        return False
    for obj in room.contents:
        if obj.attributes.get("fire_state") == "burning":
            return True
    return False

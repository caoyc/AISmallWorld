"""
v2 inventory 指令 — 查看背包

按物品和饮食分组显示，配方由 recipes 指令单独显示。
合并同名物品，显示为"名称(×数量) — 描述"格式，与房间 look 风格一致。
排除配方收藏夹（recipe_book）和配方对象。
有内容物的对象额外显示内容物列表（仅一层，不递归），使用 └─ 风格。

用法：inventory
"""

from collections import OrderedDict

from .base import SurvivalCommand


def _is_consumable(obj):
    """判断物品是否为食物/饮品（can_eat 或 can_drink）。"""
    return obj.attributes.get("can_eat") or obj.attributes.get("can_drink")


def _is_ingredient(obj):
    """判断物品是否为食材（有 hunger/thirst_restore 但不能直接吃喝）。"""
    if _is_consumable(obj):
        return False
    return obj.attributes.has("hunger_restore") or obj.attributes.has("thirst_restore")


def _format_group(items, caller):
    """格式化一组物品的显示行。

    Args:
        items: 对象列表。
        caller: 观察者。

    Returns:
        list: 格式化后的文本行。
    """
    # 按物品 key 分组，保持顺序
    seen_names = OrderedDict()
    for obj in items:
        name = obj.key
        if name not in seen_names:
            seen_names[name] = []
        seen_names[name].append(obj)

    from survival.rooms import SurvivalRoomV2
    lines = []
    for name, objs in seen_names.items():
        count = len(objs)
        desc = objs[0].get_display_desc(caller)
        if count > 1:
            line = f"  {name}(×{count})" if not desc else f"  {name}(×{count}) — {desc}"
        else:
            line = f"  {name}" if not desc else f"  {name} — {desc}"
        lines.append(line)

        # 单个对象：检查是否有内容物
        if count == 1:
            visible = [
                o for o in objs[0].contents
                if o.access(caller, "view")
            ]
            if visible:
                content_lines = SurvivalRoomV2._format_objects(
                    visible, caller, prefix="    └─ "
                )
                lines.extend(content_lines)

    return lines


class CmdInventory(SurvivalCommand):
    """
    查看背包

    用法：
      inventory    — 查看身上携带的物品
    """
    key = "inventory"
    help_category = "行动"
    stamina_cost = 0

    def func(self):
        caller = self.caller
        items = [
            obj for obj in caller.contents
            if not obj.tags.has("recipe_book", category="system")
            and not obj.attributes.has("recipe_type")
        ]

        if not items:
            caller.msg("你身上没有携带任何物品。")
            return

        # 分组：物品、食材、饮食
        consumables = [obj for obj in items if _is_consumable(obj)]
        ingredients = [obj for obj in items if not _is_consumable(obj) and _is_ingredient(obj)]
        others = [obj for obj in items if not _is_consumable(obj) and not _is_ingredient(obj)]

        output_parts = []

        if others:
            output_parts.append("|w【物品】：|n")
            output_parts.extend(_format_group(others, caller))

        if ingredients:
            output_parts.append("|w【食材】：|n")
            output_parts.extend(_format_group(ingredients, caller))

        if consumables:
            output_parts.append("|w【饮食】：|n")
            output_parts.extend(_format_group(consumables, caller))

        caller.msg("你身上带着：\n" + "\n".join(output_parts))

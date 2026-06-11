"""
v2 recipes 指令 — 查看拥有的配方

从配方收藏夹中读取所有配方，按 make/cook/build 分组显示。
显示格式与 inventory 一致。

用法：recipes
"""

from collections import OrderedDict

from .base import SurvivalCommand


def _format_group(items, caller):
    """格式化一组配方的显示行。

    Args:
        items: 配方对象列表。
        caller: 观察者。

    Returns:
        list: 格式化后的文本行。
    """
    from survival.v2.rooms import SurvivalRoomV2
    lines = []
    for obj in items:
        desc = obj.get_display_desc(caller)
        line = f"  {obj.key}" if not desc else f"  {obj.key} — {desc}"
        lines.append(line)
    return lines


class CmdRecipes(SurvivalCommand):
    """
    查看配方

    用法：
      recipes    — 查看你拥有的所有配方
    """
    key = "recipes"
    help_category = "行动"
    stamina_cost = 0

    def func(self):
        caller = self.caller

        # 查找配方收藏夹
        book = None
        for obj in caller.contents:
            if obj.tags.has("recipe_book", category="system"):
                book = obj
                break

        if not book or not book.contents:
            caller.msg("你没有掌握任何配方。")
            return

        # 按配方类型分组，保持顺序
        recipes_make = []
        recipes_cook = []
        recipes_build = []
        for obj in book.contents:
            rtype = obj.attributes.get("recipe_type")
            if rtype == "make":
                recipes_make.append(obj)
            elif rtype == "cook":
                recipes_cook.append(obj)
            elif rtype == "build":
                recipes_build.append(obj)

        output_parts = []

        if recipes_make:
            output_parts.append("|w【make】：|n")
            output_parts.extend(_format_group(recipes_make, caller))

        if recipes_cook:
            output_parts.append("|w【cook】：|n")
            output_parts.extend(_format_group(recipes_cook, caller))

        if recipes_build:
            output_parts.append("|w【build】：|n")
            output_parts.extend(_format_group(recipes_build, caller))

        caller.msg("你拥有的配方：\n" + "\n".join(output_parts))

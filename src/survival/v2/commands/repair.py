"""
v2 repair 指令 — 修理磨损工具

对磨损态工具使用相同配方的耗材（数量 ×0.5 向上取整），
修复后恢复为正常态工具。

用法：repair <磨损的工具>

参照 make.py 的材料消耗逻辑，复用 recipe_utils.py。
"""

import math

from evennia.prototypes.spawner import spawn

from .base import SurvivalCommand
from .recipe_utils import (
    autocomplete_recipe_name,
    find_recipe,
    check_materials,
    consume_materials_full,
    count_material,
)


def _halve_materials(materials):
    """将配方耗材每项 count ×0.5 向上取整，返回新列表。

    Args:
        materials: 原始材料需求列表。

    Returns:
        list: 耗材减半后的新材料列表。
    """
    halved = []
    for entry in materials:
        if "alternatives" in entry:
            new_alts = []
            for alt in entry["alternatives"]:
                new_alt = dict(alt)
                new_alt["count"] = math.ceil(alt.get("count", 1) * 0.5)
                new_alts.append(new_alt)
            halved.append({"alternatives": new_alts})
        else:
            new_entry = dict(entry)
            new_entry["count"] = math.ceil(entry.get("count", 1) * 0.5)
            halved.append(new_entry)
    return halved


class CmdRepair(SurvivalCommand):
    """
    修理磨损的工具

    用法：
      repair <磨损的工具>

    使用与制作相同的配方，耗材数量减半（向上取整）。
    """

    key = "repair"
    help_category = "制作"
    stamina_cost = -1

    def func(self):
        """执行修理。"""
        if not self.pre_check():
            return

        caller = self.caller
        args = self.args.strip() if self.args else ""

        if not args:
            caller.msg("你想修理什么？用法：repair <磨损的工具>")
            return

        # 在背包中查找磨损态工具
        target = None
        for obj in caller.contents:
            if obj.attributes.get("worn") and self._name_matches(obj, args, caller):
                target = obj
                break

        if not target:
            caller.msg(f"你没有可修理的 {args}。")
            return

        # 获取修理配方：去掉"磨损的"前缀后按 make 方式查找
        tool_key = target.key
        if tool_key.startswith("磨损的"):
            base_name = tool_key[3:]
        else:
            base_name = tool_key

        recipe_name = autocomplete_recipe_name(base_name)
        recipe = find_recipe(caller, recipe_name)
        if not recipe:
            caller.msg(f"你没有掌握修理{target.key}所需的配方。")
            return

        # 读取配方耗材，减半
        materials = recipe.attributes.get("materials", [])
        halved_materials = _halve_materials(materials)

        # 检查材料是否齐全
        if not check_materials(caller, halved_materials):
            caller.msg("你缺少修理所需的材料。")
            self.apply_stamina()
            return

        # 消耗材料
        consume_materials_full(caller, halved_materials, recipe)

        # 获取产出 prototype 和 output_overrides
        output_key = recipe.attributes.get("output")
        output_overrides = recipe.attributes.get("output_overrides", [])

        # 判断实际消耗了哪种材料（用于 output_overrides）
        consumed_keys = set()
        for entry in halved_materials:
            if "alternatives" in entry:
                for alt in entry["alternatives"]:
                    proto = alt.get("prototype")
                    if proto and count_material(caller, proto) < alt.get("count", 1):
                        consumed_keys.add(proto)
            else:
                consumed_keys.add(entry.get("prototype"))

        # 删除磨损态工具
        worn_key = target.key
        target.delete()

        # spawn 正常态工具
        objs = spawn(output_key)
        if objs:
            repaired = objs[0]
            repaired.move_to(caller, quiet=True)

            # 应用 output_overrides
            if output_overrides and consumed_keys:
                for override in output_overrides:
                    mat_key = override.get("material")
                    if mat_key in consumed_keys:
                        for attr_name, attr_value in override.items():
                            if attr_name == "material":
                                continue
                            if attr_name == "key":
                                repaired.key = attr_value
                            elif attr_name == "desc_look":
                                repaired.db.desc_look = attr_value
                            else:
                                repaired.attributes.add(attr_name, attr_value)
                        break

            caller.msg(f"你修好了{worn_key}，得到了{repaired.key}。")
        else:
            caller.msg(f"修理失败了。")

        self.apply_stamina()

    @staticmethod
    def _name_matches(obj, name, caller):
        """检查对象名称是否匹配。"""
        if obj.key == name:
            return True
        if name in obj.aliases.all():
            return True
        return False

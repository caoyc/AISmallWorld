"""
资源与物品 Typeclass

提供三个 Typeclass（WaterSource、FoodResourcePoint、FoodItem）
和一组辅助查找函数。

详见：docs/设计文档/五感系统/详细设计/资源与物品五感扩展详细设计.md
"""

from evennia.objects.objects import DefaultObject


class WaterSource(DefaultObject):
    """水源资源点，永久存在，可直接 drink 或 taste。

    Attributes:
        db.water_type (str): 水源类型，"fresh" 或 "salty"。
        db.desc (str): 通用描述。
        db.desc_look (str): 视觉描述。
        db.desc_smell (str): 嗅觉描述。
    """

    def at_object_creation(self):
        """初始化水源属性。"""
        self.db.water_type = "fresh"
        self.db.desc = ""
        self.db.desc_look = ""
        self.db.desc_smell = ""


class FoodResourcePoint(DefaultObject):
    """食物资源点，永久存在，search 概率生成 FoodItem。

    Attributes:
        db.food_type (str): 食物类型标识（"coconut" / "berry" / "shellfish"）。
        db.food_name (str): 生成物品的名称（"椰子" / "浆果" / "海贝"）。
        db.search_chance (float): search 成功概率（0.0~1.0）。
        db.food_desc (str): 生成物品的五感描述。
        db.hunger_restore (int): eat 恢复饥饿值。
        db.thirst_restore (int): drink 恢复口渴值（0 = 不可喝）。
        db.desc (str): 资源点通用描述。
        db.desc_look (str): 资源点视觉描述。
        db.desc_smell (str): 资源点嗅觉描述。
    """

    def at_object_creation(self):
        """初始化食物资源点属性。"""
        self.db.food_type = "berry"
        self.db.food_name = "浆果"
        self.db.search_chance = 0.5
        self.db.food_desc = "一些食物"
        self.db.hunger_restore = 25
        self.db.thirst_restore = 0
        self.db.desc = ""
        self.db.desc_look = ""
        self.db.desc_smell = ""


class FoodItem(DefaultObject):
    """食物物品，search 成功时创建，eat/drink 后销毁。

    Attributes:
        db.hunger_restore (int): eat 恢复饥饿值。
        db.thirst_restore (int): drink 恢复口渴值（0 = 不可喝）。
        db.can_drink (bool): 是否可 drink（thirst_restore > 0 时为 True）。
        db.can_eat (bool): 是否可 eat（hunger_restore > 0 时为 True）。
        db.times_used (int): 已使用次数。
        db.desc (str): 通用描述。
        db.desc_look (str): 视觉描述。
        db.desc_listen (str): 听觉描述。
        db.desc_smell (str): 嗅觉描述。
        db.desc_touch (str): 触觉描述。
        db.desc_taste (str): 味觉描述。
    """

    def at_object_creation(self):
        """初始化食物物品属性。"""
        self.db.hunger_restore = 0
        self.db.thirst_restore = 0
        self.db.can_drink = False
        self.db.can_eat = True
        self.db.times_used = 0
        self.db.desc = ""
        self.db.desc_look = ""
        self.db.desc_listen = ""
        self.db.desc_smell = ""
        self.db.desc_touch = ""
        self.db.desc_taste = ""

    def is_fully_consumed(self):
        """判断食物物品是否完全消耗。

        当可 eat 和可 drink 的能力都用完时返回 True。

        Returns:
            bool: 是否完全消耗。
        """
        can_still_eat = self.db.can_eat and self.db.hunger_restore > 0
        can_still_drink = self.db.can_drink and self.db.thirst_restore > 0
        return not can_still_eat and not can_still_drink


# ---------------------------------------------------------------------------
# 辅助查找函数
# ---------------------------------------------------------------------------


def find_water_sources(room):
    """返回房间内所有 WaterSource 对象。

    Args:
        room: 房间对象。

    Returns:
        list[WaterSource]: 房间内的水源列表。
    """
    return [obj for obj in room.contents if isinstance(obj, WaterSource)]


def find_food_resource_points(room):
    """返回房间内所有 FoodResourcePoint 对象。

    Args:
        room: 房间对象。

    Returns:
        list[FoodResourcePoint]: 房间内的食物资源点列表。
    """
    return [obj for obj in room.contents if isinstance(obj, FoodResourcePoint)]


def find_food_items(room, name=None):
    """返回房间内所有或指定名称的 FoodItem 对象。

    Args:
        room: 房间对象。
        name (str, optional): 食物名称，为 None 时返回全部。

    Returns:
        list[FoodItem]: 匹配的食物物品列表。
    """
    items = [obj for obj in room.contents if isinstance(obj, FoodItem)]
    if name:
        items = [obj for obj in items if obj.key == name]
    return items

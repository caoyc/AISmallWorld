"""
搜索指令

详见：docs/设计文档/五感系统/详细设计/指令改造详细设计.md
"""

import random

from evennia.commands.command import Command
from evennia.utils.create import create_object

from .resources import FoodItem, find_food_resource_points

# 食物五感描述模板
FOOD_SENSE_TEMPLATES = {
    "coconut": {
        "desc_look": "一个圆形的大椰子，外壳坚硬粗糙，顶部有几片绿色的苞叶。",
        "desc_listen": "你摇晃了一下椰子，里面传来咕噜咕噜的水声。",
        "desc_smell": "椰子散发着淡淡的奶香和清甜的气息。",
        "desc_touch": "椰壳表面粗糙坚硬，纤维纹理清晰，沉甸甸的很有分量。",
        "desc_taste": "椰汁清甜爽口，带着淡淡的椰奶香味，椰肉嫩滑可口。",
    },
    "berry": {
        "desc_look": "一把鲜红的浆果，表面覆盖着细密的绒毛，大小如指甲盖。",
        "desc_listen": "你轻轻捏了捏浆果，果肉发出细微的噗噗声。",
        "desc_smell": "浆果散发着浓郁的甜香，夹杂着一丝野花蜜的味道。",
        "desc_touch": "浆果软软的，捏起来有弹性，果皮薄而嫩，稍用力就会破。",
        "desc_taste": "果汁在口中爆开，甜中带酸，清新的果味充满口腔。",
    },
    "shellfish": {
        "desc_look": "几枚拳头大小的海贝，外壳粗糙，呈深灰色带有白色纹理。",
        "desc_listen": "你敲了敲贝壳，发出清脆的笃笃声。",
        "desc_smell": "海贝带着淡淡的海水咸腥味，混合着矿物质的气息。",
        "desc_touch": "贝壳表面粗糙冰冷，边缘锋利，沉甸甸的很有分量。",
        "desc_taste": "贝肉鲜嫩弹牙，带着淡淡的海水咸鲜味，口感清爽。",
    },
}


class CmdSearch(Command):
    """在当前房间搜索食物资源。

    key = "search"
    aliases = ["搜索", "se"]
    locks = "cmd:all()"

    流程：
        mermaid:
        TD
            A[CmdSearch.func] --> B[遍历 caller.location.contents]
            B --> C{找到 FoodResourcePoint?}
            C -->|否| D[msg: 这里没有可以搜索的东西]
            C -->|是| E[获取 search_chance]
            E --> F[random.random < search_chance?]
            F -->|否| G[msg: 你翻找了半天，没有找到可以食用的东西]
            F -->|是| H[create_object FoodItem]
            H --> I[msg: 你发现了 xxx！]
    """

    key = "search"
    aliases = ["搜索", "se"]
    locks = "cmd:all()"

    def func(self):
        """执行搜索逻辑。"""
        caller = self.caller
        room = caller.location

        # 查找房间内的食物资源点
        resource_points = find_food_resource_points(room)
        if not resource_points:
            caller.msg("这里没有可以搜索的东西。")
            return

        # 取第一个资源点
        resource = resource_points[0]

        # 概率判定
        if random.random() >= resource.db.search_chance:
            caller.msg("你翻找了半天，没有找到可以食用的东西。")
            return

        # 成功：创建 FoodItem
        sense_attrs = FOOD_SENSE_TEMPLATES.get(resource.db.food_type, {})
        item = create_object(
            FoodItem,
            key=resource.db.food_name,
            location=room,
            attributes=[
                ("hunger_restore", resource.db.hunger_restore),
                ("thirst_restore", resource.db.thirst_restore),
                ("can_drink", resource.db.thirst_restore > 0),
                ("can_eat", resource.db.hunger_restore > 0),
                ("food_desc", resource.db.food_desc),
                ("desc", sense_attrs.get("desc_look", resource.db.food_desc)),
                ("desc_look", sense_attrs.get("desc_look", "")),
                ("desc_listen", sense_attrs.get("desc_listen", "")),
                ("desc_smell", sense_attrs.get("desc_smell", "")),
                ("desc_touch", sense_attrs.get("desc_touch", "")),
                ("desc_taste", sense_attrs.get("desc_taste", "")),
            ],
        )
        caller.msg(f"你发现了 {item.key}！")

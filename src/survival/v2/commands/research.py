"""
v2 research 指令 — 配方发现

消耗耐力静心思考，从预定义配方池中抽取配方。
无参数时全随机，有参数时按关键词匹配度排序优先抽取。

算法：
  - 每个配方的抽取概率 = 0.8 / 池中配方总数
  - 按关键词匹配字数降序排列，匹配越多的越先被尝试
  - 匹配字数相同的项随机顺序
  - 无关键词或全部无匹配 = 等效全随机

用法：
  research
  research <关键词>

详见：docs/设计文档/石刃业务闭环/详细设计/research指令.md
"""

import random

from evennia.prototypes.prototypes import search_prototype
from evennia.prototypes.spawner import spawn

from .base import SurvivalCommand

# 配方池：所有可被 research 抽取的配方 prototype_key
RECIPE_POOL = [
    "recipe_stone_blade",
    "recipe_stone_axe",
    "recipe_obsidian_axe",
    "recipe_hand_drill",
    "recipe_weak_torch",
    "recipe_coconut_bidon",
    "recipe_chopsticks",
    "recipe_bamboo_straw",
    "recipe_fish_trap",
    "recipe_campfire",
    "recipe_campfire_persistent",
    "recipe_well",
    "recipe_tent",
    "recipe_leaf_bed",
    "recipe_roast_meat",
    # cook 类配方
    "recipe_boilwater",
    "recipe_boilsalt",
    "recipe_roast_aquatic",
    "recipe_tasty_roast_aquatic",
    "recipe_aquatic_soup",
    "recipe_tasty_aquatic_soup",
]

# 总成功率（每个配方的概率 = SUCCESS_RATE / N）
SUCCESS_RATE = 0.8


class CmdResearch(SurvivalCommand):
    """
    研究发现配方（概率成功）

    用法：
      research
      research <关键词>

    无参数时随机思考，有参数时围绕关键词定向思考。
    """

    key = "research"
    help_category = "制作"
    stamina_cost = -10

    def func(self):
        """执行配方思考。"""
        caller = self.caller

        if not self.pre_check():
            return

        from .recipe_utils import get_or_create_recipe_book

        # 完整配方池为空检查
        if not RECIPE_POOL:
            caller.msg("这个世界上没有任何已知的配方。")
            self.apply_stamina()
            return

        # 去重：排除已掌握的配方
        book = get_or_create_recipe_book(caller)
        owned = set()
        if book:
            for obj in book.contents:
                proto_key = obj.tags.get(category="from_prototype")
                if proto_key:
                    owned.add(proto_key)

        eligible = [k for k in RECIPE_POOL if k not in owned]

        # 检查是否已掌握所有配方
        if not eligible:
            caller.msg("你已经掌握了所有已知的配方。")
            self.apply_stamina()
            return

        # 计算匹配分数 & 排序
        keyword = self.args.strip() if self.args else ""
        scored = [(pk, self._match_score(pk, keyword)) for pk in eligible]

        # 先随机打乱（使同分组内随机），再按分数降序排列
        random.shuffle(scored)
        scored.sort(key=lambda x: x[1], reverse=True)

        # 加权随机：权重 = 1 + 匹配字数，总成功率 80%
        weights = [1 + score for _, score in scored]
        total_weight = sum(weights)

        if random.random() >= SUCCESS_RATE:
            caller.msg(
                "你闭上眼沉思了一会儿，脑子里什么清晰的画面也没出现。"
            )
            self.apply_stamina()
            return

        # 加权抽取
        chosen = None
        r = random.random() * total_weight
        cumulative = 0
        for (proto_key, _score), weight in zip(scored, weights):
            cumulative += weight
            if r < cumulative:
                chosen = proto_key
                break

        if not chosen:
            chosen = scored[-1][0]  # 兜底

        # 成功：spawn 配方到收藏夹
        objs = spawn(chosen)
        if objs:
            if not book:
                book = get_or_create_recipe_book(caller)
            objs[0].move_to(book, quiet=True)
            recipe_name = objs[0].key
            background = objs[0].attributes.get("background", "")
            parts = [
                f"你闭上眼沉思了一会儿……脑海中浮现出一个画面——{recipe_name}。"
            ]
            if background:
                parts.append(background)
            caller.msg("\n".join(parts))

        self.apply_stamina()

    @staticmethod
    def _match_score(proto_key, keyword):
        """计算关键词在配方可搜索文本中的匹配占比。

        匹配占比 = 匹配字数 / 可搜索文本总长度。
        无关键词或无可搜索文本时返回 0。

        Args:
            proto_key: 配方 prototype_key。
            keyword: 玩家输入的关键词。

        Returns:
            float: 匹配占比（0~1），0 表示无匹配。
        """
        if not keyword:
            return 0

        protos = search_prototype(key=proto_key)
        if not protos:
            return 0

        proto = protos[0]
        # 收集可搜索文本
        searchable = proto.get("key", "")
        for attr_tuple in proto.get("attrs", []):
            val = attr_tuple[1] if len(attr_tuple) > 1 else None
            if isinstance(val, str):
                searchable += val
            elif isinstance(val, list):
                for item in val:
                    if isinstance(item, str):
                        searchable += item
                    elif isinstance(item, dict):
                        for v in item.values():
                            if isinstance(v, str):
                                searchable += v

        if not searchable:
            return 0

        matched_chars = searchable.count(keyword) * len(keyword)
        return matched_chars / len(searchable)

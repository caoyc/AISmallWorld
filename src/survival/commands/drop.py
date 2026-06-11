"""
v2 drop 指令 — 放下物品

扩展 Evennia 默认 drop，支持批量放下：drop all [物品名]。
无参数 drop all 按物品类型分组，同组一次全放，组间间隔 1 秒。
有参数 drop all <名称> 一次批量完成。

用法：
    drop <物品>                — 放下一个物品
    drop all                   — 放下所有物品（分组，间隔 1 秒）
    drop all <物品名>           — 放下所有指定名称的物品
"""

import time

from evennia.utils.utils import delay

from .base import SurvivalCommand


# ── 模块级函数：供 delay() 回调，不依赖 Command 实例 ──


def _drop_one(caller, target):
    """放下单个物品。

    Args:
        caller: 玩家角色。
        target: 目标物品。

    Returns:
        bool: 是否成功。
    """
    if not target.at_pre_drop(caller):
        return False
    if target.move_to(caller.location, quiet=True, move_type="drop"):
        target.at_drop(caller)
        return True
    return False


def _drop_all_tick(caller, groups, idx, has_failed, drop_id):
    """delay() 回调：按物品类型分组放下（drop all 无参模式）。

    每次处理一组同名物品，同组一次全放并输出汇总消息，
    不同组之间间隔 1 秒。

    Args:
        caller: 玩家角色。
        groups: [(显示名, [obj, ...]), ...] 按名称分组的候选列表。
        idx: 当前组索引。
        has_failed: 是否有失败。
        drop_id: 放下会话 ID（用于检测取消）。
    """
    # 被取消（玩家发了新 drop all）
    if caller.attributes.get("_drop_all_id") != drop_id:
        return

    if idx >= len(groups):
        if has_failed:
            caller.msg("部分物品无法放下。")
        caller.attributes.remove("_drop_all_id")
        return

    name, items = groups[idx]
    dropped_count = 0
    group_failed = False

    for target in items:
        if _drop_one(caller, target):
            dropped_count += 1
        else:
            group_failed = True

    # 同组汇总输出
    if dropped_count > 1:
        caller.msg(f"你放下了 {dropped_count} 个{name}。")
    elif dropped_count == 1:
        caller.msg(f"你放下了 {name}。")

    if group_failed:
        has_failed = True

    # 调度下一组（间隔 1 秒）
    delay(1, _drop_all_tick, caller, groups, idx + 1, has_failed, drop_id)


class CmdDrop(SurvivalCommand):
    """
    放下物品

    用法：
      drop <物品>
      drop all
      drop all <物品名>

    将背包中的物品放到当前位置。
    """

    key = "drop"
    help_category = "行动"
    stamina_cost = 0

    def func(self):
        """执行放下。"""
        if not self.pre_check():
            return

        caller = self.caller
        room = caller.location
        args = self.args.strip() if self.args else ""

        if not args:
            caller.msg("放下什么？")
            return

        # ── 批量模式：drop all [物品名] ──
        if args.startswith("all"):
            item_name = args[3:].strip() or None
            self._drop_all(caller, room, item_name)
            return

        # ── 单个放下 ──
        results = caller.search(
            args,
            location=caller,
            quiet=True,
            exact=True,
        )
        if not results:
            caller.msg(f"你没有 {args}。")
            return

        target = results[0]

        if not target.at_pre_drop(caller):
            return

        if target.move_to(room, quiet=True, move_type="drop"):
            target.at_drop(caller)
            caller.msg(f"你放下了 {target.key}。")
        else:
            caller.msg(f"你不能放下 {target.key}。")

    def _drop_all(self, caller, room, item_name):
        """批量放下。

        有参数时：一次性批量放下，汇总输出。
        无参数时：按类型分组，同组一次全放，组间间隔 1 秒。

        Args:
            caller: 玩家角色。
            room: 当前房间。
            item_name: 指定物品名（None=全部）。
        """
        candidates = self._find_all_matches(caller, item_name)

        if not candidates:
            if item_name:
                caller.msg(f"你没有 {item_name}。")
            else:
                caller.msg("你没有可以放下的东西。")
            return

        if item_name:
            # ── 有参数：一次性批量放下 ──
            self._drop_all_batch(caller, candidates, item_name)
        else:
            # ── 无参数：按类型分组，组间间隔 1 秒 ──
            groups_dict = {}
            order = []
            for obj in candidates:
                key = obj.key
                if key not in groups_dict:
                    groups_dict[key] = []
                    order.append(key)
                groups_dict[key].append(obj)
            groups = [(name, groups_dict[name]) for name in order]

            drop_id = time.time()
            caller.attributes.add("_drop_all_id", drop_id)
            _drop_all_tick(caller, groups, 0, False, drop_id)

    def _drop_all_batch(self, caller, candidates, item_name):
        """有参数的批量放下：一次完成，汇总输出。

        Args:
            caller: 玩家角色。
            candidates: 候选物品列表。
            item_name: 指定物品名。
        """
        dropped = {}       # {名称: 数量}
        has_failed = False

        for target in candidates:
            if _drop_one(caller, target):
                dropped[target.key] = dropped.get(target.key, 0) + 1
            else:
                has_failed = True

        if dropped:
            summary = "、".join(
                f"{k} x{c}" if c > 1 else k for k, c in dropped.items()
            )
            caller.msg(f"你放下了：{summary}。")
        else:
            caller.msg(f"你不能放下 {item_name}。")

    def _find_all_matches(self, caller, item_name):
        """查找背包中所有匹配的物品。

        Args:
            caller: 玩家角色。
            item_name: 指定物品名（None=全部）。

        Returns:
            list: 匹配的对象列表。
        """
        matches = []
        for obj in caller.contents:
            if item_name and not self._name_matches(obj, item_name, caller):
                continue
            matches.append(obj)
        return matches

    @staticmethod
    def _name_matches(obj, name, caller):
        """检查对象名称是否匹配。"""
        if obj.key == name:
            return True
        if name in obj.aliases.all():
            return True
        display_name = obj.get_display_name(caller)
        if display_name == name:
            return True
        return False

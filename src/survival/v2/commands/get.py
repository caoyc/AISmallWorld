"""
v2 get 指令 — 拾取物品

扩展 Evennia 默认 get，支持从对象 contents 中拾取。
支持批量拾取：get all [物品名]。

用法：
    get <物品>                — 遍历房间 + 所有对象 contents，取第一个匹配
    get <物品> from <对象>     — 从指定对象 contents 中取
    get all                   — 拾取所有可拾取物品
    get all <物品名>           — 拾取所有指定名称的物品

详见：docs/设计文档/石刃业务闭环/详细设计/房间look显示.md
详见：docs/设计文档/热带环礁岛基础生存闭环/详细设计/v6/LC-03a/LC-03a详细设计.md
"""

import time

from evennia.utils.utils import delay

from .base import SurvivalCommand


# ── 模块级函数：供 delay() 回调，不依赖 Command 实例 ──


def _pick_one(caller, target):
    """拾取单个物品，返回 (成功bool, 显示名str)。

    Args:
        caller: 玩家角色。
        target: 目标物品。

    Returns:
        tuple: (是否成功, 用于汇总计数的显示名)。失败返回 (False, None)。
    """
    if not target.at_pre_get(caller):
        return False, None

    if target.attributes.get("recipe_type"):
        from .recipe_utils import get_or_create_recipe_book

        book = get_or_create_recipe_book(caller)
        if not book:
            return False, None
        target_proto = target.tags.get(category="from_prototype")
        if target_proto:
            already = any(
                obj.tags.get(category="from_prototype") == target_proto
                for obj in book.contents
            )
            if already:
                return False, None
        if target.move_to(book, quiet=True, move_type="get"):
            target.at_get(caller)
            return True, f"{target.key}（配方）"
        return False, None

    if target.move_to(caller, quiet=True, move_type="get"):
        target.at_get(caller)
        return True, target.key
    return False, None


def _get_all_tick(caller, groups, idx, has_failed, get_id):
    """delay() 回调：按物品类型分组拾取（get all 无参模式）。

    每次处理一组同名物品，同组一次全捡并输出汇总消息，
    不同组之间间隔 1 秒。

    Args:
        caller: 玩家角色。
        groups: [(显示名, [obj, ...]), ...] 按名称分组的候选列表。
        idx: 当前组索引。
        has_failed: 是否有非锁原因的失败。
        get_id: 拾取会话 ID（用于检测取消）。
    """
    # 被取消（玩家发了新 get all）
    if caller.attributes.get("_get_all_id") != get_id:
        return

    if idx >= len(groups):
        if has_failed:
            caller.msg("部分物品无法拾取。")
        caller.attributes.remove("_get_all_id")
        return

    name, items = groups[idx]
    picked_count = 0
    group_failed = False

    for target in items:
        ok, display = _pick_one(caller, target)
        if ok:
            picked_count += 1
        else:
            group_failed = True

    # 同组汇总输出
    if picked_count > 1:
        caller.msg(f"你捡起了 {picked_count} 个{name}。")
    elif picked_count == 1:
        caller.msg(f"你捡起了 {name}。")

    if group_failed:
        has_failed = True

    # 调度下一组（间隔 1 秒）
    delay(1, _get_all_tick, caller, groups, idx + 1, has_failed, get_id)


class CmdGet(SurvivalCommand):
    """
    拾取物品

    用法：
      get <物品>
      get <物品> from <对象>
      get all
      get all <物品名>

    从房间地面或对象内部拾取物品到背包。
    """

    key = "get"
    help_category = "行动"
    stamina_cost = 0

    def func(self):
        """执行拾取。

        流程：
            mermaid:
            TD
                A[解析参数] --> B{有 all?}
                B -->|有| C[批量拾取模式]
                B -->|无| D{有 from?}
                D -->|有| E[查找来源对象]
                D -->|无| F[遍历房间+对象contents]
                C --> G[收集所有匹配]
                E --> H[在来源contents中查找物品]
                F --> I[取第一个匹配]
                G --> J[逐个锁检查+拾取]
                H --> K{找到?}
                I --> K
                K -->|否| L[没有这个物品]
                K -->|是| M{get 锁检查}
                M -->|拒绝| N[提示需要工具或其他]
                M -->|通过| O[move_to 背包]
                O --> P[提示]
                J --> Q[汇总输出]
        """
        if not self.pre_check():
            return

        caller = self.caller
        room = caller.location
        args = self.args.strip() if self.args else ""

        if not args:
            caller.msg("拿什么？")
            return

        # ── 批量模式：get all [物品名] ──
        if args.startswith("all"):
            item_name = args[3:].strip() or None  # None 表示全部
            self._get_all(caller, room, item_name)
            return

        # ── 单个拾取（现有逻辑） ──
        # 解析 from 参数
        if " from " in args:
            parts = args.split(" from ", 1)
            item_name = parts[0].strip()
            source_name = parts[1].strip()
            target = self._get_from_source(caller, room, item_name, source_name)
        else:
            item_name = args
            target = self._get_from_anywhere(caller, room, item_name)

        if not target:
            return

        # get 锁检查（锁机制决定获取条件，如需要工具等）
        if not target.access(caller, "get"):
            err_msg = target.db.get_err_msg
            if err_msg:
                caller.msg(err_msg)
            else:
                caller.msg(f"你不能拿 {target.key}。")
            return

        # at_pre_get 钩子
        if not target.at_pre_get(caller):
            return

        # 配方 → 放入收藏夹（不放入背包）
        if target.attributes.get("recipe_type"):
            from .recipe_utils import get_or_create_recipe_book

            book = get_or_create_recipe_book(caller)
            if not book:
                caller.msg("无法存放配方。")
                return

            # 收藏夹唯一性检查
            target_proto = target.tags.get(category="from_prototype")
            if target_proto:
                for obj in book.contents:
                    obj_proto = obj.tags.get(category="from_prototype")
                    if obj_proto == target_proto:
                        caller.msg(f"你已经拥有 {target.key}，无法重复拾取。")
                        return

            # 移入收藏夹
            if target.move_to(book, quiet=True, move_type="get"):
                target.at_get(caller)
                caller.msg(f"你捡起了 {target.key}，收入配方收藏夹。")
            else:
                caller.msg(f"你拿不起 {target.key}。")
            return

        # 移入背包（非配方物品）
        source = target.location  # 记录来源容器（取走前）
        if target.move_to(caller, quiet=True, move_type="get"):
            target.at_get(caller)
            caller.msg(f"你捡起了 {target.key}。")

            # 椰肉壳→椰壳转化：取走椰肉后，若容器是椰肉壳且已空，转化为椰壳
            self._check_empty_shell_transform(source)
        else:
            caller.msg(f"你拿不起 {target.key}。")

    # ── 批量拾取 ──

    def _get_all(self, caller, room, item_name):
        """批量拾取所有匹配物品。

        有参数时：一次性批量拾取，汇总输出。
        无参数时：逐个拾取，每次间隔 1 秒。

        Args:
            caller: 玩家角色。
            room: 当前房间。
            item_name: 指定物品名（None=全部）。
        """
        candidates = self._find_all_matches(caller, room, item_name)

        if not candidates:
            if item_name:
                caller.msg(f"这里没有 {item_name}。")
            else:
                caller.msg("这里没有可以拾取的东西。")
            return

        if item_name:
            # ── 有参数：一次性批量拾取 ──
            self._get_all_batch(caller, candidates, item_name)
        else:
            # ── 无参数：按类型分组，同组一次全捡，组间间隔 1 秒 ──
            groups_dict = {}
            order = []
            for obj in candidates:
                key = obj.key
                if key not in groups_dict:
                    groups_dict[key] = []
                    order.append(key)
                groups_dict[key].append(obj)
            groups = [(name, groups_dict[name]) for name in order]

            get_id = time.time()
            caller.attributes.add("_get_all_id", get_id)
            _get_all_tick(caller, groups, 0, False, get_id)

    def _get_all_batch(self, caller, candidates, item_name):
        """有参数的批量拾取：一次完成，汇总输出。

        Args:
            caller: 玩家角色。
            candidates: 候选物品列表。
            item_name: 指定物品名。
        """
        picked = {}       # {名称: 数量} 成功拾取
        has_failed = False  # 有非 get:false 原因失败的

        for target in candidates:
            # at_pre_get 钩子 — 失败则记录
            if not target.at_pre_get(caller):
                has_failed = True
                continue

            # 配方 → 放入收藏夹
            if target.attributes.get("recipe_type"):
                from .recipe_utils import get_or_create_recipe_book

                book = get_or_create_recipe_book(caller)
                if not book:
                    has_failed = True
                    continue

                # 收藏夹唯一性检查
                target_proto = target.tags.get(category="from_prototype")
                if target_proto:
                    already = False
                    for obj in book.contents:
                        obj_proto = obj.tags.get(category="from_prototype")
                        if obj_proto == target_proto:
                            already = True
                            break
                    if already:
                        has_failed = True
                        continue

                if target.move_to(book, quiet=True, move_type="get"):
                    target.at_get(caller)
                    label = f"{target.key}（配方）"
                    picked[label] = picked.get(label, 0) + 1
                else:
                    has_failed = True
                continue

            # 普通物品 → move_to 背包
            if target.move_to(caller, quiet=True, move_type="get"):
                target.at_get(caller)
                picked[target.key] = picked.get(target.key, 0) + 1
            else:
                has_failed = True

        # ── 输出 ──
        if picked:
            summary = "、".join(
                f"{k} x{c}" if c > 1 else k for k, c in picked.items()
            )
            caller.msg(f"你捡起了：{summary}。")
        else:
            caller.msg(f"你不能拿 {item_name}。")

    def _find_all_matches(self, caller, room, item_name):
        """查找所有匹配的可见物品（不过滤 get 锁）。

        Args:
            caller: 玩家角色。
            room: 当前房间。
            item_name: 指定物品名（None=全部）。

        Returns:
            list: 匹配的对象列表。
        """
        matches = []

        # 1. 房间地面（只收集 get:true 的对象）
        for obj in room.contents:
            if obj.destination or obj.has_account:
                continue
            if not obj.access(caller, "get"):
                continue
            if item_name and not self._name_matches(obj, item_name, caller):
                continue
            matches.append(obj)

        # 2. 所有对象的 contents（只收集 get:true 的）
        for container in room.contents:
            if container.destination or container.has_account:
                continue
            for obj in container.contents:
                if not obj.access(caller, "get"):
                    continue
                if item_name and not self._name_matches(obj, item_name, caller):
                    continue
                # GC-01：椰子树椰子跳过
                target_pk = obj.tags.get(category="from_prototype") or ""
                source_pk = container.tags.get(category="from_prototype") or ""
                if target_pk == "coconut" and "coconut_tree" in source_pk:
                    continue
                matches.append(obj)

        return matches

    # ── 单个拾取辅助（现有逻辑） ──

    def _get_from_source(self, caller, room, item_name, source_name):
        """从指定对象中获取物品。

        Args:
            caller: 玩家角色。
            room: 当前房间。
            item_name: 物品名称。
            source_name: 来源对象名称。

        Returns:
            目标物品对象或 None。
        """
        # 查找来源对象（房间中）
        source = caller.search(source_name, location=room, quiet=True, exact=True)
        if not source:
            source = caller.search(source_name, location=caller, quiet=True, exact=True)
        if not source:
            caller.msg(f"你没有看到 {source_name}。")
            return None
        source = source[0] if isinstance(source, list) else source

        # 在来源 contents 中查找物品
        for obj in source.contents:
            if obj.access(caller, "view") and self._name_matches(obj, item_name, caller):
                # GC-01：椰子树椰子获取限制
                target_pk = obj.tags.get(category="from_prototype") or ""
                source_pk = source.tags.get(category="from_prototype") or ""
                if target_pk == "coconut" and "coconut_tree" in source_pk:
                    caller.msg("太高了，无法采集。")
                    return None
                return obj

        caller.msg(f"{source.key}上没有 {item_name}。")
        return None

    def _get_from_anywhere(self, caller, room, item_name):
        """遍历房间 + 所有对象 contents，取第一个匹配。

        搜索顺序：房间地面 → 房间中对象的 contents（按对象顺序）。

        Args:
            caller: 玩家角色。
            room: 当前房间。
            item_name: 物品名称。

        Returns:
            目标物品对象或 None。
        """
        # 1. 房间地面
        for obj in room.contents:
            if obj.destination or obj.has_account:
                continue
            if obj.access(caller, "view") and self._name_matches(obj, item_name, caller):
                # 跳过不可拾取的固定场景物（只找可拾取物品和对象内的物品）
                if obj.access(caller, "get"):
                    return obj

        # 2. 所有对象的 contents
        for container in room.contents:
            if container.destination or container.has_account:
                continue
            for obj in container.contents:
                if obj.access(caller, "view") and self._name_matches(obj, item_name, caller):
                    # GC-01：椰子树椰子获取限制（与 _get_from_source 一致）
                    target_pk = obj.tags.get(category="from_prototype") or ""
                    source_pk = container.tags.get(category="from_prototype") or ""
                    if target_pk == "coconut" and "coconut_tree" in source_pk:
                        caller.msg("太高了，无法采集。")
                        return None
                    return obj

        caller.msg(f"这里没有 {item_name}。")
        return None

    @staticmethod
    def _name_matches(obj, name, caller):
        """检查对象名称是否匹配。

        Args:
            obj: 对象。
            name: 搜索名称。
            caller: 观察者。

        Returns:
            bool: 是否匹配。
        """
        if obj.key == name:
            return True
        if name in obj.aliases.all():
            return True
        display_name = obj.get_display_name(caller)
        if display_name == name:
            return True
        return False

    def _check_empty_shell_transform(self, source):
        """检查椰肉壳取空后是否转化为椰壳。

        仅椰肉壳（coconut_meat_shell）取走椰肉后为空时转化为椰壳。
        其他容器不发生改变。

        Args:
            source: 物品原来的容器对象。
        """
        if not source:
            return

        source_proto = source.tags.get(category="from_prototype")
        if source_proto != "coconut_meat_shell":
            return

        # 检查容器是否还有可见内容物
        has_contents = any(
            obj.access(self.caller, "view")
            for obj in source.contents
        )
        if has_contents:
            return

        # 转化为椰壳
        from evennia.prototypes.spawner import spawn
        source_location = source.location
        source_key = source.key

        shell_objs = spawn("coconut_shell")
        source.delete()

        if shell_objs and source_location:
            shell_objs[0].move_to(source_location, quiet=True)
            self.caller.msg(f"{source_key}里空了，只剩下了{shell_objs[0].key}。")

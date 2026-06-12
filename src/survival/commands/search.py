"""
v2 search 指令 — 搜索资源

搜索范围包括房间自身 resource + 房间内所有有 resource 属性的对象。
成功后物品创建在来源对象上（需求收集 §4.4）。

扩展：支持指定搜索次数，缺省为 1。
不因成功停止，耐力不足或次数用尽结束，每次间隔 1 秒。

用法：
    search                — 搜索 1 次
    search <次数>          — 连续搜索 N 次
    search <对象>          — 搜索指定对象 1 次
    search <次数> <对象>    — 对指定对象搜索 N 次

详见：docs/设计文档/解决饥渴_v2/详细设计/指令实现.md
详见：docs/设计文档/石刃业务闭环/详细设计/指令修改.md
"""

import random

from evennia.prototypes.spawner import spawn
from evennia.utils.utils import delay

from .base import SurvivalCommand
from .drying_timer import attach_drying_timer
from ..scripts.coconut_drop import attach_coconut_drop_timer


# ── 模块级函数：供 delay() 回调，不依赖 Command 实例 ──


def _collect_targets(caller, room, target_name):
    """收集搜索目标列表。

    Args:
        caller: 玩家角色。
        room: 当前房间。
        target_name: 指定对象名（None=搜索全部来源）。

    Returns:
        list: 目标对象列表。None 表示无效目标。
    """
    if target_name:
        results = caller.search(target_name, location=room, quiet=True, exact=True)
        if not results:
            return None
        obj = results[0]
        return [obj] if obj.attributes.has("resource") else None
    else:
        targets = []
        if room.attributes.has("resource"):
            targets.append(room)
        for obj in room.contents:
            if obj.attributes.has("resource"):
                targets.append(obj)
        return targets if targets else []


def _search_once(caller, room, target_name):
    """执行一次搜索。

    Args:
        caller: 玩家角色。
        room: 当前房间。
        target_name: 指定对象名（None=搜索全部来源）。

    Returns:
        tuple: (bool 是否成功, str 提示消息)。
    """
    targets = _collect_targets(caller, room, target_name)
    if targets is None:
        return False, None

    for target in targets:
        resource_list = target.attributes.get("resource", [])
        for entry in resource_list:
            method = entry.get("method", "search")
            if method != "search":
                continue

            prototype_key = entry.get("prototype")
            chance = entry.get("chance", 1.0)
            if random.random() < chance:
                objs = spawn(prototype_key)
                if objs:
                    obj = objs[0]
                    obj.move_to(target, quiet=True)
                    attach_drying_timer(obj)
                    attach_coconut_drop_timer(obj)
                    desc = entry.get("success_desc")
                    return True, desc or f"你找到了 {obj.key}！"

    return False, None


def _get_fail_msg(caller, room, target_name):
    """获取自定义失败描述。

    Args:
        caller: 玩家角色。
        room: 当前房间。
        target_name: 指定对象名。

    Returns:
        str: 失败提示消息。
    """
    if target_name:
        targets = _collect_targets(caller, room, target_name)
        if targets:
            for target in targets:
                for entry in target.attributes.get("resource", []):
                    if entry.get("method", "search") != "search":
                        continue
                    fail_desc = entry.get("fail_desc")
                    if fail_desc:
                        return fail_desc
    return "你翻找了半天，什么也没找到。"


def _delayed_search_round(caller, room, target_name, remaining, search_id):
    """delay() 回调：执行一轮搜索。

    Args:
        caller: 玩家角色。
        room: 当前房间。
        target_name: 指定对象名。
        remaining: 剩余次数。
        search_id: 搜索会话 ID（用于检测取消）。
    """
    # 检查是否被取消（玩家发了新 search 或其他中断）
    if caller.attributes.get("_search_id") != search_id:
        return

    # 耐力不足则停止
    if caller.db.stamina < 1:
        caller.msg("你的耐力不足，停止搜索。")
        caller.attributes.remove("_search_id")
        return

    # 执行一次搜索
    success, msg = _search_once(caller, room, target_name)
    caller.db.stamina = max(0, caller.db.stamina - 1)

    if success and msg:
        caller.msg(msg)
    elif not success:
        fail_msg = _get_fail_msg(caller, room, target_name)
        caller.msg(fail_msg)

    remaining -= 1
    if remaining <= 0:
        # 次数用尽
        caller.attributes.remove("_search_id")
        return

    # 调度下一轮，间隔 1 秒
    delay(1, _delayed_search_round, caller, room, target_name, remaining, search_id)


# ── 指令类 ──


class CmdSearch(SurvivalCommand):
    """
    搜索资源（概率发现，可多试）

    用法：
      search
      search <次数>
      search <对象>
      search <次数> <对象>

    无参数时搜索房间内所有可搜索来源。
    指定次数时连续搜索，不因成功停止，耐力不足或次数用尽结束。
    每次搜索间隔 1 秒。
    """

    key = "search"
    help_category = "行动"
    stamina_cost = -1

    def func(self):
        """执行搜索。

        流程：
            mermaid:
            TD
                A[解析参数: 次数+对象名] --> B[pre_check]
                B --> C[检查耐力>=1]
                C --> D[执行第 1 次搜索]
                D --> E{还有剩余次数?}
                E -->|否| F[结束]
                E -->|是| G[delay 1秒 → _delayed_search_round]
                G --> H[检查耐力]
                H -->|不足| I[停止提示]
                H -->|足够| J[执行一次搜索]
                J --> K{还有剩余?}
                K -->|是| G
                K -->|否| F
        """
        if not self.pre_check():
            return

        caller = self.caller
        room = caller.location
        args = (self.args or "").strip()

        # ── 参数解析 ──
        count = 1
        target_name = None

        if args:
            parts = args.split()
            try:
                count = int(parts[0])
                if count < 1:
                    count = 1
                parts = parts[1:]
            except ValueError:
                pass

            if parts:
                target_name = " ".join(parts)

        # ── 检查目标有效性（无效则不开始） ──
        targets = _collect_targets(caller, room, target_name)
        if targets is None:
            caller.msg("这里没有可以搜索的东西。")
            self.apply_stamina()
            return
        if not targets:
            caller.msg("这里没有可以搜索的东西。")
            self.apply_stamina()
            return

        # ── 耐力检查（至少 1 点才能开始） ──
        if caller.db.stamina < 1:
            caller.msg("你的耐力不足以搜索。")
            return

        # ── 取消之前的搜索会话（如果有） ──
        import time
        search_id = time.time()
        caller.attributes.add("_search_id", search_id)

        # ── 执行第 1 次搜索 ──
        success, msg = _search_once(caller, room, target_name)
        caller.db.stamina = max(0, caller.db.stamina - 1)

        if success and msg:
            caller.msg(msg)
        elif not success:
            fail_msg = _get_fail_msg(caller, room, target_name)
            caller.msg(fail_msg)

        remaining = count - 1
        if remaining <= 0:
            caller.attributes.remove("_search_id")
            return
        delay(1, _delayed_search_round, caller, room, target_name, remaining, search_id)

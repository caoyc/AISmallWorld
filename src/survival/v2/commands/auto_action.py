"""
cut/chop 共用自动连续执行引擎。

玩家发起一次 cut/chop 后，按时间间隔自动循环攻防计算。
终止条件：目标耐久归零 / 工具耐久归零 / 玩家取消。
"""
import uuid
from evennia.prototypes.spawner import spawn
from evennia.utils import delay
from .drying_timer import attach_drying_timer
from survival.v2.prototypes import WEAR_MAP

# ── 常量 ──────────────────────────────────────────
AUTO_ACTION_INTERVAL = 3  # 每轮间隔（秒）


# ── 工具磨损转变 ──────────────────────────────────


def wear_tool(tool, caller):
    """dur=0 时将工具转变为磨损态。

    参照 DryingTimer 的 spawn+delete 模式，同步执行。

    Args:
        tool: dur 已归零的工具对象。
        caller: 玩家角色（用于通知）。

    Returns:
        bool: 是否成功转变。
    """
    proto_key = tool.tags.get(category="from_prototype")
    worn_key = WEAR_MAP.get(proto_key)
    if not worn_key:
        return False

    location = tool.location
    original_key = tool.key

    objs = spawn(worn_key)
    if objs:
        worn = objs[0]
        worn.move_to(location, quiet=True)
        if hasattr(location, 'has_account') and location.has_account:
            location.msg(f"你的{original_key}磨损了，变成了{worn.key}。")

    tool.delete()
    return True


def start_auto_action(caller, target, tool, action_type="cut"):
    """启动自动连续执行。

    Args:
        caller: 玩家角色
        target: 目标对象（需有 defense/hp/hp_max 属性）
        tool: 工具对象（需有 attack/dur 属性）
        action_type: "cut" 或 "chop"
    """
    task_id = str(uuid.uuid4())

    caller.db.auto_action = True
    caller.db.auto_action_type = action_type
    caller.db.auto_action_target = target
    caller.db.auto_action_tool = tool
    caller.db.auto_action_task_id = task_id
    caller.db.busy = True

    action_verb = "切割" if action_type == "cut" else "砍伐"
    caller.msg(f"你开始{action_verb}{target.key}...")

    # 首轮立即执行
    _auto_action_tick(caller, task_id)


def _auto_action_tick(caller, task_id):
    """每 AUTO_ACTION_INTERVAL 秒执行一次攻防计算。"""
    # 校验 task_id（防止取消后残留回调）
    if caller.db.auto_action_task_id != task_id:
        return

    target = caller.db.auto_action_target
    tool = caller.db.auto_action_tool
    action_type = caller.db.auto_action_type

    # 安全检查：目标或工具可能已被删除
    if not target or not tool:
        _cleanup(caller)
        caller.msg("操作目标已不存在。")
        return

    # 攻防计算
    attack = tool.attributes.get("attack", 0)
    defense = target.attributes.get("defense", 0)
    damage = max(0, attack - defense)

    # 扣减
    current_hp = target.db.hp - damage
    current_dur = tool.db.dur - 1
    target.db.hp = current_hp
    tool.db.dur = current_dur

    action_verb = "切割" if action_type == "cut" else "砍伐"

    # 检查终止条件
    if current_hp <= 0:
        _complete_action(caller, target, tool, action_type)
        return

    if current_dur <= 0:
        wear_tool(tool, caller)
        _interrupt_action(caller, f"你的{tool.key}耐久耗尽了。")
        return

    # 进度消息
    caller.msg(f"你继续{action_verb}{target.key}...（剩余耐久：{current_hp}）")

    # 调度下一轮
    delay(AUTO_ACTION_INTERVAL, _auto_action_tick, caller, task_id)


def _complete_action(caller, target, tool, action_type):
    """目标耐久归零，完成操作。"""
    if action_type == "cut":
        _complete_cut(caller, target)
    elif action_type == "chop":
        # LC-03b 实现具体逻辑
        _complete_chop(caller, target)

    _cleanup(caller)


def _complete_cut(caller, target):
    """cut 完成时的产出处理。

    1. 遍历 target resource 条目，筛选 method="cut"
    2. 每个 entry spawn 产品
    3. 检查 2x 翻倍：同产品是否有 method="search" 条目
    4. 产出物移入玩家背包
    5. target.hp 重置为 hp_max
    """
    from evennia import spawn

    resource = target.db.resource
    if not resource:
        caller.msg(f"你切割了{target.key}，但什么也没获得。")
        target.db.hp = target.db.hp_max
        return

    # 收集 method="cut" 的条目
    cut_entries = [r for r in resource if r.get("method") == "cut"]

    # 收集 method="search" 的 prototype 集合（用于 2x 判定）
    search_protos = {r.get("prototype") for r in resource if r.get("method") == "search"}

    products = []
    for entry in cut_entries:
        proto_key = entry.get("prototype")
        if not proto_key:
            continue

        # 2x 翻倍判定
        base_count = entry.get("count", 1)
        count = base_count * 2 if proto_key in search_protos else base_count

        for _ in range(count):
            obj_list = spawn(proto_key)
            if obj_list:
                obj = obj_list[0]
                obj.move_to(caller, quiet=True)
                attach_drying_timer(obj)
                products.append(obj)

    if products:
        # 按名称分组显示
        from collections import Counter
        names = Counter(obj.key for obj in products)
        items_str = "、".join(
            f"{name}×{count}" if count > 1 else name
            for name, count in names.items()
        )
        caller.msg(f"你完成了切割，获得了{items_str}。")
    else:
        caller.msg(f"你切割了{target.key}，但什么也没获得。")

    # 重置目标耐久
    target.db.hp = target.db.hp_max


def _complete_chop(caller, target):
    """chop 完成时的产出处理。

    1. 遍历 target chop_output 列表
    2. 每个 entry：检查 chance 字段
       - chance=1.0 或省略：固定产出 count 个
       - chance<1.0：按概率产出 count 个或 0 个
    3. spawn 产出物，移入 caller 背包
    4. target.hp 重置为 target.hp_max（不删除对象）
    """
    import random
    from evennia import spawn

    chop_output = target.db.chop_output
    if not chop_output:
        caller.msg(f"你砍倒了{target.key}，但没掉落什么有用的东西。")
        target.db.hp = target.db.hp_max
        return

    caller.msg(f"你砍倒了{target.key}！")
    products = []
    for entry in chop_output:
        # pick_one 组：随机选一个子条目
        if "pick_one" in entry:
            chosen = random.choice(entry["pick_one"])
            proto_key = chosen.get("prototype")
            count = chosen.get("count", 1)
            cr = chosen.get("count_range")
            if cr:
                count = random.randint(cr[0], cr[1])
        else:
            proto_key = entry.get("prototype")
            count = entry.get("count", 1)
            chance = entry.get("chance", 1.0)

            # count_range：随机数量
            cr = entry.get("count_range")
            if cr:
                count = random.randint(cr[0], cr[1])

            # 随机判定
            if chance < 1.0:
                if random.random() > chance:
                    continue  # 概率判定失败，跳过此条目

        for _ in range(count):
            obj_list = spawn(proto_key)
            if obj_list:
                obj = obj_list[0]
                obj.move_to(caller, quiet=True)
                attach_drying_timer(obj)
                products.append(obj)

    # 按名称分组显示获得物品
    if products:
        from collections import Counter
        names = Counter(obj.key for obj in products)
        items_str = "、".join(
            f"{name}×{count}" if count > 1 else name
            for name, count in names.items()
        )
        caller.msg(f"你获得了{items_str}。")
    else:
        caller.msg("但没有掉落什么有用的东西。")

    # 重置目标耐久
    target.db.hp = target.db.hp_max


def _interrupt_action(caller, reason):
    """工具耐久耗尽或其他原因中断。"""
    caller.msg(reason)
    _cleanup(caller)


def cancel_auto_action(caller):
    """取消正在执行的 auto-action。

    Returns:
        bool: 是否成功取消（True=有正在执行的操作被取消）
    """
    if not caller.db.auto_action:
        return False

    action_type = caller.db.auto_action_type
    action_verb = "切割" if action_type == "cut" else "砍伐"

    _cleanup(caller)

    caller.msg(f"你停止了{action_verb}操作。")
    return True


def _cleanup(caller):
    """清除 auto-action 所有状态。"""
    caller.db.auto_action = False
    caller.db.busy = False
    caller.db.auto_action_task_id = None
    caller.db.auto_action_target = None
    caller.db.auto_action_tool = None
    caller.db.auto_action_type = None

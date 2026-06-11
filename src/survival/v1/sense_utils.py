"""
感官指令共享工具函数
"""

from evennia.objects.objects import DefaultExit, DefaultCharacter


def _find_sense_target(caller, target):
    """查找感官感知的目标对象。

    无 target 时返回 [caller.location]（感知当前房间）。
    有 target 时搜索房间内容 + 背包中的匹配对象。
    排除 Exit 和 Character 对象。

    Args:
        caller: 角色对象。
        target (str): 目标名称，空字符串表示感知环境。

    Returns:
        list: 匹配的对象列表。无目标时为 [room]，有目标时为匹配对象列表。
    """
    if not target:
        return [caller.location]

    room = caller.location
    candidates = [
        obj for obj in room.contents
        if not isinstance(obj, (DefaultExit, DefaultCharacter))
    ] + [
        obj for obj in caller.contents
    ]
    return [obj for obj in candidates if target in obj.key]
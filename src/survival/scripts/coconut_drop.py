"""
椰子掉落计时器脚本。

附属椰子树对象，使用 Evennia 原生 interval + at_repeat() 调度，
每次触发后随机化下一次间隔（1~5 分钟）。

检查树上是否有椰子（通过 search 发现的），有则掉落一颗到树的所在房间。
椰子来源仅限树上已有的对象，不凭空生成。

注意：不通过 typeclass 的 at_object_creation 挂载脚本，
改为 spawn 后手动调用 attach_coconut_drop_timer(obj)，
参照 drying_timer 的鲁棒模式。
"""
import random

from evennia import DefaultScript

# ── 常量 ──────────────────────────────────────────
COCONUT_DROP_MIN = 60   # 最短掉落间隔（秒），1 分钟
COCONUT_DROP_MAX = 300  # 最长掉落间隔（秒），5 分钟


class CoconutDropTimer(DefaultScript):
    """椰子定时掉落计时器。附属椰子树对象运行。"""

    key = "coconut_drop_timer"
    description = "椰子定时掉落"

    def at_script_creation(self):
        """脚本创建时设定参数。"""
        self.interval = random.randint(COCONUT_DROP_MIN, COCONUT_DROP_MAX)
        self.persistent = True
        self.repeats = 0          # 无限循环
        self.start_delay = True   # 等 interval 后再首次触发

    def at_repeat(self):
        """检查树上是否有椰子，有则掉落一颗到房间。"""
        tree = self.obj
        if not tree or not tree.location:
            return

        room = tree.location

        # 查找树上的椰子对象（通过 prototype 识别）
        for obj in tree.contents:
            if obj.tags.get(category="from_prototype") == "coconut":
                obj.move_to(room, quiet=True)
                room.msg_contents("一个椰子从椰子树上掉了下来。")
                break

        # 随机化下一次间隔
        self.interval = random.randint(COCONUT_DROP_MIN, COCONUT_DROP_MAX)


def attach_coconut_drop_timer(tree):
    """给椰子树对象附加掉落计时器脚本。

    在 spawn 后手动调用，避免 spawner 事务内脚本持久化问题。

    Args:
        tree: 椰子树对象。
    """
    # 幂等：已有同名脚本则跳过
    if tree.scripts.get("coconut_drop_timer"):
        return
    tree.scripts.add(CoconutDropTimer)

"""
椰子掉落计时器脚本。

与 drying_timer 完全同模式：
附属椰子对象（不是树），到达时间后自动掉落到树的所在房间。
一次触发，无需轮询。

椰子来源：search 椰子树时 40% 概率在树上生成椰子对象。
掉落：spawn 后手动调用 attach_coconut_drop_timer(coconut)。
"""
import random

from evennia import DefaultScript

# ── 常量 ──────────────────────────────────────────
COCONUT_DROP_MIN = 60   # 最短掉落间隔（秒），1 分钟
COCONUT_DROP_MAX = 300  # 最长掉落间隔（秒），5 分钟


class CoconutDropTimer(DefaultScript):
    """椰子定时掉落计时器。附属椰子对象运行，与 DryingTimer 同模式。"""

    key = "coconut_drop_timer"
    description = "椰子定时掉落"

    def at_script_creation(self):
        """脚本创建时设定参数。"""
        self.interval = random.randint(COCONUT_DROP_MIN, COCONUT_DROP_MAX)
        self.persistent = True
        self.repeats = 1          # 执行一次，与 DryingTimer 一致
        self.start_delay = True   # 等 interval 后再首次触发

    def at_repeat(self):
        """到达掉落时间，将椰子从树移动到房间地面。"""
        coconut = self.obj
        if not coconut:
            return

        tree = coconut.location
        if not tree:
            return

        room = tree.location
        if not room:
            return

        # 椰子从树掉落到房间
        coconut.move_to(room, quiet=True)
        room.msg_contents("一个椰子从椰子树上掉了下来。")


def attach_coconut_drop_timer(coconut):
    """给椰子对象附加掉落计时器脚本。

    在 search 生成椰子后手动调用，与 attach_drying_timer() 同模式。

    Args:
        coconut: 椰子对象。
    """
    # 只对椰子对象生效
    proto_key = coconut.tags.get(category="from_prototype")
    if proto_key != "coconut":
        return

    # 只在椰子位于树上时附加（树上才有 from_prototype 包含 coconut_tree 的容器）
    container = coconut.location
    if not container:
        return
    container_pk = container.tags.get(category="from_prototype") or ""
    if "coconut_tree" not in container_pk:
        return

    # 幂等：已有同名脚本则跳过
    if coconut.scripts.get("coconut_drop_timer"):
        return
    coconut.scripts.add(CoconutDropTimer)

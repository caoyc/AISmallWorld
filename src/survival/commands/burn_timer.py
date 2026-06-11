"""
篝火燃烧计时器脚本。

附属篝火对象，周期性递减 burn_duration，
归零时自动熄灭篝火，销毁篝火对象并在房间生成草木灰。
"""
from evennia import DefaultScript, spawn

# ── 常量 ──────────────────────────────────────────
INITIAL_BURN_DURATION = 120    # 点火后初始燃烧时长（秒）
FUEL_TIME_PER_VALUE = 60       # 每单位 fuel_value 折算燃烧时长（秒）
BURN_TICK_INTERVAL = 60        # 计时器每轮递减间隔（秒）
WOOD_ASH_COUNT = 4             # 熄灭时生成的草木灰数量（篝火）
WOOD_ASH_COUNT_PERSISTENT = 8  # 熄灭时生成的草木灰数量（营火）


def extinguish_cleanup(fire, reason="篝火燃尽了，只剩下灰烬。"):
    """篝火熄灭后的收尾处理：内容物掉落到房间、通知房间、生成草木灰、销毁篝火。

    Args:
        fire: 篝火对象。
        reason: 通知消息。
    """
    room = fire.location
    if room:
        room.msg_contents(reason)
        # 内容物掉落到房间（不被篝火删除连带销毁）
        for obj in list(fire.contents):
            obj.move_to(room, quiet=True)
        # 在房间生成草木灰
        for _ in range(WOOD_ASH_COUNT):
            ash_list = spawn("wood_ash")
            if ash_list:
                ash_list[0].move_to(room, quiet=True)
    fire.delete()


class BurnTimer(DefaultScript):
    """篝火燃烧计时器。附属篝火对象运行。"""

    key = "burn_timer"
    description = "篝火燃烧计时"

    def at_script_creation(self):
        """脚本创建时设定参数。"""
        self.interval = BURN_TICK_INTERVAL
        self.persistent = True
        self.repeats = 0  # 无限循环

    def at_repeat(self):
        """每 BURN_TICK_INTERVAL 秒执行一次。"""
        fire = self.obj

        # BT-01：篝火已不处于燃烧状态（可能被外部 extinguish）
        if fire.db.fire_state != "burning":
            self.stop()
            return

        # 递减 burn_duration
        fire.db.burn_duration = max(0, fire.db.burn_duration - self.interval)

        # BT-02：burn_duration 耗尽，自动熄灭
        if fire.db.burn_duration <= 0:
            self.stop()
            if fire.attributes.get("persistent"):
                # 营火：转为 burnt_out 状态，生成草木灰×8，不销毁
                room = fire.location
                if room:
                    room.msg_contents("营火燃尽了，灰烬中还残留着余温。")
                    for obj in list(fire.contents):
                        obj.move_to(room, quiet=True)
                    for _ in range(WOOD_ASH_COUNT_PERSISTENT):
                        ash_list = spawn("wood_ash")
                        if ash_list:
                            ash_list[0].move_to(room, quiet=True)
                fire.db.fire_state = "burnt_out"
                fire.db.desc_look = fire.db.desc_burnt_out or "一堆灰烬残留在石块围成的火塘中。"
                fire.db.desc_smell = fire.db.desc_smell_burnt_out or fire.db.desc_smell_extinguished
            else:
                extinguish_cleanup(fire)

"""
角色 Typeclass — SurvivalCharacterV2

带饥渴系统 + 耐力系统的角色，继承 DefaultCharacter。

详见：docs/设计文档/解决饥渴_v2/详细设计/角色与耐力.md
"""

import time

from evennia.objects.objects import DefaultCharacter
from evennia.scripts.tickerhandler import TICKER_HANDLER

from survival.commands.cmdset import SurvivalV2CmdSet


class SurvivalCharacter(DefaultCharacter):
    """带饥渴系统的角色基类。

    每隔 TICK_INTERVAL 秒自动递减 hunger 和 thirst 属性，
    根据状态分段向玩家发送提示消息。
    """

    TICK_INTERVAL = 30
    HUNGER_DECAY = 1
    THIRST_DECAY = 2

    STATUS_THRESHOLDS = [
        {
            "min": 80,
            "max": 100,
            "label": "正常",
            "hunger_msg": None,
            "thirst_msg": None,
            "interval": 0,
        },
        {
            "min": 50,
            "max": 79,
            "label": "轻度",
            "hunger_msg": "你感到有些饥饿。",
            "thirst_msg": "你感到有些口渴。",
            "interval": 300,
        },
        {
            "min": 20,
            "max": 49,
            "label": "中度",
            "hunger_msg": "你很饿了，肚子咕咕直叫。",
            "thirst_msg": "你很渴，嘴唇干裂，喉咙像火烧。",
            "interval": 120,
        },
        {
            "min": 0,
            "max": 19,
            "label": "严重",
            "hunger_msg": "你饿得头晕眼花，四肢无力。",
            "thirst_msg": "你渴得快要昏过去了，视线开始模糊。",
            "interval": 60,
        },
    ]

    def at_object_creation(self):
        super().at_object_creation()
        self.db.hunger = 100
        self.db.thirst = 100
        self.db.hunger_last_warn = 0.0
        self.db.thirst_last_warn = 0.0

    def at_post_puppet(self, **kwargs):
        super().at_post_puppet(**kwargs)
        TICKER_HANDLER.add(
            self.TICK_INTERVAL,
            self.tick_hunger_thirst,
            idstring=str(self.dbref),
        )

    def at_post_unpuppet(self, account=None, session=None, **kwargs):
        TICKER_HANDLER.remove(
            self.TICK_INTERVAL,
            self.tick_hunger_thirst,
            idstring=str(self.dbref),
        )
        super().at_post_unpuppet(account=account, session=session, **kwargs)

    def tick_hunger_thirst(self, **kwargs):
        self.db.hunger = max(0, self.db.hunger - self.HUNGER_DECAY)
        self.db.thirst = max(0, self.db.thirst - self.THIRST_DECAY)
        now = time.time()
        for threshold in self.STATUS_THRESHOLDS:
            if threshold["min"] <= self.db.hunger <= threshold["max"]:
                if threshold["hunger_msg"] and threshold["interval"] > 0:
                    elapsed = now - self.db.hunger_last_warn
                    if elapsed >= threshold["interval"]:
                        self.msg(threshold["hunger_msg"])
                        self.db.hunger_last_warn = now
                break
        for threshold in self.STATUS_THRESHOLDS:
            if threshold["min"] <= self.db.thirst <= threshold["max"]:
                if threshold["thirst_msg"] and threshold["interval"] > 0:
                    elapsed = now - self.db.thirst_last_warn
                    if elapsed >= threshold["interval"]:
                        self.msg(threshold["thirst_msg"])
                        self.db.thirst_last_warn = now
                break

    def get_status_label(self, value):
        for threshold in self.STATUS_THRESHOLDS:
            if threshold["min"] <= value <= threshold["max"]:
                return threshold["label"]
        return "未知"

    def get_status_display(self):
        hunger_label = self.get_status_label(self.db.hunger)
        thirst_label = self.get_status_label(self.db.thirst)
        return (
            f"--- 状态 ---\n"
            f"饥饿: {self.db.hunger} [{hunger_label}]\n"
            f"口渴: {self.db.thirst} [{thirst_label}]"
        )

    def restore_hunger(self, amount):
        self.db.hunger = min(100, self.db.hunger + amount)

    def restore_thirst(self, amount):
        self.db.thirst = min(100, self.db.thirst + amount)

    def increase_thirst(self, amount):
        self.db.thirst = max(0, self.db.thirst - amount)


class SurvivalCharacterV2(SurvivalCharacter):
    """v2 生存角色，饥渴 + 耐力系统。

    Attributes:
        db.stamina (int): 当前耐力值（0~100），默认 100。
        db.stamina_last_warn (float): 上次耐力提示时间戳。
        db.resting (bool): 是否处于休息状态。
        db.rest_start_time (float): 本次休息开始时间戳。
        db.rest_bonus (float): 休息恢复效率加成。
        db.rest_last_settle (float): 上次结算恢复的时间戳。
    """

    # 持续恢复常量
    RECOVERY_UNIT_TIME = 1     # 恢复公式中的单位时间（秒）
    RECOVERY_PER_UNIT = 1      # 单位时间恢复的基础耐力值

    def at_object_creation(self):
        """角色创建时初始化耐力属性，挂载 SurvivalV2CmdSet。"""
        super().at_object_creation()
        self.db.stamina = 100
        self.db.stamina_last_warn = 0.0
        self.db.resting = False
        self.db.rest_start_time = None
        self.db.rest_bonus = 0.0
        self.db.rest_last_settle = None
        # 用 v2 指令集替换 v1
        self.cmdset.add(SurvivalV2CmdSet, persistent=True)

    def at_post_move(self, source_location, move_type="move", **kwargs):
        """移动后自动 look + map，驱动跟随者。"""
        if self.location and self.location.access(self, "view"):
            look_result = self.at_look(self.location)
            # 追加地图
            from survival.commands.map import _render_map
            exits_info = [
                (ex.key, ex.destination.key)
                for ex in self.location.exits
                if ex.destination
            ]
            map_text = _render_map(self.location.key, exits_info)
            self.msg(text=(f"{look_result}\n\n{map_text}\n", {"type": "look"}))

        # 驱动跟随者：被跟随者移动后，检查并移动跟随者
        followers = self.db.followers
        if followers:
            for follower in list(followers):
                # 跟随者不在旧房间？跳过（可能已经自己移动了）
                if follower.location != source_location:
                    continue
                # 跟随者有 auto_action？跳过
                if follower.db.auto_action:
                    action_type = follower.db.auto_action_type or "操作"
                    follower.msg(f"你正在{action_type}，无法跟随 {self.key}。")
                    continue
                # 跟随者耐力不足？跳过
                if follower.db.stamina < 1:
                    follower.msg(f"你太累了，无法跟随 {self.key}。")
                    continue
                # 执行跟随移动
                follower.move_to(self.location, move_type="follow")
                follower.db.stamina = max(0, follower.db.stamina - 1)

    def restore_stamina(self, amount):
        """恢复耐力值，钳制在 0~100。

        Args:
            amount (int): 恢复量。
        """
        self.db.stamina = max(0, min(100, self.db.stamina + amount))

    def tick_hunger_thirst(self, **kwargs):
        """每 tick 执行：v1 饥渴衰减 + 耐力逻辑。

        流程：
            mermaid:
            TD
                A[tick_hunger_thirst] --> B[v1 饥渴衰减]
                B --> C{resting?}
                C -->|否| D{hunger<30 或 thirst<30?}
                C -->|是| G[跳过耐力消耗]
                D -->|是| E[stamina -= 1]
                D -->|否| G
                E --> F[check_stamina_threshold]
                G --> F
        """
        super().tick_hunger_thirst(**kwargs)
        self._tick_stamina()

    def _settle_recovery(self):
        """结算持续恢复的耐力值。

        在 _tick_stamina 中按 tick 调用，或在 pre_check 打断时调用，
        或在 status 指令中查看状态前调用（重置计时，不打断休息）。
        计算自上次结算以来的增量恢复值，取整后恢复。
        始终重置 rest_last_settle，确保后续恢复从当前时刻重新计算。
        """
        import time
        now = time.time()
        last = self.db.rest_last_settle
        if last is None:
            return

        elapsed = now - last
        bonus = self.db.rest_bonus or 0.0
        recovery = (elapsed / self.RECOVERY_UNIT_TIME
                    * self.RECOVERY_PER_UNIT
                    * (1.0 + bonus))

        int_recovery = int(recovery)
        if int_recovery >= 1:
            self.restore_stamina(int_recovery)
        self.db.rest_last_settle = now

    def _tick_stamina(self):
        """耐力 tick 逻辑：持续恢复 + 帐篷保护 + 饥渴消耗 + 分档提示。"""
        room = self.location

        if self.db.resting:
            # ── 持续恢复 ──
            self._settle_recovery()
            # 沿用：resting 时跳过饥渴导致的耐力衰减
            # resting 时不提示耐力警示信息（澄清3）
            return

        # ── R40 帐篷自动保护 ──
        has_tent = False
        if room:
            for obj in room.contents:
                if obj.tags.get(category="from_prototype") == "tent":
                    has_tent = True
                    break

        # 无帐篷时，饥渴低则消耗耐力
        if not has_tent:
            if self.db.hunger < 30 or self.db.thirst < 30:
                self.db.stamina = max(0, self.db.stamina - 1)

        self._check_stamina_threshold()

    def _check_stamina_threshold(self):
        """检查耐力分档并按间隔发送提示。"""
        import time

        stamina = self.db.stamina
        now = time.time()

        for threshold_min, msg, interval in self.STAMINA_THRESHOLDS:
            if stamina >= threshold_min:
                if msg and interval > 0:
                    elapsed = now - self.db.stamina_last_warn
                    if elapsed >= interval:
                        self.msg(msg)
                        self.db.stamina_last_warn = now
                break

    # 耐力分档配置
    STAMINA_THRESHOLDS = [
        (80, None, 0),                                       # 80~100: 无提示
        (50, "你感到有些疲惫。", 300),                        # 50~79: 5分钟
        (20, "你很累，四肢沉重。", 120),                      # 20~49: 2分钟
        (0, "你已经筋疲力尽，一步都走不动了。", 60),          # 0~19: 1分钟
    ]

    def get_status_display(self):
        """返回完整状态信息字符串（含耐力）。

        Returns:
            str: 格式化的状态信息。
        """
        hunger_label = self.get_status_label(self.db.hunger)
        thirst_label = self.get_status_label(self.db.thirst)
        stamina_label = self._get_stamina_label()
        return (
            f"--- 状态 ---\n"
            f"饥饿: {self.db.hunger} [{hunger_label}]\n"
            f"口渴: {self.db.thirst} [{thirst_label}]\n"
            f"耐力: {self.db.stamina} [{stamina_label}]"
        )

    def _get_stamina_label(self):
        """根据耐力值返回状态标签。

        Returns:
            str: 状态标签。
        """
        for threshold_min, _, _ in self.STAMINA_THRESHOLDS:
            if self.db.stamina >= threshold_min:
                labels = {80: "充沛", 50: "轻度疲劳", 20: "疲劳", 0: "精疲力竭"}
                return labels.get(threshold_min, "未知")
        return "未知"

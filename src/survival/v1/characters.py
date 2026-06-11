"""
角色扩展 - 带饥渴系统的角色 Typeclass

提供 SurvivalCharacter，继承 DefaultCharacter，添加饥饿/口渴递减机制。

详见：docs/设计文档/解决饥饿/详细设计/角色扩展详细设计.md
"""

import time

from evennia.scripts.tickerhandler import TICKER_HANDLER
from evennia.objects.objects import DefaultCharacter

from .cmdset_survival import SurvivalCmdSet


class SurvivalCharacter(DefaultCharacter):
    """带饥渴系统的角色。

    每隔 TICK_INTERVAL 秒自动递减 hunger 和 thirst 属性，
    根据状态分段向玩家发送提示消息。

    Constants:
        TICK_INTERVAL (int): tick 间隔秒数。
        HUNGER_DECAY (int): 每 tick 饥饿递减量。
        THIRST_DECAY (int): 每 tick 口渴递减量。
        STATUS_THRESHOLDS (list[dict]): 状态分段配置。
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
        """初始化饥渴属性，挂载 SurvivalCmdSet。

        在角色首次创建时调用，设置初始属性值并添加生存指令集。
        """
        super().at_object_creation()
        self.db.hunger = 100
        self.db.thirst = 100
        self.db.hunger_last_warn = 0.0
        self.db.thirst_last_warn = 0.0
        self.cmdset.add(SurvivalCmdSet, persistent=True)

    def at_post_puppet(self, **kwargs):
        """启动饥渴递减 ticker。

        角色被玩家控制时调用，注册定时回调。

        Args:
            **kwargs: Evennia 传递的额外参数。
        """
        super().at_post_puppet(**kwargs)
        TICKER_HANDLER.add(
            self.TICK_INTERVAL,
            self.tick_hunger_thirst,
            idstring=str(self.dbref),
        )

    def at_post_unpuppet(self, account=None, session=None, **kwargs):
        """停止饥渴递减 ticker。

        角色被玩家释放时调用，取消定时回调。

        Args:
            account: 玩家账户对象。
            session: 会话对象。
            **kwargs: Evennia 传递的额外参数。
        """
        TICKER_HANDLER.remove(
            self.TICK_INTERVAL,
            self.tick_hunger_thirst,
            idstring=str(self.dbref),
        )
        super().at_post_unpuppet(account=account, session=session, **kwargs)

    def tick_hunger_thirst(self, **kwargs):
        """每个 tick 执行：递减饥渴值 + 检查状态段 + 发送提示。

        流程：
            mermaid:
            TD
                A[tick_hunger_thirst] --> B[递减 hunger, clamp 0~100]
                B --> C[递减 thirst, clamp 0~100]
                C --> D{检查 hunger 状态段}
                D -->|有提示文案且达到间隔| E[msg 发送饥饿提示]
                D -->|无提示或未达间隔| F[跳过]
                E --> G{检查 thirst 状态段}
                F --> G
                G -->|有提示文案且达到间隔| H[msg 发送口渴提示]
                G -->|无提示或未达间隔| I[结束]
                H --> I
        """
        # 递减饥渴值
        self.db.hunger = max(0, self.db.hunger - self.HUNGER_DECAY)
        self.db.thirst = max(0, self.db.thirst - self.THIRST_DECAY)

        now = time.time()

        # 检查饥饿状态段
        for threshold in self.STATUS_THRESHOLDS:
            if threshold["min"] <= self.db.hunger <= threshold["max"]:
                if threshold["hunger_msg"] and threshold["interval"] > 0:
                    elapsed = now - self.db.hunger_last_warn
                    if elapsed >= threshold["interval"]:
                        self.msg(threshold["hunger_msg"])
                        self.db.hunger_last_warn = now
                break

        # 检查口渴状态段
        for threshold in self.STATUS_THRESHOLDS:
            if threshold["min"] <= self.db.thirst <= threshold["max"]:
                if threshold["thirst_msg"] and threshold["interval"] > 0:
                    elapsed = now - self.db.thirst_last_warn
                    if elapsed >= threshold["interval"]:
                        self.msg(threshold["thirst_msg"])
                        self.db.thirst_last_warn = now
                break

    def get_status_label(self, value):
        """根据数值返回状态段标签。

        Args:
            value (int): 饥饿或口渴值（0~100）。

        Returns:
            str: 状态段标签（"正常"/"轻度"/"中度"/"严重"）。
        """
        for threshold in self.STATUS_THRESHOLDS:
            if threshold["min"] <= value <= threshold["max"]:
                return threshold["label"]
        return "未知"

    def get_status_display(self):
        """返回完整状态信息字符串（status 指令调用）。

        Returns:
            str: 格式化的状态信息。

        输出格式::

            --- 状态 ---
            饥饿: 85 [正常]
            口渴: 42 [中度]
        """
        hunger_label = self.get_status_label(self.db.hunger)
        thirst_label = self.get_status_label(self.db.thirst)
        return (
            f"--- 状态 ---\n"
            f"饥饿: {self.db.hunger} [{hunger_label}]\n"
            f"口渴: {self.db.thirst} [{thirst_label}]"
        )

    def restore_hunger(self, amount):
        """恢复饥饿值（eat 调用）。

        Args:
            amount (int): 恢复量。
        """
        self.db.hunger = min(100, self.db.hunger + amount)

    def restore_thirst(self, amount):
        """恢复口渴值（drink 淡水调用）。

        Args:
            amount (int): 恢复量。
        """
        self.db.thirst = min(100, self.db.thirst + amount)

    def increase_thirst(self, amount):
        """加重口渴值（drink 咸水调用）。

        Args:
            amount (int): 加重量。
        """
        self.db.thirst = max(0, self.db.thirst - amount)

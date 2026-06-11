"""
v2 rest 指令 — 持续恢复耐力

进入持续恢复状态，按公式随时间累积恢复耐力。
帐篷和床提供恢复效率增益（stamina_bonus），两者叠加。
被动作类指令打断时，结算已累积的恢复值。

详见：docs/设计文档/热带环礁岛基础生存闭环/详细设计/v5/LC-02/LC-02详细设计.md
"""
import time

from .base import SurvivalCommand


class CmdRest(SurvivalCommand):
    """
    休息，持续恢复耐力

    用法：
      rest

    坐下休息，持续恢复耐力。
    在帐篷内休息效率更高，有床时效率进一步提升。
    """

    key = "rest"
    help_category = "生存"
    stamina_cost = 0
    rest_interrupt = False

    def func(self):
        """进入持续恢复状态。"""
        caller = self.caller
        room = caller.location

        # RS-02：不在任何地方
        if not room:
            caller.msg("你不在任何地方。")
            return

        # RS-01：已在休息中
        if caller.db.resting:
            caller.msg("你已经在休息了。")
            return

        # ── 检测帐篷和床 ──
        # 床在帐篷 contents 内，需搜索两层
        bonus = 0.0
        in_tent = False
        has_bed = False
        for obj in room.contents:
            proto_key = obj.tags.get(category="from_prototype")
            if proto_key == "tent":
                bonus += obj.attributes.get("stamina_bonus", 0.0)
                in_tent = True
                # 检查帐篷内部是否有床
                for inner in obj.contents:
                    inner_key = inner.tags.get(category="from_prototype")
                    if inner_key == "leaf_bed":
                        bonus += inner.attributes.get("stamina_bonus", 0.0)
                        has_bed = True
            elif proto_key == "leaf_bed":
                # 床直接在房间里（不在帐篷内）
                bonus += obj.attributes.get("stamina_bonus", 0.0)
                has_bed = True

        # ── 设置休息状态 ──
        now = time.time()
        caller.db.resting = True
        caller.db.rest_start_time = now
        caller.db.rest_bonus = bonus
        caller.db.rest_last_settle = now

        # ── 提示消息 ──
        if in_tent and has_bed:
            caller.msg("你躺在帐篷里的床上，进入深度休息。")
        elif in_tent:
            caller.msg("你在帐篷里躺下休息，体力恢复得很快。")
        else:
            caller.msg("你坐下来休息，恢复了一些体力。")

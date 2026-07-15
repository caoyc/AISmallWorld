"""
捕鱼笼对象级指令（LC-04 重构）

原 CmdFish 全局指令已移除，改为定义在 fish_trap 对象上的对象级指令：
- settrap：设置捕鱼笼（需在水域附近）
- collect：收取渔获（概率抽取机制）
"""

import time
import random
from collections import Counter

from evennia import Command, CmdSet
from evennia.prototypes.spawner import spawn

# ── 常量 ──
FISH_INTERVAL = 1 * 60  # 1 分钟（现实时间）


# ── 对象级 CmdSet ──

class FishTrapCmdSet(CmdSet):
    """捕鱼笼对象级指令集。"""
    key = "fish_trap_cmdset"
    priority = 0
    mergetype = "Union"

    def at_cmdset_creation(self):
        self.add(CmdSetTrap())
        self.add(CmdCollect())


# ── 设置捕鱼笼 ──

class CmdSetTrap(Command):
    """设置捕鱼笼（对象级指令）"""
    key = "settrap"
    help_category = "行动"
    locks = "cmd:all()"

    def func(self):
        caller = self.caller
        trap = self.obj

        # 前置检查：捕鱼笼状态
        if trap.db.trap_state == "set":
            caller.msg("捕鱼笼已经设置了。")
            return

        # 前置检查：捕鱼笼在背包中
        if trap.location != caller:
            caller.msg("你需要先把捕鱼笼拿在手中。")
            return

        # 前置检查：忙碌状态
        if caller.db.busy:
            caller.msg("你正在执行其他操作。")
            return

        # 前置检查：查找水域对象
        room = caller.location
        water_source = None
        for obj in room.contents:
            if obj == trap:
                continue
            fish_resource = obj.attributes.get("fish_resource", None)
            if fish_resource and len(fish_resource) > 0:
                water_source = obj
                break

        if not water_source:
            caller.msg("这里附近没有适合设置捕鱼笼的水域。")
            return

        # 执行设置
        trap.db.trap_state = "set"
        trap.db.set_time = time.time()
        trap.db.set_room_water = water_source.tags.get(category="from_prototype")
        trap.move_to(room, quiet=True)

        caller.msg(f"你将{trap.key}放入{water_source.key}附近的水中，等待鱼儿上钩。")


# ── 收取渔获 ──

class CmdCollect(Command):
    """收取渔获（对象级指令）"""
    key = "collect"
    help_category = "行动"
    locks = "cmd:all()"

    def func(self):
        caller = self.caller
        trap = self.obj

        # 前置检查：捕鱼笼状态
        if trap.db.trap_state != "set":
            caller.msg("捕鱼笼还没有设置。")
            return

        # 前置检查：捕鱼笼在房间中
        if trap.location != caller.location:
            caller.msg("这里没有已设置的捕鱼笼。")
            return

        # 前置检查：忙碌状态
        if caller.db.busy:
            caller.msg("你正在执行其他操作。")
            return

        # 计算抽取次数
        set_time = trap.db.set_time or 0
        elapsed = time.time() - set_time
        draw_count = int(elapsed // FISH_INTERVAL)

        if draw_count <= 0:
            caller.msg(f"你收起{trap.key}，但这次什么都没有捕获。")
            # 即使无渔获也重置捕鱼笼
            self._reset_trap(trap, caller)
            return

        # 查找水域对象获取 resource
        room = caller.location
        water_source = None
        set_room_water = trap.db.set_room_water

        if set_room_water:
            for obj in room.contents:
                if obj.tags.get(category="from_prototype") == set_room_water:
                    water_source = obj
                    break

        # 获取 fish_resource 列表
        if water_source:
            resource_list = water_source.attributes.get("fish_resource", [])
        else:
            # fallback：水域对象可能已消失，使用退化策略
            resource_list = [{"prototype": "shellfish_item", "chance": 0.3}]

        # 概率抽取
        catches = []
        for _ in range(draw_count):
            for entry in resource_list:
                chance = entry.get("chance", 0.3)
                if random.random() < chance:
                    proto_key = entry.get("prototype")
                    catches.append(proto_key)
                    break  # 每次只抽一种

        # 产出水产
        if catches:
            for proto_key in catches:
                objs = spawn(proto_key)
                if objs:
                    catch = objs[0]
                    if caller.contents:  # 检查背包是否可接收
                        catch.move_to(caller, quiet=True)
                    else:
                        catch.move_to(room, quiet=True)
                        caller.msg("背包已满，渔获放在了地上。")
            catch_names = []
            for proto_key, count in Counter(catches).items():
                objs_in_inv = [o for o in caller.contents
                               if o.tags.get(category="from_prototype") == proto_key]
                if objs_in_inv:
                    catch_names.append(f"{objs_in_inv[-1].key}×{count}")
            caller.msg(f"你收起{trap.key}，收获了：\n{'\n'.join(catch_names)}")
        else:
            caller.msg(f"你收起{trap.key}，但这次什么都没有捕获。")

        # 重置捕鱼笼
        self._reset_trap(trap, caller)

    @staticmethod
    def _reset_trap(trap, caller):
        """重置捕鱼笼状态并移回玩家背包。"""
        trap.db.trap_state = "empty"
        trap.db.set_time = None
        trap.db.set_room_water = None
        trap.move_to(caller, quiet=True)

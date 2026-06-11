"""
v2 eat 指令 — 吃食物

前置检查 hunger 是否满值，消费后处理 becomes_on_consume 替换或删除食物对象。

详见：docs/设计文档/解决饥渴_v2/详细设计/指令实现.md
详见：docs/设计文档/石刃业务闭环/详细设计/指令修改.md
"""

from .base import SurvivalCommand


class CmdEat(SurvivalCommand):
    """
    吃食物

    用法：
      eat <食物>

    吃掉背包中的食物，恢复饥饿值。
    """

    key = "eat"
    help_category = "生存"
    stamina_cost = 0
    rest_interrupt = False

    def func(self):
        """执行吃食物。

        流程：
            mermaid:
            TD
                A[pre_check] --> B{hunger >= 100?}
                B -->|是| C[你不饿]
                B -->|否| D[查找 can_eat 物品]
                D --> E{找到?}
                E -->|否| F[没有可以吃的东西]
                E -->|是| G[restore_hunger]
                G --> H[delete 物品]
                H --> I[提示]
        """
        if not self.pre_check():
            return

        caller = self.caller

        # 前置检查：hunger 已满
        if caller.db.hunger >= 100:
            caller.msg("你不饿。")
            return

        # 查找可吃物品（房间 + 背包）
        target, message = self._find_edible(caller)
        if not target:
            if message:
                caller.msg(message)
            return

        # 恢复饥饿值
        hunger_restore = target.attributes.get("hunger_restore", 0)
        caller.restore_hunger(hunger_restore)

        # 恢复耐力（鲜美的产出物）
        stamina_restore = target.attributes.get("stamina_restore", 0)
        if stamina_restore > 0:
            caller.restore_stamina(stamina_restore)

        # 双消费检查（机制三：汤类 embedded_vessel）
        embedded_vessel = target.attributes.get("embedded_vessel")
        if embedded_vessel:
            # 检查是否已经吃过
            if target.attributes.get("eat_consumed"):
                caller.msg(f"{target.key}已经吃完了。")
                return
            # 标记食用完成
            target.attributes.add("eat_consumed", True)
            # 检查饮用是否也完成
            if target.attributes.get("drink_consumed"):
                # 全部用尽 → 销毁并返还椰壳
                caller.msg(f"你吃掉了 {target.key}，饥饿值恢复 {hunger_restore}。")
                original_location = target.location
                target.delete()
                from evennia.prototypes.spawner import spawn
                objs = spawn(embedded_vessel)
                if objs:
                    objs[0].move_to(original_location, quiet=True)
                    caller.msg(f"椰壳已返还。")
            else:
                # 仅食用完成，汤仍存在
                caller.msg(f"你吃了 {target.key}中的食物，饥饿值恢复 {hunger_restore}。汤中还有饮品。")
            return

        # 标准消费后处理：becomes_on_consume 替换 或 直接删除
        caller.msg(f"你吃掉了 {target.key}，饥饿值恢复 {hunger_restore}。")
        becomes = target.attributes.get("becomes_on_consume")
        original_location = target.location
        original_contents = list(target.contents)
        target.delete()
        if becomes:
            from evennia.prototypes.spawner import spawn
            objs = spawn(becomes)
            if objs:
                new_obj = objs[0]
                new_obj.move_to(original_location, quiet=True)
                for item in original_contents:
                    item.move_to(new_obj, quiet=True)

    def _find_edible(self, caller):
        """在房间和背包中查找可吃物品。

        Args:
            caller: 角色对象。

        Returns:
            tuple: (target对象或None, 提示消息或None)
            - (target, None): 找到可吃物品
            - (None, message): 未找到，message 为应显示的提示
        """
        item_name = self.args.strip() if self.args else ""

        if item_name:
            # 第一次搜索：房间 + 背包中的 edible candidates（quiet=True）
            candidates = self._get_edible_candidates(caller)
            results = caller.search(
                item_name,
                location=caller.location,
                candidates=candidates,
                quiet=True,
                exact=True,
            )
            if results:
                obj = results[0] if isinstance(results, list) else results
                if obj.attributes.get("can_eat"):
                    return (obj, None)
                if obj.attributes.get("cut_into"):
                    return (None, f"你不能直接吃 {obj.key}，需要先用切割工具切开。")

            # 第二次搜索：背包（quiet=True）
            results = caller.search(item_name, location=caller, quiet=True, exact=True)
            if results:
                obj = results[0] if isinstance(results, list) else results
                if obj.attributes.get("cut_into"):
                    return (None, f"你不能直接吃 {obj.key}，需要先用切割工具切开。")
                if obj.attributes.get("can_eat"):
                    return (obj, None)
                # 区分：物品存在但不能吃
                return (None, f"{obj.key}不能吃。")

            # 物品不存在
            return (None, f"你没有 {item_name}。")

        # 无参数：找第一个可吃的
        for candidate in self._get_edible_candidates(caller):
            if candidate.attributes.get("can_eat"):
                return (candidate, None)
        return (None, "这里没有可以吃的东西。")

    def _get_edible_candidates(self, caller):
        """获取所有可吃候选物品（房间 + 背包）。

        Args:
            caller: 角色对象。

        Returns:
            list: 候选物品列表。
        """
        candidates = []
        # 房间内
        for obj in caller.location.contents:
            if obj != caller and obj.attributes.get("can_eat"):
                candidates.append(obj)
        # 背包
        for obj in caller.contents:
            if obj.attributes.get("can_eat"):
                candidates.append(obj)
        return candidates

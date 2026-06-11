"""
v2 drink 指令 — 喝饮品或饮水

无参数时查找资源来源对象（水源），有参数时查找可喝物品。
前置检查 thirst 是否满值，消费后处理 becomes_on_consume 替换或删除物品。

新增能力：
  - 椰子 drink（需吸管）
  - 容器饮用（从椰壳水壶等容器中喝）
  - vessel_only 支持（脏水等必须用容器盛装才能喝）

详见：docs/设计文档/热带环礁岛基础生存闭环/详细设计/v1/基础生存闭环详细设计.md
"""

from .base import SurvivalCommand


class CmdDrink(SurvivalCommand):
    """
    喝饮品

    用法：
      drink
      drink <饮品>
      drink <水源>

    无参数时自动在背包和房间中寻找可饮品。
    """

    key = "drink"
    help_category = "生存"
    stamina_cost = 0
    rest_interrupt = False

    def func(self):
        """执行喝操作。

        流程：
            mermaid:
            TD
                A[pre_check] --> B{thirst >= 100?}
                B -->|是| C[你不渴]
                B -->|否| D{有参数?}
                D -->|无| E[自动查找可喝源]
                D -->|有| F[按名称查找]
                F --> G{找到?}
                G -->|否| H[没找到]
                G -->|是| I{类型判断}
                I -->|coconut| J[椰子drink需吸管]
                I -->|container| K[容器饮用]
                I -->|can_drink物品| L[物品饮用]
                I -->|resource来源| M[来源饮用]
                I -->|cut_into| N[需先切开]
                E --> O{找到?}
                O -->|否| P[没有可以喝的]
                O -->|是| I
        """
        if not self.pre_check():
            return

        caller = self.caller

        # 前置检查：thirst 已满
        if caller.db.thirst >= 100:
            caller.msg("你不渴。")
            return

        if self.args:
            target_name = self.args.strip()

            # 先搜背包
            target = self._search_in(caller, target_name, caller)

            if not target:
                # 再搜房间
                target = self._search_in(caller, target_name, caller.location)

            if not target:
                caller.msg(f"你没有看到 {target_name}。")
                return

            # 类型分发
            proto_key = target.tags.get(category="from_prototype")
            if proto_key == "coconut":
                # 椰子 drink（需吸管）
                self._drink_coconut(caller, target)
            elif proto_key == "travelers_palm":
                # 旅人蕉 drink（需吸管，可重复饮用）
                self._drink_travelers_palm(caller, target)
            elif target.attributes.get("can_drink"):
                # 物品饮用（优先于容器：cut_coconut 同时是容器和可饮品）
                self._drink_item(caller, target)
            elif target.attributes.get("is_container"):
                # 容器饮用
                self._drink_from_container(caller, target)
            elif target.attributes.has("resource"):
                self._drink_from_source(caller, target)
            elif target.attributes.get("cut_into"):
                caller.msg(f"你不能直接喝 {target.key}，需要先用切割工具切开。")
            else:
                caller.msg("这里没有可以喝的东西。")
        else:
            # 无参数：优先级自动查找
            from evennia.prototypes.prototypes import search_prototype as _search_proto

            candidates = []

            # ── 扫描所有可饮品 ──

            # 1. 房间/房间对象的 resource 来源
            room = caller.location
            if room.attributes.has("resource"):
                quality = self._water_quality(room.attributes.get("resource", []))
                if quality:
                    candidates.append(("resource", room, quality))
            for obj in room.contents:
                if obj != caller and obj.attributes.has("resource"):
                    quality = self._water_quality(obj.attributes.get("resource", []))
                    if quality:
                        candidates.append(("resource", obj, quality))

            # 2. 旅人蕉（需吸管）
            for obj in room.contents:
                if obj != caller and obj.tags.get(category="from_prototype") == "travelers_palm":
                    if self._has_straw(caller):
                        candidates.append(("travelers_palm", obj, "fresh"))

            # 3. 椰子（需吸管）
            for obj in room.contents:
                if obj != caller and obj.tags.get(category="from_prototype") == "coconut":
                    if self._has_straw(caller) and obj.attributes.get("thirst_restore", 0) > 0:
                        candidates.append(("coconut", obj, "fresh"))
            for obj in caller.contents:
                if obj.tags.get(category="from_prototype") == "coconut":
                    if self._has_straw(caller) and obj.attributes.get("thirst_restore", 0) > 0:
                        candidates.append(("coconut", obj, "fresh"))

            # 4. 可喝物品（can_drink）— 房间 + 背包
            for obj in room.contents:
                if obj != caller and obj.attributes.get("can_drink"):
                    tr = obj.attributes.get("thirst_restore", 0)
                    quality = "salt" if tr < 0 else "fresh"
                    candidates.append(("drinkable", obj, quality))
            for obj in caller.contents:
                if obj.attributes.get("can_drink"):
                    tr = obj.attributes.get("thirst_restore", 0)
                    quality = "salt" if tr < 0 else "fresh"
                    candidates.append(("drinkable", obj, quality))

            # 5. 填充容器
            for obj in caller.contents:
                if obj.attributes.get("is_container") and obj.attributes.get("vessel_content") is not None:
                    content_key = obj.attributes.get("vessel_content")
                    quality = self._water_quality_by_proto(content_key)
                    if quality:
                        candidates.append(("container", obj, quality))

            # ── 优先级排序 & 处理 ──

            # 分组：先淡水，再脏水，最后咸水
            fresh = [c for c in candidates if c[2] == "fresh"]
            dirty = [c for c in candidates if c[2] == "dirty"]
            salt = [c for c in candidates if c[2] == "salt"]

            # Tier 1: 非消耗类淡水
            tier1_order = {"resource": 0, "travelers_palm": 1}
            tier1 = [c for c in fresh if c[0] in tier1_order]
            tier1.sort(key=lambda c: tier1_order[c[0]])

            # Tier 2: 消耗类淡水
            tier2_order = {"drinkable": 0, "coconut": 1, "container": 2}
            tier2 = [c for c in fresh if c[0] in tier2_order]
            tier2.sort(key=lambda c: tier2_order[c[0]])

            # 按优先级处理
            if tier1:
                target_type, target, _ = tier1[0]
                if target_type == "resource":
                    self._drink_from_source(caller, target)
                elif target_type == "travelers_palm":
                    self._drink_travelers_palm(caller, target)
            elif tier2:
                target_type, target, _ = tier2[0]
                if target_type == "drinkable":
                    self._drink_item(caller, target)
                elif target_type == "coconut":
                    self._drink_coconut(caller, target)
                elif target_type == "container":
                    self._drink_from_container(caller, target)
            elif dirty:
                caller.msg("附近的水源都很浑浊，需要先用器皿盛装后煮沸。")
            elif salt:
                target_type, target, _ = salt[0]
                if target_type == "resource":
                    self._drink_from_source(caller, target)
                elif target_type == "drinkable":
                    self._drink_item(caller, target)
                else:
                    caller.msg("这里没有可以喝的东西。")
            else:
                caller.msg("这里没有可以喝的东西。")

    def _drink_coconut(self, caller, coconut):
        """椰子 drink（需吸管）。

        椰子有 thirst_value，可以喝，但需要背包中有吸管。
        喝完后 thirst_value 置为 0，如果 hunger_value 也为 0 则提示已空。

        Args:
            caller: 角色对象。
            coconut: 椰子对象。
        """
        thirst_value = coconut.attributes.get("thirst_restore", 0)
        hunger_value = coconut.attributes.get("hunger_restore", 0)

        if thirst_value <= 0 and hunger_value <= 0:
            caller.msg("这个椰子已经被吃喝空了。")
            return

        if thirst_value <= 0:
            caller.msg("椰子里的椰汁已经喝完了。")
            return

        # 检查吸管
        has_straw = False
        for obj in caller.contents:
            if obj.attributes.get("tool_type") == "utensil" and \
               obj.tags.get(category="from_prototype") == "bamboo_straw":
                has_straw = True
                break

        if not has_straw:
            caller.msg("你需要一根吸管才能喝到椰汁。")
            return

        # 喝
        caller.restore_thirst(thirst_value)
        caller.msg(f"你用吸管喝掉了椰子里的椰汁，口渴值恢复 {thirst_value}。")
        coconut.attributes.add("thirst_restore", 0)

        # 检查是否全空
        if coconut.attributes.get("hunger_restore", 0) <= 0:
            caller.msg("椰子已经被吃喝空了。")

    def _drink_travelers_palm(self, caller, palm):
        """旅人蕉 drink（需吸管，可重复饮用）。

        旅人蕉叶鞘中积蓄水分，用吸管即可饮用。
        与椰子不同，旅人蕉是活体植物，水持续积蓄，可反复饮用。

        Args:
            caller: 角色对象。
            palm: 旅人蕉对象。
        """
        thirst_restore = palm.attributes.get("thirst_restore", 0)
        if thirst_restore <= 0:
            caller.msg("这棵旅人蕉的叶鞘里已经没有水了。")
            return

        # 检查吸管
        has_straw = False
        for obj in caller.contents:
            if obj.attributes.get("tool_type") == "utensil" and \
               obj.tags.get(category="from_prototype") == "bamboo_straw":
                has_straw = True
                break

        if not has_straw:
            caller.msg("你需要一根吸管才能喝到旅人蕉叶鞘里的水。")
            return

        # 喝（不消耗水的积蓄，可重复饮用）
        caller.restore_thirst(thirst_restore)
        caller.msg(f"你用吸管从旅人蕉的叶鞘中吸出清凉的水，口渴值恢复 {thirst_restore}。")

    def _drink_from_container(self, caller, container):
        """从容器中饮用内容物。

        读取 vessel_content 获取内容物 prototype_key，
        从 prototype 查找 thirst_restore 属性恢复口渴值。
        如果内容物有 stamina_cost，扣除耐力（如脏水）。

        Args:
            caller: 角色对象。
            container: 容器对象。
        """
        content_key = container.attributes.get("vessel_content")
        if content_key is None:
            caller.msg(f"{container.key} 是空的。")
            return

        # 从 prototype 获取属性
        from evennia.prototypes.prototypes import search_prototype
        protos = search_prototype(key=content_key)
        if not protos:
            caller.msg("容器里的东西不能喝。")
            return

        proto = protos[0]
        thirst_restore = 0
        stamina_cost = 0
        for attr_tuple in proto.get("attrs", []):
            if attr_tuple[0] == "thirst_restore":
                thirst_restore = attr_tuple[1]
            elif attr_tuple[0] == "stamina_cost":
                stamina_cost = attr_tuple[1]

        if not thirst_restore and thirst_restore != 0:
            # 没找到 thirst_restore，检查 can_drink
            can_drink = False
            for attr_tuple in proto.get("attrs", []):
                if attr_tuple[0] == "can_drink" and attr_tuple[1]:
                    can_drink = True
                    break
            if not can_drink:
                caller.msg("容器里的东西不能喝。")
                return

        if thirst_restore == 0:
            caller.msg("容器里的东西没有饮用价值。")
            return

        # 恢复口渴
        caller.restore_thirst(thirst_restore)
        if thirst_restore >= 0:
            caller.msg(f"你从 {container.key} 里喝了些东西，口渴值恢复 {thirst_restore}。")
        else:
            caller.msg(f"你从 {container.key} 里喝了些东西，口渴值恢复 {thirst_restore}，你感觉更渴了。")

        # 耐力消耗（脏水）
        if stamina_cost > 0:
            caller.db.stamina = max(0, caller.db.stamina - stamina_cost)
            caller.msg(f"喝下去后你感到一阵不适，耐力 -{stamina_cost}。")

        # 清空容器
        container.attributes.add("vessel_content", None)

    def _drink_item(self, caller, target):
        """喝一个可喝物品，处理双消费和 becomes_on_consume。

        Args:
            caller: 角色对象。
            target: 可喝物品对象。
        """
        thirst_restore = target.attributes.get("thirst_restore", 0)
        caller.restore_thirst(thirst_restore)

        # 恢复耐力（鲜美的汤）
        stamina_restore = target.attributes.get("stamina_restore", 0)
        if stamina_restore > 0:
            caller.restore_stamina(stamina_restore)

        # 双消费检查（机制三：汤类 embedded_vessel）
        embedded_vessel = target.attributes.get("embedded_vessel")
        if embedded_vessel:
            if target.attributes.get("drink_consumed"):
                caller.msg(f"{target.key}已经喝完了。")
                return
            target.attributes.add("drink_consumed", True)
            if target.attributes.get("eat_consumed"):
                # 全部用尽 → 销毁并返还椰壳
                caller.msg(f"你喝了 {target.key}，口渴值恢复 {thirst_restore}。")
                original_location = target.location
                target.delete()
                from evennia.prototypes.spawner import spawn
                objs = spawn(embedded_vessel)
                if objs:
                    objs[0].move_to(original_location, quiet=True)
                    caller.msg(f"椰壳已返还。")
            else:
                caller.msg(f"你喝了 {target.key}，口渴值恢复 {thirst_restore}。汤中还有食物。")
            return

        # 标准消费后处理
        caller.msg(f"你喝了 {target.key}，口渴值恢复 {thirst_restore}。")
        becomes = target.attributes.get("becomes_on_consume")
        original_location = target.location
        original_contents = list(target.contents)

        # cut_coconut 条件变身：drink 后检查椰肉是否仍在
        if target.attributes.get("initial_contents"):
            has_meat = any(
                obj.tags.get(category="from_prototype") == "coconut_meat"
                for obj in original_contents
            )
            becomes = "coconut_meat_shell" if has_meat else "coconut_shell"

        target.delete()
        if becomes:
            from evennia.prototypes.spawner import spawn
            objs = spawn(becomes)
            if objs:
                new_obj = objs[0]
                new_obj.move_to(original_location, quiet=True)
                for item in original_contents:
                    item.move_to(new_obj, quiet=True)

    def _drink_from_source(self, caller, source):
        """从资源来源直接喝水。

        检查产出物是否有 vessel_only 属性。
        如果有，提示需要容器。

        Args:
            caller: 角色对象。
            source: 资源来源对象。
        """
        resource_list = source.attributes.get("resource", [])
        if not resource_list:
            caller.msg("这里没有可以喝的东西。")
            return

        entry = resource_list[0]
        prototype_key = entry.get("prototype", "")

        # 检查 vessel_only
        from evennia.prototypes.prototypes import search_prototype
        protos = search_prototype(key=prototype_key)
        if protos:
            proto = protos[0]
            for attr_tuple in proto.get("attrs", []):
                if attr_tuple[0] == "vessel_only" and attr_tuple[1]:
                    caller.msg("这些水太脏了，需要先用容器盛装。")
                    return

            # 正常饮用
            thirst_restore = 0
            for attr_tuple in proto.get("attrs", []):
                if attr_tuple[0] == "thirst_restore":
                    thirst_restore = attr_tuple[1]
                    break
            if thirst_restore == 0:
                caller.msg(f"{source.key}里没有可以喝的水。")
                return
            caller.restore_thirst(thirst_restore)
            if thirst_restore >= 0:
                caller.msg(f"你从{source.key}取了一些水喝，口渴值恢复 {thirst_restore}。")
            else:
                caller.msg(f"你从{source.key}取了一些水喝，口渴值恢复 {thirst_restore}，你感觉更渴了。")

    @staticmethod
    def _search_in(caller, name, location):
        """在指定位置搜索对象（exact=True）。

        Args:
            caller: 角色对象。
            name: 目标名称。
            location: 搜索位置（caller 或 caller.location）。

        Returns:
            找到的对象或 None。
        """
        results = caller.search(name, location=location, quiet=True, exact=True)
        if results:
            return results[0] if isinstance(results, list) else results
        return None

    def _water_quality(self, resource_list):
        """从 resource 列表判断水质。

        Args:
            resource_list: resource 属性值（列表）。

        Returns:
            "fresh" / "dirty" / "salt" / None（thirst_restore=0 视为无效水源）
        """
        if not resource_list:
            return None
        proto_key = resource_list[0].get("prototype", "")
        from evennia.prototypes.prototypes import search_prototype
        protos = search_prototype(key=proto_key)
        if not protos:
            return None
        attrs = {a[0]: a[1] for a in protos[0].get("attrs", [])}
        tr = attrs.get("thirst_restore", 0)
        if tr == 0:
            return None  # 无实际饮水价值，不算水源
        if attrs.get("vessel_only"):
            return "dirty"
        if tr < 0:
            return "salt"
        return "fresh"

    def _water_quality_by_proto(self, proto_key):
        """从 prototype_key 判断水质。

        Args:
            proto_key: prototype 标识。

        Returns:
            "fresh" / "dirty" / "salt" / None（thirst_restore=0 视为无效水源）
        """
        from evennia.prototypes.prototypes import search_prototype
        protos = search_prototype(key=proto_key)
        if not protos:
            return None
        attrs = {a[0]: a[1] for a in protos[0].get("attrs", [])}
        tr = attrs.get("thirst_restore", 0)
        if tr == 0:
            return None  # 无实际饮水价值，不算水源
        if attrs.get("vessel_only"):
            return "dirty"
        if tr < 0:
            return "salt"
        return "fresh"

    def _has_straw(self, caller):
        """检查玩家是否有竹吸管。"""
        for obj in caller.contents:
            if obj.attributes.get("tool_type") == "utensil" and \
               obj.tags.get(category="from_prototype") == "bamboo_straw":
                return True
        return False

    @staticmethod
    def _find_filled_container(caller):
        """查找背包中有内容物的容器。

        Args:
            caller: 角色对象。

        Returns:
            容器对象或 None。
        """
        for obj in caller.contents:
            if obj.attributes.get("is_container"):
                if obj.attributes.get("vessel_content") is not None:
                    return obj
        return None

    @staticmethod
    def _find_drinkable_item(caller):
        """查找第一个可喝物品（房间 + 背包）。

        Args:
            caller: 角色对象。

        Returns:
            可喝物品对象，或 None。
        """
        for candidate in caller.location.contents:
            if candidate != caller and candidate.attributes.get("can_drink"):
                return candidate
        for obj in caller.contents:
            if obj.attributes.get("can_drink"):
                return obj
        return None

    @staticmethod
    def _find_resource_source(caller):
        """查找房间内第一个有 resource 属性的来源对象。

        Args:
            caller: 角色对象。

        Returns:
            资源来源对象，或 None。
        """
        room = caller.location
        if room.attributes.has("resource"):
            return room
        for obj in room.contents:
            if obj != caller and obj.attributes.has("resource"):
                return obj
        return None

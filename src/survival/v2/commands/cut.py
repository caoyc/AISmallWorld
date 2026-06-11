"""
v2 cut 指令 — 切割

三种模式：
    cut <目标>                → 自动连续切割（资源对象，模式 A）
    cut <目标>                → 切开对象（椰子 → 切开的椰子，模式 B）
    cut <产物> from <来源>     → 从资源来源提取产物（藤蔓，模式 C）

详见：docs/设计文档/热带环礁岛基础生存闭环/详细设计/v6/LC-03a/LC-03a详细设计.md
"""

import random

from evennia.prototypes.spawner import spawn

from .base import SurvivalCommand
from .auto_action import start_auto_action, wear_tool


class CmdCut(SurvivalCommand):
    """
    切割物品

    用法：
      cut <目标>
      cut <产物> from <来源>

    切开对象、自动连续切割资源、或从来源中提取产物。
    """

    key = "cut"
    help_category = "行动"
    stamina_cost = -1

    def func(self):
        """执行切割。"""
        caller = self.caller
        room = caller.location
        if not room:
            caller.msg("你不在任何地方。")
            return

        args = self.args.strip() if self.args else ""

        # 模式 C：cut <product> from <source>
        if " from " in args:
            parts = args.split(" from ", 1)
            product_name = parts[0].strip()
            source_name = parts[1].strip()
            self._extract_product(product_name, source_name)
            return

        # 无参数
        if not args:
            caller.msg("你想切什么？用法：cut <目标> / cut <产物> from <来源>")
            return

        target_name = args.strip()

        # 查找目标
        target = self._search_target(caller, target_name)
        if not target:
            caller.msg(f"你没有看到 {target_name}。")
            return

        # 路由判定
        has_defense = target.attributes.has("defense") or target.attributes.has("hp")
        has_resource_cut = self._has_resource_cut(target)
        has_cut_into = target.attributes.has("cut_into")

        if has_defense and has_resource_cut:
            # 模式 A：自动连续切割（资源对象）
            self._auto_cut(target)
        elif has_cut_into:
            # 模式 B：切割转化（材料）
            self._cut_open_target(target)
        else:
            # AC-03
            caller.msg(f"你不能切割{target.key}。")

    def _has_resource_cut(self, target):
        """检查目标是否有 resource 条目含 method='cut'。"""
        resource = target.db.resource
        if not resource:
            return False
        return any(r.get("method") == "cut" for r in resource)

    def _auto_cut(self, target):
        """模式 A：自动连续切割资源对象。"""
        caller = self.caller

        # AC-07：忙碌检查
        if caller.db.busy:
            caller.msg("你正在执行其他操作。")
            return

        # AC-04/AC-05：查找切割工具
        tool = self._find_cutting_tool(caller)
        if not tool:
            broken = self._find_any_cutting_tool(caller)
            if broken:
                caller.msg(f"你的{broken.key}已经磨损，无法再使用了。")
                wear_tool(broken, caller)
            else:
                caller.msg("你需要一把切割工具。")
            return

        # AC-06：攻击不足检查
        attack = tool.attributes.get("attack", 0)
        defense = target.attributes.get("defense", 0)
        if attack < defense:
            caller.msg(f"你的{tool.key}不够锋利，切不动{target.key}。")
            return

        # 启动自动连续执行
        start_auto_action(caller, target, tool, "cut")

    def _cut_open_target(self, target):
        """模式 B：切开对象（原 _cut_open 逻辑）。

        将对象变为其切开版（如椰子 → 切开的椰子）。
        原对象销毁，切开版 spawn 到原位置。

        Args:
            target: 目标对象。
        """
        caller = self.caller

        # 检查 cut_into 属性
        cut_into = target.attributes.get("cut_into")
        if not cut_into:
            caller.msg(f"你不能切开 {target.key}。")
            self.apply_stamina()
            return

        # 查找切割工具
        tool = self._find_cutting_tool(caller)
        if not tool:
            broken_tool = self._find_any_cutting_tool(caller)
            if broken_tool:
                caller.msg(f"你的 {broken_tool.key} 已经磨损，无法再使用了。")
                wear_tool(broken_tool, caller)
            else:
                caller.msg("你需要一把切割工具。")
            self.apply_stamina()
            return

        # 切割攻击-防御公式
        attack = tool.attributes.get("attack", 2)
        defense = target.attributes.get("defense", 0)
        if attack < defense:
            caller.msg(f"你的 {tool.key} 不够锋利，切不动 {target.key}。")
            self.apply_stamina()
            return

        hp = target.attributes.get("hp", 1)
        if hp > 1:
            damage = attack - defense
            new_hp = max(0, hp - damage)
            target.attributes.add("hp", new_hp)
            # 工具耐久 -1
            cur_dur = tool.attributes.get("dur", 0)
            new_dur = max(0, cur_dur - 1)
            tool.attributes.add("dur", new_dur)
            tool_key = tool.key
            if new_dur <= 0:
                wear_tool(tool, caller)
            if new_hp > 0:
                caller.msg(f"你用 {tool_key} 切割 {target.key}...还需要继续切割。")
            else:
                target.attributes.add("hp", 1)  # 恢复默认值，对象不消失
                caller.msg(f"你用 {tool_key} 切开了 {target.key}。")
            self.apply_stamina()
            return

        # hp <= 1，执行原有切开逻辑
        # 记录原位置和名称
        original_location = target.location
        original_key = target.key

        # 判断是否为可食用/饮用对象（椰子专用逻辑前置）
        is_consumable = (target.attributes.has("thirst_restore")
                         or target.attributes.has("hunger_restore"))

        # 读取原对象的状态值（状态继承前置）
        src_thirst = target.attributes.get("thirst_restore", 0)
        src_hunger = target.attributes.get("hunger_restore", 0)

        # CT-01：双值归零 → 直接生成椰壳（仅限可食用/饮用对象）
        if is_consumable and src_thirst <= 0 and src_hunger <= 0:
            shell_objs = spawn("coconut_shell")
            if shell_objs:
                shell_objs[0].move_to(original_location, quiet=True)
            target.delete()
            # 工具耐久 -1
            cur_dur = tool.attributes.get("dur", 0)
            new_dur = max(0, cur_dur - 1)
            tool.attributes.add("dur", new_dur)
            tool_key = tool.key
            if new_dur <= 0:
                wear_tool(tool, caller)
            caller.msg(f"你用 {tool_key} 切开了 {original_key}，但里面已经空了，只得到了椰壳。")
            self.apply_stamina()
            return

        # CT-01b：drink 归零但 eat > 0 → 椰肉壳（无椰汁，仅椰肉）
        if is_consumable and src_thirst <= 0 and src_hunger > 0:
            cut_into = "coconut_meat_shell"

        # spawn 切开版
        objs = spawn(cut_into)
        if not objs:
            caller.msg("切开失败了。")
            return
        cut_obj = objs[0]

        # 处理 initial_contents（如切开的椰子自动创建椰肉）
        initial_contents = cut_obj.attributes.get("initial_contents", [])
        for proto_key in initial_contents:
            inner_objs = spawn(proto_key)
            if inner_objs:
                inner_objs[0].move_to(cut_obj, quiet=True)

        # 处理切割附加产物（如藤蔓 → 藤条 + 藤条皮×4）
        cut_products = target.attributes.get("cut_products", [])
        for proto_key in cut_products:
            extra_objs = spawn(proto_key)
            if extra_objs:
                extra_objs[0].move_to(original_location, quiet=True)

        # CT-02/CT-03：状态继承 — 将原对象的饮用值覆盖到切开版（仅限可饮用对象）
        if is_consumable:
            if src_thirst != cut_obj.attributes.get("thirst_restore", 20):
                cut_obj.attributes.add("thirst_restore", src_thirst)

            # CT-02 附加：椰汁已喝完时调整描述（仅 cut_coconut，椰肉壳有自己的描述）
            if src_thirst <= 0 and cut_obj.key == "切开的椰子":
                cut_obj.db.desc_look = "一个被切开的椰子，椰汁已经喝完了，只剩下雪白的椰肉。"

        # 移到原位置
        cut_obj.move_to(original_location, quiet=True)

        # 销毁原对象
        target.delete()

        # 工具耐久 -1
        cur_dur = tool.attributes.get("dur", 0)
        new_dur = max(0, cur_dur - 1)
        tool.attributes.add("dur", new_dur)
        tool_key = tool.key
        if new_dur <= 0:
            wear_tool(tool, caller)

        # 反馈
        if is_consumable and src_thirst <= 0:
            caller.msg(f"你用 {tool_key} 切开了 {original_key}，椰汁已经喝完了，但椰肉还在。")
        else:
            caller.msg(f"你用 {tool_key} 切开了 {original_key}，得到了 {cut_obj.key}。")
        self.apply_stamina()

    def _extract_product(self, product_name, source_name):
        """从资源来源提取切割产物。

        产物必须已存在于 source.contents 中（由 search 创建）。
        不 spawn 新实例，直接从 contents 中取出。
        不检查 get 锁（cut 绕过 get:false）。

        Args:
            product_name: 产物名称。
            source_name: 来源对象名称。
        """
        caller = self.caller
        room = caller.location

        # 查找来源对象
        source = caller.search(source_name, location=room, quiet=True, exact=True)
        if not source:
            caller.msg(f"你没有看到 {source_name}。")
            return
        source = source[0]

        # 在 source.contents 中查找产物（search 创建的实例）
        product = None
        for obj in source.contents:
            if obj.access(caller, "view") and self._name_matches(obj, product_name, caller):
                product = obj
                break

        if not product:
            caller.msg(f"你需要先在 {source.key} 上搜索发现 {product_name}。")
            self.apply_stamina()
            return

        # 检查来源对象的 resource 是否有 cut 条目
        resource_list = source.attributes.get("resource", [])
        cut_entries = [e for e in resource_list if e.get("method") == "cut"]

        if not cut_entries:
            caller.msg(f"你不能从 {source.key} 身上割下什么。")
            self.apply_stamina()
            return

        # 查找切割工具
        tool = self._find_cutting_tool(caller)
        if not tool:
            broken_tool = self._find_any_cutting_tool(caller)
            if broken_tool:
                caller.msg(f"你的 {broken_tool.key} 已经磨损，无法再使用了。")
                wear_tool(broken_tool, caller)
            else:
                caller.msg("你需要一把切割工具。")
            self.apply_stamina()
            return

        # 遍历 cut 条目，概率判定
        for entry in cut_entries:
            chance = entry.get("chance", 1.0)
            if random.random() < chance:
                # EC-03：2x 翻倍判定
                product_proto = product.attributes.get("prototype_key", "")
                if self._check_double_output(source, product_proto):
                    # 翻倍：额外 spawn 一个同类产品
                    extra_list = spawn(product_proto)
                    if extra_list:
                        extra = extra_list[0]
                        extra.move_to(caller, quiet=True)
                        # 成功：从 source.contents 移到玩家背包（绕过 get 锁）
                        product.move_to(caller, quiet=True)
                        # 工具耐久 -1
                        cur_dur = tool.attributes.get("dur", 0)
                        new_dur = max(0, cur_dur - 1)
                        tool.attributes.add("dur", new_dur)
                        if new_dur <= 0:
                            wear_tool(tool, caller)
                        desc = entry.get("success_desc")
                        if desc:
                            caller.msg(desc)
                        else:
                            caller.msg(f"你从 {source.key} 上割下了 {product.key}。")
                        self.apply_stamina()
                        return
                else:
                    # 成功：从 source.contents 移到玩家背包（绕过 get 锁）
                    product.move_to(caller, quiet=True)
                    # 工具耐久 -1
                    cur_dur = tool.attributes.get("dur", 0)
                    new_dur = max(0, cur_dur - 1)
                    tool.attributes.add("dur", new_dur)
                    if new_dur <= 0:
                        wear_tool(tool, caller)
                    # 提示
                    desc = entry.get("success_desc")
                    if desc:
                        caller.msg(desc)
                    else:
                        caller.msg(f"你从 {source.key} 上割下了 {product.key}。")
                    self.apply_stamina()
                    return
            else:
                # 失败：显示 fail_desc
                fail_desc = entry.get("fail_desc")
                if fail_desc:
                    caller.msg(fail_desc)
                    self.apply_stamina()
                    return

        caller.msg(f"你试图从 {source.key} 上割点什么，但没成功。")
        self.apply_stamina()

    @staticmethod
    def _check_double_output(source, product_proto):
        """检查产出物是否适用 2x 翻倍。

        条件：来源的 resource 中同一 prototype 同时有
        method="search" 和 method="cut" 条目。
        """
        resource = source.db.resource
        if not resource:
            return False
        methods = {r.get("method") for r in resource if r.get("prototype") == product_proto}
        return "search" in methods and "cut" in methods

    def _find_cutting_tool(self, caller):
        """在背包和房间中查找可用的切割工具。

        Args:
            caller: 玩家角色。

        Returns:
            工具对象或 None。
        """
        candidates = list(caller.contents) + list(caller.location.contents)
        for obj in candidates:
            if obj.attributes.get("tool_type") == "cutting":
                dur = obj.attributes.get("dur", 0)
                if dur > 0:
                    return obj
        return None

    def _find_any_cutting_tool(self, caller):
        """在背包和房间中查找切割工具（含耐久为 0 的）。

        用于区分"没有工具"和"工具已损坏"两种提示。

        Args:
            caller: 玩家角色。

        Returns:
            工具对象或 None。
        """
        candidates = list(caller.contents) + list(caller.location.contents)
        for obj in candidates:
            if obj.attributes.get("tool_type") == "cutting":
                return obj
        return None

    def _search_target(self, caller, target_name):
        """在房间和背包中搜索目标对象。

        使用 exact=True 关闭 Evennia 默认的模糊匹配，
        避免"椰子"误命中"椰子树"等 partial match 问题。

        Args:
            caller: 玩家角色。
            target_name: 目标名称。

        Returns:
            目标对象或 None。
        """
        # 先搜房间（exact=True 禁止模糊匹配）
        results = caller.search(target_name, location=caller.location,
                               quiet=True, exact=True)
        if results:
            return results[0]
        # 再搜背包
        results = caller.search(target_name, location=caller,
                               quiet=True, exact=True)
        if results:
            return results[0]
        caller.msg(f"你没有看到 {target_name}。")
        return None

    @staticmethod
    def _name_matches(obj, name, caller):
        """检查对象名称是否匹配。

        Args:
            obj: 对象。
            name: 搜索名称。
            caller: 观察者。

        Returns:
            bool: 是否匹配。
        """
        if obj.key == name:
            return True
        if name in obj.aliases.all():
            return True
        display_name = obj.get_display_name(caller)
        if display_name == name:
            return True
        return False

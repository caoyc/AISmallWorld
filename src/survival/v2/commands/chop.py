"""
v2 chop 指令 — 砍伐

双模式：
    chop <目标>  → 自动连续砍伐（资源对象，模式 A）
    chop <目标>  → 长→短砍伐转化（长木棍→木棍，模式 B）

属性名统一为 defense/hp/hp_max（迁移自 chop_defense/chop_hp/chop_hp_max）。

详见：docs/设计文档/热带环礁岛基础生存闭环/详细设计/v6/LC-03b/LC-03b详细设计.md
"""

from evennia.prototypes.spawner import spawn

from .base import SurvivalCommand
from .auto_action import start_auto_action, wear_tool


class CmdChop(SurvivalCommand):
    """
    砍伐

    用法：
      chop <目标>
      chop <目标> from <容器>

    用斧头砍伐树木、竹子，或将长木棍/长竹棍砍成短木棍/短竹棍。
    指定 from 时，在容器内查找目标对象。
    """

    key = "chop"
    help_category = "行动"
    stamina_cost = -1

    def func(self):
        """执行砍伐。"""
        if not self.pre_check():
            return

        caller = self.caller
        args = self.args.strip() if self.args else ""

        # CH-01：无参数
        if not args:
            caller.msg("你想砍什么？用法：chop <目标> [from <容器>]")
            return

        room = caller.location

        # 解析 "from" 语法
        container = None
        if " from " in args:
            parts = args.split(" from ", 1)
            target_name = parts[0].strip()
            container_name = parts[1].strip()
            # 查找容器
            results = caller.search(container_name, location=room, quiet=True, exact=True)
            if not results:
                caller.msg(f"你没有看到{container_name}。")
                return
            container = results[0]
        else:
            target_name = args

        # 查找目标
        target = self._search_target(caller, target_name, room, container)
        if not target:
            return

        # 检查目标是否有砍伐属性
        has_chop_output = target.attributes.has("chop_output")
        has_defense = target.attributes.has("defense")

        # CH-03：不可砍伐
        if not has_chop_output or not has_defense:
            caller.msg(f"{target.key}不能被砍伐。")
            self.apply_stamina()
            return

        # 路由判定
        defense = target.attributes.get("defense", 0)
        hp = target.attributes.get("hp", 1)

        if defense == 0 and hp <= 1:
            # 模式 B：长→短砍伐转化
            self._chop_transform(caller, target)
        else:
            # 模式 A：自动连续砍伐
            self._chop_auto(caller, target)

    def _chop_auto(self, caller, target):
        """模式 A：自动连续砍伐资源对象。"""
        # CH-07：忙碌检查
        if caller.db.busy:
            caller.msg("你正在执行其他操作。")
            return

        # CH-04/CH-05：查找砍伐工具
        tool = self._find_chopping_tool(caller)
        if not tool:
            broken = self._find_any_chopping_tool(caller)
            if broken:
                caller.msg(f"你的{broken.key}已经磨损，无法使用了。")
                wear_tool(broken, caller)
            else:
                caller.msg("你需要一把斧头才能砍伐。")
            self.apply_stamina()
            return

        # CH-06：攻击不足
        attack = tool.attributes.get("attack", 0)
        defense = target.attributes.get("defense", 0)
        if attack < defense:
            caller.msg(f"你的{tool.key}砍不动{target.key}。")
            self.apply_stamina()
            return

        # 启动自动连续执行
        start_auto_action(caller, target, tool, "chop")

    def _chop_transform(self, caller, target):
        """模式 B：长→短砍伐转化（单次执行）。"""
        # CH-07：忙碌检查
        if caller.db.busy:
            caller.msg("你正在执行其他操作。")
            return

        # CH-04/CH-05：查找砍伐工具
        tool = self._find_chopping_tool(caller)
        if not tool:
            broken = self._find_any_chopping_tool(caller)
            if broken:
                caller.msg(f"你的{broken.key}已经磨损，无法使用了。")
                wear_tool(broken, caller)
            else:
                caller.msg("你需要一把斧头才能砍伐。")
            self.apply_stamina()
            return

        # 执行转化
        chop_output = target.attributes.get("chop_output", [])
        if not chop_output:
            caller.msg(f"你砍了{target.key}，但没有获得什么。")
            self.apply_stamina()
            return

        # 记录目标位置
        target_location = target.location

        # 消耗工具耐久 -1
        cur_dur = tool.attributes.get("dur", 0)
        new_dur = max(0, cur_dur - 1)
        tool.attributes.add("dur", new_dur)
        tool_key = tool.key
        if new_dur <= 0:
            wear_tool(tool, caller)

        # 产出
        caller.msg(f"你用{tool_key}把{target.key}砍成了短材料。")
        for entry in chop_output:
            proto_key = entry.get("prototype")
            count = entry.get("count", 1)
            for _ in range(count):
                objs = spawn(proto_key)
                if objs:
                    # TR-01/TR-02：产出物放到目标原位置
                    objs[0].move_to(target_location, quiet=True)
                    caller.msg(f"  你获得了{objs[0].key}。")

        # 删除原对象（长→短转化后原对象消失）
        target.delete()

        self.apply_stamina()

    def _search_target(self, caller, name, room, container=None):
        """在房间中搜索目标对象，包括容器内部。

        Args:
            caller: 玩家角色。
            name: 目标名称。
            room: 当前房间。
            container: 指定容器（from 语法时使用）。

        Returns:
            目标对象或 None。
        """
        if container:
            # 指定容器：只在该容器内查找
            for obj in container.contents:
                if obj.access(caller, "view") and self._name_matches(obj, name, caller):
                    return obj
            caller.msg(f"你在{container.key}中没有看到{name}。")
            return None

        # 三层查找：房间 → 房间中容器内部 → 玩家背包
        # 1. 房间直接内容
        results = caller.search(name, location=room, quiet=True, exact=True)
        if results:
            return results[0]

        # 2. 房间中容器内部（如榕树里的粗壮树枝）
        for room_obj in room.contents:
            for obj in room_obj.contents:
                if obj.access(caller, "view") and self._name_matches(obj, name, caller):
                    return obj

        # 3. 玩家背包
        results = caller.search(name, location=caller, quiet=True, exact=True)
        if results:
            return results[0]

        caller.msg(f"你没有看到{name}。")
        return None

    @staticmethod
    def _name_matches(obj, name, caller):
        """检查对象名称是否匹配。"""
        if obj.key == name:
            return True
        if name in obj.aliases.all():
            return True
        display_name = obj.get_display_name(caller)
        if display_name == name:
            return True
        return False

    def _find_chopping_tool(self, caller):
        """在背包和房间中查找可用的砍伐工具。

        Args:
            caller: 玩家角色。

        Returns:
            工具对象或 None。
        """
        candidates = list(caller.contents) + list(caller.location.contents)
        for obj in candidates:
            if obj.attributes.get("tool_type") == "chopping":
                dur = obj.attributes.get("dur", 0)
                if dur > 0:
                    return obj
        return None

    def _find_any_chopping_tool(self, caller):
        """在背包和房间中查找砍伐工具（含耐久为 0 的）。

        Args:
            caller: 玩家角色。

        Returns:
            工具对象或 None。
        """
        candidates = list(caller.contents) + list(caller.location.contents)
        for obj in candidates:
            if obj.attributes.get("tool_type") == "chopping":
                return obj
        return None

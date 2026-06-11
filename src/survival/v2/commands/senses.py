"""
v2 五感指令 — look / smell / listen / touch / taste

五个指令共用一套框架，纯信息描述，不改变任何状态。
taste 有独立的退化链（desc_taste → can_eat/can_drink → 默认值）。

详见：docs/设计文档/解决饥渴_v2/详细设计/指令实现.md
"""

from .base import SurvivalCommand

DEFAULT_MESSAGES = {
    "look": "你看到了一片平凡的景象。",
    "smell": "你闻到了周围的气息。",
    "listen": "你听到了周围的声音。",
    "touch": "你伸手触摸了一下。",
    "taste": "你没有尝出什么特别的味道。",
}


def get_sense_desc(target, sense):
    """读取对象的感官描述。

    有设置返回设置值，无设置退化返回默认值。

    Args:
        target: 房间或对象。
        sense (str): 感官类型（look/smell/listen/touch/taste）。

    Returns:
        str: 描述文本。
    """
    desc = target.attributes.get(f"desc_{sense}")
    if desc:
        return desc
    return DEFAULT_MESSAGES.get(sense, "你没有什么特别的感觉。")


def get_taste_desc(target):
    """taste 的退化链。

    1. desc_taste 有设置 → 返回
    2. can_eat/can_drink 有设置 → 返回默认可食用/可饮用信息
    3. 都没有 → DEFAULT_MESSAGES["taste"]

    Args:
        target: 对象。

    Returns:
        str: 味觉描述文本。
    """
    desc = target.attributes.get("desc_taste")
    if desc:
        return desc
    can_eat = target.attributes.get("can_eat")
    can_drink = target.attributes.get("can_drink")
    if can_eat:
        return "这东西尝起来可以吃。"
    if can_drink:
        return "这东西尝起来可以喝。"
    return DEFAULT_MESSAGES["taste"]


class _SenseCommand(SurvivalCommand):
    """五感指令基类。子类只需设 key 和 sense。"""

    stamina_cost = 0
    rest_interrupt = False
    sense = None  # 子类覆写

    @staticmethod
    def _find_target(caller, room, name):
        """四层查找目标对象：房间→房间中对象→收藏夹→背包。

        Args:
            caller: 玩家对象。
            room: 当前房间。
            name: 目标名称。

        Returns:
            匹配的对象，未找到返回 None。
        """
        from .recipe_utils import get_or_create_recipe_book

        # 第一层：房间 contents
        for obj in room.contents:
            if obj.destination or obj.has_account:
                continue
            if obj.access(caller, "view") and _SenseCommand._name_matches(obj, name, caller):
                return obj

        # 第二层：房间中对象的 contents
        for container in room.contents:
            if container.destination or container.has_account:
                continue
            for obj in container.contents:
                if obj.access(caller, "view") and _SenseCommand._name_matches(obj, name, caller):
                    return obj

        # 第三层：配方收藏夹
        book = get_or_create_recipe_book(caller)
        if book:
            for obj in book.contents:
                if obj.access(caller, "view") and _SenseCommand._name_matches(obj, name, caller):
                    return obj

        # 第四层：玩家背包（排除收藏夹本身）
        for obj in caller.contents:
            if obj.tags.has("recipe_book", category="system"):
                continue
            if obj.access(caller, "view") and _SenseCommand._name_matches(obj, name, caller):
                return obj

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

    def func(self):
        """统一五感流程。

        流程：
            mermaid:
            TD
                A[pre_check] --> B{参数为空?}
                B -->|是| C[操作对象=房间]
                B -->|否| D[查找目标]
                C --> E[读取 desc_sense]
                D --> E
                E --> F{sense=taste?}
                F -->|是| G[get_taste_desc]
                F -->|否| H[get_sense_desc]
                G --> I[msg]
                H --> I
        """
        if not self.pre_check():
            return

        caller = self.caller
        room = caller.location

        if not self.args:
            # 无参数：操作对象为房间
            target = room
        else:
            # 有参数：四层查找（房间→房间中对象→收藏夹→背包）
            target = self._find_target(caller, room, self.args.strip())
            if not target:
                caller.msg(f"你没有看到 {self.args.strip()}。")
                return

        # 读取描述
        # 配方对象：动态生成结构化描述
        if target.attributes.get("recipe_type"):
            from .recipe_utils import generate_recipe_desc
            desc = generate_recipe_desc(caller, target)
        elif self.sense == "taste":
            desc = get_taste_desc(target)
        else:
            desc = get_sense_desc(target, self.sense)

        # look <对象> 时，动态追加对象级指令（help 格式）和内容物
        if self.sense == "look" and target != room:
            # 运行时检测对象 cmdset 上的真实指令
            _cmdset_handler = target.cmdset
            _current = _cmdset_handler.current if _cmdset_handler else None
            if _current:
                _obj_cmds = getattr(_current, "commands", None) or []
                if _obj_cmds:
                    cmd_lines = []
                    for cmd in _obj_cmds:
                        key = getattr(cmd, "key", "")
                        if not key:
                            continue
                        doc = (getattr(cmd, "__doc__", "") or "").strip()
                        summary = doc.split("\n", 1)[0] if doc else ""
                        if summary:
                            cmd_lines.append(f"  {key}  {summary}")
                        else:
                            cmd_lines.append(f"  {key}")
                    if cmd_lines:
                        desc += "\n可用指令：\n" + "\n".join(cmd_lines)

            # 显示内容物（与 look 房间的"你注意到："列表风格一致，含 └─ 嵌套）
            visible_contents = [
                obj for obj in target.contents
                if obj.access(caller, "view")
                and not obj.destination  # 排除出口
                and not obj.has_account  # 排除角色
            ]
            if visible_contents:
                from survival.v2.rooms import SurvivalRoomV2
                content_lines = SurvivalRoomV2._format_objects(
                    visible_contents, caller, prefix="  └─ "
                )
                desc += "\n你注意到：\n" + "\n".join(content_lines)

        caller.msg(desc)


class CmdLook(_SenseCommand):
    """
    查看周围或目标

    用法：
      look
      look <目标>

    无参数时查看当前房间的完整描述，有参数时查看指定目标。
    """
    key = "look"
    help_category = "感知"
    sense = "look"

    def func(self):
        """look 特殊处理：无参数时委托 Evennia 内置 look + 追加地图。"""
        if not self.args:
            # 委托 Evennia 内置 look，完整显示描述+出口+对象
            caller = self.caller
            room = caller.location
            if room:
                look_result = caller.at_look(room)
                # 追加地图（出口下方，上下各空一行）
                from .map import _render_map
                exits_info = [
                    (ex.key, ex.destination.key)
                    for ex in room.exits
                    if ex.destination
                ]
                map_text = _render_map(room.key, exits_info)
                caller.msg(f"{look_result}\n\n{map_text}\n")
            return
        super().func()


class CmdSmell(_SenseCommand):
    """
    闻气味

    用法：
      smell
      smell <目标>

    无参数时闻当前环境的气味，有参数时闻指定目标的气味。
    """
    key = "smell"
    help_category = "感知"
    sense = "smell"


class CmdListen(_SenseCommand):
    """
    听声音

    用法：
      listen
      listen <目标>

    无参数时听当前环境的声音，有参数时听指定目标的声音。
    """
    key = "listen"
    help_category = "感知"
    sense = "listen"


class CmdTouch(_SenseCommand):
    """
    触摸物体

    用法：
      touch
      touch <目标>

    无参数时触摸当前环境，有参数时触摸指定目标的触感。
    """
    key = "touch"
    help_category = "感知"
    sense = "touch"


class CmdTaste(_SenseCommand):
    """
    尝味道

    用法：
      taste
      taste <目标>

    无参数时尝当前环境的味道，有参数时尝指定目标的味道。
    """
    key = "taste"
    help_category = "感知"
    sense = "taste"

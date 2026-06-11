"""
房间类型类 — SurvivalRoomV2

支持五感描述 + 房间级资源的房间类型。

详见：docs/设计文档/解决饥渴_v2/详细设计/
"""

from collections import defaultdict

from evennia.objects.objects import DefaultRoom


class SurvivalRoom(DefaultRoom):
    """支持五感描述的房间基类。"""

    DEFAULT_SENSE_MESSAGES = {
        "listen": "这里安安静静的，没有什么特别的声音。",
        "smell": "这里的空气没有什么特别的气味。",
        "touch": "你感受了一下周围，没有什么特别的触感。",
        "taste": "空气中没有什么可以品尝的味道。",
    }

    def get_display_desc(self, looker, **kwargs):
        return self.db.desc_look or self.db.desc or self.default_description

    def get_sense_description(self, sense):
        desc = self.attributes.get(f"desc_{sense}")
        if desc:
            return desc
        if sense == "look":
            return self.db.desc or self.default_description
        return self.DEFAULT_SENSE_MESSAGES.get(sense, "你什么也没有感受到。")


class SurvivalRoomV2(SurvivalRoom):
    """v2 房间，自定义 look 显示格式。

    Attributes:
        db.resource (list[dict], optional): 场景资源产出表
        db.desc_look (str): 视觉描述（由 build_island 设置）
        db.desc_listen (str): 听觉描述
        db.desc_smell (str): 嗅觉描述
        db.desc_touch (str): 触觉描述
        db.desc_taste (str): 味觉描述
    """

    def return_appearance(self, looker, **kwargs):
        """组装房间外观：房间名 + 描述 + 场景物(含内部资源) + 可拾取物 + 角色 + 出口。

        输出格式：
            【房间名】
            desc_look 描述文本

            你注意到：
              场景物 — desc_look
                内部资源(×N) — desc_look
            地上有：
              可拾取物(×N) — desc_look
            角色也在这里。

            出口：别名(方向)

        流程：
            mermaid:
            TD
                A[获取房间名和描述] --> B[遍历 room.contents]
                B --> C[分类: exits / characters / fixed_objs / items]
                C --> D[对象按名称分组合并]
                D --> E[场景物: 检查 contents 展示内部资源]
                E --> F[组装输出]

        Args:
            looker: 观察者（角色对象）。
            **kwargs: Evennia 传递的额外参数。

        Returns:
            str: 格式化的房间外观文本。
        """
        if not looker:
            return ""

        parts = []

        # 1. 房间名
        name = self.get_display_name(looker, **kwargs)
        parts.append(f"|w【{name}】|n")

        # 2. 描述
        desc = self.get_display_desc(looker, **kwargs)
        if desc:
            parts.append(desc)

        # 3. 分类 contents
        exits = []
        characters = []
        fixed_objs = []  # get:false（资源来源、场景物）
        items = []       # get:true（可拾取物品，直接在房间中的）

        for obj in self.contents:
            # 出口：有 destination 的对象
            if obj.destination:
                exits.append(obj)
            # 在线角色（排除 looker 自身，looker 不展示）
            elif obj.has_account:
                if obj != looker:
                    characters.append(obj)
            # 不可拾取的固定场景物
            elif not obj.access(looker, "get"):
                fixed_objs.append(obj)
            # 可拾取物品（直接在房间中）
            else:
                items.append(obj)

        # 4. 场景物（含内部资源）
        if fixed_objs:
            parts.append("")
            parts.append("|w你注意到：|n")
            parts.extend(self._format_fixed_objects(fixed_objs, looker))

        # 5. 可拾取物品（直接在房间中的）
        if items:
            parts.append("")
            parts.append("|w地上有：|n")
            parts.extend(self._format_objects(items, looker, indent="  "))

        # 6. 角色
        if characters:
            parts.append("")
            for char in characters:
                char_name = char.get_display_name(looker, **kwargs)
                parts.append(f"{char_name}也在这里。")

        # 7. 出口
        if exits:
            parts.append("")
            exit_parts = []
            for exit_obj in exits:
                exit_name = exit_obj.get_display_name(looker, **kwargs)
                aliases = exit_obj.aliases.all()
                alias = aliases[0] if aliases else exit_name
                exit_parts.append(f"{exit_name}({alias})")
            parts.append(f"|w出口：|n" + "  ".join(exit_parts))

        return "\n".join(parts)

    @staticmethod
    def _format_fixed_objects(objects, looker):
        """格式化固定场景物，含其内部已发现的资源实例。

        场景物本身按名称分组。内部资源按名称分组，缩进显示。

        Args:
            objects: 固定场景物列表。
            looker: 观察者。

        Returns:
            list[str]: 格式化后的文本行列表。
        """
        grouped = defaultdict(list)
        for obj in objects:
            name = obj.get_display_name(looker)
            grouped[name].append(obj)

        lines = []
        for name, obj_list in grouped.items():
            obj = obj_list[0]
            desc = obj.get_display_desc(looker)
            count = len(obj_list)
            if count > 1:
                lines.append(f"  {name}(×{count}) — {desc}")
            else:
                lines.append(f"  {name} — {desc}")

            # 收集所有同名对象的内部资源（合并显示）
            inner_items = []
            for o in obj_list:
                for inner in o.contents:
                    if inner.access(looker, "view"):
                        inner_items.append(inner)

            if inner_items:
                inner_lines = SurvivalRoomV2._format_objects(
                    inner_items, looker, prefix="    └─ "
                )
                lines.extend(inner_lines)

        return lines

    @staticmethod
    def _format_objects(objects, looker, indent="  ", prefix=None):
        """将对象列表格式化为名称+描述行。

        同名对象合并，附 (×N) 标记。

        Args:
            objects: 对象列表。
            looker: 观察者。
            indent: 缩进字符串（prefix 为 None 时使用）。
            prefix: 固定前缀（如 "    └─ "），优先于 indent。

        Returns:
            list[str]: 格式化后的文本行列表。
        """
        grouped = defaultdict(list)
        for obj in objects:
            name = obj.get_display_name(looker)
            grouped[name].append(obj)

        lines = []
        for name, obj_list in grouped.items():
            obj = obj_list[0]
            desc = obj.get_display_desc(looker)
            count = len(obj_list)
            lead = prefix if prefix else indent
            if count > 1:
                lines.append(f"{lead}{name}(×{count}) — {desc}")
            else:
                lines.append(f"{lead}{name} — {desc}")
        return lines

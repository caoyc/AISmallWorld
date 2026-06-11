"""
v2 fill 指令 — 容器盛入

从资源来源将液体/物质盛入容器中。

用法：fill <容器> from <来源>

详见：docs/设计文档/热带环礁岛基础生存闭环/详细设计/v1/基础生存闭环详细设计.md
"""

from .base import SurvivalCommand


class CmdFill(SurvivalCommand):
    """
    容器盛入

    用法：
      fill <容器> from <来源>

    从资源来源将内容物盛入容器。
    """

    key = "fill"
    help_category = "行动"
    stamina_cost = -1

    def func(self):
        """执行容器盛入。

        流程：
            mermaid:
            TD
                A[pre_check] --> B{有参数?}
                B -->|否| C[用法提示]
                B -->|是| D{有 from?}
                D -->|否| C
                D -->|是| E[查找容器]
                E --> F{找到?}
                F -->|否| G[你没有容器]
                F -->|是| H{容器已空?}
                H -->|否| I[容器已有内容物]
                H -->|是| J[查找资源来源]
                J --> K{找到?}
                K -->|否| L[没有这个来源]
                K -->|是| M[检查 supported_contents]
                M --> N{支持?}
                N -->|否| O[容器不能盛这个]
                N -->|是| P[vessel_content = 产出物]
                P --> Q[提示]
        """
        if not self.pre_check():
            return

        caller = self.caller
        args = self.args.strip() if self.args else ""

        if not args or " from " not in args:
            caller.msg("用法：fill <容器> from <来源>")
            return

        parts = args.split(" from ", 1)
        container_name = parts[0].strip()
        source_name = parts[1].strip()

        if not container_name or not source_name:
            caller.msg("用法：fill <容器> from <来源>")
            return

        # 查找容器（GP-LC01-08: 房间 → 房间中的对象 → 玩家背包）
        room = caller.location
        container = None

        # 第一层：房间中的对象
        if not container:
            for obj in room.contents:
                if obj != caller and obj.attributes.get("is_container") and self._name_matches(obj, container_name):
                    container = obj
                    break

        # 第二层：房间中对象的内容物
        if not container:
            for room_obj in room.contents:
                if room_obj == caller or not hasattr(room_obj, 'contents'):
                    continue
                for inner_obj in room_obj.contents:
                    if inner_obj.attributes.get("is_container") and self._name_matches(inner_obj, container_name):
                        container = inner_obj
                        break
                if container:
                    break

        # 第三层：玩家背包
        if not container:
            for obj in caller.contents:
                if obj.attributes.get("is_container") and self._name_matches(obj, container_name):
                    container = obj
                    break

        if not container:
            caller.msg(f"你没有 {container_name}。")
            self.apply_stamina()
            return

        # 检查容器是否已空
        current_content = container.attributes.get("vessel_content")
        if current_content is not None:
            caller.msg(f"{container.key} 里已经有东西了，先 empty 清空。")
            self.apply_stamina()
            return

        # 查找资源来源（房间中）
        room = caller.location
        source = None
        for obj in room.contents:
            if obj != caller and obj.attributes.has("resource") and self._name_matches(obj, source_name):
                source = obj
                break

        if not source:
            caller.msg(f"你没有看到 {source_name}。")
            self.apply_stamina()
            return

        # 从 resource 列表取第一个产出物
        resource_list = source.attributes.get("resource", [])
        if not resource_list:
            caller.msg(f"你不能从 {source.key} 盛东西。")
            self.apply_stamina()
            return

        entry = resource_list[0]
        product_key = entry.get("prototype", "")

        # 检查容器是否支持该内容物
        supported = container.attributes.get("supported_contents", [])
        if supported and product_key not in supported:
            caller.msg(f"{container.key} 不能盛装这种东西。")
            self.apply_stamina()
            return

        # 盛入
        container.attributes.add("vessel_content", product_key)
        desc = entry.get("success_desc", f"你用 {container.key} 盛了 {product_key}。")
        caller.msg(desc)
        self.apply_stamina()

    @staticmethod
    def _name_matches(obj, name):
        """检查对象名称是否匹配。

        Args:
            obj: 对象。
            name: 搜索名称。

        Returns:
            bool: 是否匹配。
        """
        if obj.key == name:
            return True
        if name in obj.aliases.all():
            return True
        return False

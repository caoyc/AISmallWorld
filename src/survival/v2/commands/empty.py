"""
v2 empty 指令 — 容器清空

清空容器中的内容物。

用法：empty <容器>

详见：docs/设计文档/热带环礁岛基础生存闭环/详细设计/v1/基础生存闭环详细设计.md
"""

from .base import SurvivalCommand


class CmdEmpty(SurvivalCommand):
    """
    容器清空

    用法：
      empty <容器>

    倒掉容器中的内容物。
    """

    key = "empty"
    help_category = "行动"
    stamina_cost = 0

    def func(self):
        """执行容器清空。

        流程：
            mermaid:
            TD
                A[pre_check] --> B{有参数?}
                B -->|否| C[用法提示]
                B -->|是| D[查找容器]
                D --> E{找到?}
                E -->|否| F[你没有这个容器]
                E -->|是| G{vessel_content != None?}
                G -->|否| H[容器是空的]
                G -->|是| I[vessel_content = None]
                I --> J[提示]
        """
        if not self.pre_check():
            return

        caller = self.caller
        args = self.args.strip() if self.args else ""

        if not args:
            caller.msg("用法：empty <容器>")
            return

        # 汤类产出物清空（机制三：embedded_vessel）
        embedded_vessel = None
        # 先按名称查找汤类产出物（非容器但有 embedded_vessel）
        soup_target = None
        for obj in caller.contents:
            if obj.attributes.get("embedded_vessel") and self._name_matches(obj, args):
                soup_target = obj
                break
        # 若未在背包中找到，按 GP-LC01-08 继续查找房间
        if not soup_target:
            room = caller.location
            for obj in room.contents:
                if obj != caller and obj.attributes.get("embedded_vessel") and self._name_matches(obj, args):
                    soup_target = obj
                    break

        if soup_target:
            embedded_vessel = soup_target.attributes.get("embedded_vessel")
            original_location = soup_target.location
            soup_target.delete()
            from evennia.prototypes.spawner import spawn
            objs = spawn(embedded_vessel)
            if objs:
                objs[0].move_to(original_location, quiet=True)
            caller.msg(f"你倒掉了 {soup_target.key}，椰壳已返还。")
            return

        # 查找容器（GP-LC01-08: 房间 → 房间中的对象 → 玩家背包）
        room = caller.location
        container = None

        # 第一层：房间中的对象
        if not container:
            for obj in room.contents:
                if obj != caller and obj.attributes.get("is_container") and self._name_matches(obj, args):
                    container = obj
                    break

        # 第二层：房间中对象的内容物
        if not container:
            for room_obj in room.contents:
                if room_obj == caller or not hasattr(room_obj, 'contents'):
                    continue
                for inner_obj in room_obj.contents:
                    if inner_obj.attributes.get("is_container") and self._name_matches(inner_obj, args):
                        container = inner_obj
                        break
                if container:
                    break

        # 第三层：玩家背包
        if not container:
            for obj in caller.contents:
                if obj.attributes.get("is_container") and self._name_matches(obj, args):
                    container = obj
                    break

        if not container:
            caller.msg(f"你没有 {args}。")
            return

        # 检查是否有内容物
        current_content = container.attributes.get("vessel_content")
        if current_content is None:
            caller.msg(f"{container.key} 是空的。")
            return

        # 清空
        container.attributes.add("vessel_content", None)
        caller.msg(f"你倒掉了 {container.key} 里的内容物。")

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

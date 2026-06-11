"""
v2 follow 指令 — 跟随角色

跟随指定角色，目标移动时自动跟随到同一房间。
无参数时取消跟随。

用法：
    follow                — 取消跟随
    follow <某人>         — 开始跟随指定角色

详见：docs/开发测试/热带环礁岛基础生存闭环/BUG排查/v1/BUG-016_新增follow跟随指令根因分析.md
"""

from .base import SurvivalCommand


class CmdFollow(SurvivalCommand):
    """
    跟随某人

    用法：
      follow
      follow <某人>

    无参数时取消当前跟随。
    跟随期间目标移动时自动跟随，消耗耐力。
    主动移动时自动取消跟随。
    """

    key = "follow"
    help_category = "行动"
    stamina_cost = 0        # follow 本身不消耗耐力
    rest_interrupt = False  # 查询/设置状态类指令，不打断休息

    def func(self):
        """执行跟随/取消跟随。

        流程：
            mermaid:
            TD
                A[解析参数] --> B{有参数?}
                B -->|无| C[取消跟随]
                B -->|有| D[查找目标角色]
                D --> E{目标有效?}
                E -->|否| F[提示]
                E -->|是| G{已在跟随同一人?}
                G -->|是| H[提示已在跟随]
                G -->|否| I[清理旧跟随关系]
                I --> J[建立新跟随关系]
                J --> K[提示]
        """
        caller = self.caller
        args = (self.args or "").strip()

        # ── 无参数：取消跟随 ──
        if not args:
            self._cancel_follow(caller)
            return

        # ── 有参数：开始跟随 ──
        self._start_follow(caller, args)

    def _cancel_follow(self, caller):
        """取消跟随状态。

        Args:
            caller: 玩家角色。
        """
        target = caller.db.following
        if not target:
            caller.msg("你没有在跟随任何人。")
            return

        # 从目标的 followers 列表中移除自己
        followers = target.db.followers or []
        if caller in followers:
            followers.remove(caller)
            target.db.followers = followers

        # 清除自己的跟随状态
        caller.db.following = None
        caller.msg(f"你停止跟随 {target.key}。")

    def _start_follow(self, caller, target_name):
        """开始跟随目标。

        Args:
            caller: 玩家角色。
            target_name: 目标名称。
        """
        # 查找目标（同房间）
        room = caller.location
        results = caller.search(target_name, location=room, quiet=True, exact=True)
        if not results:
            caller.msg(f"这里没有 {target_name}。")
            return

        target = results[0]

        # 不能跟随自己
        if target == caller:
            caller.msg("你不能跟随自己。")
            return

        # 目标必须是角色（有 account）
        if not target.has_account:
            caller.msg(f"你不能跟随 {target.key}。")
            return

        # 已在跟随同一人
        if caller.db.following == target:
            caller.msg(f"你已经在跟随 {target.key}。")
            return

        # 清理旧的跟随关系
        old_target = caller.db.following
        if old_target:
            old_followers = old_target.db.followers or []
            if caller in old_followers:
                old_followers.remove(caller)
                old_target.db.followers = old_followers

        # 建立新的跟随关系
        caller.db.following = target
        followers = target.db.followers or []
        if caller not in followers:
            followers.append(caller)
        target.db.followers = followers

        caller.msg(f"你开始跟随 {target.key}。")

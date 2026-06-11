"""
v2 help 指令 — 自定义指令列表

覆写 Evennia 默认 help 索引格式，改为列表+功能说明，
一次性输出完整列表，对 AI 玩家友好。

详见：docs/设计文档/help指令改造/详细设计/help指令.md
"""

from collections import defaultdict

from evennia.commands.default.help import CmdHelp as DefaultCmdHelp


class CmdHelp(DefaultCmdHelp):
    """
    查看指令帮助

    用法：
      help
      help <指令名>

    无参数时显示所有可用指令及其功能说明。
    有参数时显示指定指令的详细用法。
    """

    key = "help"
    aliases = []
    help_more = False
    rest_interrupt = False

    def func(self):
        """执行 help 命令。

        无参数时覆写索引格式为分组列表+功能说明。
        有参数时走 Evennia 默认的详细页格式。

        流程：
            mermaid:
            TD
                A{有参数?} -->|有| B[父类 func 查询详细页]
                A -->|无| C[collect_topics 获取命令]
                C --> D[按 help_category 分组]
                D --> E[提取 docstring 首行]
                E --> F[组装分组列表输出]

        Returns:
            None。
        """
        if self.topic:
            # 有查询参数 → 走父类的详细页逻辑
            super().func()
            return

        # 无参数 → 自定义索引格式
        caller = self.caller

        # 获取所有可用命令的 help topics
        cmd_help_topics, _, _ = self.collect_topics(caller, mode="list")
        # cmd_help_topics: {key: cmd_instance}

        # 按 help_category 分组
        groups = defaultdict(dict)
        for key, cmd in cmd_help_topics.items():
            cat = getattr(cmd, "help_category", "general")
            groups[cat][key] = cmd

        # 分组顺序
        category_order = ["生存", "感知", "行动", "制作"]

        category_labels = {
            "生存": "【生存】饮食休息",
            "感知": "【感知】五感探索",
            "行动": "【行动】采集移动",
            "制作": "【制作】配方研究",
        }

        lines = ["|w可用指令：|n"]
        for cat in category_order:
            if cat not in groups:
                continue
            cmds = groups[cat]
            lines.append(f"  |c{category_labels.get(cat, cat)}|n")
            for key in sorted(cmds.keys()):
                desc = self._get_short_desc(cmds[key])
                lines.append(f"    {key}  {desc}")
            lines.append("")

        # 非预设分组（系统命令等）— 按 Evennia 自带分类归组
        seen_cats = set(category_order)
        for cat in sorted(groups.keys()):
            if cat in seen_cats:
                continue
            cmds = groups[cat]
            lines.append(f"  |c【{cat}】|n")
            for key in sorted(cmds.keys()):
                desc = self._get_short_desc(cmds[key])
                lines.append(f"    {key}  {desc}")
            lines.append("")

        lines.append("使用 |whelp <指令名>|n 查看详细用法。")

        self.msg_help("\n".join(lines))

    @staticmethod
    def _get_short_desc(cmd):
        """从标准三段式 docstring 中提取首行 + 用法段，拼接为单行摘要。

        解析规则：
          首行 → 功能描述（注意事项）
          用法段 → "用法：" 之后到下一个空行之间的行
          拼接 → "功能描述（注意事项）：格式1 | 格式2 | ..."
        无 docstring 或无用法段时只返回首行。

        Args:
            cmd: 命令实例。

        Returns:
            str: 拼接后的单行摘要。
        """
        if not cmd.__doc__:
            return ""

        doc = cmd.__doc__.strip()
        lines = doc.split("\n")

        # 提取首行
        first_line = lines[0].strip() if lines else ""

        # 查找用法段
        usage_lines = []
        in_usage = False
        for line in lines[1:]:
            stripped = line.strip()
            if stripped.startswith("用法：") or stripped.startswith("用法:"):
                in_usage = True
                continue
            if in_usage:
                if stripped == "":
                    break
                usage_lines.append(stripped)

        if usage_lines:
            formats = " | ".join(usage_lines)
            return f"{first_line}：{formats}"
        return first_line

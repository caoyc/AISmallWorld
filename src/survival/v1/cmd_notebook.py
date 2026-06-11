"""
笔记本指令

详见：docs/设计文档/解决饥饿/详细设计/笔记本系统详细设计.md
"""

from evennia.commands.command import Command

from .notebook_db import NotebookDB


class CmdNotebook(Command):
    """分类笔记增删改查。

    key = "nb"
    aliases = ["笔记本", "note"]
    locks = "cmd:all()"

    用法::

        nb                      列出所有分类
        nb <分类>               列出分类下所有条目
        nb <分类>/<标题>        查看笔记内容
        nb add <分类>/<标题> = <内容>   新增笔记
        nb edit <分类>/<标题> = <内容>  修改笔记
        nb del <分类>/<标题>             删除笔记

    parse() 逻辑::

        raw = self.args.strip()
        无 raw       → 子命令 = "list_categories"
        raw 以 "add " 开头 → 子命令 = "add"，rest = raw[4:]
        raw 以 "edit " 开头 → 子命令 = "edit"，rest = raw[5:]
        raw 以 "del " 开头 → 子命令 = "del"，rest = raw[4:]
        其余 → 子命令 = "show"，rest = raw

    func() 分发::

        mermaid:
        TD
            A[CmdNotebook.func] --> B{子命令?}
            B -->|list_categories| C[db.list_categories → 格式化输出]
            B -->|show + 含/| D[解析 category/title → db.get_note → 输出]
            B -->|show + 不含/| E[整个作为 category → db.list_notes → 输出]
            B -->|add| F[解析 category/title = content → db.add_note]
            B -->|edit| G[解析 category/title = content → db.edit_note]
            B -->|del| H[解析 category/title → db.delete_note]
    """

    key = "nb"
    aliases = ["笔记本", "note"]
    locks = "cmd:all()"

    def parse(self):
        """解析子命令和参数。"""
        super().parse()
        raw = self.args.strip()

        if not raw:
            self.subcmd = "list_categories"
            self.rest = ""
        elif raw.startswith("add "):
            self.subcmd = "add"
            self.rest = raw[4:].strip()
        elif raw.startswith("edit "):
            self.subcmd = "edit"
            self.rest = raw[5:].strip()
        elif raw.startswith("del "):
            self.subcmd = "del"
            self.rest = raw[4:].strip()
        else:
            self.subcmd = "show"
            self.rest = raw

    def func(self):
        """分发子命令。"""
        db = NotebookDB()
        character_id = str(self.caller.dbref)

        if self.subcmd == "list_categories":
            self._list_categories(db, character_id)
        elif self.subcmd == "show":
            if "/" in self.rest:
                self._show_note(db, character_id)
            else:
                self._list_notes(db, character_id)
        elif self.subcmd == "add":
            self._add_note(db, character_id)
        elif self.subcmd == "edit":
            self._edit_note(db, character_id)
        elif self.subcmd == "del":
            self._del_note(db, character_id)

    def _list_categories(self, db, character_id):
        """列出所有分类。

        Args:
            db (NotebookDB): 数据库实例。
            character_id (str): 角色 ID。
        """
        categories = db.list_categories(character_id)
        if not categories:
            self.caller.msg("笔记本是空的。")
            return

        lines = ["笔记本分类："]
        for cat in categories:
            lines.append(f"  {cat['category']} ({cat['count']}条)")
        self.caller.msg("\n".join(lines))

    def _list_notes(self, db, character_id):
        """列出分类下所有条目。

        Args:
            db (NotebookDB): 数据库实例。
            character_id (str): 角色 ID。
        """
        category = self.rest
        notes = db.list_notes(character_id, category)
        if not notes:
            self.caller.msg(f"分类 [{category}] 是空的。")
            return

        lines = [f"[{category}]"]
        for i, note in enumerate(notes, 1):
            lines.append(f"  {i}. {note['title']} — {note['updated_at']}")
        self.caller.msg("\n".join(lines))

    def _show_note(self, db, character_id):
        """查看笔记内容。

        Args:
            db (NotebookDB): 数据库实例。
            character_id (str): 角色 ID。
        """
        parts = self.rest.split("/", 1)
        if len(parts) != 2:
            self.caller.msg("用法：nb <分类>/<标题>")
            return

        category, title = parts[0].strip(), parts[1].strip()
        note = db.get_note(character_id, category, title)
        if not note:
            self.caller.msg(f"不存在：{category}/{title}")
            return

        self.caller.msg(
            f"[{category}/{title}]\n{note['content']}"
        )

    def _add_note(self, db, character_id):
        """新增笔记。

        Args:
            db (NotebookDB): 数据库实例。
            character_id (str): 角色 ID。
        """
        parts = self._parse_add_edit_args()
        if parts is None:
            return

        category, title, content = parts
        if not db.add_note(character_id, category, title, content):
            self.caller.msg(f"已存在：{category}/{title}")
            return

        self.caller.msg(f"已记录：{category}/{title}")

    def _edit_note(self, db, character_id):
        """修改笔记。

        Args:
            db (NotebookDB): 数据库实例。
            character_id (str): 角色 ID。
        """
        parts = self._parse_add_edit_args()
        if parts is None:
            return

        category, title, content = parts
        if not db.edit_note(character_id, category, title, content):
            self.caller.msg(f"不存在：{category}/{title}")
            return

        self.caller.msg(f"已更新：{category}/{title}")

    def _del_note(self, db, character_id):
        """删除笔记。

        Args:
            db (NotebookDB): 数据库实例。
            character_id (str): 角色 ID。
        """
        parts = self.rest.split("/", 1)
        if len(parts) != 2:
            self.caller.msg("用法：nb del <分类>/<标题>")
            return

        category, title = parts[0].strip(), parts[1].strip()
        if not db.delete_note(character_id, category, title):
            self.caller.msg(f"不存在：{category}/{title}")
            return

        self.caller.msg(f"已删除：{category}/{title}")

    def _parse_add_edit_args(self):
        """解析 add/edit 的参数格式。

        格式：<分类>/<标题> = <内容>

        Returns:
            tuple or None: (category, title, content) 或 None（格式错误时）。
        """
        eq_parts = self.rest.split("=", 1)
        if len(eq_parts) != 2:
            self.caller.msg("用法：nb add <分类>/<标题> = <内容>")
            return None

        left, content = eq_parts[0].strip(), eq_parts[1].strip()
        slash_parts = left.split("/", 1)
        if len(slash_parts) != 2:
            self.caller.msg("用法：nb add <分类>/<标题> = <内容>")
            return None

        category, title = slash_parts[0].strip(), slash_parts[1].strip()
        return category, title, content

"""
笔记本系统 SQLite 数据层

提供基于 SQLite 的分类笔记增删改查。

数据库路径：data/notebook.db

详见：docs/设计文档/解决饥饿/详细设计/笔记本系统详细设计.md
"""

import os
import sqlite3

# 数据库默认路径：项目根目录/data/notebook.db
_DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "notebook.db",
)


class NotebookDB:
    """笔记本 SQLite 数据层。

    每次操作使用 `with sqlite3.connect()` 上下文管理，操作完自动关闭。
    character_id 使用 `str(caller.dbref)` 格式，如 `"#42"`。
    """

    def __init__(self, db_path=None):
        """初始化数据库连接，自动建表。

        Args:
            db_path (str, optional): 数据库文件路径，默认为 data/notebook.db。
        """
        self.db_path = db_path or _DEFAULT_DB_PATH
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        self._ensure_table()

    def _ensure_table(self):
        """确保 notebook 表存在。"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS notebook (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    character_id TEXT NOT NULL,
                    category TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT DEFAULT '',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(character_id, category, title)
                )
                """
            )

    def list_categories(self, character_id):
        """返回角色的所有分类名，按条目数降序。

        Args:
            character_id (str): 角色 ID（如 "#42"）。

        Returns:
            list[str]: 分类名列表。
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT category, COUNT(*) as cnt
                FROM notebook
                WHERE character_id = ?
                GROUP BY category
                ORDER BY cnt DESC
                """,
                (character_id,),
            )
            return [{"category": row[0], "count": row[1]} for row in cursor.fetchall()]

    def list_notes(self, character_id, category):
        """返回某分类下所有条目。

        Args:
            character_id (str): 角色 ID。
            category (str): 分类名。

        Returns:
            list[dict]: 每项含 id, title, updated_at。
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT id, title, updated_at
                FROM notebook
                WHERE character_id = ? AND category = ?
                ORDER BY updated_at DESC
                """,
                (character_id, category),
            )
            return [
                {"id": row[0], "title": row[1], "updated_at": row[2]}
                for row in cursor.fetchall()
            ]

    def get_note(self, character_id, category, title):
        """获取单条笔记。

        Args:
            character_id (str): 角色 ID。
            category (str): 分类名。
            title (str): 笔记标题。

        Returns:
            dict or None: 含 id, title, content, created_at, updated_at，不存在返回 None。
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT id, title, content, created_at, updated_at
                FROM notebook
                WHERE character_id = ? AND category = ? AND title = ?
                """,
                (character_id, category, title),
            )
            row = cursor.fetchone()
            if row is None:
                return None
            return {
                "id": row[0],
                "title": row[1],
                "content": row[2],
                "created_at": row[3],
                "updated_at": row[4],
            }

    def add_note(self, character_id, category, title, content):
        """新增笔记。

        Args:
            character_id (str): 角色 ID。
            category (str): 分类名。
            title (str): 笔记标题。
            content (str): 笔记内容。

        Returns:
            bool: 成功返回 True，已存在返回 False。
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO notebook (character_id, category, title, content)
                    VALUES (?, ?, ?, ?)
                    """,
                    (character_id, category, title, content),
                )
            return True
        except sqlite3.IntegrityError:
            return False

    def edit_note(self, character_id, category, title, content):
        """修改笔记内容和 updated_at。

        Args:
            character_id (str): 角色 ID。
            category (str): 分类名。
            title (str): 笔记标题。
            content (str): 新内容。

        Returns:
            bool: 成功返回 True，不存在返回 False。
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                UPDATE notebook
                SET content = ?, updated_at = CURRENT_TIMESTAMP
                WHERE character_id = ? AND category = ? AND title = ?
                """,
                (content, character_id, category, title),
            )
            return cursor.rowcount > 0

    def delete_note(self, character_id, category, title):
        """删除笔记。

        Args:
            character_id (str): 角色 ID。
            category (str): 分类名。
            title (str): 笔记标题。

        Returns:
            bool: 成功返回 True，不存在返回 False。
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                DELETE FROM notebook
                WHERE character_id = ? AND category = ? AND title = ?
                """,
                (character_id, category, title),
            )
            return cursor.rowcount > 0

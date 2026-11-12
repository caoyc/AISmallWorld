"""分类路径校验与矫正。

输入路径不合法时**就地矫正成合法类别路径**（而非拒掉）——校验不是目的，
矫正成可用类别才是。矫正范围：字符级非法 → '_'、冗余 // 与结尾 / 归一；
只剩结构性不可救（空路径、非绝对路径）才拒绝。

注：这里的"合法"是分类节点的命名规范（仅许字母/数字/下划线/中划线/指定
Unicode 段，禁空格/点/标点/控制字符），比 OS 层 POSIX 规则（只禁 / 与 NUL）更严；
非"Linux 路径合法性"。
"""

import re


class PathValidator:
    """分类路径校验与矫正器。

    命名规范（比 OS POSIX 更严的产品策略）：
    - 绝对路径，以 / 开头
    - / 分隔每一级
    - 有效字符：字母、数字、下划线、中划线、指定 Unicode 段
    - 禁止：空格、点、标点、控制字符、连续 //、以 / 结尾（根 / 除外）
    - 大小写敏感
    """

    # 首字符与内部字符的合法集（命名规范本体；首字符限 [\w-]，内部允许扩展 Unicode 段）
    _FIRST_CHAR_RE = re.compile(r"[\w\-]", re.UNICODE)
    _INNER_CHAR_RE = re.compile(r"[\w\-·一-鿿㐀-䶿　-〿＀-￯]", re.UNICODE)

    @staticmethod
    def validate(path: str) -> tuple[str | None, str]:
        """检查并矫正路径，返回 ``(合法路径 | None, 错误信息)``。

        错误信息为空即成功（路径已就绪可用，含已矫正的情形）。

        矫正（就地修正、返回合法路径）：
        - 字符级非法（空格 / 点 / 标点 / 控制字符等）→ ``_``
        - 冗余 ``//``、结尾 ``/`` → 归一（去空段）

        拒绝（结构性、无法矫正）：
        - 空路径
        - 非绝对路径（不以 ``/`` 开头）

        Args:
            path: 待检查的路径字符串

        Returns:
            ``(合法路径 | None, 错误信息)``。成功时错误信息为空、首项即可用路径。
        """
        if not path:
            return None, "路径不能为空"
        if not path.startswith("/"):
            return None, "路径必须以 / 开头（绝对路径）"
        if path == "/":
            return "/", ""
        # split 去空段：顺带吃掉 // 与结尾 /；逐级矫正非法字符
        segments = [s for s in path.split("/") if s]
        corrected = "/" + "/".join(PathValidator._correct_segment(s) for s in segments)
        return corrected, ""

    @staticmethod
    def _correct_segment(seg: str) -> str:
        """逐位矫正一个层级名称：首字符不在合法首集、内部字符不在合法内集 → ``_``。"""
        if not seg:
            return seg
        out = []
        for i, ch in enumerate(seg):
            cls = PathValidator._FIRST_CHAR_RE if i == 0 else PathValidator._INNER_CHAR_RE
            out.append(ch if cls.match(ch) else "_")
        return "".join(out)

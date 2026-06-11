"""
v2 map 指令 — 查看当前位置地图

显示当前房间和紧邻房间的 ASCII 地图。
从当前房间的出口方向推断相邻房间的方位。

用法：map
"""

from .base import SurvivalCommand

# 出口方向 → 网格位置 (col, row)
_DIR_POS = {
    "北": (1, 0),
    "南": (1, 2),
    "东": (2, 1),
    "西": (0, 1),
    "东南": (2, 2),
    "西北": (0, 0),
    "东北": (2, 0),
    "西南": (0, 2),
}

# 列间距（字符数）
_GAP = 3


def _display_width(s):
    """计算字符串的终端显示宽度（CJK 字符 = 2，ASCII = 1）。"""
    w = 0
    for ch in s:
        cp = ord(ch)
        if (0x4E00 <= cp <= 0x9FFF or
            0x3000 <= cp <= 0x303F or
            0xFF00 <= cp <= 0xFFEF or
            0x3400 <= cp <= 0x4DBF or
            0x2E80 <= cp <= 0x2EFF or
            0xF900 <= cp <= 0xFAFF):
            w += 2
        else:
            w += 1
    return w


def _pad_center(s, width):
    """将字符串居中填充到指定显示宽度。"""
    current = _display_width(s)
    pad = max(0, width - current)
    left = pad // 2
    right = pad - left
    return ' ' * left + s + ' ' * right


def _render_map(center_name, exits_info):
    """渲染 3×3 格位地图。

    Args:
        center_name: 当前房间名称。
        exits_info: [(出口方向key, 目标房间名称), ...]

    Returns:
        str: ASCII 地图文本。
    """
    # 构建网格
    grid = [[None] * 3 for _ in range(3)]
    grid[1][1] = f"*{center_name}"

    for dir_key, dest_name in exits_info:
        pos = _DIR_POS.get(dir_key)
        if pos:
            grid[pos[1]][pos[0]] = dest_name

    # 计算每列最大显示宽度
    col_w = [0, 0, 0]
    for r in range(3):
        for c in range(3):
            if grid[r][c]:
                col_w[c] = max(col_w[c], _display_width(grid[r][c]))

    # 列起始 x 位置
    col_x = [0]
    for c in range(1, 3):
        col_x.append(col_x[c - 1] + col_w[c - 1] + _GAP)

    total_w = col_x[2] + col_w[2]

    if total_w == 0:
        return center_name

    # ── 辅助：构建房间名行 ──
    def build_room_row(r):
        parts = []
        for c in range(3):
            name = grid[r][c]
            parts.append(_pad_center(name or '', col_w[c]) if col_w[c] > 0 else '')
        return (' ' * _GAP).join(parts).rstrip()

    # ── 辅助：构建中间行（含水平连接线）──
    def build_middle_row():
        parts = []
        for c in range(3):
            parts.append(_pad_center(grid[1][c] or '', col_w[c]) if col_w[c] > 0 else '')

        # 左间隙：W 和 Center 之间
        w_conn = "───" if grid[1][0] else "   "
        # 右间隙：Center 和 E 之间
        e_conn = "───" if grid[1][2] else "   "

        left = parts[0] if len(parts) > 0 else ''
        mid = parts[1] if len(parts) > 1 else ''
        right = parts[2] if len(parts) > 2 else ''

        result = ''
        if col_w[0] > 0:
            result = left.rstrip() + w_conn
        result += mid.rstrip()
        if col_w[2] > 0:
            result += e_conn + right.lstrip()
        return result

    # ── 辅助：构建连接行 ──
    def build_conn_row(row_idx):
        """构建连接行。row_idx=1 为顶部连接，row_idx=3 为底部连接。"""
        row = [' '] * total_w

        is_top = (row_idx == 1)

        # 判断哪些方向有连接
        if is_top:
            # 上方行：NW, N, NE → 连接到 Center
            n_dir, nw_dir, ne_dir = "北", "西北", "东北"
            n_pos = (1, 0)
            nw_pos = (0, 0)
            ne_pos = (2, 0)
        else:
            # 下方行：SW, S, SE → 连接到 Center
            n_dir, nw_dir, ne_dir = "南", "西南", "东南"
            n_pos = (1, 2)
            nw_pos = (0, 2)
            ne_pos = (2, 2)

        # 北/南：垂直线 │
        if grid[n_pos[1]][n_pos[0]]:
            cx = col_x[1] + col_w[1] // 2
            if 0 <= cx < total_w:
                row[cx] = '│'

        # 左列对角线：NW→Center 用 ╲，SW→Center 用 ╱
        if grid[nw_pos[1]][nw_pos[0]] and col_w[0] > 0:
            gx = col_x[0] + col_w[0] + _GAP // 2
            if 0 <= gx < total_w:
                row[gx] = '╲' if is_top else '╱'

        # 右列对角线：NE→Center 用 ╱，SE→Center 用 ╲
        if grid[ne_pos[1]][ne_pos[0]] and col_w[2] > 0:
            gx = col_x[1] + col_w[1] + _GAP // 2
            if 0 <= gx < total_w:
                row[gx] = '╱' if is_top else '╲'

        result = ''.join(row).rstrip()
        return result if result.strip() else None

    # ── 组装 5 行 ──
    lines = []

    # 第 1 行：顶部房间
    top = build_room_row(0)
    if top.strip():
        lines.append(top)

    # 第 2 行：顶部连接
    conn1 = build_conn_row(1)
    if conn1:
        lines.append(conn1)

    # 第 3 行：中间房间（含水平连接）
    lines.append(build_middle_row())

    # 第 4 行：底部连接
    conn2 = build_conn_row(3)
    if conn2:
        lines.append(conn2)

    # 第 5 行：底部房间
    bottom = build_room_row(2)
    if bottom.strip():
        lines.append(bottom)

    return '\n'.join(lines)


class CmdMap(SurvivalCommand):
    """
    查看地图

    用法：
      map    — 显示当前位置和紧邻房间的地图
    """

    key = "map"
    help_category = "行动"
    stamina_cost = 0

    def func(self):
        caller = self.caller
        room = caller.location
        if not room:
            caller.msg("你不在任何地方。")
            return

        # 收集出口信息
        exits_info = []
        for exit_obj in room.exits:
            if exit_obj.destination:
                exits_info.append((exit_obj.key, exit_obj.destination.key))

        map_text = _render_map(room.key, exits_info)
        caller.msg(map_text)

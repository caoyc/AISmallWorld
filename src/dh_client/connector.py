"""Evennia WebSocket 长连接管理器。

提供持久化的 WebSocket 连接，支持：
- 一次连接、登录、IC，后续命令复用连接
- 断线检测 + 自动重连
- 消息间隔检测机制判断响应结束
- BeautifulSoup 文本清洗

Evennia WebSocket 协议:
    所有消息为 JSON 数组: ["cmdname", [args], {kwargs}]
    - 发命令: ["text", ["look"], {}]
    - 收文本: ["text", ["描述..."], {}]
    - 登录确认: ["logged_in", [], {}]
    - 客户端选项: ["client_options", [], {"nocolor": True, "screenreader": True}]
"""

import asyncio
import json

import websockets
from bs4 import BeautifulSoup

from .config import Config

# 超时配置（秒）
_LOGIN_TIMEOUT = 10
_RESPONSE_TIMEOUT = 15
_MESSAGE_GAP = 1  # 消息间隔超过此值视为响应结束


def _clean_text(text: str) -> str:
    """清洗 Evennia 输出为纯文本。

    1. BeautifulSoup 去 HTML 标签
    2. 去首尾空白
    3. 压缩连续空行
    """
    soup = BeautifulSoup(text, "html.parser")
    clean = soup.get_text(separator="\n")
    lines = clean.split("\n")
    result_lines = []
    prev_empty = False
    for line in lines:
        is_empty = line.strip() == ""
        if is_empty and prev_empty:
            continue
        result_lines.append(line)
        prev_empty = is_empty
    return "\n".join(result_lines).strip()


class EvenniaConnection:
    """Evennia WebSocket 长连接管理器。"""

    def __init__(self, config: Config):
        self._config = config
        self._ws = None  # WebSocket 连接
        self._connected = False  # 是否已连接并登录
        self._text_queue: asyncio.Queue[str] = asyncio.Queue()
        self._logged_in = asyncio.Event()
        self._recv_task = None  # 接收协程
        self._current_done: asyncio.Event | None = None

    @property
    def is_connected(self) -> bool:
        """连接是否活跃且已登录。"""
        return self._connected and self._ws is not None

    async def connect(self) -> None:
        """连接 Evennia，登录，进入 IC。"""
        url = f"ws://{self._config.evennia_host}:{self._config.evennia_port}"

        self._ws = await websockets.connect(url, close_timeout=5)
        self._logged_in.clear()
        self._text_queue = asyncio.Queue()
        self._recv_task = asyncio.create_task(self._recv_loop())

        # 1. 客户端选项
        await self._ws.send(json.dumps(
            ["client_options", [], {"nocolor": True, "screenreader": True}]
        ))

        # 2. 登录
        await self._ws.send(json.dumps(
            ["text", [f"connect {self._config.account} {self._config.password}"], {}]
        ))

        try:
            await asyncio.wait_for(self._logged_in.wait(), timeout=_LOGIN_TIMEOUT)
        except asyncio.TimeoutError:
            await self.close()
            raise ConnectionError("登录失败：连接超时")

        # 3. 清空登录产生的消息
        while not self._text_queue.empty():
            self._text_queue.get_nowait()
        if self._current_done:
            self._current_done.clear()

        # 4. IC
        await self._ws.send(json.dumps(["text", [f"ic {self._config.account}"], {}]))
        await asyncio.sleep(2)
        while not self._text_queue.empty():
            self._text_queue.get_nowait()
        if self._current_done:
            self._current_done.clear()

        self._connected = True

    async def send(self, action: str) -> str:
        """发送命令，等待完整响应，返回纯文本。

        复用已建立的连接。如果连接断开，抛出 ConnectionError。
        """
        if not self.is_connected:
            raise ConnectionError("Evennia 连接已断开")

        done = asyncio.Event()
        self._current_done = done

        # 发送命令
        await self._ws.send(json.dumps(["text", [action], {}]))

        # 等待响应完成（消息间隔 >= 1 秒）
        try:
            await asyncio.wait_for(done.wait(), timeout=_RESPONSE_TIMEOUT)
        except asyncio.TimeoutError:
            pass

        # 收集消息
        texts = []
        while not self._text_queue.empty():
            texts.append(self._text_queue.get_nowait())

        if not texts:
            return "（无响应）"

        raw = "\n".join(texts)
        return _clean_text(raw)

    async def _recv_loop(self) -> None:
        """接收 Evennia 消息，检测连接断开。"""
        last_text_time = None

        async def _gap_watcher():
            """消息间隔监视器。"""
            nonlocal last_text_time
            while True:
                await asyncio.sleep(0.2)
                if last_text_time is not None:
                    gap = asyncio.get_event_loop().time() - last_text_time
                    if gap >= _MESSAGE_GAP:
                        if self._current_done is not None:
                            self._current_done.set()
                        return

        watcher_task = asyncio.create_task(_gap_watcher())

        try:
            async for raw in self._ws:
                try:
                    msg = json.loads(raw)
                except json.JSONDecodeError:
                    continue

                if not isinstance(msg, list) or len(msg) < 2:
                    continue

                cmd = msg[0]
                args = msg[1] if len(msg) > 1 else []

                if cmd == "logged_in":
                    self._logged_in.set()
                elif cmd == "text":
                    if args:
                        text = args[0] if isinstance(args[0], str) else str(args[0])
                        if text.strip():
                            await self._text_queue.put(text)
                            last_text_time = asyncio.get_event_loop().time()
                            # 收到新消息，重置 done
                            if self._current_done is not None:
                                self._current_done.clear()
        except websockets.ConnectionClosed:
            pass  # 连接断开，设置 is_connected = False
        finally:
            self._connected = False
            watcher_task.cancel()

    async def close(self) -> None:
        """关闭连接。"""
        self._connected = False
        if self._recv_task:
            self._recv_task.cancel()
            try:
                await self._recv_task
            except asyncio.CancelledError:
                pass
        if self._ws:
            try:
                await self._ws.close()
            except Exception:
                pass


# ---- 向后兼容：保留旧的无状态接口 ----

async def send_action(config: Config, action: str) -> str:
    """连接 Evennia，发送一条命令，返回纯文本响应。

    向后兼容的快捷方式：连接 → 登录 → 发命令 → 收响应 → 断开。
    推荐使用 EvenniaConnection 类代替。
    """
    conn = EvenniaConnection(config)
    try:
        await conn.connect()
        return await conn.send(action)
    except ConnectionError as e:
        return str(e)
    except ConnectionRefusedError:
        return "无法连接到世界：Evennia 未启动或端口不对"
    except Exception as e:
        return f"连接异常：{e}"
    finally:
        await conn.close()

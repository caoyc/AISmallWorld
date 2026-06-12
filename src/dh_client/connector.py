"""Evennia WebSocket 长连接管理器。

回调驱动：Evennia 每推一条消息，立即触发 on_text 回调。
不再使用消息间隔检测队列模式，消除所有延迟。

同时保留 send() 方法供请求-响应式调用（CLI）。
"""

import asyncio
import json
from typing import Awaitable, Callable, Optional

import websockets
from bs4 import BeautifulSoup

from .config import Config

# 超时配置（秒）
_LOGIN_TIMEOUT = 10


def _clean_text(text: str) -> str:
    """清洗 Evennia 输出为纯文本。"""
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
    """Evennia WebSocket 长连接管理器（回调驱动）。"""

    def __init__(self, config: Config):
        self._config = config
        self._ws = None
        self._connected = False
        self._logged_in = False
        self._recv_task = None

        # 回调：Evennia 每推一条文本消息，立即触发
        self._on_text: Optional[Callable[[str], Awaitable[None]]] = None

        # 登录等待
        self._login_event = asyncio.Event()

        # 账号密码（断线重连用）
        self._account: Optional[str] = None
        self._password: Optional[str] = None

    @property
    def is_connected(self) -> bool:
        return self._connected and self._ws is not None

    def on_text(self, callback: Callable[[str], Awaitable[None]]) -> None:
        """注册文本消息回调。每条 Evennia 文本到达时立即触发。"""
        self._on_text = callback

    async def connect(self) -> None:
        """连接 Evennia，登录，进入 IC。"""
        url = f"ws://{self._config.evennia_host}:{self._config.evennia_port}"

        self._ws = await websockets.connect(url, close_timeout=5)
        self._connected = True
        self._login_event.clear()
        self._recv_task = asyncio.create_task(self._recv_loop())

        # 1. 客户端选项
        await self._ws.send(json.dumps(
            ["client_options", [], {"nocolor": True, "screenreader": True}]
        ))

        # 2. 登录
        self._account = self._config.account
        self._password = self._config.password
        await self._ws.send(json.dumps(
            ["text", [f"connect {self._account} {self._password}"], {}]
        ))

        try:
            await asyncio.wait_for(self._login_event.wait(), timeout=_LOGIN_TIMEOUT)
        except asyncio.TimeoutError:
            await self.close()
            raise ConnectionError("登录失败：连接超时")

        # 3. IC
        await self._ws.send(json.dumps(["text", [f"ic {self._config.account}"], {}]))
        await asyncio.sleep(2)  # 等 IC 消息输出完毕

        self._logged_in = True

    async def send_command(self, command: str) -> None:
        """发送游戏命令（不等响应，响应通过 on_text 回调异步到达）。"""
        if not self.is_connected:
            raise ConnectionError("Evennia 连接已断开")
        await self._ws.send(json.dumps(["text", [command], {}]))

    async def close(self) -> None:
        """关闭连接。"""
        self._connected = False
        self._logged_in = False
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

    async def _recv_loop(self) -> None:
        """接收 Evennia 消息，立即触发回调。"""
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
                    self._logged_in = True
                    self._login_event.set()

                elif cmd == "text":
                    if args:
                        text = args[0] if isinstance(args[0], str) else str(args[0])
                        cleaned = _clean_text(text)
                        if cleaned.strip() and self._on_text:
                            await self._on_text(cleaned)

        except websockets.ConnectionClosed:
            pass
        finally:
            self._connected = False
            self._logged_in = False


# ---- 向后兼容：保留旧的无状态接口 ----

async def send_action(config: Config, action: str) -> str:
    """向后兼容：连接 → 登录 → 发命令 → 收响应 → 断开。"""
    texts = []
    event = asyncio.Event()

    async def _collect(text: str):
        texts.append(text)
        event.set()

    conn = EvenniaConnection(config)
    conn.on_text(_collect)
    try:
        await conn.connect()
        await conn.send_command(action)
        # 等第一条响应
        await asyncio.wait_for(event.wait(), timeout=15)
        return "\n".join(texts)
    except ConnectionError as e:
        return str(e)
    except ConnectionRefusedError:
        return "无法连接到世界：Evennia 未启动或端口不对"
    except Exception as e:
        return f"连接异常：{e}"
    finally:
        await conn.close()

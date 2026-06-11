"""Evennia WebSocket 连接器。

连接 Evennia，发送一条命令，收集完整响应，返回纯文本。

流程:
    1. WebSocket 连接 Evennia
    2. 发送 client_options（nocolor + screenreader）
    3. 登录（等待 logged_in 信号）
    4. 发送命令
    5. 收集响应（等待消息间隔 >= 1 秒，视为响应结束）
    6. 清洗输出（BeautifulSoup 去 HTML）
    7. 关闭连接

Evennia WebSocket 协议:
    所有消息为 JSON 数组: ["cmdname", [args], {kwargs}]
    - 发命令: ["text", ["look"], {}]
    - 收文本: ["text", ["描述..."], {}]
    - 登录确认: ["logged_in", [], {}]
    - 客户端选项: ["client_options", [], {"nocolor": True, "screenreader": True}]

注意:
    Evennia 不一定发送 prompt 消息，因此不能用 prompt 作为响应结束信号。
    改用消息间隔检测：收到第一条消息后，如果 1 秒内没有新消息，视为响应结束。
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


async def send_action(config: Config, action: str) -> str:
    """连接 Evennia，发送一条命令，返回纯文本响应。

    每次调用独立：连接 → 登录 → 发命令 → 收响应 → 断开。
    """
    url = f"ws://{config.evennia_host}:{config.evennia_port}"

    try:
        async with websockets.connect(url, close_timeout=5) as ws:
            logged_in = asyncio.Event()
            text_queue: asyncio.Queue[str] = asyncio.Queue()
            done = asyncio.Event()

            recv_task = asyncio.create_task(
                _recv_loop(ws, text_queue, logged_in, done)
            )

            try:
                # 1. 客户端选项
                await ws.send(json.dumps(
                    ["client_options", [], {"nocolor": True, "screenreader": True}]
                ))

                # 2. 登录
                await ws.send(json.dumps(
                    ["text", [f"connect {config.account} {config.password}"], {}]
                ))

                try:
                    await asyncio.wait_for(logged_in.wait(), timeout=_LOGIN_TIMEOUT)
                except asyncio.TimeoutError:
                    return "登录失败：连接超时"

                # 3. 清空登录产生的消息（自动 look 等）
                while not text_queue.empty():
                    text_queue.get_nowait()
                done.clear()

                # 3.5 进入游戏（IC）
                await ws.send(json.dumps(["text", [f"ic {config.account}"], {}]))
                await asyncio.sleep(2)
                while not text_queue.empty():
                    text_queue.get_nowait()
                done.clear()

                # 4. 发送命令
                await ws.send(json.dumps(["text", [action], {}]))

                # 5. 等待响应完成（done 事件由 _recv_loop 设置）
                try:
                    await asyncio.wait_for(done.wait(), timeout=_RESPONSE_TIMEOUT)
                except asyncio.TimeoutError:
                    # 超时也返回已收集的内容
                    pass

                # 6. 收集消息
                texts = []
                while not text_queue.empty():
                    texts.append(text_queue.get_nowait())

                if not texts:
                    return "（无响应）"

                raw = "\n".join(texts)
                return _clean_text(raw)

            finally:
                recv_task.cancel()
                try:
                    await recv_task
                except asyncio.CancelledError:
                    pass

    except ConnectionRefusedError:
        return "无法连接到世界：Evennia 未启动或端口不对"
    except Exception as e:
        return f"连接异常：{e}"


async def _recv_loop(
    ws,
    text_queue: asyncio.Queue,
    logged_in: asyncio.Event,
    done: asyncio.Event,
) -> None:
    """接收 Evennia 消息。

    响应完成检测：收到第一条 text 后启动间隔计时器，
    每收到新 text 重置计时器，间隔超 1 秒无新消息则设置 done。
    """
    last_text_time = None

    async def _gap_watcher():
        """消息间隔监视器。"""
        nonlocal last_text_time
        while True:
            await asyncio.sleep(0.2)
            if last_text_time is not None:
                gap = asyncio.get_event_loop().time() - last_text_time
                if gap >= _MESSAGE_GAP:
                    done.set()
                    return

    watcher_task = asyncio.create_task(_gap_watcher())

    try:
        async for raw in ws:
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            if not isinstance(msg, list) or len(msg) < 2:
                continue

            cmd = msg[0]
            args = msg[1] if len(msg) > 1 else []

            if cmd == "logged_in":
                logged_in.set()

            elif cmd == "text":
                if args:
                    text = args[0] if isinstance(args[0], str) else str(args[0])
                    if text.strip():
                        await text_queue.put(text)
                        last_text_time = asyncio.get_event_loop().time()
                        # 收到新消息，重置 done（可能被 watcher 设置后又来了新消息）
                        done.clear()
    finally:
        watcher_task.cancel()

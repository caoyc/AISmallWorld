"""dh_client 守护进程。

架构：
- connector 回调驱动：Evennia 每推一条消息，立即通过 on_text 回调转发
- HTTP API (5000)：发命令后等待响应返回给 CLI（兼容现有用法）
- SSE 旁观 (8080)：实时推送所有消息给浏览器（包括服务器主动推送）
- 两者不冲突：回调同时推给旁观者和等待中的 HTTP 请求

启动方式:
    cd AISmallWorld
    PYTHONPATH=src python -m dh_client.daemon
"""

import asyncio
import json
import os
import signal
import sys
from dataclasses import dataclass, field
from datetime import datetime

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

from aiohttp import web

from .config import Config, load_config
from .connector import EvenniaConnection


# ---- 数据结构 ----


@dataclass
class Observer:
    """旁观者连接。"""
    resp: web.StreamResponse

    async def send_event(self, event_type: str, data: dict):
        try:
            payload = json.dumps(data, ensure_ascii=False)
            await self.resp.write(f"event: {event_type}\ndata: {payload}\n\n".encode("utf-8"))
        except (ConnectionResetError, RuntimeError):
            pass


@dataclass
class DaemonState:
    config: Config
    conn: EvenniaConnection | None = None
    observers: list = field(default_factory=list)
    action_log: list = field(default_factory=list)
    _stop_event: asyncio.Event = field(default_factory=asyncio.Event)

    # HTTP 响应等待：发送命令后，on_text 回调收集响应并设置 future
    _response_future: asyncio.Future | None = None
    _response_texts: list = field(default_factory=list)
    _response_timer_task: asyncio.Task | None = None

    # 未读消息：两次命令之间到达的消息（椰子掉落、被攻击、别人说话……）
    _unread: list = field(default_factory=list)

    # 持久化日志路径
    _log_path: str = ""


def _now_ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _get_log_dir() -> str:
    """日志目录：项目根目录/logs/"""
    root = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
    log_dir = os.path.join(root, "logs")
    os.makedirs(log_dir, exist_ok=True)
    return log_dir


def _get_log_path() -> str:
    """本次会话的日志文件路径：logs/observer_YYYY-MM-DD_HH-MM-SS.jsonl"""
    log_dir = _get_log_dir()
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return os.path.join(log_dir, f"observer_{ts}.jsonl")


def _persist_entry(log_path: str, entry: dict):
    """追加一条日志到 JSONL 文件。"""
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        pass


def _load_history(log_path: str) -> list:
    """从 JSONL 文件加载全部历史记录。"""
    if not os.path.exists(log_path):
        return []
    entries = []
    try:
        with open(log_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))
    except (OSError, json.JSONDecodeError):
        pass
    return entries


# ---- Evennia 消息回调 ----


async def _on_evennia_text(state: DaemonState, text: str):
    """Evennia 每推一条消息，立即触发。

    1. 广播给所有旁观者（实时推送）
    2. 如果有 HTTP 请求在等响应，收集文本
    """
    ts = _now_ts()

    # 1. 广播给旁观者
    for obs in list(state.observers):
        await obs.send_event("resp", {"ts": ts, "text": text})

    # 2. 如果有 HTTP 请求在等响应，收集文本；否则记录日志
    if state._response_future and not state._response_future.done():
        state._response_texts.append(text)
        # 重置计时器：收到新消息，重新等 0.5 秒
        if state._response_timer_task:
            state._response_timer_task.cancel()
        state._response_timer_task = asyncio.create_task(
            _response_timeout(state, 0.5)
        )
    else:
        # 没人在等 → 未读消息（椰子掉落、被攻击、社交……），记录日志
        state._unread.append({"ts": ts, "text": text})
        entry = {"ts": ts, "text": text}
        state.action_log.append(entry)
        if len(state.action_log) > 1000:
            state.action_log = state.action_log[-500:]
        _persist_entry(state._log_path, entry)


async def _response_timeout(state: DaemonState, delay: float):
    """响应超时：等待 delay 秒没有新消息，认为响应结束。"""
    await asyncio.sleep(delay)
    if state._response_future and not state._response_future.done():
        texts = state._response_texts
        state._response_texts = []
        state._response_future.set_result("\n".join(texts) if texts else "（无响应）")


# ---- HTTP API (端口 5000) ----


async def _handle_action(request: web.Request) -> web.Response:
    """POST /action — Agent 发送命令，等待响应返回。"""
    state: DaemonState = request.app["state"]

    try:
        body = await request.json()
    except json.JSONDecodeError:
        return web.json_response({"ok": False, "error": "无效的 JSON"}, status=400)

    action = body.get("action", "").strip()
    if not action:
        return web.json_response({"ok": False, "error": "缺少 action 字段"}, status=400)

    if not state.conn or not state.conn.is_connected:
        return web.json_response({"ok": False, "error": "与世界的连接中断了，正在重连"})

    ts = _now_ts()

    # 广播命令给旁观者
    for obs in list(state.observers):
        await obs.send_event("cmd", {"ts": ts, "action": action})

    # 先取走所有未读消息
    unread = state._unread
    state._unread = []

    # 设置响应等待
    state._response_future = asyncio.get_event_loop().create_future()
    state._response_texts = []

    try:
        await state.conn.send_command(action)
    except ConnectionError:
        # 归还未读消息
        state._unread = unread + state._unread
        return web.json_response({"ok": False, "error": "连接中断，正在重连"})

    # 等待响应（回调收集文本，超时触发返回）
    try:
        response = await asyncio.wait_for(state._response_future, timeout=15)
    except asyncio.TimeoutError:
        response = "\n".join(state._response_texts) if state._response_texts else "（无响应）"
        state._response_texts = []

    state._response_future = None
    if state._response_timer_task:
        state._response_timer_task.cancel()
        state._response_timer_task = None

    # 记录
    entry = {"ts": ts, "action": action, "response": response}
    state.action_log.append(entry)
    if len(state.action_log) > 1000:
        state.action_log = state.action_log[-500:]
    _persist_entry(state._log_path, entry)

    result = {
        "ok": True,
        "response": response,
    }
    if unread:
        result["unread"] = [u["text"] for u in unread]

    return web.json_response(result)


async def _handle_status(request: web.Request) -> web.Response:
    state: DaemonState = request.app["state"]
    connected = state.conn is not None and state.conn.is_connected
    return web.json_response({"connected": connected, "account": state.config.account})


# ---- SSE 旁观端点 (端口 8080) ----


async def _handle_history(request: web.Request) -> web.Response:
    """GET /history — 返回全量历史记录。支持 ?limit=N 只返回最近 N 条。"""
    state: DaemonState = request.app["state"]
    limit = request.query.get("limit")
    entries = _load_history(state._log_path)
    if limit:
        try:
            n = int(limit)
            entries = entries[-n:]
        except ValueError:
            pass
    return web.json_response(entries)


async def _observer_page(request: web.Request) -> web.Response:
    html_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    return web.FileResponse(html_path)


async def _observer_events(request: web.Request) -> web.StreamResponse:
    resp = web.StreamResponse()
    resp.content_type = "text/event-stream"
    resp.headers["Cache-Control"] = "no-cache"
    resp.headers["Connection"] = "keep-alive"
    resp.headers["Access-Control-Allow-Origin"] = "*"
    await resp.prepare(request)

    observer = Observer(resp=resp)
    state: DaemonState = request.app["state"]
    state.observers.append(observer)

    # 推送连接状态
    connected = state.conn is not None and state.conn.is_connected
    await observer.send_event("status", {"connected": connected})

    # 回放最近日志
    for entry in state.action_log[-50:]:
        if "action" in entry:
            await observer.send_event("cmd", {"ts": entry["ts"], "action": entry["action"]})
        await observer.send_event("resp", {"ts": entry["ts"], "text": entry.get("response", entry.get("text", ""))})

    try:
        await state._stop_event.wait()
    except asyncio.CancelledError:
        pass
    finally:
        if observer in state.observers:
            state.observers.remove(observer)

    return resp


# ---- 断线重连 ----


async def _watch_connection(state: DaemonState):
    retry_count = 0
    while not state._stop_event.is_set():
        await asyncio.sleep(1)
        if state._stop_event.is_set():
            break
        if state.conn and state.conn.is_connected:
            retry_count = 0
            continue
        retry_count += 1
        print(f"[daemon] 连接断开，第 {retry_count} 次重连...")
        for obs in list(state.observers):
            await obs.send_event("status", {"connected": False})
        wait = 3 if retry_count <= 10 else 30
        await asyncio.sleep(wait)
        if state._stop_event.is_set():
            break
        if state.conn:
            await state.conn.close()
        state.conn = EvenniaConnection(state.config)
        state.conn.on_text(lambda text: _on_evennia_text(state, text))
        try:
            await state.conn.connect()
            print("[daemon] 重连成功")
            for obs in list(state.observers):
                await obs.send_event("status", {"connected": True})
            retry_count = 0
        except Exception as e:
            print(f"[daemon] 重连失败: {e}")


# ---- 服务启动 ----


async def _serve_api(state: DaemonState):
    app = web.Application()
    app["state"] = state
    app.router.add_post("/action", _handle_action)
    app.router.add_get("/status", _handle_status)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 5000)
    await site.start()
    print("[daemon] HTTP API 已启动: http://localhost:5000")


async def _serve_observer(state: DaemonState):
    app = web.Application()
    app["state"] = state
    app.router.add_get("/", _observer_page)
    app.router.add_get("/events", _observer_events)
    app.router.add_get("/history", _handle_history)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()
    print("[daemon] 旁观页面已启动: http://localhost:8080")


async def _sse_heartbeat(state: DaemonState):
    while not state._stop_event.is_set():
        await asyncio.sleep(30)
        for obs in list(state.observers):
            try:
                await obs.resp.write(b": keepalive\n\n")
            except (ConnectionResetError, RuntimeError):
                pass


# ---- 主入口 ----


async def _run(state: DaemonState):
    # 加载历史记录
    state._log_path = _get_log_path()
    history = _load_history(state._log_path)
    state.action_log = history
    print(f"[daemon] 已加载 {len(history)} 条历史记录")

    print("[daemon] 正在连接 Evennia...")
    state.conn = EvenniaConnection(state.config)
    state.conn.on_text(lambda text: _on_evennia_text(state, text))
    try:
        await state.conn.connect()
        print(f"[daemon] 已连接 Evennia，账号: {state.config.account}")
    except Exception as e:
        print(f"[daemon] 连接 Evennia 失败: {e}")
        print("[daemon] 将自动重试...")
    await asyncio.gather(
        _serve_api(state),
        _serve_observer(state),
        _watch_connection(state),
        _sse_heartbeat(state),
    )


def main():
    config = load_config()
    state = DaemonState(config=config)
    print(f"[daemon] 守护进程启动，账号: {config.account}")
    print(f"[daemon] Evennia: {config.evennia_host}:{config.evennia_port}")
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    if sys.platform != "win32":
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda: state._stop_event.set())
    try:
        loop.run_until_complete(_run(state))
    except KeyboardInterrupt:
        print("\n[daemon] 收到中断信号，正在关闭...")
    finally:
        if state.conn:
            loop.run_until_complete(state.conn.close())
        loop.close()
        print("[daemon] 已关闭")


if __name__ == "__main__":
    main()

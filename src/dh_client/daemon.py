"""dh_client 守护进程。

后台常驻，维护 Evennia 长连接，提供：
- HTTP API (端口 5000)：接受 agent 命令
- SSE 旁观端点 (端口 8080)：实时推送 agent 活动给浏览器

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

# Windows 下强制 UTF-8 输出
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

    async def send_cmd(self, ts: str, action: str):
        """推送命令事件。"""
        data = json.dumps({"ts": ts, "action": action}, ensure_ascii=False)
        try:
            await self.resp.write(f"event: cmd\ndata: {data}\n\n".encode("utf-8"))
        except ConnectionResetError:
            pass

    async def send_resp(self, ts: str, text: str):
        """推送响应事件。"""
        data = json.dumps({"ts": ts, "text": text}, ensure_ascii=False)
        try:
            await self.resp.write(f"event: resp\ndata: {data}\n\n".encode("utf-8"))
        except ConnectionResetError:
            pass

    async def send_status(self, connected: bool):
        """推送连接状态事件。"""
        data = json.dumps({"connected": connected})
        try:
            await self.resp.write(f"event: status\ndata: {data}\n\n".encode("utf-8"))
        except ConnectionResetError:
            pass


@dataclass
class DaemonState:
    """守护进程全局状态。"""

    config: Config
    conn: EvenniaConnection | None = None
    observers: list = field(default_factory=list)
    action_log: list = field(default_factory=list)
    _stop_event: asyncio.Event = field(default_factory=asyncio.Event)


# ---- HTTP API (端口 5000) ----


async def _handle_action(request: web.Request) -> web.Response:
    """POST /action — Agent 发送命令。"""
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

    # 抄送给旁观者：命令
    await _broadcast_cmd(state, ts, action)

    try:
        response = await state.conn.send(action)
    except ConnectionError:
        return web.json_response({"ok": False, "error": "连接中断，正在重连"})

    # 抄送给旁观者：响应
    await _broadcast_resp(state, _now_ts(), response)

    # 记录日志
    state.action_log.append({"ts": ts, "action": action, "response": response})
    if len(state.action_log) > 200:
        state.action_log = state.action_log[-100:]

    return web.json_response({"ok": True, "response": response})


async def _handle_status(request: web.Request) -> web.Response:
    """GET /status — 查询守护进程状态。"""
    state: DaemonState = request.app["state"]
    connected = state.conn is not None and state.conn.is_connected
    return web.json_response({
        "connected": connected,
        "account": state.config.account,
    })


# ---- SSE 旁观端点 (端口 8080) ----


async def _observer_page(request: web.Request) -> web.Response:
    """GET / — 返回旁观页面 HTML。"""
    html_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    return web.FileResponse(html_path)


async def _observer_events(request: web.Request) -> web.StreamResponse:
    """GET /events — SSE 端点，实时推送 agent 活动。"""
    resp = web.StreamResponse()
    resp.content_type = "text/event-stream"
    resp.headers["Cache-Control"] = "no-cache"
    resp.headers["Connection"] = "keep-alive"
    resp.headers["Access-Control-Allow-Origin"] = "*"
    await resp.prepare(request)

    observer = Observer(resp=resp)
    state: DaemonState = request.app["state"]
    state.observers.append(observer)

    # 先推送当前连接状态
    connected = state.conn is not None and state.conn.is_connected
    await observer.send_status(connected)

    # 回放最近的日志（最多 50 条）
    for entry in state.action_log[-50:]:
        await observer.send_cmd(entry["ts"], entry["action"])
        await observer.send_resp(entry["ts"], entry["response"])

    try:
        # 保持连接，直到客户端断开或守护进程停止
        stop_event = state._stop_event
        client_closed = asyncio.ensure_future(_watch_client_disconnect(request, resp))
        daemon_stop = asyncio.ensure_future(stop_event.wait())

        done, pending = await asyncio.wait(
            [client_closed, daemon_stop],
            return_when=asyncio.FIRST_COMPLETED,
        )
        for p in pending:
            p.cancel()
    finally:
        if observer in state.observers:
            state.observers.remove(observer)

    return resp


async def _watch_client_disconnect(request: web.Request, resp: web.StreamResponse):
    """监视客户端是否断开。"""
    try:
        while not resp.task.done() if hasattr(resp, "task") else True:
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        pass


# ---- 广播辅助 ----


async def _broadcast_cmd(state: DaemonState, ts: str, action: str):
    """向所有旁观者广播命令。"""
    for obs in list(state.observers):
        await obs.send_cmd(ts, action)


async def _broadcast_resp(state: DaemonState, ts: str, text: str):
    """向所有旁观者广播响应。"""
    for obs in list(state.observers):
        await obs.send_resp(ts, text)


async def _broadcast_status(state: DaemonState, connected: bool):
    """向所有旁观者广播连接状态。"""
    for obs in list(state.observers):
        await obs.send_status(connected)


# ---- 断线重连监视 ----


async def _watch_connection(state: DaemonState):
    """监视 Evennia 连接，断线后自动重连。"""
    retry_count = 0

    while not state._stop_event.is_set():
        await asyncio.sleep(1)

        if state._stop_event.is_set():
            break

        if state.conn and state.conn.is_connected:
            retry_count = 0
            continue

        # 连接断开
        retry_count += 1
        print(f"[daemon] 连接断开，第 {retry_count} 次重连...")

        await _broadcast_status(state, False)

        # 重连间隔
        if retry_count <= 10:
            wait = 3
        else:
            wait = 30
        await asyncio.sleep(wait)

        if state._stop_event.is_set():
            break

        # 关闭旧连接
        if state.conn:
            await state.conn.close()

        # 重建连接
        state.conn = EvenniaConnection(state.config)
        try:
            await state.conn.connect()
            print("[daemon] 重连成功")
            await _broadcast_status(state, True)
            retry_count = 0
        except Exception as e:
            print(f"[daemon] 重连失败: {e}")


# ---- 服务启动 ----


async def _serve_api(state: DaemonState):
    """启动 HTTP API 服务（端口 5000）。"""
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
    """启动旁观 HTTP+SSE 服务（端口 8080）。"""
    app = web.Application()
    app["state"] = state
    app.router.add_get("/", _observer_page)
    app.router.add_get("/events", _observer_events)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()
    print("[daemon] 旁观页面已启动: http://localhost:8080")


# ---- SSE 心跳 ----


async def _sse_heartbeat(state: DaemonState):
    """每 30 秒向所有旁观者发送心跳，防止连接超时。"""
    while not state._stop_event.is_set():
        await asyncio.sleep(30)
        for obs in list(state.observers):
            try:
                await obs.resp.write(b": keepalive\n\n")
            except (ConnectionResetError, RuntimeError):
                pass


# ---- 主入口 ----


def _now_ts() -> str:
    """返回当前时间戳字符串。"""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


async def _run(state: DaemonState):
    """运行所有服务。"""
    # 连接 Evennia
    print("[daemon] 正在连接 Evennia...")
    state.conn = EvenniaConnection(state.config)

    try:
        await state.conn.connect()
        print(f"[daemon] 已连接 Evennia，账号: {state.config.account}")
    except Exception as e:
        print(f"[daemon] 连接 Evennia 失败: {e}")
        print("[daemon] 将自动重试...")

    # 启动所有服务
    await asyncio.gather(
        _serve_api(state),
        _serve_observer(state),
        _watch_connection(state),
        _sse_heartbeat(state),
    )


def main():
    """守护进程入口。"""
    config = load_config()
    state = DaemonState(config=config)

    print(f"[daemon] 守护进程启动，账号: {config.account}")
    print(f"[daemon] Evennia: {config.evennia_host}:{config.evennia_port}")

    # 信号处理
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

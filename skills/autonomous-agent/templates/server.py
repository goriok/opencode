"""HTTP server: webhook endpoints + MCP SSE endpoint."""
from __future__ import annotations

import asyncio
import json
import os
from concurrent.futures import ThreadPoolExecutor

from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

from .mcp_server import mcp
from .triggers.chat import handle, fetch_history
from .triggers.webhook import main as alert_main

_executor = ThreadPoolExecutor(max_workers=4)


def _chat_task(channel: str, message: str) -> None:
    print(f"[chat] started: channel={channel} message={message[:50]!r}")
    try:
        history = fetch_history(channel)
        handle(channel, message, history)
        print("[chat] done")
    except Exception as e:
        import traceback
        print(f"[chat] error: {e}")
        traceback.print_exc()


def _alert_task(payload: dict) -> None:
    try:
        os.environ["ALERT_PAYLOAD"] = json.dumps(payload)
        alert_main()
    except Exception as e:
        import traceback
        print(f"[alert] error: {e}")
        traceback.print_exc()


async def health(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


async def webhook_chat(request: Request) -> JSONResponse:
    body = await request.json()
    channel = body.get("channel", "cluster")
    message = body.get("body", "")
    if message:
        loop = asyncio.get_running_loop()
        loop.run_in_executor(_executor, _chat_task, channel, message)
    return JSONResponse({"ok": True})


async def webhook_alert(request: Request) -> JSONResponse:
    body = await request.json()
    loop = asyncio.get_running_loop()
    loop.run_in_executor(_executor, _alert_task, body)
    return JSONResponse({"ok": True})


sse_transport = SseServerTransport("/mcp/messages/")


async def handle_mcp_sse(request: Request):
    async with sse_transport.connect_sse(
        request.scope, request.receive, request._send
    ) as streams:
        await mcp._mcp_server.run(
            streams[0],
            streams[1],
            mcp._mcp_server.create_initialization_options(),
        )


routes = [
    Route("/health", health, methods=["GET"]),
    Route("/webhook/chat", webhook_chat, methods=["POST"]),
    Route("/webhook/alert", webhook_alert, methods=["POST"]),
    Route("/mcp/sse", handle_mcp_sse, methods=["GET"]),
    Mount("/mcp/messages/", app=sse_transport.handle_post_message),
]

application = Starlette(routes=routes)


def serve(port: int = 8080) -> None:
    import uvicorn
    print(f"$AGENT_NAME server listening on :{port}")
    uvicorn.run(application, host="0.0.0.0", port=port)

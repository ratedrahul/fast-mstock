"""Live market-data streaming relay.

mStock streams ticks and order/trade updates over a binary WebSocket at
``wss://ws.mstock.trade``. Browsers and mobile apps usually should not embed
the raw ``access_token`` in a client-side socket URL, so MS-Fast exposes a
relay: the client connects here, and the server proxies frames to/from mStock.

Protocol
--------
Connect to::

    /ws/ticks?api_key=<API_KEY>&access_token=<ACCESS_TOKEN>

* Text frames you send are forwarded verbatim to mStock. Use mStock's control
  messages, e.g. subscribe / set mode::

      {"a": "subscribe", "v": [5633]}
      {"a": "mode", "v": ["full", [5633]]}
      {"a": "unsubscribe", "v": [5633]}

* Binary frames (raw tick packets) and text frames (order/trade updates) from
  mStock are relayed back to you untouched, so you keep full control over
  parsing.
"""

from __future__ import annotations

import asyncio
import logging

import websockets
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from websockets.exceptions import WebSocketException

from app.core.config import get_settings

logger = logging.getLogger("ms_fast.ws")

router = APIRouter()


def _build_upstream_url(base: str, api_key: str, access_token: str) -> str:
    return f"{base}?ACCESS_TOKEN={access_token}&API_KEY={api_key}"


@router.websocket("/ws/ticks")
async def ticks(
    websocket: WebSocket,
    api_key: str = Query(..., description="mStock API key"),
    access_token: str = Query(..., description="mStock daily access token"),
):
    await websocket.accept()
    settings = get_settings()
    upstream_url = _build_upstream_url(settings.mstock_ws_url, api_key, access_token)

    try:
        async with websockets.connect(
            upstream_url,
            ping_interval=20,
            ping_timeout=20,
            max_size=None,
        ) as upstream:
            # mStock requires a LOGIN message immediately after connecting.
            await upstream.send(f"LOGIN:{access_token}")

            await _pump(websocket, upstream)
    except WebSocketException as exc:
        logger.warning("Upstream websocket error: %s", exc)
        await _safe_close(websocket, code=1011, reason="Upstream connection failed")
    except WebSocketDisconnect:
        pass
    except Exception as exc:  # noqa: BLE001 - defensive guard for relay loop
        logger.exception("Unexpected streaming error: %s", exc)
        await _safe_close(websocket, code=1011, reason="Internal streaming error")


async def _pump(client: WebSocket, upstream: websockets.WebSocketClientProtocol) -> None:
    """Relay frames between the browser client and mStock until either closes."""

    async def client_to_upstream() -> None:
        while True:
            message = await client.receive()
            if message.get("type") == "websocket.disconnect":
                raise WebSocketDisconnect()
            if (text := message.get("text")) is not None:
                await upstream.send(text)
            elif (data := message.get("bytes")) is not None:
                await upstream.send(data)

    async def upstream_to_client() -> None:
        async for frame in upstream:
            if isinstance(frame, (bytes, bytearray)):
                await client.send_bytes(bytes(frame))
            else:
                await client.send_text(frame)

    task_a = asyncio.create_task(client_to_upstream())
    task_b = asyncio.create_task(upstream_to_client())
    done, pending = await asyncio.wait(
        {task_a, task_b}, return_when=asyncio.FIRST_COMPLETED
    )
    for task in pending:
        task.cancel()
    # Surface non-disconnect exceptions for logging.
    for task in done:
        exc = task.exception()
        if exc and not isinstance(exc, (WebSocketDisconnect, asyncio.CancelledError)):
            raise exc


async def _safe_close(websocket: WebSocket, *, code: int, reason: str) -> None:
    try:
        await websocket.close(code=code, reason=reason)
    except RuntimeError:
        pass

"""MS-Fast application entrypoint.

A fast, production-ready FastAPI gateway over the mStock Trading API (Type A).
"""

from __future__ import annotations

import logging
import re
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app import __version__
from app.api.routers import (
    auth,
    basket,
    margin,
    market,
    movers,
    options,
    orders,
    portfolio,
    system,
)
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.mstock.client import MStockClient
from app.mstock.exceptions import MStockAPIError, MStockError
from app.ws import streaming

logger = logging.getLogger("ms_fast")

# Paths that bypass gateway-key enforcement.
_OPEN_PATHS = {"/", "/health", "/docs", "/redoc", "/openapi.json", "/favicon.ico"}

# Detects the mStock "IP address not whitelisted" family of errors.
_IP_MISMATCH_RE = re.compile(
    r"(primary\s+and\s+secondary\s+ip|ip\s+address.*(not\s+matching|mismatch|not\s+whitelist)"
    r"|not\s+matching.*ip\s+address)",
    re.IGNORECASE,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)

    client = MStockClient(
        base_url=settings.mstock_base_url,
        version=settings.mstock_version,
        timeout=settings.request_timeout,
    )
    await client.startup()
    app.state.mstock_client = client
    logger.info("%s v%s started", settings.app_name, __version__)
    try:
        yield
    finally:
        await client.shutdown()


class GatewayAuthMiddleware(BaseHTTPMiddleware):
    """Optional shared-secret protection for the whole gateway."""

    def __init__(self, app, gateway_key: str | None) -> None:
        super().__init__(app)
        self._gateway_key = gateway_key

    async def dispatch(self, request: Request, call_next):
        if self._gateway_key and request.method != "OPTIONS":
            path = request.url.path
            is_open = path in _OPEN_PATHS or path.startswith("/ws/")
            if not is_open and request.headers.get("X-Gateway-Key") != self._gateway_key:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={
                        "status": "error",
                        "message": "Invalid or missing X-Gateway-Key.",
                        "error_type": "GatewayAuthException",
                        "data": None,
                    },
                )
        return await call_next(request)


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(
        title="MS-Fast — mStock Trading API Gateway",
        version=__version__,
        description=(
            "A fast, deployable FastAPI backend that exposes every mStock "
            "Trading API (Type A) capability as a clean REST endpoint, plus a "
            "live market-data WebSocket relay.\n\n"
            "**Authentication**: send your mStock `X-Api-Key` and `X-Access-Token` "
            "headers on every authenticated call (or configure server defaults). "
            "Use `/auth/login` → `/auth/session` (or `/auth/verify-totp`) to obtain "
            "the daily access token."
        ),
        lifespan=lifespan,
        contact={"name": "MS-Fast"},
        license_info={"name": "MIT"},
        # Keep credentials entered via the Authorize button across reloads.
        swagger_ui_parameters={"persistAuthorization": True},
    )

    # --- Middleware ----------------------------------------------------------
    # NOTE: Starlette applies the LAST-added middleware as the OUTERMOST layer.
    # The gateway is added first (inner) and CORS last (outer) so that CORS
    # preflight (OPTIONS) requests are always answered and CORS headers are
    # attached to every response — including gateway 401s.
    app.add_middleware(GatewayAuthMiddleware, gateway_key=settings.gateway_api_key)

    allow_all_origins = settings.cors_origins_list == ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        # Credentials cannot be combined with the "*" origin wildcard, and the
        # frontend authenticates via headers (not cookies), so only enable
        # credentials when explicit origins are configured.
        allow_credentials=not allow_all_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Exception handlers --------------------------------------------------
    @app.exception_handler(MStockAPIError)
    async def _mstock_api_error(request: Request, exc: MStockAPIError):
        data = exc.data
        message = exc.message

        # If mStock rejects the call because the caller IP isn't whitelisted,
        # attach the server's outbound IP and clear remediation instructions.
        if message and _IP_MISMATCH_RE.search(message):
            client = getattr(request.app.state, "mstock_client", None)
            server_ip = await client.get_egress_ip() if client else None
            data = {
                "ip_whitelist_required": True,
                "server_ip": server_ip,
                "help_url": "https://trade.mstock.com",
                "instructions": (
                    f"mStock rejected this request because the calling IP is not "
                    f"whitelisted. Add this server's outbound IP "
                    f"{f'({server_ip}) ' if server_ip else ''}as the Primary or "
                    f"Secondary IP in your mStock API settings at "
                    f"trade.mstock.com, then retry."
                ),
            }

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": "error",
                "message": message,
                "error_type": exc.error_type,
                "data": data,
            },
        )

    @app.exception_handler(MStockError)
    async def _mstock_error(_: Request, exc: MStockError):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status": "error",
                "message": exc.message,
                "error_type": "UpstreamException",
                "data": None,
            },
        )

    # --- Routers -------------------------------------------------------------
    api_routers = [
        system.router,
        auth.router,
        orders.router,
        portfolio.router,
        margin.router,
        market.router,
        options.router,
        basket.router,
        movers.router,
    ]
    for r in api_routers:
        app.include_router(r, prefix="/api/v1")

    # WebSocket relay (no prefix – mounted at /ws/ticks)
    app.include_router(streaming.router)

    @app.get("/", tags=["System"], summary="Service banner")
    async def root():
        return {
            "service": settings.app_name,
            "version": __version__,
            "docs": "/docs",
            "openapi": "/openapi.json",
            "streaming": "/ws/ticks?api_key=...&access_token=...",
        }

    @app.get("/health", tags=["System"], summary="Liveness probe for MS-Fast itself")
    async def health():
        client = getattr(app.state, "mstock_client", None)
        return {"status": "ok", "mstock_client": bool(client and client.ws_ready)}

    return app


app = create_app()

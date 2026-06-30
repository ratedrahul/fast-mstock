"""FastAPI dependencies: credentials, upstream client, and gateway auth."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader

from app.core.config import Settings, get_settings
from app.mstock.client import MStockClient

# --- OpenAPI security schemes --------------------------------------------------
# Declaring these makes the "Authorize" button appear in Swagger UI (/docs), so
# you enter your credentials once and every request reuses them.
api_key_scheme = APIKeyHeader(
    name="X-Api-Key",
    scheme_name="mStockApiKey",
    description="Your mStock API key.",
    auto_error=False,
)
access_token_scheme = APIKeyHeader(
    name="X-Access-Token",
    scheme_name="mStockAccessToken",
    description="Your daily mStock access token (from /auth/session or /auth/verify-totp).",
    auto_error=False,
)
gateway_key_scheme = APIKeyHeader(
    name="X-Gateway-Key",
    scheme_name="gatewayKey",
    description="Optional MS-Fast gateway secret (only if GATEWAY_API_KEY is configured).",
    auto_error=False,
)


@dataclass(slots=True)
class Credentials:
    """mStock credentials resolved for the current request."""

    api_key: str
    access_token: str


def get_client(request: Request) -> MStockClient:
    """Return the shared mStock client created during app startup."""
    client: MStockClient | None = getattr(request.app.state, "mstock_client", None)
    if client is None:  # pragma: no cover - only if misconfigured
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="mStock client is not available",
        )
    return client


def get_credentials(
    x_api_key: str | None = Security(api_key_scheme),
    x_access_token: str | None = Security(access_token_scheme),
    _gateway_key: str | None = Security(gateway_key_scheme),
    settings: Settings = Depends(get_settings),
) -> Credentials:
    """Resolve mStock credentials from request headers or server defaults.

    Multi-tenant deployments: every client sends ``X-Api-Key`` and
    ``X-Access-Token`` (use the Authorize button in Swagger UI). Single-user
    deployments may instead set ``MSTOCK_API_KEY`` / ``MSTOCK_ACCESS_TOKEN`` in
    the environment.
    """
    api_key = x_api_key or settings.mstock_api_key
    access_token = x_access_token or settings.mstock_access_token

    if not api_key or not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "Missing mStock credentials. Send 'X-Api-Key' and 'X-Access-Token' "
                "headers, or configure server defaults."
            ),
        )
    return Credentials(api_key=api_key, access_token=access_token)

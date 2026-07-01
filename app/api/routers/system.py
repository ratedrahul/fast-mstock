"""System / health endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import Credentials, get_client, get_credentials
from app.mstock.client import MStockClient

router = APIRouter(tags=["System"])


@router.get(
    "/system/egress-ip",
    summary="Server outbound IP (the IP to whitelist at mStock)",
)
async def egress_ip(client: MStockClient = Depends(get_client)):
    ip = await client.get_egress_ip()
    return {
        "status": "success",
        "data": {
            "ip": ip,
            "help_url": "https://trade.mstock.com",
            "note": (
                "Whitelist this IP as Primary/Secondary IP in your mStock API "
                "settings. This is the address that calls mStock, not your "
                "device's IP."
            ),
        },
    }


@router.get(
    "/mstock/health-statistics",
    tags=["System"],
    summary="mStock upstream health statistics",
)
async def mstock_health(
    creds: Credentials = Depends(get_credentials),
    client: MStockClient = Depends(get_client),
):
    return await client.get(
        "health_statistics", api_key=creds.api_key, access_token=creds.access_token
    )

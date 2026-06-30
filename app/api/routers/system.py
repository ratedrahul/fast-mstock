"""System / health endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import Credentials, get_client, get_credentials
from app.mstock.client import MStockClient

router = APIRouter(tags=["System"])


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

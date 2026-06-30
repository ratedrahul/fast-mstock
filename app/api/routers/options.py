"""Option chain endpoints (mStock "Option Chain APIs" section)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Path

from app.api.deps import Credentials, get_client, get_credentials
from app.mstock.client import MStockClient

router = APIRouter(prefix="/option-chain", tags=["Option Chain"])


@router.get("/master/{exchange_id}", summary="Option chain master (expiries & tokens)")
async def option_chain_master(
    exchange_id: str = Path(..., description="Exchange id", examples=["5"]),
    creds: Credentials = Depends(get_credentials),
    client: MStockClient = Depends(get_client),
):
    return await client.get(
        "option_chain_master",
        url_args={"exchange_id": exchange_id},
        api_key=creds.api_key,
        access_token=creds.access_token,
    )


@router.get(
    "/data/{exchange_id}/{expiry}/{token}",
    summary="Option chain data for an expiry & underlying token",
)
async def option_chain_data(
    exchange_id: str = Path(..., description="Exchange id", examples=["2"]),
    expiry: str = Path(..., description="Expiry (epoch as returned by master)", examples=["1432996200"]),
    token: str = Path(..., description="Underlying instrument token", examples=["22"]),
    creds: Credentials = Depends(get_credentials),
    client: MStockClient = Depends(get_client),
):
    return await client.get(
        "option_chain_data",
        url_args={"exchange_id": exchange_id, "expiry": expiry, "token": token},
        api_key=creds.api_key,
        access_token=creds.access_token,
    )

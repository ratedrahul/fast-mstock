"""Portfolio & positions endpoints (mStock "Portfolio" + "Position" sections)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import Credentials, get_client, get_credentials
from app.mstock.client import FORM, MStockClient
from app.schemas.common import to_form
from app.schemas.portfolio import ConvertPositionRequest

router = APIRouter(prefix="/portfolio", tags=["Portfolio & Positions"])


@router.get("/holdings", summary="Long-term equity delivery holdings")
async def holdings(
    creds: Credentials = Depends(get_credentials),
    client: MStockClient = Depends(get_client),
):
    return await client.get(
        "holdings", api_key=creds.api_key, access_token=creds.access_token
    )


@router.get("/positions", summary="Net positions for the day")
async def positions(
    creds: Credentials = Depends(get_credentials),
    client: MStockClient = Depends(get_client),
):
    return await client.get(
        "net_position", api_key=creds.api_key, access_token=creds.access_token
    )


@router.post("/convert-position", summary="Convert a position's margin product")
async def convert_position(
    body: ConvertPositionRequest,
    creds: Credentials = Depends(get_credentials),
    client: MStockClient = Depends(get_client),
):
    return await client.post(
        "position_conversion",
        api_key=creds.api_key,
        access_token=creds.access_token,
        data=to_form(body),
        content_type=FORM,
    )

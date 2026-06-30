"""Order margin calculator (mStock "Calculate Order Margin" section)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import Credentials, get_client, get_credentials
from app.mstock.client import JSON_CT, MStockClient
from app.schemas.margin import MarginOrderRequest

router = APIRouter(prefix="/margins", tags=["Margins"])


@router.post("/orders", summary="Calculate margin & charges for an order")
async def calculate_order_margin(
    body: MarginOrderRequest,
    creds: Credentials = Depends(get_credentials),
    client: MStockClient = Depends(get_client),
):
    # This endpoint expects a JSON body (unlike most others which are form-encoded).
    return await client.post(
        "calculate_order_margin",
        api_key=creds.api_key,
        access_token=creds.access_token,
        json=body.model_dump(mode="json"),
        content_type=JSON_CT,
    )

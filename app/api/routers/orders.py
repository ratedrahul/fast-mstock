"""Order management endpoints (mStock "Orders" section)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Path

from app.api.deps import Credentials, get_client, get_credentials
from app.mstock.client import FORM, MStockClient
from app.schemas.common import Variety, to_form
from app.schemas.orders import (
    ModifyOrderRequest,
    OrderDetailsRequest,
    PlaceOrderRequest,
    TradeHistoryRequest,
)

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("/{variety}", summary="Place a new order")
async def place_order(
    body: PlaceOrderRequest,
    variety: Variety = Path(..., description="Order variety: regular | amo | co"),
    creds: Credentials = Depends(get_credentials),
    client: MStockClient = Depends(get_client),
):
    return await client.post(
        "place_order",
        url_args={"variety": variety.value},
        api_key=creds.api_key,
        access_token=creds.access_token,
        data=to_form(body),
        content_type=FORM,
    )


@router.put("/regular/{order_id}", summary="Modify a pending order")
async def modify_order(
    body: ModifyOrderRequest,
    order_id: str = Path(..., description="Order id to modify"),
    creds: Credentials = Depends(get_credentials),
    client: MStockClient = Depends(get_client),
):
    return await client.put(
        "modify_order",
        url_args={"order_id": order_id},
        api_key=creds.api_key,
        access_token=creds.access_token,
        data=to_form(body),
        content_type=FORM,
    )


@router.delete("/regular/{order_id}", summary="Cancel a pending order")
async def cancel_order(
    order_id: str = Path(..., description="Order id to cancel"),
    creds: Credentials = Depends(get_credentials),
    client: MStockClient = Depends(get_client),
):
    return await client.delete(
        "cancel_order",
        url_args={"order_id": order_id},
        api_key=creds.api_key,
        access_token=creds.access_token,
    )


@router.post("/cancel-all", summary="Cancel all pending orders")
async def cancel_all(
    creds: Credentials = Depends(get_credentials),
    client: MStockClient = Depends(get_client),
):
    return await client.post(
        "cancel_all", api_key=creds.api_key, access_token=creds.access_token
    )


@router.get("/book", summary="Order book – all of today's orders")
async def order_book(
    creds: Credentials = Depends(get_credentials),
    client: MStockClient = Depends(get_client),
):
    return await client.get(
        "order_book", api_key=creds.api_key, access_token=creds.access_token
    )


@router.post("/details", summary="Status of an individual order")
async def order_details(
    body: OrderDetailsRequest,
    creds: Credentials = Depends(get_credentials),
    client: MStockClient = Depends(get_client),
):
    return await client.post(
        "order_details",
        api_key=creds.api_key,
        access_token=creds.access_token,
        data=to_form(body),
        content_type=FORM,
    )


@router.get("/trade-book", summary="Trade book – all executed trades")
async def trade_book(
    creds: Credentials = Depends(get_credentials),
    client: MStockClient = Depends(get_client),
):
    return await client.get(
        "trade_book", api_key=creds.api_key, access_token=creds.access_token
    )


@router.post("/trades", summary="Trade history for a date range")
async def trade_history(
    body: TradeHistoryRequest,
    creds: Credentials = Depends(get_credentials),
    client: MStockClient = Depends(get_client),
):
    return await client.post(
        "trade_history",
        api_key=creds.api_key,
        access_token=creds.access_token,
        data=to_form(body),
        content_type=FORM,
    )

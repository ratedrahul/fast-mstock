"""Basket endpoints (mStock "Basket APIs" section)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import Credentials, get_client, get_credentials
from app.mstock.client import FORM, MStockClient
from app.schemas.basket import (
    CalculateBasketRequest,
    CreateBasketRequest,
    DeleteBasketRequest,
    RenameBasketRequest,
)
from app.schemas.common import to_form

router = APIRouter(prefix="/baskets", tags=["Baskets"])


@router.post("", summary="Create a basket")
async def create_basket(
    body: CreateBasketRequest,
    creds: Credentials = Depends(get_credentials),
    client: MStockClient = Depends(get_client),
):
    return await client.post(
        "create_basket",
        api_key=creds.api_key,
        access_token=creds.access_token,
        data=to_form(body),
        content_type=FORM,
    )


@router.get("", summary="Fetch all baskets")
async def fetch_baskets(
    creds: Credentials = Depends(get_credentials),
    client: MStockClient = Depends(get_client),
):
    return await client.get(
        "fetch_basket", api_key=creds.api_key, access_token=creds.access_token
    )


@router.put("", summary="Rename a basket")
async def rename_basket(
    body: RenameBasketRequest,
    creds: Credentials = Depends(get_credentials),
    client: MStockClient = Depends(get_client),
):
    return await client.put(
        "rename_basket",
        api_key=creds.api_key,
        access_token=creds.access_token,
        data=to_form(body),
        content_type=FORM,
    )


@router.delete("", summary="Delete a basket")
async def delete_basket(
    body: DeleteBasketRequest,
    creds: Credentials = Depends(get_credentials),
    client: MStockClient = Depends(get_client),
):
    return await client.delete(
        "delete_basket",
        api_key=creds.api_key,
        access_token=creds.access_token,
        data=to_form(body),
        content_type=FORM,
    )


@router.post("/calculate", summary="Add / price a leg in a basket")
async def calculate_basket(
    body: CalculateBasketRequest,
    creds: Credentials = Depends(get_credentials),
    client: MStockClient = Depends(get_client),
):
    return await client.post(
        "calculate_basket",
        api_key=creds.api_key,
        access_token=creds.access_token,
        data=to_form(body),
        content_type=FORM,
    )

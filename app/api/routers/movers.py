"""Top gainers / losers (mStock "Top Gainers/Losers" section)."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import Credentials, get_client, get_credentials
from app.mstock.client import FORM, MStockClient
from app.schemas.common import to_form
from app.schemas.movers import MoversRequest

router = APIRouter(prefix="/movers", tags=["Top Gainers / Losers"])


@router.post("", summary="Top gainers or losers for a segment")
async def gainers_losers(
    body: MoversRequest,
    creds: Credentials = Depends(get_credentials),
    client: MStockClient = Depends(get_client),
):
    return await client.post(
        "loser_gainer",
        api_key=creds.api_key,
        access_token=creds.access_token,
        data=to_form(body),
        content_type=FORM,
    )

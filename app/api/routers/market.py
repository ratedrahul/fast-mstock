"""Market quotes, instruments & charts (mStock "Market Quotes and Instruments",
"Historical Data" and "Intraday Chart Data" sections)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Path, Query
from fastapi.responses import PlainTextResponse

from app.api.deps import Credentials, get_client, get_credentials
from app.mstock.client import FORM, MStockClient

router = APIRouter(prefix="/market", tags=["Market Data"])


@router.get("/quote/ohlc", summary="OHLC + LTP quote for one or more instruments")
async def ohlc(
    i: list[str] = Query(
        ...,
        description="Instrument keys as EXCHANGE:SYMBOL (repeatable).",
        examples=["NSE:ACC", "BSE:ACC"],
    ),
    creds: Credentials = Depends(get_credentials),
    client: MStockClient = Depends(get_client),
):
    return await client.get(
        "market_ohlc",
        api_key=creds.api_key,
        access_token=creds.access_token,
        params=[("i", sym) for sym in i],
    )


@router.get("/quote/ltp", summary="Last traded price for one or more instruments")
async def ltp(
    i: list[str] = Query(
        ...,
        description="Instrument keys as EXCHANGE:SYMBOL (repeatable).",
        examples=["NSE:ACC", "NFO:CDSL25JAN2220CE"],
    ),
    creds: Credentials = Depends(get_credentials),
    client: MStockClient = Depends(get_client),
):
    return await client.get(
        "market_ltp",
        api_key=creds.api_key,
        access_token=creds.access_token,
        params=[("i", sym) for sym in i],
    )


@router.get(
    "/instruments",
    summary="Consolidated instrument scrip master (CSV)",
    response_class=PlainTextResponse,
)
async def instruments(
    creds: Credentials = Depends(get_credentials),
    client: MStockClient = Depends(get_client),
):
    result = await client.get(
        "instrument_scrip",
        api_key=creds.api_key,
        access_token=creds.access_token,
        expect="raw",
    )
    body = result["body"] if isinstance(result, dict) and "body" in result else str(result)
    return PlainTextResponse(content=body, media_type="text/csv")


@router.get(
    "/historical/{segment}/{security_token}/{interval}",
    summary="Historical OHLC candles",
)
async def historical(
    segment: str = Path(..., description="Segment, e.g. NSE", examples=["NSE"]),
    security_token: str = Path(..., description="Instrument/security token", examples=["11536"]),
    interval: str = Path(
        ...,
        description="Candle interval, e.g. minute / 5minute / 60minute / day",
        examples=["60minute"],
    ),
    from_: str = Query(..., alias="from", description="Start date (YYYY-MM-DD)", examples=["2025-01-05"]),
    to: str = Query(..., description="End date (YYYY-MM-DD)", examples=["2025-01-10"]),
    creds: Credentials = Depends(get_credentials),
    client: MStockClient = Depends(get_client),
):
    return await client.get(
        "historical_chart",
        url_args={
            "segment": segment,
            "security_token": security_token,
            "interval": interval,
        },
        api_key=creds.api_key,
        access_token=creds.access_token,
        params={"from": from_, "to": to},
        content_type=FORM,
    )


@router.get(
    "/intraday/{segment_id}/{symbol}/{interval}",
    summary="Intraday chart candles",
)
async def intraday(
    segment_id: str = Path(..., description="Segment id", examples=["1"]),
    symbol: str = Path(..., description="Security/symbol token", examples=["22"]),
    interval: str = Path(..., description="Interval, e.g. Minute", examples=["Minute"]),
    creds: Credentials = Depends(get_credentials),
    client: MStockClient = Depends(get_client),
):
    return await client.get(
        "intraday_chart",
        url_args={"segment_id": segment_id, "symbol": symbol, "interval": interval},
        api_key=creds.api_key,
        access_token=creds.access_token,
    )

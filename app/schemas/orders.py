from __future__ import annotations

from pydantic import BaseModel, Field

from .common import (
    Exchange,
    OrderType,
    ProductType,
    Segment,
    TransactionType,
    Validity,
)


class PlaceOrderRequest(BaseModel):
    tradingsymbol: str = Field(..., description="Trading symbol, e.g. INFY-EQ", examples=["INFY-EQ"])
    exchange: Exchange = Exchange.NSE
    transaction_type: TransactionType
    order_type: OrderType
    quantity: int = Field(..., ge=1, description="Number of shares/lots")
    product: ProductType
    validity: Validity = Validity.DAY
    price: float = Field(0, ge=0, description="Limit price (0 for MARKET orders)")
    trigger_price: float = Field(0, ge=0, description="Trigger price for SL / SL-M orders")
    disclosed_quantity: int = Field(0, ge=0, description="Disclosed quantity")
    tag: str | None = Field(None, max_length=20, description="Free-form tag to identify the order")


class ModifyOrderRequest(BaseModel):
    order_type: OrderType
    quantity: int = Field(..., ge=1)
    price: float = Field(0, ge=0)
    validity: Validity = Validity.DAY
    trigger_price: float = Field(0, ge=0)
    disclosed_quantity: int = Field(0, ge=0)


class OrderDetailsRequest(BaseModel):
    order_no: str = Field(..., description="The order id to look up", examples=["1157250130101"])
    segment: Segment | None = Field(Segment.E, description="E = Equity, D = Derivative (optional)")


class TradeHistoryRequest(BaseModel):
    fromdate: str = Field(..., description="Start date (YYYY-MM-DD)", examples=["2025-01-05"])
    todate: str = Field(..., description="End date (YYYY-MM-DD)", examples=["2025-01-10"])

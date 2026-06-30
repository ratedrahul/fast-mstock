from __future__ import annotations

from pydantic import BaseModel, Field

from .common import Exchange, OrderType, ProductType, TransactionType, Variety


class MarginOrderRequest(BaseModel):
    """Body for the margin calculator. Sent to mStock as JSON."""

    exchange: Exchange = Exchange.NSE
    tradingsymbol: str = Field(..., examples=["INFY"])
    transaction_type: TransactionType
    variety: Variety = Variety.regular
    product: ProductType
    order_type: OrderType
    quantity: int = Field(..., ge=1)
    price: float = Field(0, ge=0)
    trigger_price: float = Field(0, ge=0)

from __future__ import annotations

from pydantic import BaseModel, Field


class CreateBasketRequest(BaseModel):
    BaskName: str = Field(..., description="Basket name", examples=["My Basket"])
    BaskDesc: str = Field("", description="Basket description", examples=["Intraday picks"])


class RenameBasketRequest(BaseModel):
    basketName: str = Field(..., description="New basket name")
    BasketId: str = Field(..., description="Id of the basket to rename")


class DeleteBasketRequest(BaseModel):
    BasketId: str = Field(..., description="Id of the basket to delete")


class CalculateBasketRequest(BaseModel):
    """Add / price a leg within a basket.

    Field names mirror the upstream mStock contract exactly.
    """

    include_exist_pos: str = Field("0", description="Include existing positions (0/1)")
    ord_product: str = Field(..., description="Order product, e.g. C / I / M")
    disc_qty: str = Field("0", description="Disclosed quantity")
    segment: str = Field(..., description="Segment, e.g. E (equity)")
    trigger_price: str = Field("0")
    scriptcode: str = Field(..., description="Instrument / security code", examples=["11915"])
    ord_type: str = Field(..., description="Order type, e.g. LMT / MKT")
    basket_name: str = Field(...)
    operation: str = Field(..., description="Operation flag, e.g. I (insert)")
    order_validity: str = Field("DAY")
    order_qty: str = Field(..., examples=["1"])
    script_stat: str = Field(..., description="Script status flag, e.g. A")
    buy_sell_indi: str = Field(..., description="Buy/Sell indicator, e.g. B / S")
    basket_priority: str = Field("1")
    order_price: str = Field(..., examples=["19.02"])
    basket_id: str = Field(...)
    exch_id: str = Field(..., description="Exchange id, e.g. NSE")

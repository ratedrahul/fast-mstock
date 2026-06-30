from __future__ import annotations

from pydantic import BaseModel, Field

from .common import Exchange, ProductType, TransactionType


class ConvertPositionRequest(BaseModel):
    tradingsymbol: str = Field(..., examples=["ACC"])
    exchange: Exchange = Exchange.NSE
    transaction_type: TransactionType
    position_type: str = Field("DAY", description="Position type", examples=["DAY"])
    quantity: int = Field(..., ge=1)
    old_product: ProductType = Field(..., description="Current product type")
    new_product: ProductType = Field(..., description="Target product type")

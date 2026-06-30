from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class MoverType(str, Enum):
    GAINER = "G"
    LOSER = "L"


class MoversRequest(BaseModel):
    Exchange: str = Field(..., description="Exchange id code", examples=["1"])
    SecurityIdCode: str = Field(..., description="Security/segment id code", examples=["13"])
    segment: str = Field(..., description="Segment code", examples=["1"])
    TypeFlag: MoverType = Field(..., description="G = top gainers, L = top losers")

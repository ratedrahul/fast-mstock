"""Shared enums, response envelopes and serialisation helpers."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Enumerations (mirroring the mStock "Glossary")
# ---------------------------------------------------------------------------
class Exchange(str, Enum):
    NSE = "NSE"
    BSE = "BSE"
    NFO = "NFO"
    BFO = "BFO"
    CDS = "CDS"
    MCX = "MCX"


class TransactionType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    SL = "SL"
    SL_M = "SL-M"


class ProductType(str, Enum):
    CNC = "CNC"   # Cash & Carry (equity delivery)
    NRML = "NRML"  # Normal (F&O)
    MIS = "MIS"   # Margin Intraday Squareoff
    MTF = "MTF"   # Margin Trading Facility


class Validity(str, Enum):
    DAY = "DAY"
    IOC = "IOC"


class Variety(str, Enum):
    regular = "regular"
    amo = "amo"
    co = "co"


class Segment(str, Enum):
    """Equity vs Derivative segment used by order-details."""

    E = "E"  # Equity
    D = "D"  # Derivative


# ---------------------------------------------------------------------------
# Response envelope (documentation aid – mStock always returns this shape)
# ---------------------------------------------------------------------------
class APIResponse(BaseModel):
    status: str
    data: Any | None = None
    message: str | None = None
    error_type: str | None = None


class ErrorResponse(BaseModel):
    status: str = "error"
    message: str
    error_type: str | None = None
    data: Any | None = None


# ---------------------------------------------------------------------------
# Serialisation helpers
# ---------------------------------------------------------------------------
def _stringify(value: Any) -> str:
    """Render a scalar as the string mStock expects in form bodies."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, Enum):
        return str(value.value)
    return str(value)


def to_form(model: BaseModel, *, exclude_none: bool = True) -> dict[str, str]:
    """Convert a Pydantic model into a flat ``str: str`` form payload."""
    raw = model.model_dump(mode="json", exclude_none=exclude_none)
    return {key: _stringify(val) for key, val in raw.items() if val is not None}

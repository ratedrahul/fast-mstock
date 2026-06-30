"""Exceptions for the mStock integration layer.

mStock returns errors as JSON envelopes shaped like::

    {"status": "error", "message": "...", "error_type": "TokenException", "data": null}

These exceptions normalise that contract so the API layer can translate them
into clean HTTP responses.
"""

from __future__ import annotations

from typing import Any

# mStock `error_type` -> sensible HTTP status code.
# (mStock is inconsistent about the HTTP status it returns, so we normalise.)
ERROR_TYPE_STATUS: dict[str, int] = {
    "TokenException": 401,
    "APIKeyException": 401,
    "VersionException": 400,
    "InputException": 400,
    "MiraeException": 400,
    "DataException": 502,
    "GeneralException": 500,
    "OrderException": 400,
    "NetworkException": 503,
    "PermissionException": 403,
}


class MStockError(Exception):
    """Base class for all mStock integration errors."""

    def __init__(self, message: str, status_code: int = 500) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class MStockAPIError(MStockError):
    """A structured error returned by the mStock API itself."""

    def __init__(
        self,
        message: str,
        error_type: str | None = None,
        status_code: int | None = None,
        data: Any = None,
    ) -> None:
        resolved = status_code or ERROR_TYPE_STATUS.get(error_type or "", 400)
        super().__init__(message, resolved)
        self.error_type = error_type
        self.data = data


class MStockUpstreamError(MStockError):
    """Network / transport level failure while talking to mStock."""

    def __init__(self, message: str, status_code: int = 502) -> None:
        super().__init__(message, status_code)

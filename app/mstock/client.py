"""Async HTTP client that wraps the mStock Trading API (Type A).

A single :class:`MStockClient` instance is created at application startup and
reused for every request, so connection pooling / keep-alive give us the
low-latency behaviour required for trading.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx

from .exceptions import MStockAPIError, MStockUpstreamError
from .routes import path_for

logger = logging.getLogger("ms_fast.mstock")

JSON = dict[str, Any] | list[Any]

# Content type constants
FORM = "application/x-www-form-urlencoded"
JSON_CT = "application/json"


class MStockClient:
    def __init__(
        self,
        base_url: str,
        version: str = "1",
        timeout: float = 15.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._version = version
        self._timeout = timeout
        self._client: httpx.AsyncClient | None = None
        self._egress_ip: str | None = None
        self._egress_ip_ts: float = 0.0

    # -- lifecycle ------------------------------------------------------------
    async def startup(self) -> None:
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=httpx.Timeout(self._timeout),
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
            headers={"User-Agent": "MS-Fast/1.0"},
        )
        logger.info("mStock client ready (base_url=%s)", self._base_url)

    async def shutdown(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None
            logger.info("mStock client closed")

    @property
    def ws_ready(self) -> bool:
        return self._client is not None

    async def get_egress_ip(self, *, force: bool = False) -> str | None:
        """Return the server's public outbound IP (the IP mStock sees).

        This is the address that must be whitelisted in the mStock API IP
        settings. Result is cached for an hour since it rarely changes.
        """
        now = time.time()
        if not force and self._egress_ip and (now - self._egress_ip_ts) < 3600:
            return self._egress_ip
        if self._client is None:
            return None

        # Absolute URLs bypass the configured base_url.
        providers = (
            ("https://api.ipify.org?format=json", "ip"),
            ("https://ifconfig.co/json", "ip"),
        )
        for url, key in providers:
            try:
                resp = await self._client.get(url, timeout=5.0)
                resp.raise_for_status()
                ip = resp.json().get(key)
                if ip:
                    self._egress_ip = str(ip)
                    self._egress_ip_ts = now
                    return self._egress_ip
            except Exception:  # noqa: BLE001 - best-effort lookup, try next provider
                continue
        return self._egress_ip

    # -- header construction --------------------------------------------------
    def _headers(
        self,
        *,
        api_key: str | None,
        access_token: str | None,
        content_type: str | None,
    ) -> dict[str, str]:
        headers = {"X-Mirae-Version": self._version}
        if content_type:
            headers["Content-Type"] = content_type
        if api_key and access_token:
            headers["Authorization"] = f"token {api_key}:{access_token}"
        return headers

    # -- core request ---------------------------------------------------------
    async def request(
        self,
        method: str,
        route: str,
        *,
        url_args: dict[str, Any] | None = None,
        api_key: str | None = None,
        access_token: str | None = None,
        data: dict[str, Any] | None = None,
        json: Any | None = None,
        params: list[tuple[str, Any]] | dict[str, Any] | None = None,
        content_type: str | None = None,
        expect: str = "json",
    ) -> Any:
        """Perform a request against an mStock route.

        ``expect`` controls parsing: ``"json"`` returns the decoded payload,
        ``"raw"`` returns the response body as text (e.g. CSV scrip master).
        """
        if self._client is None:  # pragma: no cover - guarded by lifespan
            raise MStockUpstreamError("mStock client is not initialised", status_code=503)

        path = path_for(route, **(url_args or {}))
        headers = self._headers(
            api_key=api_key, access_token=access_token, content_type=content_type
        )

        try:
            response = await self._client.request(
                method,
                path,
                headers=headers,
                data=data if json is None else None,
                json=json,
                params=params,
            )
        except httpx.TimeoutException as exc:
            logger.warning("mStock timeout: %s %s (%s)", method, path, exc)
            raise MStockUpstreamError("Upstream mStock request timed out", status_code=504)
        except httpx.HTTPError as exc:
            logger.warning("mStock transport error: %s %s (%s)", method, path, exc)
            raise MStockUpstreamError(f"Failed to reach mStock: {exc}", status_code=502)

        return self._handle(response, expect=expect)

    # -- response handling ----------------------------------------------------
    def _handle(self, response: httpx.Response, *, expect: str) -> Any:
        content_type = response.headers.get("content-type", "")

        if expect == "raw" or ("json" not in content_type and "csv" in content_type):
            return {
                "content_type": content_type,
                "body": response.text,
            }

        if "json" in content_type:
            try:
                payload = response.json()
            except ValueError:
                raise MStockUpstreamError(
                    "Could not decode JSON response from mStock", status_code=502
                )

            # mStock occasionally wraps a single dict inside a list.
            envelope = payload[0] if isinstance(payload, list) and payload else payload

            if isinstance(envelope, dict) and envelope.get("status") == "error":
                raise MStockAPIError(
                    message=envelope.get("message", "Unknown error from mStock"),
                    error_type=envelope.get("error_type"),
                    status_code=response.status_code if response.status_code >= 400 else None,
                    data=envelope.get("data"),
                )
            return payload

        # Fallback: text / plain or unknown content type
        return {"content_type": content_type, "body": response.text}

    # -- convenience verb helpers --------------------------------------------
    async def get(self, route: str, **kwargs: Any) -> Any:
        return await self.request("GET", route, **kwargs)

    async def post(self, route: str, **kwargs: Any) -> Any:
        return await self.request("POST", route, **kwargs)

    async def put(self, route: str, **kwargs: Any) -> Any:
        return await self.request("PUT", route, **kwargs)

    async def delete(self, route: str, **kwargs: Any) -> Any:
        return await self.request("DELETE", route, **kwargs)

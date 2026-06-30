"""Canonical map of mStock Trading API (Type A) endpoints.

Paths are relative to ``MSTOCK_BASE_URL`` (https://api.mstock.trade).
Segments wrapped in ``{}`` are formatted at call time.

Source of truth: the official ``tradingapi_a`` Python SDK route table.
"""

ROUTES: dict[str, str] = {
    # --- User / session ------------------------------------------------------
    "login": "/openapi/typea/connect/login",
    "generate_session": "/openapi/typea/session/token",
    "verify_totp": "/openapi/typea/session/verifytotp",
    "fund_summary": "/openapi/typea/user/fundsummary",
    "logout": "/openapi/typea/logout",
    # --- Orders --------------------------------------------------------------
    # Order placement variety is appended at call time: regular | amo | co
    "place_order": "/openapi/typea/orders/{variety}",
    "modify_order": "/openapi/typea/orders/regular/{order_id}",
    "cancel_order": "/openapi/typea/orders/regular/{order_id}",
    "cancel_all": "/openapi/typea/orders/cancelall",
    "order_book": "/openapi/typea/orders",
    "order_details": "/openapi/typea/order/details",
    "trade_book": "/openapi/typea/tradebook",
    "trade_history": "/openapi/typea/trades",
    # --- Portfolio / positions ----------------------------------------------
    "holdings": "/openapi/typea/portfolio/holdings",
    "net_position": "/openapi/typea/portfolio/positions",
    "position_conversion": "/openapi/typea/portfolio/convertposition",
    # --- Margin --------------------------------------------------------------
    "calculate_order_margin": "/openapi/typea/margins/orders",
    # --- Market data / instruments ------------------------------------------
    "market_ohlc": "/openapi/typea/instruments/quote/ohlc",
    "market_ltp": "/openapi/typea/instruments/quote/ltp",
    "instrument_scrip": "/openapi/typea/instruments/scriptmaster",
    "historical_chart": "/openapi/typea/instruments/historical/{segment}/{security_token}/{interval}",
    "intraday_chart": "/openapi/typea/instruments/intraday/{segment_id}/{symbol}/{interval}",
    # --- Option chain --------------------------------------------------------
    "option_chain_master": "/openapi/typea/getoptionchainmaster/{exchange_id}",
    "option_chain_data": "/openapi/typea/GetOptionChain/{exchange_id}/{expiry}/{token}",
    # --- Top gainers / losers ------------------------------------------------
    "loser_gainer": "/openapi/typea/losergainer",
    # --- Basket --------------------------------------------------------------
    "create_basket": "/openapi/typea/CreateBasket",
    "fetch_basket": "/openapi/typea/FetchBasket",
    "rename_basket": "/openapi/typea/RenameBasket",
    "delete_basket": "/openapi/typea/DeleteBasket",
    "calculate_basket": "/openapi/typea/CalculateBasket",
    # --- Misc ----------------------------------------------------------------
    "health_statistics": "/openapi/typea/Health/GetHealthStatistics",
}


def path_for(route: str, **url_args: object) -> str:
    """Return the formatted upstream path for ``route``."""
    try:
        template = ROUTES[route]
    except KeyError as exc:  # pragma: no cover - programmer error
        raise KeyError(f"Unknown mStock route: {route!r}") from exc
    return template.format(**url_args) if url_args else template

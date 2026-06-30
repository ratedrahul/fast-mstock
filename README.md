# MS-Fast — mStock Trading API Gateway

A fast, production-ready **FastAPI** backend that wraps the entire
[mStock Trading API (Type A)](https://tradingapi.mstock.com/docs/v1/Introduction/)
as clean, documented REST endpoints — ready to deploy behind any website or
mobile app for **fast trading** and custom integrations.

- **Every Type A endpoint** is exposed: auth/session, orders, portfolio,
  positions, margins, market data, historical/intraday charts, option chain,
  baskets, and top gainers/losers.
- **Async + connection-pooled** upstream client (`httpx`) for low latency.
- **Multi-tenant by design** — clients pass their own mStock credentials per
  request, so one deployment serves many users.
- **Live market-data WebSocket relay** so browsers/apps never expose the raw
  access token.
- Auto-generated **Swagger UI** (`/docs`) and **ReDoc** (`/redoc`), plus a
  ready-to-import **Postman collection**.

---

## Architecture

```
app/
├── main.py                 # FastAPI app: lifespan, CORS, gateway auth, error handlers
├── core/
│   ├── config.py           # Settings (env / .env)
│   └── logging.py
├── mstock/
│   ├── client.py           # Async httpx client (one shared, pooled instance)
│   ├── routes.py           # Canonical upstream route map
│   └── exceptions.py       # Error normalisation
├── schemas/                # Pydantic request models + enums
├── api/
│   ├── deps.py             # Credential + client dependencies, gateway auth
│   └── routers/            # One router per mStock domain
└── ws/streaming.py         # WebSocket tick relay
```

Requests flow: **client → MS-Fast router → `MStockClient` → mStock** and the
normalised JSON envelope flows straight back.

---

## Quick start

```bash
# 1. Install
pip install -r requirements.txt

# 2. Configure (optional – needed only for single-user defaults / gateway key)
cp .env.example .env

# 3. Run (dev)
python run.py
# or production
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Open **http://localhost:8000/docs**.

### Docker

```bash
docker compose up --build
```

---

## Authentication

mStock uses a daily access token. The login flow:

| Step | Endpoint | What happens |
| ---- | -------- | ------------ |
| 1 | `POST /api/v1/auth/login` | Username + password → OTP sent to your mobile |
| 2 | `POST /api/v1/auth/session` | `api_key` + OTP (`request_token`) + `checksum` → returns `access_token` |
| 2′ | `POST /api/v1/auth/verify-totp` | If TOTP is enabled, use `api_key` + `totp` instead |

Then send these headers on every other call:

```
X-Api-Key:       <your api key>
X-Access-Token:  <daily access token>
```

> Single-user deployments can instead set `MSTOCK_API_KEY` and
> `MSTOCK_ACCESS_TOKEN` in `.env`; the headers then become optional.

### Optional gateway protection

Set `GATEWAY_API_KEY` in `.env` to require an `X-Gateway-Key` header on every
request (docs, `/health` and `/ws/*` are exempt). Useful for locking down a
public deployment.

---

## Endpoint map

All REST endpoints are mounted under `/api/v1`.

### Authentication (`/auth`)
| Method | Path | Description |
| ------ | ---- | ----------- |
| POST | `/auth/login` | Login & trigger OTP |
| POST | `/auth/session` | Exchange OTP for access token |
| POST | `/auth/verify-totp` | Generate session via TOTP |
| GET | `/auth/fund-summary` | Funds, cash & margin |
| GET | `/auth/logout` | Invalidate session |

### Orders (`/orders`)
| Method | Path | Description |
| ------ | ---- | ----------- |
| POST | `/orders/{variety}` | Place order (`regular`/`amo`/`co`) |
| PUT | `/orders/regular/{order_id}` | Modify order |
| DELETE | `/orders/regular/{order_id}` | Cancel order |
| POST | `/orders/cancel-all` | Cancel all orders |
| GET | `/orders/book` | Order book |
| POST | `/orders/details` | Individual order status |
| GET | `/orders/trade-book` | Trade book |
| POST | `/orders/trades` | Trade history (date range) |

### Portfolio & Positions (`/portfolio`)
| Method | Path | Description |
| ------ | ---- | ----------- |
| GET | `/portfolio/holdings` | Holdings |
| GET | `/portfolio/positions` | Net positions |
| POST | `/portfolio/convert-position` | Convert position product |

### Margins (`/margins`)
| Method | Path | Description |
| ------ | ---- | ----------- |
| POST | `/margins/orders` | Calculate order margin & charges |

### Market Data (`/market`)
| Method | Path | Description |
| ------ | ---- | ----------- |
| GET | `/market/quote/ohlc?i=NSE:ACC&i=BSE:ACC` | OHLC + LTP |
| GET | `/market/quote/ltp?i=NSE:ACC` | LTP |
| GET | `/market/instruments` | Scrip master (CSV) |
| GET | `/market/historical/{segment}/{security_token}/{interval}?from=&to=` | Historical candles |
| GET | `/market/intraday/{segment_id}/{symbol}/{interval}` | Intraday candles |

### Option Chain (`/option-chain`)
| Method | Path | Description |
| ------ | ---- | ----------- |
| GET | `/option-chain/master/{exchange_id}` | Expiries & tokens |
| GET | `/option-chain/data/{exchange_id}/{expiry}/{token}` | Option chain |

### Baskets (`/baskets`)
| Method | Path | Description |
| ------ | ---- | ----------- |
| POST | `/baskets` | Create basket |
| GET | `/baskets` | Fetch baskets |
| PUT | `/baskets` | Rename basket |
| DELETE | `/baskets` | Delete basket |
| POST | `/baskets/calculate` | Add / price a basket leg |

### Top Gainers / Losers (`/movers`)
| Method | Path | Description |
| ------ | ---- | ----------- |
| POST | `/movers` | Top gainers (`G`) or losers (`L`) |

### System
| Method | Path | Description |
| ------ | ---- | ----------- |
| GET | `/health` | Liveness probe |
| GET | `/api/v1/mstock/health-statistics` | mStock upstream health |

---

## Live streaming

```
ws://<host>/ws/ticks?api_key=<API_KEY>&access_token=<ACCESS_TOKEN>
```

After connecting, send mStock control messages as text frames:

```json
{"a": "subscribe", "v": [5633]}
{"a": "mode", "v": ["full", [5633]]}
{"a": "unsubscribe", "v": [5633]}
```

Binary tick packets and text order/trade updates are relayed back to you
untouched (parse with the same scheme as mStock's official `mticker`).

---

## Example

```bash
# Place a limit buy
curl -X POST 'http://localhost:8000/api/v1/orders/regular' \
  -H 'X-Api-Key: <API_KEY>' \
  -H 'X-Access-Token: <ACCESS_TOKEN>' \
  -H 'Content-Type: application/json' \
  -d '{
        "tradingsymbol": "INFY-EQ",
        "exchange": "NSE",
        "transaction_type": "BUY",
        "order_type": "LIMIT",
        "quantity": 10,
        "product": "MIS",
        "validity": "DAY",
        "price": 1250
      }'
```

---

## Notes

- Responses are passed through from mStock with its standard
  `{"status": "...", "data": ...}` envelope. Errors are normalised to a
  consistent shape with proper HTTP status codes.
- Respect mStock rate limits (Order: 30/s, Quote: 20/s, Data: 1/s — see the
  [docs](https://tradingapi.mstock.com/docs/v1/Introduction/)).
- The access token expires at midnight — re-run the login flow daily.

## License

MIT

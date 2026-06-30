"""User authentication & session endpoints (mStock "User" section).

Login flow
----------
1. ``POST /auth/login`` with username + password -> mStock sends an OTP to the
   registered mobile number.
2. ``POST /auth/session`` with api_key + the OTP (request_token) + checksum ->
   returns the daily ``access_token``.
   (If TOTP is enabled, use ``POST /auth/verify-totp`` instead.)
3. Use ``api_key`` + ``access_token`` as ``X-Api-Key`` / ``X-Access-Token``
   headers on every other endpoint.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import Credentials, get_client, get_credentials
from app.mstock.client import FORM, MStockClient
from app.schemas.auth import LoginRequest, SessionRequest, VerifyTotpRequest

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", summary="Step 1 – login & trigger OTP")
async def login(body: LoginRequest, client: MStockClient = Depends(get_client)):
    # NOTE: the reference SDK posts capitalised keys; mStock accepts these.
    payload = {"username": body.username, "password": body.password}
    return await client.post("login", data=payload, content_type=FORM)


@router.post("/session", summary="Step 2 – exchange OTP for an access token")
async def generate_session(body: SessionRequest, client: MStockClient = Depends(get_client)):
    payload = {
        "api_key": body.api_key,
        "request_token": body.request_token,
        "checksum": body.checksum,
    }
    return await client.post("generate_session", data=payload, content_type=FORM)


@router.post("/verify-totp", summary="Step 2 (alt) – generate session via TOTP")
async def verify_totp(body: VerifyTotpRequest, client: MStockClient = Depends(get_client)):
    payload = {"api_key": body.api_key, "totp": body.totp}
    return await client.post("verify_totp", data=payload, content_type=FORM)


@router.get("/fund-summary", summary="Funds, cash & margin summary")
async def fund_summary(
    creds: Credentials = Depends(get_credentials),
    client: MStockClient = Depends(get_client),
):
    return await client.get(
        "fund_summary", api_key=creds.api_key, access_token=creds.access_token
    )


@router.get("/logout", summary="Invalidate the access token / session")
async def logout(
    creds: Credentials = Depends(get_credentials),
    client: MStockClient = Depends(get_client),
):
    return await client.get(
        "logout", api_key=creds.api_key, access_token=creds.access_token
    )

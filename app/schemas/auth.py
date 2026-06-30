from __future__ import annotations

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(..., description="mStock client / user id", examples=["MA1234567"])
    password: str = Field(..., description="Account password", examples=["Secret@123"])


class SessionRequest(BaseModel):
    api_key: str = Field(..., description="Your mStock API key")
    request_token: str = Field(
        ...,
        description="OTP delivered to the registered mobile after /auth/login",
        examples=["123456"],
    )
    checksum: str = Field(
        "L",
        description="Source/checksum value. The reference clients use 'L'.",
        examples=["L"],
    )


class VerifyTotpRequest(BaseModel):
    api_key: str = Field(..., description="Your mStock API key")
    totp: str = Field(..., description="Current TOTP from your authenticator app", examples=["654321"])

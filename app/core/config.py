from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, loaded from environment variables / `.env`."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- App -----------------------------------------------------------------
    app_name: str = "MS-Fast"
    debug: bool = False
    log_level: str = "INFO"

    # --- mStock upstream -----------------------------------------------------
    mstock_base_url: str = "https://api.mstock.trade"
    mstock_ws_url: str = "wss://ws.mstock.trade"
    mstock_version: str = "1"
    request_timeout: float = 15.0

    # --- Default credentials (optional, single-tenant deployments) -----------
    mstock_api_key: str | None = None
    mstock_access_token: str | None = None

    # --- Gateway protection (optional) ---------------------------------------
    gateway_api_key: str | None = None

    # --- CORS ----------------------------------------------------------------
    cors_origins: str = "*"

    @property
    def cors_origins_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

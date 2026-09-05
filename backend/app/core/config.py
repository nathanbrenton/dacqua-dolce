from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """D'Acqua Dolce application configuration."""

    app_name: str = "D'Acqua Dolce"
    environment: str = "development"
    api_prefix: str = "/api"
    database_url: str

    # Production-safe default. Local development explicitly overrides this.
    session_cookie_name: str = "dacqua_session"
    session_cookie_secure: bool = True
    session_cookie_samesite: Literal["lax", "strict", "none"] = "lax"
    session_max_age_seconds: int = 12 * 60 * 60
    max_active_sessions_per_user: int = 5

    csrf_cookie_name: str = "dacqua_csrf"
    csrf_request_header_name: str = "X-CSRF-Token"
    csrf_response_header_name: str = "X-CSRF-Token"
    csrf_token_max_age_seconds: int = 12 * 60 * 60
    csrf_protection_enabled: bool = True

    request_user_agent_max_length: int = 512

    auth_rate_limit_window_seconds: int = 15 * 60
    auth_rate_limit_ip_attempts: int = 25
    auth_rate_limit_account_attempts: int = 10
    registration_rate_limit_ip_attempts: int = 10

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="DACQUA_",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()

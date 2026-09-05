from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """D'Acqua Dolce application configuration."""

    app_name: str = "D'Acqua Dolce"
    environment: str = "development"
    api_prefix: str = "/api"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="DACQUA_",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()

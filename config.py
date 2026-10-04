from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables (and optionally a .env file).
    Uses pydantic-settings for typed, validated configuration.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Required: primary provider
    exchange_rate_api_key: str = Field(..., description="API key for ExchangeRate-API (primary)")

    # Optional: fallback provider. If missing, the app runs in degraded mode.
    fastforex_api_key: str | None = Field(
        default=None,
        description="API key for FastForex (fallback). Optional.",
    )

    # Timeouts (in seconds)
    primary_timeout: float = Field(default=5.0, ge=1.0, le=30.0)
    fallback_timeout: float = Field(default=5.0, ge=1.0, le=30.0)


settings = Settings()
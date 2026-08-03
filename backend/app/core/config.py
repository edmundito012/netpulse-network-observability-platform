"""Application configuration loaded from environment variables."""

from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


INSECURE_SECRET_KEYS = {
    "change-this-secret",
    "change-me",
    "secret",
    "test-secret-key",
    "netpulse-super-secret-dev-key",
    "replace-with-a-random-secret-of-at-least-32-characters",
}


class Settings(BaseSettings):
    """Validated NetPulse application settings."""

    # Runtime environment
    ENVIRONMENT: Literal[
        "development",
        "test",
        "production",
    ] = "development"

    # Database
    DATABASE_URL: str
    TEST_DATABASE_URL: str | None = None

    # JWT authentication
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Scheduler
    MONITOR_INTERVAL_SECONDS: int = 30
    SNMP_INTERVAL_SECONDS: int = 60
    DASHBOARD_BROADCAST_INTERVAL_SECONDS: int = 5

    # Correlation worker
    CORRELATION_WORKER_ENABLED: bool = False
    CORRELATION_WORKER_INTERVAL_SECONDS: int = 30
    CORRELATION_WORKER_BATCH_SIZE: int = 25
    CORRELATION_WINDOW_SECONDS: int = 900
    CORRELATION_THRESHOLD: float = 0.65
    CORRELATION_MAX_CANDIDATES: int = 25

    # Monitoring
    PING_TIMEOUT_SECONDS: int = 2

    # SNMP
    SNMP_PORT: int = 1161
    SNMP_TIMEOUT_SECONDS: int = 2
    SNMP_RETRIES: int = 1

    # Optional Telegram notifications
    TELEGRAM_BOT_TOKEN: str | None = None
    TELEGRAM_CHAT_ID: str | None = None

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        """Reject insecure configuration in production."""

        if self.ENVIRONMENT != "production":
            return self

        if self.SECRET_KEY in INSECURE_SECRET_KEYS:
            raise ValueError(
                "SECRET_KEY cannot use a known development value "
                "when ENVIRONMENT=production"
            )

        if len(self.SECRET_KEY) < 32:
            raise ValueError(
                "SECRET_KEY must contain at least 32 characters "
                "when ENVIRONMENT=production"
            )

        if not self.DATABASE_URL.startswith(
            (
                "postgresql://",
                "postgresql+psycopg2://",
            )
        ):
            raise ValueError(
                "DATABASE_URL must use PostgreSQL in production"
            )

        return self


settings = Settings()

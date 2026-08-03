from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


class Settings(BaseSettings):

    # Database
    DATABASE_URL: str = (
        "postgresql+psycopg2://admin:admin@postgres:5432/netpulse"
    )
    TEST_DATABASE_URL: str = (
        "postgresql+psycopg2://admin:admin@postgres:5432/netpulse_test"
    )
    # JWT / Auth
    SECRET_KEY: str = (
        "netpulse-super-secret-dev-key"
    )

    ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Scheduler
    MONITOR_INTERVAL_SECONDS: int = 30

    SNMP_INTERVAL_SECONDS: int = 60

    DASHBOARD_BROADCAST_INTERVAL_SECONDS: int = 5

    # Correlation worker
    CORRELATION_WORKER_ENABLED: bool = True

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

    # Telegram Notifications
    TELEGRAM_BOT_TOKEN: str | None = None

    TELEGRAM_CHAT_ID: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    # Database
    DATABASE_URL: str = (
        "postgresql+psycopg2://admin:admin@localhost:5433/netpulse"
    )

    # JWT / Auth
    SECRET_KEY: str = "netpulse-super-secret-dev-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Scheduler
    MONITOR_INTERVAL_SECONDS: int = 30
    SNMP_INTERVAL_SECONDS: int = 60
    DASHBOARD_BROADCAST_INTERVAL_SECONDS: int = 5

    # Monitoring
    PING_TIMEOUT_SECONDS: int = 2

    # SNMP
    SNMP_PORT: int = 1161
    SNMP_TIMEOUT_SECONDS: int = 2
    SNMP_RETRIES: int = 1

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
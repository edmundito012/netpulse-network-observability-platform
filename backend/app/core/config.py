from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg2://admin:admin@localhost:5433/netpulse"

    class Config:
        env_file = ".env"


settings = Settings()
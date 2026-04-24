import os
import secrets
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    PROJECT_NAME: str = "Uzum Market Analytics Platform"

    POSTGRES_USER: str = "uzum_user"
    POSTGRES_PASSWORD: str = "uzum_password"
    POSTGRES_DB: str = "uzum_db"
    DATABASE_URL: str = f"sqlite:///{os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'uzum.db')}"

    REDIS_URL: str = "redis://localhost:6379/0"

    UZUM_API_TOKEN: str = ""

    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    BACKEND_CORS_ORIGINS: str = (
        "http://localhost:3000,http://localhost:3001,"
        "http://127.0.0.1:3000,http://127.0.0.1:3001"
    )


settings = Settings()

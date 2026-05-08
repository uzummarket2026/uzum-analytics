import os
import secrets
import sys
from typing import Optional
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

    # SECRET_KEY env'dan kelishi kerak. Bo'sh bo'lsa — productionda crash, dev'da
    # ogohlantirish bilan vaqtinchalik tasodifiy kalit. ENV=production qo'yilsa,
    # bo'sh kalit dasturning ishga tushishini bloklaydi.
    SECRET_KEY: str = ""
    ENV: str = "development"

    # Maxfiy ma'lumotlarni (Uzum API token va b.) DB'da shifrlash uchun.
    # Yo'q bo'lsa SECRET_KEY'dan derive qilinadi.
    ENCRYPTION_KEY: Optional[str] = None

    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    BACKEND_CORS_ORIGINS: str = (
        "http://localhost:3000,http://localhost:3001,"
        "http://127.0.0.1:3000,http://127.0.0.1:3001"
    )


settings = Settings()

# Productionda SECRET_KEY majburiy
if not settings.SECRET_KEY:
    if settings.ENV.lower() in ("prod", "production"):
        sys.stderr.write(
            "FATAL: SECRET_KEY env o'rnatilmagan. Productionda majburiy.\n"
            "Generatsiya: python -c \"import secrets; print(secrets.token_urlsafe(64))\"\n"
        )
        raise RuntimeError("SECRET_KEY is required in production")
    # Dev fallback — har restartda yangidan, bu OK emas, lekin lokal ishlash uchun
    settings.SECRET_KEY = secrets.token_urlsafe(32)
    sys.stderr.write(
        "WARNING: SECRET_KEY env yo'q. Dev rejimida vaqtinchalik kalit ishlatildi.\n"
        "Har restartda barcha JWT tokenlar bekor bo'ladi.\n"
    )

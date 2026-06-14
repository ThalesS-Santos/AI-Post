from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str
    GEMINI_API_KEY: str
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    model_config = {"env_file": BACKEND_DIR / ".env"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()

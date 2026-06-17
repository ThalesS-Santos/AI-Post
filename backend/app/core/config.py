from pydantic_settings import BaseSettings
from functools import lru_cache
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    # Valores padrões mockados para rodar offline sem Supabase
    SUPABASE_URL: str = "http://localhost:8000"
    SUPABASE_ANON_KEY: str = "mock-anon"
    SUPABASE_SERVICE_ROLE_KEY: str = "mock-service-role"
    GEMINI_API_KEY: str = ""
    VERTEX_API_KEY: str = ""
    JWT_SECRET: str = "mock-jwt-secret"
    JWT_ALGORITHM: str = "HS256"
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    model_config = {"env_file": BACKEND_DIR / ".env"}

@lru_cache()
def get_settings() -> Settings:
    return Settings()

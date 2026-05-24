from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    # API Server configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Database configurations (SQLite async local fallback)
    DATABASE_URL: str = "sqlite+aiosqlite:///./docuflow.db"
    
    # Model API Keys (optional for skeletal fallback operations)
    GEMINI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    
    # Allow reading environment variables from a .env file
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()

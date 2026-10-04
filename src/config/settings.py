"""
Configuration settings for TAES 2
"""

import os
from typing import List, Optional
from urllib.parse import quote_plus

from dotenv import load_dotenv

load_dotenv()


def _build_database_url() -> str:
    """Return DATABASE_URL, or assemble it from DB_* parts (handy when the
    password is injected as its own variable)."""
    url = os.getenv("DATABASE_URL")
    if url:
        return url

    host = os.getenv("DB_HOST")
    if host:
        user = quote_plus(os.getenv("DB_USER", "taes2_db_user"))
        password = quote_plus(os.getenv("DB_PASSWORD", ""))
        port = os.getenv("DB_PORT", "5432")
        name = os.getenv("DB_NAME", "taes2_db")
        return f"postgresql://{user}:{password}@{host}:{port}/{name}"

    return "postgresql://taes2_db_user@localhost:5432/taes2_db"


DEFAULT_MODEL_CHOICES = [
    "gpt-4o-mini",
    "gpt-4o",
    "anthropic/claude-3-5-haiku-latest",
    "anthropic/claude-sonnet-4-20250514",
    "gemini/gemini-2.0-flash",
    "ollama/llama3",
    "ollama/mistral",
]


def _model_choices(default_model: str) -> List[str]:
    """Models offered in the UI. Override with a comma separated MODEL_CHOICES."""
    raw = os.getenv("MODEL_CHOICES", "")
    choices = [m.strip() for m in raw.split(",") if m.strip()] or list(DEFAULT_MODEL_CHOICES)
    if default_model not in choices:
        choices.insert(0, default_model)
    return choices


class Settings:
    """Application settings and configuration"""
    
    # Database settings
    DATABASE_URL: str = _build_database_url()
    DB_CONNECT_RETRIES: int = int(os.getenv("DB_CONNECT_RETRIES", "10"))
    
    # LLM settings
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "gpt-4o-mini")
    DEFAULT_TEMPERATURE: float = float(os.getenv("DEFAULT_TEMPERATURE", "0.3"))
    DEFAULT_MAX_TOKENS: int = int(os.getenv("DEFAULT_MAX_TOKENS", "2000"))
    MODEL_CHOICES: List[str] = _model_choices(DEFAULT_MODEL)
    
    # Application settings
    BATCH_SIZE: int = int(os.getenv("BATCH_SIZE", "32"))
    MAX_UPLOAD_SIZE: int = int(os.getenv("MAX_UPLOAD_SIZE", "100"))
    VECTOR_DIMENSION: int = int(os.getenv("VECTOR_DIMENSION", "384"))
    
    # File upload settings
    UPLOAD_FOLDER: str = "uploads"
    ALLOWED_EXTENSIONS: set = {".pdf", ".docx", ".txt"}
    MAX_FILE_SIZE_MB: int = 50
    
    # Logging settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = "logs/taes2.log"

# Global settings instance
settings = Settings()

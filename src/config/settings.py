"""
Configuration settings for TAES 2
"""

import os
from typing import Optional

class Settings:
    """Application settings and configuration"""
    
    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://username:password@localhost:5432/taes2_db")
    
    # LLM settings
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = os.getenv("ANTHROPIC_API_KEY")
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "gpt-3.5-turbo")
    DEFAULT_TEMPERATURE: float = float(os.getenv("DEFAULT_TEMPERATURE", "0.3"))
    DEFAULT_MAX_TOKENS: int = int(os.getenv("DEFAULT_MAX_TOKENS", "2000"))
    
    # Application settings
    BATCH_SIZE: int = int(os.getenv("BATCH_SIZE", "32"))
    MAX_UPLOAD_SIZE: int = int(os.getenv("MAX_UPLOAD_SIZE", "100"))
    VECTOR_DIMENSION: int = int(os.getenv("VECTOR_DIMENSION", "384"))
    
    # File upload settings
    UPLOAD_FOLDER: str = "uploads"
    ALLOWED_EXTENSIONS: set = {".pdf", ".docx", ".doc", ".txt"}
    MAX_FILE_SIZE_MB: int = 50
    
    # Logging settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = "logs/taes2.log"

# Global settings instance
settings = Settings()

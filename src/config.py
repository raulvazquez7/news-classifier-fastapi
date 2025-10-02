"""
Application configuration using Pydantic Settings.

All environment variables are validated at startup.
If any required variable is missing, the app fails to start with a clear error.
"""

from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Variables are loaded from .env file automatically.
    Missing required variables will cause the app to fail at startup.
    """
    
    # OpenAI Configuration (required)
    openai_api_key: str = Field(
        ...,
        description="OpenAI API key for Responses API",
        min_length=20
    )
    
    openai_model: str = Field(
        default="gpt-4o-mini",
        description="OpenAI model to use for classification"
    )
    
    # Application Configuration (optional with defaults)
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR)"
    )
    
    hn_base_url: str = Field(
        default="https://news.ycombinator.com",
        description="Base URL for Hacker News"
    )
    
    api_host: str = Field(
        default="0.0.0.0",
        description="API host address"
    )
    
    api_port: int = Field(
        default=3000,
        description="API port number"
    )
    
    @field_validator("openai_api_key")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        """Validate that API key looks like an OpenAI key"""
        if not v.startswith("sk-"):
            raise ValueError("OPENAI_API_KEY must start with 'sk-'")
        return v
    
    @field_validator("openai_model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        """Validate that model is supported"""
        supported_models = ["gpt-4o-mini", "gpt-4o", "gpt-4o-2024-08-06"]
        if v not in supported_models:
            logger.warning(f"Model {v} not in known models: {supported_models}")
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False  # OPENAI_API_KEY = openai_api_key


# Singleton instance - validated at import time
# If this fails, the entire app fails to start (fail-fast)
try:
    settings = Settings()
    logger.info("✅ Configuration loaded and validated successfully")
    logger.info(f"   - OpenAI Model: {settings.openai_model}")
    logger.info(f"   - API Port: {settings.api_port}")
except Exception as e:
    logger.error(f"❌ Configuration validation failed: {e}")
    raise

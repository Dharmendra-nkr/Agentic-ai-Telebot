"""
Centralized configuration management for the Agentic AI Assistant.
Uses Pydantic Settings for type-safe configuration with environment variable support.
"""

from typing import Optional, List
from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application Settings
    app_name: str = Field(default="AgenticAI_Assistant")
    environment: str = Field(default="development")
    debug: bool = Field(default=True)
    log_level: str = Field(default="INFO")
    
    # Telegram Bot Configuration
    telegram_bot_token: str = Field(..., description="Telegram Bot API token")
    telegram_webhook_url: Optional[str] = Field(default=None)
    telegram_webhook_secret: Optional[str] = Field(default=None)
    
    # LLM Configuration
    llm_provider: str = Field(default="openai", description="LLM provider: openai, anthropic, or groq")
    
    # OpenAI
    openai_api_key: Optional[str] = Field(default=None)
    openai_model: str = Field(default="gpt-4-turbo-preview")
    openai_max_tokens: int = Field(default=4096)
    openai_temperature: float = Field(default=0.7)
    
    # Anthropic
    anthropic_api_key: Optional[str] = Field(default=None)
    anthropic_model: str = Field(default="claude-3-sonnet-20240229")
    
    # Groq
    groq_api_key: Optional[str] = Field(default=None)
    groq_model: str = Field(default="llama-3.1-70b-versatile")
    groq_base_url: str = Field(default="https://api.groq.com/openai/v1")
    
    # Database Configuration
    database_url: str = Field(
        default="sqlite+aiosqlite:///./agentic_ai.db",
        description="Database connection URL"
    )
    database_echo: bool = Field(default=False)
    
    # Redis Configuration
    redis_url: str = Field(default="redis://localhost:6379/0")
    use_redis: bool = Field(default=False)
    
    # Google Calendar API
    google_client_id: Optional[str] = Field(default=None)
    google_client_secret: Optional[str] = Field(default=None)
    google_redirect_uri: str = Field(default="http://localhost:8000/auth/google/callback")
    google_credentials_file: str = Field(default="credentials/google_credentials.json")
    
    # Brave Search API
    brave_search_api_key: Optional[str] = Field(default=None, description="Brave Search API key")
    enable_brave_search: bool = Field(default=True, description="Enable Brave Search MCP")
    
    # Browserbase API
    browserbase_api_key: Optional[str] = Field(default=None, description="Browserbase API key")
    enable_browserbase: bool = Field(default=True, description="Enable Browserbase MCP")
    
    # Scheduler Configuration
    scheduler_timezone: str = Field(default="Asia/Kolkata")
    scheduler_job_store: str = Field(default="sqlalchemy")
    
    # Memory Configuration
    short_term_memory_size: int = Field(default=20)
    long_term_memory_enabled: bool = Field(default=True)
    temporal_memory_enabled: bool = Field(default=True)
    
    # Agent Configuration
    agent_max_iterations: int = Field(default=5)
    agent_timeout_seconds: int = Field(default=30)
    enable_clarifying_questions: bool = Field(default=True)
    enable_proactive_suggestions: bool = Field(default=True)
    
    # Notification Settings
    notification_retry_attempts: int = Field(default=3)
    notification_retry_delay_seconds: int = Field(default=60)
    
    # Security
    secret_key: str = Field(default="change-me-in-production")
    allowed_user_ids: Optional[str] = Field(default=None)
    
    # Feature Flags
    enable_voice_messages: bool = Field(default=False)
    enable_image_processing: bool = Field(default=False)
    enable_web_dashboard: bool = Field(default=False)
    
    @validator("llm_provider")
    def validate_llm_provider(cls, v):
        """Validate LLM provider selection."""
        allowed = ["openai", "anthropic", "groq"]
        if v not in allowed:
            raise ValueError(f"LLM provider must be one of {allowed}")
        return v
    
    @validator("openai_api_key")
    def validate_openai_key(cls, v, values):
        """Ensure OpenAI API key is set if using OpenAI."""
        if values.get("llm_provider") == "openai" and not v:
            raise ValueError("OPENAI_API_KEY must be set when using OpenAI provider")
        return v
    
    @validator("anthropic_api_key")
    def validate_anthropic_key(cls, v, values):
        """Ensure Anthropic API key is set if using Anthropic."""
        if values.get("llm_provider") == "anthropic" and not v:
            raise ValueError("ANTHROPIC_API_KEY must be set when using Anthropic provider")
        return v
    
    @validator("groq_api_key")
    def validate_groq_key(cls, v, values):
        """Ensure Groq API key is set if using Groq."""
        if values.get("llm_provider") == "groq" and not v:
            raise ValueError("GROQ_API_KEY must be set when using Groq provider")
        return v
    
    @property
    def allowed_users(self) -> Optional[List[int]]:
        """Parse allowed user IDs from comma-separated string."""
        if not self.allowed_user_ids:
            return None
        return [int(uid.strip()) for uid in self.allowed_user_ids.split(",")]
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() == "development"
    
    @property
    def use_webhook(self) -> bool:
        """Check if webhook mode is enabled."""
        return self.telegram_webhook_url is not None
    
    def get_credentials_path(self) -> Path:
        """Get the path to Google credentials file."""
        return Path(self.google_credentials_file)


# Global settings instance
settings = Settings()


# Validate critical settings on import
def validate_settings():
    """Validate critical settings and raise errors if misconfigured."""
    errors = []
    
    if not settings.telegram_bot_token:
        errors.append("TELEGRAM_BOT_TOKEN is required")
    
    if settings.llm_provider == "openai" and not settings.openai_api_key:
        errors.append("OPENAI_API_KEY is required when using OpenAI provider")
    
    if settings.llm_provider == "anthropic" and not settings.anthropic_api_key:
        errors.append("ANTHROPIC_API_KEY is required when using Anthropic provider")
    
    if settings.llm_provider == "groq" and not settings.groq_api_key:
        errors.append("GROQ_API_KEY is required when using Groq provider")
    
    if settings.is_production and settings.secret_key == "change-me-in-production":
        errors.append("SECRET_KEY must be changed in production")
    
    if errors:
        raise ValueError(f"Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors))


# Validate on module import (can be disabled for testing)
if settings.environment != "testing":
    try:
        validate_settings()
    except ValueError as e:
        print(f"⚠️  Configuration Warning: {e}")
        print("Please check your .env file and ensure all required variables are set.")

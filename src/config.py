"""Application configuration loaded from environment variables."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly typed application configuration."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    groq_api_key: str = Field(
        ...,
        description="Groq API key from https://console.groq.com/keys",
    )
    default_model: str = Field(
        default="openai/gpt-oss-120b",
        description="Primary model for complex reasoning and planning",
    )
    fallback_model: str = Field(
        default="qwen/qwen3.8-27b",
        description="Fast fallback model for simple tasks or rate-limit recovery",
    )
    llm_temperature: float = Field(
        default=0.1,
        ge=0.0,
        le=2.0,
        description="Sampling temperature; lower values ensure deterministic tool calls",
    )


# Global singleton instance
settings = Settings()

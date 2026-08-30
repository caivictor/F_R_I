"""Application configuration settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """F.R.I. backend configuration settings."""

    GEMINI_API_KEY: str = ""
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEFAULT_TIMEOUT_SECONDS: int = 15

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()

"""NFL Script Generator — Configuration."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from .env / environment."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # ── API Keys ──────────────────────────────────────────
    x_bearer_token: str = ""
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

    # ── Logging ───────────────────────────────────────────
    log_level: str = "INFO"

    # ── Output ────────────────────────────────────────────
    output_dir: str = "output"

    # ── Tuning ────────────────────────────────────────────
    min_engagement_score: float = 15.0
    min_credibility_score: float = 25.0
    max_tweets_per_query: int = 200
    num_narratives: int = 5
    script_target_minutes: int = 10


settings = Settings()  # type: ignore[call-arg]

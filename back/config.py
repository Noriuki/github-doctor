"""Application configuration."""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """App settings from environment or .env."""

    model_config = SettingsConfigDict(env_prefix="GITHUB_DOCTOR_", env_file=".env")

    github_token: Optional[str] = None
    api_title: str = "GitHub Doctor"
    api_version: str = "0.1.0"
    cache_ttl_seconds: int = 300  # 5 min TTL for report cache


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_github_client():
    """Return configured GitHub client (used by API)."""
    from back.infrastructure.github_client import GitHubClient
    settings = get_settings()
    return GitHubClient(token=settings.github_token)

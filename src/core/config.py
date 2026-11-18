from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized configuration loaded from .env and environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Target Application
    base_url: str = "https://www.saucedemo.com"
    api_health_url: str = "https://www.saucedemo.com/"
    monitor_username: str = ""
    monitor_password: str = ""

    # SLA & Execution
    sla_threshold_seconds: float = 3.0
    browser_headless: bool = True
    viewport_width: int = 1920
    viewport_height: int = 1080
    artifacts_dir: Path = Path("artifacts")

    # Alerting (Telegram / Slack)
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    slack_webhook_url: str = ""

    @property
    def telegram_enabled(self) -> bool:
        return bool(self.telegram_bot_token and self.telegram_chat_id)

    @property
    def slack_enabled(self) -> bool:
        return bool(self.slack_webhook_url)

    def ensure_artifacts_dir(self) -> Path:
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        return self.artifacts_dir


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
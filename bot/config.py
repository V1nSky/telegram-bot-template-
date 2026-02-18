"""Application configuration via pydantic-settings.

All settings are loaded from environment variables or a .env file.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    """Deployment environment."""

    development = "development"
    staging = "staging"
    production = "production"


class BotMode(str, Enum):
    """Update receiving mode."""

    polling = "polling"
    webhook = "webhook"


class Settings(BaseSettings):
    """Central configuration object.

    Populate via environment variables or a ``.env`` file.

    Example .env::

        BOT_TOKEN=123456:ABC-DEF...
        ENVIRONMENT=development
        BOT_MODE=polling
        DATABASE_URL=sqlite+aiosqlite:///./dev.db
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Telegram ─────────────────────────────────────────────────────────────
    bot_token: SecretStr = Field(..., description="Telegram Bot API token")

    # ── App ──────────────────────────────────────────────────────────────────
    environment: Environment = Environment.development
    bot_mode: BotMode = BotMode.polling
    debug: bool = False

    # ── Webhook (only used when bot_mode=webhook) ─────────────────────────
    webhook_host: Optional[str] = Field(None, description="Public HTTPS host, e.g. https://example.com")
    webhook_path: str = "/webhook"
    webhook_secret: Optional[SecretStr] = None
    webapp_host: str = "0.0.0.0"
    webapp_port: int = 8080

    # ── Database ─────────────────────────────────────────────────────────────
    database_url: str = Field(
        "sqlite+aiosqlite:///./dev.db",
        description="SQLAlchemy async DB URL",
    )
    db_echo: bool = False  # set True to log all SQL

    # ── Redis (optional) ─────────────────────────────────────────────────────
    redis_url: Optional[str] = Field(None, description="redis://host:6379/0")

    # ── Throttling ────────────────────────────────────────────────────────────
    throttle_rate: float = Field(0.5, description="Min seconds between user requests")

    # ── Logging ──────────────────────────────────────────────────────────────
    log_level: str = "INFO"
    log_json: bool = False  # structured JSON logs in production

    @field_validator("log_json", mode="before")
    @classmethod
    def auto_json_logs(cls, v: bool, info: object) -> bool:  # type: ignore[override]
        # Force JSON logs in production unless explicitly overridden
        return v

    @property
    def webhook_url(self) -> Optional[str]:
        """Full webhook URL."""
        if self.webhook_host:
            return f"{self.webhook_host.rstrip('/')}{self.webhook_path}"
        return None

    @property
    def is_production(self) -> bool:
        return self.environment == Environment.production

    @property
    def is_development(self) -> bool:
        return self.environment == Environment.development


# Module-level singleton — import and use directly:
#   from bot.config import settings
settings = Settings()  # type: ignore[call-arg]

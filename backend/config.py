"""
LK Clinic Tools - Application Configuration
Loads settings from environment variables with validation.
"""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # --- App ---
    app_env: str = "development"
    app_debug: bool = True
    app_secret_key: str = "change-this-to-a-random-secret"
    app_base_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:3000"

    # --- Supabase ---
    supabase_url: str
    supabase_anon_key: str
    supabase_service_role_key: str
    supabase_jwt_secret: str

    # --- Redis ---
    redis_url: str = "redis://redis:6379/0"

    # --- Anthropic Claude ---
    anthropic_api_key: str = ""
    claude_model: str = "claude-sonnet-4-5-20250929"

    # --- Google APIs ---
    google_places_api_key: str = ""
    google_calendar_client_id: str = ""
    google_calendar_client_secret: str = ""

    # --- Evolution API (WhatsApp) ---
    evolution_api_url: str = ""
    evolution_api_key: str = ""

    # --- Timezone & Locale ---
    tz: str = "America/Sao_Paulo"
    default_locale: str = "pt-BR"

    # --- Rate Limiting ---
    rate_limit_per_minute: int = 60
    whatsapp_daily_limit_per_clinic: int = 1000

    # --- Widget ---
    widget_websocket_url: str = "ws://localhost:8000/ws/widget"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def cors_origins(self) -> list[str]:
        origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
        if self.frontend_url and self.frontend_url not in origins:
            origins.append(self.frontend_url)
        return origins

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()

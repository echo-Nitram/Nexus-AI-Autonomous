from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    app_name: str = "Nexus AI Autonomous Trader"
    environment: str = "development"
    log_level: str = "INFO"
    secret_key: str = "change-this-to-a-random-secret-key"
    encryption_key: str = ""

    # Database
    database_url: str = "postgresql+asyncpg://nexus:nexus_secret@127.0.0.1:5432/nexus_trader"
    redis_url: str = "redis://127.0.0.1:6379/0"

    # LLM
    llm_provider: str = "anthropic"
    anthropic_api_key: str = ""
    openai_api_key: str = ""

    # Exchanges
    binance_api_key: str = ""
    binance_api_secret: str = ""
    hyperliquid_api_key: str = ""
    hyperliquid_api_secret: str = ""

    # Telegram
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    # Trading
    shadow_mode: bool = True
    max_position_size_pct: float = 0.05
    max_daily_loss_pct: float = 0.02
    max_open_positions: int = 5

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()

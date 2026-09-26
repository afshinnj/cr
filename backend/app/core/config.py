"""Application configuration.

This module is the **only** place in the codebase that reads environment
variables. Everything else receives settings via dependency injection.

See docs/00-overview.md (invariants I9, I10, I11).
"""

from __future__ import annotations

import functools
from enum import StrEnum
from pathlib import Path

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_REPO_ROOT = Path(__file__).resolve().parents[3]


class Environment(StrEnum):
    DEVELOPMENT = "development"
    TEST = "test"
    PRODUCTION = "production"


class DataMode(StrEnum):
    """Where market data comes from.

    ``MOCK`` exists only so automated tests can run without network access and
    is rejected at startup when ``ENV=production`` (requirement §29).
    """

    LIVE = "live"
    MOCK = "mock"
    REPLAY = "replay"


class LogFormat(StrEnum):
    CONSOLE = "console"
    JSON = "json"


class AIProviderName(StrEnum):
    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    NULL = "null"


class UniverseProfile(StrEnum):
    SMALL = "small"
    MEDIUM = "medium"
    FULL = "full"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(_REPO_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Application -----------------------------------------------------
    app_name: str = "AI Market Intelligence Platform"
    env: Environment = Environment.DEVELOPMENT
    debug: bool = False
    log_level: str = "INFO"
    log_format: LogFormat = LogFormat.CONSOLE
    data_mode: DataMode = DataMode.LIVE

    # --- API -------------------------------------------------------------
    api_host: str = "0.0.0.0"
    api_port: int = 8787
    api_prefix: str = "/api/v1"
    local_api_token: SecretStr = SecretStr("")
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])

    # --- PostgreSQL ------------------------------------------------------
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "amip"
    postgres_user: str = "amip"
    postgres_password: SecretStr = SecretStr("")
    postgres_pool_size: int = 10
    postgres_max_overflow: int = 20
    postgres_echo: bool = False
    # Full override (used by tests / CI); when set it wins over the parts above.
    database_url: str | None = None

    # --- Redis -----------------------------------------------------------
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: SecretStr = SecretStr("")

    # --- Universe --------------------------------------------------------
    universe_profile: UniverseProfile = UniverseProfile.SMALL
    persisted_timeframes: list[str] = Field(default_factory=lambda: ["1h", "4h", "1d"])

    # --- Providers -------------------------------------------------------
    binance_base_url: str = "https://api.binance.com"
    binance_futures_base_url: str = "https://fapi.binance.com"
    binance_ws_url: str = "wss://stream.binance.com:9443/ws"
    coingecko_base_url: str = "https://api.coingecko.com/api/v3"
    coingecko_api_key: SecretStr = SecretStr("")
    tsetmc_base_url: str = "http://www.tsetmc.com"
    tsetmc_cdn_url: str = "http://cdn.tsetmc.com"
    tsetmc_user_agent: str = "Mozilla/5.0 (compatible; AMIP/0.1)"
    tsetmc_request_timeout: int = 20

    # --- Resilience ------------------------------------------------------
    http_max_retries: int = 5
    http_backoff_base_seconds: float = 1.0
    http_backoff_max_seconds: float = 60.0
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_reset_seconds: int = 60

    # --- AI --------------------------------------------------------------
    ai_provider: AIProviderName = AIProviderName.OLLAMA
    ollama_host: str = "http://localhost:11434"
    ai_model: str = "qwen2.5:7b-instruct"
    ai_temperature: float = 0.2
    ai_top_p: float = 0.9
    ai_seed: int = 42
    ai_num_ctx: int = 8192
    ai_timeout_seconds: int = 90
    ai_max_concurrency: int = 1
    ai_cache_ttl_seconds: int = 1800
    ai_fallback_provider: AIProviderName = AIProviderName.NULL

    # --- Paths -----------------------------------------------------------
    config_dir: Path = _REPO_ROOT / "config"

    # ---------------------------------------------------------------- utils
    @field_validator("log_level")
    @classmethod
    def _upper_log_level(cls, value: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = value.upper()
        if upper not in allowed:
            raise ValueError(f"log_level must be one of {sorted(allowed)}")
        return upper

    @model_validator(mode="after")
    def _enforce_production_invariants(self) -> Settings:
        """Invariant I9 / requirement §29: no fake data in production."""
        if self.env is Environment.PRODUCTION:
            if self.data_mode is DataMode.MOCK:
                raise ValueError(
                    "DATA_MODE=mock is forbidden when ENV=production "
                    "(requirement §29: no fake data in production)"
                )
            if not self.local_api_token.get_secret_value():
                raise ValueError("LOCAL_API_TOKEN must be set in production")
            if not self.postgres_password.get_secret_value():
                raise ValueError("POSTGRES_PASSWORD must be set in production")
            if self.debug:
                raise ValueError("DEBUG must be false in production")
        return self

    # --------------------------------------------------------------- derived
    @property
    def sqlalchemy_dsn(self) -> str:
        if self.database_url:
            return self.database_url
        pwd = self.postgres_password.get_secret_value()
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{pwd}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def alembic_dsn(self) -> str:
        """Synchronous DSN used by Alembic."""
        return self.sqlalchemy_dsn.replace("+asyncpg", "+psycopg").replace("+aiosqlite", "")

    @property
    def redis_dsn(self) -> str:
        pwd = self.redis_password.get_secret_value()
        auth = f":{pwd}@" if pwd else ""
        return f"redis://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def is_production(self) -> bool:
        return self.env is Environment.PRODUCTION

    def safe_dump(self) -> dict[str, object]:
        """Settings with every secret redacted — safe for logs and the API."""
        data = self.model_dump(mode="json")
        for key, value in list(data.items()):
            if isinstance(getattr(self, key, None), SecretStr):
                data[key] = "***" if getattr(self, key).get_secret_value() else ""
            elif isinstance(value, Path):
                data[key] = str(value)
        return data


@functools.lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings singleton (cleared in tests via ``get_settings.cache_clear()``)."""
    return Settings()

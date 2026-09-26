"""Configuration invariants — the guardrails that keep §25 and §29 true."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.core.config import DataMode, Environment, Settings

BASE = {
    "_env_file": None,
    "local_api_token": "x" * 32,
    "postgres_password": "pw",
}


def make(**overrides: object) -> Settings:
    return Settings(**{**BASE, **overrides})  # type: ignore[arg-type]


class TestProductionInvariants:
    def test_mock_data_mode_is_rejected_in_production(self) -> None:
        """Requirement §29: no fake data in production."""
        with pytest.raises(ValidationError, match="forbidden when ENV=production"):
            make(env=Environment.PRODUCTION, data_mode=DataMode.MOCK, debug=False)

    def test_mock_data_mode_is_allowed_outside_production(self) -> None:
        settings = make(env=Environment.TEST, data_mode=DataMode.MOCK)
        assert settings.data_mode is DataMode.MOCK

    def test_missing_local_token_is_rejected_in_production(self) -> None:
        with pytest.raises(ValidationError, match="LOCAL_API_TOKEN"):
            Settings(
                _env_file=None,  # type: ignore[call-arg]
                env=Environment.PRODUCTION,
                debug=False,
                local_api_token="",
                postgres_password="pw",
            )

    def test_debug_is_rejected_in_production(self) -> None:
        with pytest.raises(ValidationError, match="DEBUG must be false"):
            make(env=Environment.PRODUCTION, debug=True)

    def test_valid_production_settings_pass(self) -> None:
        settings = make(env=Environment.PRODUCTION, debug=False, data_mode=DataMode.LIVE)
        assert settings.is_production


class TestSecretHandling:
    def test_safe_dump_redacts_every_secret(self) -> None:
        settings = make(postgres_password="super-secret-value")
        dumped = settings.safe_dump()
        assert dumped["postgres_password"] == "***"
        assert "super-secret-value" not in str(dumped)

    def test_empty_secrets_render_as_empty_not_stars(self) -> None:
        settings = make(coingecko_api_key="")
        assert settings.safe_dump()["coingecko_api_key"] == ""

    def test_dsn_contains_password_but_dump_does_not(self) -> None:
        settings = make(postgres_password="pw123")
        assert "pw123" in settings.sqlalchemy_dsn
        assert "pw123" not in str(settings.safe_dump())


class TestDerivedValues:
    def test_database_url_override_wins(self) -> None:
        settings = make(database_url="sqlite+aiosqlite:///:memory:")
        assert settings.sqlalchemy_dsn == "sqlite+aiosqlite:///:memory:"

    def test_async_dsn_uses_asyncpg(self) -> None:
        assert make().sqlalchemy_dsn.startswith("postgresql+asyncpg://")

    def test_alembic_dsn_is_synchronous(self) -> None:
        assert "+asyncpg" not in make().alembic_dsn

    def test_redis_dsn_without_password(self) -> None:
        assert make(redis_password="").redis_dsn == "redis://localhost:6379/0"

    def test_redis_dsn_with_password(self) -> None:
        assert make(redis_password="s3cret").redis_dsn == "redis://:s3cret@localhost:6379/0"

    def test_invalid_log_level_is_rejected(self) -> None:
        with pytest.raises(ValidationError):
            make(log_level="CHATTY")

    def test_log_level_is_normalised(self) -> None:
        assert make(log_level="debug").log_level == "DEBUG"

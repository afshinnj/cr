"""Shared pytest fixtures.

Unit tests run against SQLite so they need no external services. Tests marked
``integration`` require a real PostgreSQL/TimescaleDB instance and are skipped
unless ``TEST_DATABASE_URL`` is exported.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import DataMode, Environment, Settings
from app.models import Base

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    """Isolated settings that never read the developer's real ``.env``."""
    return Settings(
        _env_file=None,  # type: ignore[call-arg]
        env=Environment.TEST,
        debug=True,
        data_mode=DataMode.MOCK,
        database_url="sqlite+aiosqlite:///" + str(tmp_path / "test.db"),
        local_api_token="test-token",
        config_dir=REPO_ROOT / "config",
    )


@pytest.fixture
async def engine(settings: Settings) -> AsyncIterator[object]:
    eng = create_async_engine(settings.sqlalchemy_dsn, future=True)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    await eng.dispose()


@pytest.fixture
async def session(engine: object) -> AsyncIterator[AsyncSession]:
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)  # type: ignore[arg-type]
    async with factory() as s:
        yield s
        await s.rollback()


@pytest.fixture
async def api_client(settings: Settings, engine: object) -> AsyncIterator[AsyncClient]:
    """HTTP client bound to the ASGI app, with the test engine already wired."""
    from app.database import session as session_module
    from app.main import create_app

    session_module._engine = engine  # type: ignore[assignment]
    session_module._session_factory = async_sessionmaker(  # type: ignore[assignment]
        engine,
        class_=AsyncSession,
        expire_on_commit=False,  # type: ignore[arg-type]
    )
    app = create_app(settings)
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test" + settings.api_prefix,
        headers={"X-Local-Token": settings.local_api_token.get_secret_value()},
    ) as client:
        yield client


@pytest.fixture
def integration_dsn() -> Iterator[str]:
    dsn = os.environ.get("TEST_DATABASE_URL")
    if not dsn:
        pytest.skip("TEST_DATABASE_URL not set; integration tests skipped")
    yield dsn

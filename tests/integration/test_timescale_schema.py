"""Integration tests that need a real PostgreSQL + TimescaleDB instance.

Run with:  TEST_DATABASE_URL=postgresql+asyncpg://... pytest -m integration
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.enums import AssetClass, MarketType, Timeframe, ValidationStatus
from app.database.repositories.market import OHLCVRepository
from app.database.timescale import HYPERTABLES
from app.models import Asset, Exchange

pytestmark = pytest.mark.integration

TS = datetime(2024, 1, 1, tzinfo=UTC)


@pytest.fixture
async def pg_session(integration_dsn: str):  # type: ignore[no-untyped-def]
    engine = create_async_engine(integration_dsn)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session
        await session.rollback()
    await engine.dispose()


async def test_timescaledb_extension_is_installed(pg_session: AsyncSession) -> None:
    result = await pg_session.execute(
        text("SELECT extversion FROM pg_extension WHERE extname = 'timescaledb'")
    )
    assert result.first() is not None


async def test_every_declared_hypertable_is_registered(pg_session: AsyncSession) -> None:
    result = await pg_session.execute(
        text("SELECT hypertable_name FROM timescaledb_information.hypertables")
    )
    found = {row[0] for row in result}
    expected = {spec.table for spec in HYPERTABLES}
    assert expected <= found, f"missing hypertables: {sorted(expected - found)}"


async def test_compression_policies_are_applied(pg_session: AsyncSession) -> None:
    result = await pg_session.execute(
        text(
            "SELECT hypertable_name FROM timescaledb_information.jobs "
            "WHERE proc_name = 'policy_compression'"
        )
    )
    compressed = {row[0] for row in result}
    expected = {s.table for s in HYPERTABLES if s.compress_after is not None}
    assert expected <= compressed, f"missing compression: {sorted(expected - compressed)}"


async def test_retention_policy_exists_for_high_volume_tables(pg_session: AsyncSession) -> None:
    result = await pg_session.execute(
        text(
            "SELECT hypertable_name FROM timescaledb_information.jobs "
            "WHERE proc_name = 'policy_retention'"
        )
    )
    retained = {row[0] for row in result}
    assert {"trades", "order_book_snapshots"} <= retained


async def test_predictions_have_no_retention_policy(pg_session: AsyncSession) -> None:
    """The prediction audit trail must never be auto-deleted (§15)."""
    result = await pg_session.execute(
        text(
            "SELECT 1 FROM timescaledb_information.jobs "
            "WHERE proc_name = 'policy_retention' AND hypertable_name = 'predictions'"
        )
    )
    assert result.first() is None


class TestOHLCVUpsert:
    async def _asset(self, session: AsyncSession) -> Asset:
        exchange = Exchange(code="TEST_EX", name="Test", market_type=MarketType.CRYPTO)
        session.add(exchange)
        await session.flush()
        asset = Asset(
            exchange_id=exchange.id, symbol="TESTUSDT", asset_class=AssetClass.SPOT_CRYPTO
        )
        session.add(asset)
        await session.flush()
        return asset

    def _row(self, asset_id: int, close: str) -> dict[str, object]:
        return {
            "asset_id": asset_id,
            "timeframe": Timeframe.H1,
            "ts": TS,
            "source_id": 1,
            "open": Decimal("1"),
            "high": Decimal("2"),
            "low": Decimal("0.5"),
            "close": Decimal(close),
            "volume": Decimal("10"),
            "ingested_at": TS,
            "quality_score": 100,
            "validation_status": ValidationStatus.VALID,
        }

    async def test_reingesting_the_same_candle_updates_instead_of_duplicating(
        self, pg_session: AsyncSession
    ) -> None:
        """Collector restarts must be safe (docs/05 §5.4)."""
        asset = await self._asset(pg_session)
        repo = OHLCVRepository(pg_session)

        await repo.upsert_many([self._row(asset.id, "100")])
        await repo.upsert_many([self._row(asset.id, "111")])
        await pg_session.flush()

        rows = await repo.get_range(asset.id, Timeframe.H1)
        assert len(rows) == 1
        assert rows[0].close == Decimal("111")

    async def test_bulk_upsert_inserts_every_candle(self, pg_session: AsyncSession) -> None:
        from datetime import timedelta

        asset = await self._asset(pg_session)
        repo = OHLCVRepository(pg_session)
        rows = []
        for hour in range(24):
            row = self._row(asset.id, str(hour))
            row["ts"] = TS + timedelta(hours=hour)
            rows.append(row)
        await repo.upsert_many(rows)
        await pg_session.flush()
        assert len(await repo.get_range(asset.id, Timeframe.H1, limit=100)) == 24

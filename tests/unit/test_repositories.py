"""Repository behaviour against an in-process SQLite database."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import AssetClass, DataSourceKind, MarketType, Timeframe
from app.database.repositories.market import OHLCVRepository
from app.database.repositories.reference import (
    AssetRepository,
    DataSourceRepository,
    ExchangeRepository,
)
from app.models import OHLCV, Asset, DataSource, Exchange

TS = datetime(2024, 1, 1, tzinfo=UTC)


async def _make_exchange(session: AsyncSession) -> Exchange:
    exchange = Exchange(code="BINANCE", name="Binance", market_type=MarketType.CRYPTO)
    session.add(exchange)
    await session.flush()
    return exchange


async def _make_asset(session: AsyncSession, symbol: str = "BTCUSDT") -> Asset:
    exchange = await _make_exchange(session)
    asset = Asset(
        exchange_id=exchange.id,
        symbol=symbol,
        asset_class=AssetClass.SPOT_CRYPTO,
    )
    session.add(asset)
    await session.flush()
    return asset


class TestReferenceRepositories:
    async def test_exchange_lookup_by_code(self, session: AsyncSession) -> None:
        await _make_exchange(session)
        found = await ExchangeRepository(session).get_by_code("BINANCE")
        assert found is not None and found.market_type is MarketType.CRYPTO

    async def test_missing_exchange_returns_none(self, session: AsyncSession) -> None:
        assert await ExchangeRepository(session).get_by_code("NOPE") is None

    async def test_asset_lookup_by_symbol(self, session: AsyncSession) -> None:
        asset = await _make_asset(session)
        found = await AssetRepository(session).get_by_symbol(asset.exchange_id, "BTCUSDT")
        assert found is not None and found.id == asset.id

    async def test_tracked_assets_exclude_untracked(self, session: AsyncSession) -> None:
        asset = await _make_asset(session)
        asset.is_tracked = False
        await session.flush()
        assert await AssetRepository(session).list_tracked() == []

    async def test_data_sources_are_ordered_by_priority(self, session: AsyncSession) -> None:
        session.add_all(
            [
                DataSource(code="B", name="b", kind=DataSourceKind.MARKET, priority=50),
                DataSource(code="A", name="a", kind=DataSourceKind.MARKET, priority=10),
                DataSource(
                    code="OFF", name="off", kind=DataSourceKind.MARKET, priority=1, is_enabled=False
                ),
            ]
        )
        await session.flush()
        codes = [s.code for s in await DataSourceRepository(session).list_enabled()]
        assert codes == ["A", "B"]


class TestOHLCVRepository:
    async def _insert(self, session: AsyncSession, asset_id: int, ts: datetime, close: str) -> None:
        session.add(
            OHLCV(
                asset_id=asset_id,
                timeframe=Timeframe.H1,
                ts=ts,
                source_id=1,
                open=Decimal("1"),
                high=Decimal("2"),
                low=Decimal("0.5"),
                close=Decimal(close),
                volume=Decimal("100"),
                ingested_at=TS,
            )
        )
        await session.flush()

    async def test_get_latest_returns_the_newest_candle(self, session: AsyncSession) -> None:
        asset = await _make_asset(session)
        await self._insert(session, asset.id, datetime(2024, 1, 1, 1, tzinfo=UTC), "10")
        await self._insert(session, asset.id, datetime(2024, 1, 1, 5, tzinfo=UTC), "50")
        latest = await OHLCVRepository(session).get_latest(asset.id, Timeframe.H1)
        assert latest is not None and latest.close == Decimal("50")

    async def test_get_range_is_half_open(self, session: AsyncSession) -> None:
        asset = await _make_asset(session)
        for hour in range(5):
            await self._insert(session, asset.id, datetime(2024, 1, 1, hour, tzinfo=UTC), str(hour))
        rows = await OHLCVRepository(session).get_range(
            asset.id,
            Timeframe.H1,
            start=datetime(2024, 1, 1, 1, tzinfo=UTC),
            end=datetime(2024, 1, 1, 3, tzinfo=UTC),
        )
        assert [int(r.close) for r in rows] == [1, 2]

    async def test_range_is_ordered_ascending_by_default(self, session: AsyncSession) -> None:
        asset = await _make_asset(session)
        for hour in (3, 1, 2):
            await self._insert(session, asset.id, datetime(2024, 1, 1, hour, tzinfo=UTC), str(hour))
        rows = await OHLCVRepository(session).get_range(asset.id, Timeframe.H1)
        assert [r.ts.hour for r in rows] == [1, 2, 3]

    async def test_precision_is_preserved(self, session: AsyncSession) -> None:
        """Decimal round-trips without float error — the reason for NUMERIC."""
        asset = await _make_asset(session)
        session.add(
            OHLCV(
                asset_id=asset.id,
                timeframe=Timeframe.H1,
                ts=TS,
                source_id=1,
                open=Decimal("0.000000012345"),
                high=Decimal("0.000000012345"),
                low=Decimal("0.000000012345"),
                close=Decimal("0.000000012345"),
                volume=Decimal("1"),
                ingested_at=TS,
            )
        )
        await session.flush()
        session.expunge_all()
        row = await OHLCVRepository(session).get_latest(asset.id, Timeframe.H1)
        assert row is not None and row.close == Decimal("0.000000012345")

    async def test_upsert_many_is_a_noop_for_empty_input(self, session: AsyncSession) -> None:
        assert await OHLCVRepository(session).upsert_many([]) == 0

    @pytest.mark.integration
    async def test_upsert_is_idempotent(self, session: AsyncSession) -> None:
        """ON CONFLICT is PostgreSQL-only; covered by the integration suite."""
        pytest.skip("requires PostgreSQL")

"""Time-series repositories (OHLCV and long-format market metrics)."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.enums import Timeframe
from app.database.repositories.base import BaseRepository
from app.models.market import OHLCV, MarketMetric

#: Columns overwritten when a candle is re-fetched from the same source.
_OHLCV_UPDATABLE = (
    "open",
    "high",
    "low",
    "close",
    "volume",
    "quote_volume",
    "trade_count",
    "close_adj",
    "is_final",
    "ingested_at",
    "quality_score",
    "validation_status",
)


class OHLCVRepository(BaseRepository[OHLCV]):
    model = OHLCV

    async def get_range(
        self,
        asset_id: int,
        timeframe: Timeframe,
        start: datetime | None = None,
        end: datetime | None = None,
        limit: int = 1000,
        ascending: bool = True,
    ) -> Sequence[OHLCV]:
        stmt = select(OHLCV).where(OHLCV.asset_id == asset_id, OHLCV.timeframe == timeframe)
        if start is not None:
            stmt = stmt.where(OHLCV.ts >= start)
        if end is not None:
            stmt = stmt.where(OHLCV.ts < end)
        stmt = stmt.order_by(OHLCV.ts.asc() if ascending else OHLCV.ts.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_latest(self, asset_id: int, timeframe: Timeframe) -> OHLCV | None:
        result = await self.session.execute(
            select(OHLCV)
            .where(OHLCV.asset_id == asset_id, OHLCV.timeframe == timeframe)
            .order_by(OHLCV.ts.desc())
            .limit(1)
        )
        return result.scalars().first()

    async def latest_timestamp(self, asset_id: int, timeframe: Timeframe) -> datetime | None:
        result = await self.session.execute(
            select(OHLCV.ts)
            .where(OHLCV.asset_id == asset_id, OHLCV.timeframe == timeframe)
            .order_by(OHLCV.ts.desc())
            .limit(1)
        )
        return result.scalars().first()

    async def upsert_many(self, rows: Sequence[dict[str, Any]]) -> int:
        """Idempotent bulk insert on ``(asset_id, timeframe, ts, source_id)``.

        Re-running a collector must never duplicate or corrupt history
        (docs/05-data-flow.md §5.4).
        """
        if not rows:
            return 0
        stmt = pg_insert(OHLCV).values(list(rows))
        stmt = stmt.on_conflict_do_update(
            index_elements=[OHLCV.asset_id, OHLCV.timeframe, OHLCV.ts, OHLCV.source_id],
            set_={col: stmt.excluded[col] for col in _OHLCV_UPDATABLE},
        )
        result = await self.session.execute(stmt)
        return int(getattr(result, "rowcount", 0) or 0)


class MarketMetricRepository(BaseRepository[MarketMetric]):
    model = MarketMetric

    async def latest(
        self, metric_code: str, asset_id: int | None = None, scope_ref: str = ""
    ) -> MarketMetric | None:
        stmt = (
            select(MarketMetric)
            .where(MarketMetric.metric_code == metric_code, MarketMetric.scope_ref == scope_ref)
            .order_by(MarketMetric.ts.desc())
            .limit(1)
        )
        if asset_id is not None:
            stmt = stmt.where(MarketMetric.asset_id == asset_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def upsert_many(self, rows: Sequence[dict[str, Any]]) -> int:
        if not rows:
            return 0
        stmt = pg_insert(MarketMetric).values(list(rows))
        stmt = stmt.on_conflict_do_update(
            index_elements=[
                MarketMetric.metric_code,
                MarketMetric.scope_ref,
                MarketMetric.ts,
                MarketMetric.source_id,
            ],
            set_={
                "value": stmt.excluded.value,
                "meta": stmt.excluded.meta,
                "ingested_at": stmt.excluded.ingested_at,
                "quality_score": stmt.excluded.quality_score,
            },
        )
        result = await self.session.execute(stmt)
        return int(getattr(result, "rowcount", 0) or 0)

"""Raw market time-series. These tables become TimescaleDB hypertables."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    ForeignKey,
    Index,
    Integer,
    PrimaryKeyConstraint,
    SmallInteger,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import OrderSide, Timeframe, ValidationStatus
from app.models.base import (
    MONEY,
    RATIO,
    Base,
    BigIntPK,
    JSONColumn,
    TZDateTime,
    pg_enum,
)


class OHLCV(Base):
    """Candles. Composite PK makes ingestion idempotent (docs/05 §5.4)."""

    __tablename__ = "ohlcv"
    __table_args__ = (
        PrimaryKeyConstraint("asset_id", "timeframe", "ts", "source_id", name="pk_ohlcv"),
        Index("ix_ohlcv_asset_id_timeframe_ts", "asset_id", "timeframe", "ts"),
        Index("ix_ohlcv_ts", "ts"),
    )

    asset_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    timeframe: Mapped[Timeframe] = mapped_column(pg_enum(Timeframe, "timeframe"), nullable=False)
    #: Candle **open** time, UTC.
    ts: Mapped[datetime] = mapped_column(TZDateTime, nullable=False)
    source_id: Mapped[int] = mapped_column(SmallInteger, nullable=False)

    open: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    high: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    low: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    close: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    volume: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    quote_volume: Mapped[Decimal | None] = mapped_column(MONEY)
    trade_count: Mapped[int | None] = mapped_column(Integer)
    #: Corporate-action adjusted close (equities). NULL for crypto.
    close_adj: Mapped[Decimal | None] = mapped_column(MONEY)

    is_final: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    ingested_at: Mapped[datetime] = mapped_column(TZDateTime, nullable=False)
    quality_score: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=100)
    validation_status: Mapped[ValidationStatus] = mapped_column(
        pg_enum(ValidationStatus, "validation_status"),
        nullable=False,
        default=ValidationStatus.VALID,
    )


class Trade(Base):
    """Individual trades — high volume, short retention."""

    __tablename__ = "trades"
    __table_args__ = (
        PrimaryKeyConstraint("asset_id", "ts", "trade_id", "source_id", name="pk_trades"),
        Index("ix_trades_asset_id_ts", "asset_id", "ts"),
    )

    asset_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    ts: Mapped[datetime] = mapped_column(TZDateTime, nullable=False)
    trade_id: Mapped[str] = mapped_column(String(64), nullable=False)
    source_id: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    price: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    qty: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    side: Mapped[OrderSide | None] = mapped_column(pg_enum(OrderSide, "order_side"))


class OrderBookSnapshot(Base):
    """Fixed-interval top-N snapshots (not every book update)."""

    __tablename__ = "order_book_snapshots"
    __table_args__ = (
        PrimaryKeyConstraint("asset_id", "ts", "source_id", name="pk_order_book_snapshots"),
        Index("ix_order_book_snapshots_asset_id_ts", "asset_id", "ts"),
    )

    asset_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    ts: Mapped[datetime] = mapped_column(TZDateTime, nullable=False)
    source_id: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    bids: Mapped[dict[str, Any]] = mapped_column(JSONColumn, nullable=False)
    asks: Mapped[dict[str, Any]] = mapped_column(JSONColumn, nullable=False)
    depth_levels: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    #: (bid_vol - ask_vol) / (bid_vol + ask_vol)
    imbalance: Mapped[Decimal | None] = mapped_column(RATIO)
    spread: Mapped[Decimal | None] = mapped_column(MONEY)


class MarketMetric(Base):
    """Long-format store for every non-OHLCV metric (docs/03 §Group B).

    Using ``metric_code`` instead of one column per metric means new metrics
    (funding rate, BTC dominance, retail buy power, ...) need no migration.
    """

    __tablename__ = "market_metrics"
    __table_args__ = (
        PrimaryKeyConstraint(
            "metric_code", "scope_ref", "ts", "source_id", name="pk_market_metrics"
        ),
        Index("ix_market_metrics_asset_id_metric_code_ts", "asset_id", "metric_code", "ts"),
        Index("ix_market_metrics_ts", "ts"),
    )

    #: NULL for market-wide metrics such as ``btc_dominance``.
    asset_id: Mapped[int | None] = mapped_column(BigInteger)
    #: Free-form scope key ("" for market-wide) — part of the PK so it is never NULL.
    scope_ref: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    metric_code: Mapped[str] = mapped_column(String(64), nullable=False)
    ts: Mapped[datetime] = mapped_column(TZDateTime, nullable=False)
    source_id: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    value: Mapped[Decimal | None] = mapped_column(MONEY)
    meta: Mapped[dict[str, Any] | None] = mapped_column(JSONColumn)
    ingested_at: Mapped[datetime] = mapped_column(TZDateTime, nullable=False)
    quality_score: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=100)


class DataQuarantine(Base, BigIntPK):
    """Records rejected by validation. Never silently dropped (docs/05 §5.4)."""

    __tablename__ = "data_quarantine"
    __table_args__ = (Index("ix_data_quarantine_source_id_created_at", "source_id", "created_at"),)

    source_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("data_sources.id"), nullable=False
    )
    table_name: Mapped[str] = mapped_column(String(64), nullable=False)
    asset_id: Mapped[int | None] = mapped_column(BigInteger)
    reason_code: Mapped[str] = mapped_column(String(64), nullable=False)
    reason_detail: Mapped[str | None] = mapped_column(Text)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONColumn, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TZDateTime, nullable=False)

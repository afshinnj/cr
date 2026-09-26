"""Reference data: exchanges, sectors, assets, aliases, data sources."""

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
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import (
    AssetClass,
    AssetStatus,
    CorporateActionType,
    DataSourceKind,
    MarketType,
    SourceStatus,
)
from app.models.base import (
    MONEY,
    RATIO,
    SMALLINT_PK,
    Base,
    BigIntPK,
    JSONColumn,
    TimestampMixin,
    TZDateTime,
    pg_enum,
)


class Exchange(Base, TimestampMixin):
    __tablename__ = "exchanges"

    id: Mapped[int] = mapped_column(SMALLINT_PK, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    market_type: Mapped[MarketType] = mapped_column(
        pg_enum(MarketType, "market_type"), nullable=False
    )
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="UTC")
    #: Trading hours, weekdays and holidays — drives the collector calendar.
    trading_calendar: Mapped[dict[str, Any] | None] = mapped_column(JSONColumn)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    assets: Mapped[list[Asset]] = relationship(back_populates="exchange")


class Sector(Base, TimestampMixin):
    """Industry classification, primarily for the Tehran Stock Exchange."""

    __tablename__ = "sectors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    name_fa: Mapped[str] = mapped_column(String(128), nullable=False)
    name_en: Mapped[str | None] = mapped_column(String(128))
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("sectors.id"))


class Asset(Base, BigIntPK, TimestampMixin):
    __tablename__ = "assets"
    __table_args__ = (
        UniqueConstraint("exchange_id", "symbol", name="uq_assets_exchange_id_symbol"),
        Index("ix_assets_status_class", "status", "asset_class"),
    )

    exchange_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("exchanges.id"), nullable=False, index=True
    )
    symbol: Mapped[str] = mapped_column(String(64), nullable=False)
    name_fa: Mapped[str | None] = mapped_column(String(256))
    name_en: Mapped[str | None] = mapped_column(String(256))
    asset_class: Mapped[AssetClass] = mapped_column(
        pg_enum(AssetClass, "asset_class"), nullable=False
    )
    #: Stable identifiers for Iranian equities (symbol names change over time).
    isin: Mapped[str | None] = mapped_column(String(32), index=True)
    tsetmc_ins_code: Mapped[str | None] = mapped_column(String(32), unique=True)
    sector_id: Mapped[int | None] = mapped_column(ForeignKey("sectors.id"), index=True)
    base_currency: Mapped[str | None] = mapped_column(String(16))
    quote_currency: Mapped[str | None] = mapped_column(String(16))
    tick_size: Mapped[Decimal | None] = mapped_column(MONEY)
    lot_size: Mapped[Decimal | None] = mapped_column(MONEY)
    #: Kept populated so historical universes avoid survivorship bias (§16).
    listed_at: Mapped[datetime | None] = mapped_column(TZDateTime)
    delisted_at: Mapped[datetime | None] = mapped_column(TZDateTime)
    status: Mapped[AssetStatus] = mapped_column(
        pg_enum(AssetStatus, "asset_status"), nullable=False, default=AssetStatus.ACTIVE
    )
    is_tracked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    meta: Mapped[dict[str, Any] | None] = mapped_column(JSONColumn)

    exchange: Mapped[Exchange] = relationship(back_populates="assets")
    aliases: Mapped[list[SymbolAlias]] = relationship(
        back_populates="asset", cascade="all, delete-orphan"
    )


class SymbolAlias(Base, BigIntPK):
    """Maps a provider-specific identifier to a canonical asset (docs/05 §5.6)."""

    __tablename__ = "symbol_aliases"
    __table_args__ = (
        UniqueConstraint(
            "source_id", "external_symbol", name="uq_symbol_aliases_source_id_external_symbol"
        ),
    )

    asset_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("assets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("data_sources.id"), nullable=False
    )
    external_symbol: Mapped[str] = mapped_column(String(128), nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(128))

    asset: Mapped[Asset] = relationship(back_populates="aliases")


class DataSource(Base, TimestampMixin):
    __tablename__ = "data_sources"

    id: Mapped[int] = mapped_column(SMALLINT_PK, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(48), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    kind: Mapped[DataSourceKind] = mapped_column(
        pg_enum(DataSourceKind, "data_source_kind"), nullable=False
    )
    base_url: Mapped[str | None] = mapped_column(Text)
    auth_type: Mapped[str | None] = mapped_column(String(32))
    #: Token-bucket configuration consumed by providers/rate_limit.py.
    rate_limit: Mapped[dict[str, Any] | None] = mapped_column(JSONColumn)
    #: Lower value = preferred source when several can serve a capability.
    priority: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=100)
    #: 0..1 — feeds the news impact score (docs/07 §7.6).
    credibility: Mapped[Decimal | None] = mapped_column(RATIO)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    notes: Mapped[str | None] = mapped_column(Text)


class DataSourceHealth(Base, BigIntPK):
    """Backs the red 'source unavailable' banner in the UI (§29)."""

    __tablename__ = "data_source_health"
    __table_args__ = (
        Index("ix_data_source_health_source_id_checked_at", "source_id", "checked_at"),
    )

    source_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("data_sources.id"), nullable=False
    )
    checked_at: Mapped[datetime] = mapped_column(TZDateTime, nullable=False)
    status: Mapped[SourceStatus] = mapped_column(
        pg_enum(SourceStatus, "source_status"), nullable=False
    )
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    error_code: Mapped[str | None] = mapped_column(String(64))
    error_message: Mapped[str | None] = mapped_column(Text)
    consecutive_failures: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class CorporateAction(Base, BigIntPK, TimestampMixin):
    """Splits / capital increases / dividends — required for adjusted prices (ADR-012)."""

    __tablename__ = "corporate_actions"
    __table_args__ = (
        UniqueConstraint(
            "asset_id", "type", "ex_date", name="uq_corporate_actions_asset_id_type_ex_date"
        ),
        Index("ix_corporate_actions_asset_id_ex_date", "asset_id", "ex_date"),
    )

    asset_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("assets.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[CorporateActionType] = mapped_column(
        pg_enum(CorporateActionType, "corporate_action_type"), nullable=False
    )
    ex_date: Mapped[datetime] = mapped_column(TZDateTime, nullable=False)
    #: Multiplicative adjustment factor applied to prices before ``ex_date``.
    ratio: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    details: Mapped[dict[str, Any] | None] = mapped_column(JSONColumn)
    source_id: Mapped[int | None] = mapped_column(SmallInteger, ForeignKey("data_sources.id"))

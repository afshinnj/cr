"""Repositories for reference data."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.core.enums import AssetStatus, MarketType
from app.database.repositories.base import BaseRepository
from app.models.reference import Asset, DataSource, Exchange, Sector, SymbolAlias


class ExchangeRepository(BaseRepository[Exchange]):
    model = Exchange

    async def get_by_code(self, code: str) -> Exchange | None:
        result = await self.session.execute(select(Exchange).where(Exchange.code == code))
        return result.scalar_one_or_none()


class SectorRepository(BaseRepository[Sector]):
    model = Sector

    async def get_by_code(self, code: str) -> Sector | None:
        result = await self.session.execute(select(Sector).where(Sector.code == code))
        return result.scalar_one_or_none()


class DataSourceRepository(BaseRepository[DataSource]):
    model = DataSource

    async def get_by_code(self, code: str) -> DataSource | None:
        result = await self.session.execute(select(DataSource).where(DataSource.code == code))
        return result.scalar_one_or_none()

    async def list_enabled(self) -> Sequence[DataSource]:
        result = await self.session.execute(
            select(DataSource).where(DataSource.is_enabled.is_(True)).order_by(DataSource.priority)
        )
        return result.scalars().all()


class AssetRepository(BaseRepository[Asset]):
    model = Asset

    async def get_by_symbol(self, exchange_id: int, symbol: str) -> Asset | None:
        result = await self.session.execute(
            select(Asset).where(Asset.exchange_id == exchange_id, Asset.symbol == symbol)
        )
        return result.scalar_one_or_none()

    async def get_by_ins_code(self, ins_code: str) -> Asset | None:
        """Tehran Stock Exchange lookup by the stable instrument code."""
        result = await self.session.execute(select(Asset).where(Asset.tsetmc_ins_code == ins_code))
        return result.scalar_one_or_none()

    async def list_tracked(
        self, market_type: MarketType | None = None, limit: int = 1000
    ) -> Sequence[Asset]:
        stmt = (
            select(Asset)
            .join(Exchange, Asset.exchange_id == Exchange.id)
            .where(Asset.is_tracked.is_(True), Asset.status == AssetStatus.ACTIVE)
            .order_by(Asset.symbol)
            .limit(limit)
        )
        if market_type is not None:
            stmt = stmt.where(Exchange.market_type == market_type)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def upsert(self, asset: Asset) -> None:
        """Insert-or-update keyed on the natural key ``(exchange_id, symbol)``.

        PostgreSQL-only: uses ``ON CONFLICT`` so collectors stay idempotent.
        """
        values = {
            column.name: getattr(asset, column.name)
            for column in Asset.__table__.columns
            if column.name not in {"id", "created_at", "updated_at"}
            and getattr(asset, column.name) is not None
        }
        stmt = pg_insert(Asset).values(**values)
        update_cols = {
            key: stmt.excluded[key] for key in values if key not in {"exchange_id", "symbol"}
        }
        stmt = stmt.on_conflict_do_update(
            index_elements=[Asset.exchange_id, Asset.symbol], set_=update_cols
        )
        await self.session.execute(stmt)


class SymbolAliasRepository(BaseRepository[SymbolAlias]):
    model = SymbolAlias

    async def resolve(self, source_id: int, external_symbol: str) -> int | None:
        """Map a provider symbol to a canonical ``asset_id`` (docs/05 §5.6)."""
        result = await self.session.execute(
            select(SymbolAlias.asset_id).where(
                SymbolAlias.source_id == source_id,
                SymbolAlias.external_symbol == external_symbol,
            )
        )
        return result.scalar_one_or_none()

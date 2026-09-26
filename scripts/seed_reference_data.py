#!/usr/bin/env python
"""Seed reference data: exchanges, data sources, sectors, scoring profiles, assets.

This script is idempotent — running it twice leaves the database unchanged.

It seeds only *reference* data that we control. It never invents market data:
Iranian instrument codes are left NULL until Milestone 3 resolves them from the
live TSETMC service (requirement §29).

Usage:
    python scripts/seed_reference_data.py [--profile small]
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "backend"))

from sqlalchemy import select  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.core.config_files import ConfigFiles  # noqa: E402
from app.core.enums import AssetClass, AssetStatus, DataSourceKind, MarketType  # noqa: E402
from app.core.logging import configure_logging, get_logger  # noqa: E402
from app.database.session import init_engine, session_scope  # noqa: E402
from app.models import Asset, DataSource, Exchange, ScoringProfile, Sector  # noqa: E402

logger = get_logger("seed")

EXCHANGES: list[dict[str, Any]] = [
    {
        "code": "BINANCE",
        "name": "Binance",
        "market_type": MarketType.CRYPTO,
        "timezone": "UTC",
        "trading_calendar": {"always_open": True},
    },
    {
        "code": "TSE",
        "name": "Tehran Stock Exchange",
        "market_type": MarketType.IRAN_STOCK,
        "timezone": "Asia/Tehran",
        "trading_calendar": {
            "session": {"open": "09:00", "close": "12:30"},
            "weekdays": [5, 6, 0, 1, 2],
        },
    },
    {
        "code": "IFB",
        "name": "Iran Fara Bourse",
        "market_type": MarketType.IRAN_STOCK,
        "timezone": "Asia/Tehran",
        "trading_calendar": {
            "session": {"open": "09:00", "close": "12:30"},
            "weekdays": [5, 6, 0, 1, 2],
        },
    },
]


async def seed_exchanges(session: Any) -> dict[str, int]:
    ids: dict[str, int] = {}
    for spec in EXCHANGES:
        existing = (
            await session.execute(select(Exchange).where(Exchange.code == spec["code"]))
        ).scalar_one_or_none()
        if existing is None:
            existing = Exchange(**spec)
            session.add(existing)
            await session.flush()
            logger.info("exchange_created", code=spec["code"])
        ids[spec["code"]] = existing.id
    return ids


async def seed_data_sources(session: Any, config: ConfigFiles) -> dict[str, int]:
    ids: dict[str, int] = {}
    for spec in config.sources:
        existing = (
            await session.execute(select(DataSource).where(DataSource.code == spec["code"]))
        ).scalar_one_or_none()
        if existing is None:
            existing = DataSource(
                code=spec["code"],
                name=spec["name"],
                kind=DataSourceKind(spec["kind"]),
                base_url=spec.get("base_url"),
                auth_type=spec.get("auth_type"),
                rate_limit=spec.get("rate_limit"),
                priority=spec.get("priority", 100),
                credibility=spec.get("credibility"),
                is_enabled=spec.get("is_enabled", True),
                notes=spec.get("notes"),
            )
            session.add(existing)
            await session.flush()
            logger.info("data_source_created", code=spec["code"])
        ids[spec["code"]] = existing.id
    return ids


async def seed_scoring_profiles(session: Any, config: ConfigFiles) -> None:
    for spec in config.scoring_profiles:
        existing = (
            await session.execute(select(ScoringProfile).where(ScoringProfile.name == spec["name"]))
        ).scalar_one_or_none()
        if existing is not None:
            continue
        session.add(
            ScoringProfile(
                name=spec["name"],
                market_type=spec.get("market_type"),
                is_active=spec.get("is_active", False),
                weights=spec["weights"],
                thresholds=spec["thresholds"],
                notes=spec.get("notes"),
            )
        )
        logger.info("scoring_profile_created", name=spec["name"])


async def seed_sectors(session: Any, sector_names: set[str]) -> dict[str, int]:
    ids: dict[str, int] = {}
    for index, name in enumerate(sorted(sector_names), start=1):
        code = f"TSE-{index:03d}"
        existing = (
            await session.execute(select(Sector).where(Sector.name_fa == name))
        ).scalar_one_or_none()
        if existing is None:
            existing = Sector(code=code, name_fa=name)
            session.add(existing)
            await session.flush()
            logger.info("sector_created", name=name)
        ids[name] = existing.id
    return ids


async def seed_assets(
    session: Any, config: ConfigFiles, profile: str, exchange_ids: dict[str, int]
) -> int:
    universe = config.universe(profile)
    created = 0

    crypto = universe.get("crypto", {})
    symbols: list[str] = crypto.get("symbols", [])
    exchange_id = exchange_ids[crypto.get("exchange", "BINANCE")]
    for symbol in symbols:
        existing = (
            await session.execute(
                select(Asset).where(Asset.exchange_id == exchange_id, Asset.symbol == symbol)
            )
        ).scalar_one_or_none()
        if existing is not None:
            continue
        quote = crypto.get("quote", "USDT")
        session.add(
            Asset(
                exchange_id=exchange_id,
                symbol=symbol,
                name_en=symbol,
                asset_class=AssetClass.SPOT_CRYPTO,
                base_currency=symbol.removesuffix(quote),
                quote_currency=quote,
                status=AssetStatus.ACTIVE,
                is_tracked=True,
            )
        )
        created += 1

    iran = universe.get("iran_stock", {})
    entries: list[dict[str, Any]] = iran.get("symbols", [])
    if entries:
        sector_ids = await seed_sectors(session, {e["sector"] for e in entries if e.get("sector")})
        exchange_id = exchange_ids[iran.get("exchange", "TSE")]
        for entry in entries:
            existing = (
                await session.execute(
                    select(Asset).where(
                        Asset.exchange_id == exchange_id, Asset.symbol == entry["symbol"]
                    )
                )
            ).scalar_one_or_none()
            if existing is not None:
                continue
            session.add(
                Asset(
                    exchange_id=exchange_id,
                    symbol=entry["symbol"],
                    name_fa=entry.get("name_fa"),
                    asset_class=AssetClass.STOCK,
                    sector_id=sector_ids.get(entry.get("sector", "")),
                    quote_currency="IRR",
                    status=AssetStatus.ACTIVE,
                    # ins_code is resolved from the live service in Milestone 3;
                    # we do not guess identifiers (requirement §29).
                    tsetmc_ins_code=None,
                    is_tracked=True,
                )
            )
            created += 1
    return created


async def main(profile: str) -> int:
    settings = get_settings()
    configure_logging(settings)
    init_engine(settings)
    config = ConfigFiles(settings.config_dir)

    async with session_scope() as session:
        exchange_ids = await seed_exchanges(session)
        await seed_data_sources(session, config)
        await seed_scoring_profiles(session, config)
        created = await seed_assets(session, config, profile, exchange_ids)

    logger.info("seed_completed", profile=profile, assets_created=created)
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", default=None, help="universe profile (default: from .env)")
    args = parser.parse_args()
    selected = args.profile or get_settings().universe_profile.value
    raise SystemExit(asyncio.run(main(selected)))

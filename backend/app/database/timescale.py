"""TimescaleDB helpers.

Hypertables, compression and retention cannot be expressed with plain DDL, so
they are declared here as data and applied by Alembic migrations. Keeping the
declaration in one place means `docs/03-database.md` has a single counterpart
in code.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class HypertableSpec:
    table: str
    time_column: str
    chunk_interval: str
    #: Columns used as the compression segment key (usually the entity id).
    compress_segmentby: tuple[str, ...] = ()
    #: Compress chunks older than this interval. ``None`` disables compression.
    compress_after: str | None = None
    #: Drop chunks older than this interval. ``None`` keeps data forever.
    retention: str | None = None
    extra_indexes: tuple[str, ...] = field(default_factory=tuple)


#: Every time-series table in the system (docs/03-database.md §3.3).
HYPERTABLES: tuple[HypertableSpec, ...] = (
    HypertableSpec(
        table="ohlcv",
        time_column="ts",
        chunk_interval="7 days",
        compress_segmentby=("asset_id", "timeframe"),
        compress_after="30 days",
    ),
    HypertableSpec(
        table="trades",
        time_column="ts",
        chunk_interval="1 day",
        compress_segmentby=("asset_id",),
        compress_after="2 days",
        # Tick data is only needed for short-term microstructure metrics.
        retention="7 days",
    ),
    HypertableSpec(
        table="order_book_snapshots",
        time_column="ts",
        chunk_interval="1 day",
        compress_segmentby=("asset_id",),
        compress_after="2 days",
        retention="30 days",
    ),
    HypertableSpec(
        table="market_metrics",
        time_column="ts",
        chunk_interval="7 days",
        compress_segmentby=("metric_code",),
        compress_after="30 days",
    ),
    HypertableSpec(
        table="technical_indicators",
        time_column="ts",
        chunk_interval="7 days",
        compress_segmentby=("asset_id", "timeframe", "indicator_code"),
        compress_after="30 days",
    ),
    HypertableSpec(
        table="feature_snapshots",
        time_column="ts",
        chunk_interval="7 days",
        compress_segmentby=("asset_id", "timeframe"),
        compress_after="30 days",
    ),
    HypertableSpec(
        table="asset_scores",
        time_column="ts",
        chunk_interval="7 days",
        compress_segmentby=("asset_id", "timeframe"),
        compress_after="60 days",
    ),
    HypertableSpec(
        table="risk_metrics",
        time_column="ts",
        chunk_interval="7 days",
        compress_segmentby=("asset_id", "timeframe"),
        compress_after="60 days",
    ),
    HypertableSpec(
        table="predictions",
        time_column="ts",
        chunk_interval="30 days",
        compress_segmentby=("asset_id",),
        # Predictions are the audit trail of the system: never dropped.
    ),
    HypertableSpec(
        table="paper_equity_curve",
        time_column="ts",
        chunk_interval="30 days",
    ),
)


def create_hypertable_sql(spec: HypertableSpec) -> str:
    return (
        f"SELECT create_hypertable('{spec.table}', '{spec.time_column}', "
        f"chunk_time_interval => INTERVAL '{spec.chunk_interval}', "
        f"if_not_exists => TRUE, migrate_data => TRUE);"
    )


def enable_compression_sql(spec: HypertableSpec) -> list[str]:
    if spec.compress_after is None:
        return []
    statements = []
    segmentby = ", ".join(spec.compress_segmentby)
    opts = ["timescaledb.compress = true"]
    if segmentby:
        opts.append(f"timescaledb.compress_segmentby = '{segmentby}'")
    opts.append(f"timescaledb.compress_orderby = '{spec.time_column} DESC'")
    statements.append(f"ALTER TABLE {spec.table} SET ({', '.join(opts)});")
    statements.append(
        f"SELECT add_compression_policy('{spec.table}', INTERVAL '{spec.compress_after}', "
        f"if_not_exists => TRUE);"
    )
    return statements


def add_retention_sql(spec: HypertableSpec) -> list[str]:
    if spec.retention is None:
        return []
    return [
        f"SELECT add_retention_policy('{spec.table}', INTERVAL '{spec.retention}', "
        f"if_not_exists => TRUE);"
    ]


def all_statements() -> list[str]:
    """Every Timescale statement, in application order."""
    statements: list[str] = []
    for spec in HYPERTABLES:
        statements.append(create_hypertable_sql(spec))
        statements.extend(enable_compression_sql(spec))
        statements.extend(add_retention_sql(spec))
    return statements


def teardown_statements() -> list[str]:
    """Policies removed on downgrade (tables themselves are dropped by Alembic)."""
    statements: list[str] = []
    for spec in reversed(HYPERTABLES):
        if spec.retention is not None:
            statements.append(f"SELECT remove_retention_policy('{spec.table}', if_exists => TRUE);")
        if spec.compress_after is not None:
            statements.append(
                f"SELECT remove_compression_policy('{spec.table}', if_exists => TRUE);"
            )
    return statements

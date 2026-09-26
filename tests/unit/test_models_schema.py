"""Schema-level invariants from docs/03-database.md §3.1."""

from __future__ import annotations

import pytest
from sqlalchemy import DateTime, Float, Numeric

from app.models import Base

#: Tables from docs/03-database.md that must exist.
REQUIRED_TABLES = {
    "assets",
    "exchanges",
    "ohlcv",
    "trades",
    "order_book_snapshots",
    "market_metrics",
    "technical_indicators",
    "news_articles",
    "news_events",
    "sentiments",
    "market_regimes",
    "predictions",
    "signals",
    "backtests",
    "model_versions",
    "model_metrics",
    "risk_metrics",
    "ai_analysis",
    "system_logs",
    "data_sources",
}

#: Columns that hold money and must never be floating point.
MONEY_COLUMNS = {
    "ohlcv": ["open", "high", "low", "close", "volume"],
    "signals": ["entry", "stop_loss", "take_profit_1"],
    "paper_accounts": ["initial_balance", "current_balance", "equity"],
    "backtest_trades": ["entry_price", "qty"],
}


def test_all_required_tables_exist() -> None:
    missing = REQUIRED_TABLES - set(Base.metadata.tables)
    assert not missing, f"missing tables: {sorted(missing)}"


def test_no_datetime_column_is_naive() -> None:
    naive = [
        f"{table.name}.{column.name}"
        for table in Base.metadata.tables.values()
        for column in table.columns
        if isinstance(column.type, DateTime) and not column.type.timezone
    ]
    assert not naive, f"naive timestamps found: {naive}"


def test_no_float_columns_anywhere() -> None:
    """Float arithmetic on prices silently loses money; NUMERIC is mandatory."""
    floats = [
        f"{table.name}.{column.name}"
        for table in Base.metadata.tables.values()
        for column in table.columns
        if isinstance(column.type, Float)
    ]
    assert not floats, f"float columns found: {floats}"


@pytest.mark.parametrize(("table_name", "columns"), MONEY_COLUMNS.items())
def test_money_columns_use_numeric_38_12(table_name: str, columns: list[str]) -> None:
    table = Base.metadata.tables[table_name]
    for name in columns:
        column_type = table.columns[name].type
        assert isinstance(column_type, Numeric)
        assert (column_type.precision, column_type.scale) == (38, 12), (
            f"{table_name}.{name} is {column_type}"
        )


def test_ohlcv_primary_key_makes_ingestion_idempotent() -> None:
    pk = {c.name for c in Base.metadata.tables["ohlcv"].primary_key.columns}
    assert pk == {"asset_id", "timeframe", "ts", "source_id"}


def test_every_raw_market_table_records_its_source() -> None:
    for name in ("ohlcv", "trades", "order_book_snapshots", "market_metrics"):
        assert "source_id" in Base.metadata.tables[name].columns, f"{name} has no source_id"


def test_assets_track_delisting_for_survivorship_bias() -> None:
    columns = Base.metadata.tables["assets"].columns
    assert "listed_at" in columns
    assert "delisted_at" in columns


def test_assets_keep_a_stable_iranian_identifier() -> None:
    """Symbol names change in Tehran; ins_code does not (docs/05 §5.6)."""
    column = Base.metadata.tables["assets"].columns["tsetmc_ins_code"]
    assert column.unique is True


def test_predictions_store_the_resolution_outcome() -> None:
    """Continuous learning requires comparing predictions with reality (§15)."""
    columns = Base.metadata.tables["predictions"].columns
    for name in ("resolve_at", "resolved_at", "actual_return", "actual_direction", "is_correct"):
        assert name in columns, f"predictions.{name} missing"


def test_asset_scores_keep_the_full_component_breakdown() -> None:
    """Explainability: every final score must be decomposable (§11, §14)."""
    columns = Base.metadata.tables["asset_scores"].columns
    assert "components" in columns
    assert "data_completeness" in columns
    assert "scoring_profile_id" in columns


def test_ai_analysis_records_provider_model_and_prompt_version() -> None:
    """Past AI outputs must be reproducible (docs/06 §6.3)."""
    columns = Base.metadata.tables["ai_analysis"].columns
    for name in ("provider", "model", "prompt_version", "input_features", "status"):
        assert name in columns, f"ai_analysis.{name} missing"


def test_corporate_actions_table_exists_for_price_adjustment() -> None:
    """ADR-012: without this every Iranian indicator and backtest is wrong."""
    assert "corporate_actions" in Base.metadata.tables
    assert "close_adj" in Base.metadata.tables["ohlcv"].columns


def test_no_real_trading_tables_exist() -> None:
    """ADR-014: this version must be structurally incapable of live trading."""
    forbidden = {"live_orders", "broker_accounts", "exchange_credentials", "real_positions"}
    assert not (forbidden & set(Base.metadata.tables))

"""The Timescale declaration must stay consistent with the ORM metadata."""

from __future__ import annotations

import pytest

from app.database.timescale import (
    HYPERTABLES,
    HypertableSpec,
    all_statements,
    create_hypertable_sql,
    teardown_statements,
)
from app.models import Base


def test_every_hypertable_exists_in_the_orm_metadata() -> None:
    tables = set(Base.metadata.tables)
    missing = [spec.table for spec in HYPERTABLES if spec.table not in tables]
    assert not missing, f"hypertables declared for unknown tables: {missing}"


def test_time_column_exists_on_each_table() -> None:
    for spec in HYPERTABLES:
        columns = Base.metadata.tables[spec.table].columns
        assert spec.time_column in columns, f"{spec.table}.{spec.time_column} missing"


def test_time_column_is_timezone_aware() -> None:
    for spec in HYPERTABLES:
        column = Base.metadata.tables[spec.table].columns[spec.time_column]
        assert getattr(column.type, "timezone", False), f"{spec.table}.{spec.time_column} is naive"


def test_primary_key_includes_the_partitioning_column() -> None:
    """TimescaleDB requires the time column in every unique constraint."""
    for spec in HYPERTABLES:
        pk_columns = {c.name for c in Base.metadata.tables[spec.table].primary_key.columns}
        assert spec.time_column in pk_columns, (
            f"{spec.table} primary key {sorted(pk_columns)} must include '{spec.time_column}'"
        )


def test_segmentby_columns_exist() -> None:
    for spec in HYPERTABLES:
        columns = set(Base.metadata.tables[spec.table].columns.keys())
        unknown = set(spec.compress_segmentby) - columns
        assert not unknown, f"{spec.table}: unknown segmentby columns {unknown}"


def test_predictions_are_never_dropped() -> None:
    """Predictions are the audit trail for continuous learning (§15)."""
    spec = next(s for s in HYPERTABLES if s.table == "predictions")
    assert spec.retention is None


def test_high_volume_tables_have_retention() -> None:
    for name in ("trades", "order_book_snapshots"):
        spec = next(s for s in HYPERTABLES if s.table == name)
        assert spec.retention is not None, f"{name} would grow unbounded"


def test_sql_generation_is_wellformed() -> None:
    spec = HypertableSpec(
        table="t", time_column="ts", chunk_interval="7 days", compress_after="30 days"
    )
    sql = create_hypertable_sql(spec)
    assert "create_hypertable('t', 'ts'" in sql
    assert "if_not_exists => TRUE" in sql


def test_all_statements_cover_every_hypertable() -> None:
    statements = all_statements()
    for spec in HYPERTABLES:
        assert any(f"'{spec.table}'" in s for s in statements)


@pytest.mark.parametrize("statement", all_statements() + teardown_statements())
def test_statements_are_terminated(statement: str) -> None:
    assert statement.rstrip().endswith(";")

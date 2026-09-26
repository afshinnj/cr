"""Declarative base, shared column types and mixins.

Conventions (docs/03-database.md §3.1):
  * every timestamp is ``TIMESTAMP WITH TIME ZONE`` and stored in UTC;
  * monetary values use ``NUMERIC(38, 12)`` — never float;
  * enums are stored as native PostgreSQL enums with an explicit name.

Types declare a SQLite variant so the schema can also be materialised in
lightweight tests without a PostgreSQL server.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from sqlalchemy import (
    JSON,
    BigInteger,
    DateTime,
    Integer,
    MetaData,
    Numeric,
    SmallInteger,
    func,
)
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Predictable constraint names make Alembic autogenerate diffs stable.
NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_N_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

#: Price / money. 38 digits with 12 decimals covers crypto satoshis and IRR alike.
MONEY = Numeric(38, 12)
#: Scores are 0..100 with two decimals.
SCORE = Numeric(5, 2)
#: Ratios / probabilities in [-1, 1] or [0, 1].
RATIO = Numeric(10, 6)

#: Portable JSON column (JSONB on PostgreSQL, JSON elsewhere).
JSONColumn = JSONB().with_variant(JSON(), "sqlite")

TZDateTime = DateTime(timezone=True)

#: SQLite only auto-increments INTEGER PRIMARY KEY, so small surrogate keys
#: declare an INTEGER variant for the test backend.
SMALLINT_PK = SmallInteger().with_variant(Integer(), "sqlite")
BIGINT_PK = BigInteger().with_variant(Integer(), "sqlite")


def pg_enum(enum_cls: type[StrEnum], name: str) -> SAEnum:
    """Native PostgreSQL enum built from a :class:`StrEnum`.

    ``values_callable`` makes PostgreSQL store the *value* (e.g. ``"1h"``)
    rather than the Python member name (``"H1"``).
    """
    return SAEnum(
        enum_cls,
        name=name,
        native_enum=True,
        create_constraint=False,
        validate_strings=True,
        values_callable=lambda e: [member.value for member in e],
    )


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)

    type_annotation_map = {  # noqa: RUF012
        datetime: TZDateTime,
        Decimal: MONEY,
        dict[str, Any]: JSONColumn,
        list[str]: JSONColumn,
    }

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        pk = getattr(self, "id", None)
        return f"<{type(self).__name__} id={pk}>"


class TimestampMixin:
    """``created_at`` / ``updated_at`` maintained by the database."""

    created_at: Mapped[datetime] = mapped_column(
        TZDateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        TZDateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )


class BigIntPK:
    """64-bit surrogate primary key."""

    id: Mapped[int] = mapped_column(BIGINT_PK, primary_key=True, autoincrement=True)


class ProvenanceMixin:
    """Source + ingestion metadata required for every raw data point (§4, §29)."""

    source_id: Mapped[int] = mapped_column(nullable=False, index=True)
    ingested_at: Mapped[datetime] = mapped_column(
        TZDateTime, server_default=func.now(), nullable=False
    )
    quality_score: Mapped[int] = mapped_column(nullable=False, default=100)

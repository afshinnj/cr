"""timescale hypertables, compression and retention policies

Revision ID: b1f2c3d4e5a6
Revises: 766f1fa633ff
Create Date: 2026-09-26 07:10:00.000000+00:00

TimescaleDB objects cannot be expressed through SQLAlchemy metadata, so they
are applied here from the declarative specs in ``app.database.timescale``.
The migration is a no-op on non-PostgreSQL backends (SQLite is used by fast
unit tests that do not need chunking).
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op
from sqlalchemy import text

from app.database.timescale import all_statements, teardown_statements

revision: str = "b1f2c3d4e5a6"
down_revision: str | None = "766f1fa633ff"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _is_postgres() -> bool:
    return op.get_bind().dialect.name == "postgresql"


def upgrade() -> None:
    if not _is_postgres():
        return
    bind = op.get_bind()
    bind.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;"))
    for statement in all_statements():
        bind.execute(text(statement))


def downgrade() -> None:
    if not _is_postgres():
        return
    bind = op.get_bind()
    for statement in teardown_statements():
        bind.execute(text(statement))

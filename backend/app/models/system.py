"""Alerts, structured logs, job bookkeeping and local user settings."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import AlertConditionType, AlertScope, RunStatus, Timeframe
from app.models.base import (
    Base,
    BigIntPK,
    JSONColumn,
    TimestampMixin,
    TZDateTime,
    pg_enum,
)


class AlertRule(Base, TimestampMixin):
    __tablename__ = "alert_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    scope: Mapped[AlertScope] = mapped_column(pg_enum(AlertScope, "alert_scope"), nullable=False)
    asset_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("assets.id"))
    condition_type: Mapped[AlertConditionType] = mapped_column(
        pg_enum(AlertConditionType, "alert_condition_type"), nullable=False
    )
    params: Mapped[dict[str, Any]] = mapped_column(JSONColumn, nullable=False)
    timeframe: Mapped[Timeframe | None] = mapped_column(pg_enum(Timeframe, "timeframe"))
    #: Delivery channels; desktop now, telegram/email later without schema change.
    channels: Mapped[dict[str, Any]] = mapped_column(JSONColumn, nullable=False)
    cooldown_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=900)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class AlertEvent(Base, BigIntPK):
    __tablename__ = "alert_events"
    __table_args__ = (Index("ix_alert_events_triggered_at", "triggered_at"),)

    rule_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("alert_rules.id", ondelete="CASCADE"), nullable=False
    )
    asset_id: Mapped[int | None] = mapped_column(BigInteger)
    triggered_at: Mapped[datetime] = mapped_column(TZDateTime, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONColumn, nullable=False)
    delivery_status: Mapped[dict[str, Any] | None] = mapped_column(JSONColumn)
    acknowledged_at: Mapped[datetime | None] = mapped_column(TZDateTime)


class SystemLog(Base, BigIntPK):
    """Persisted structured events (secrets are masked before they get here)."""

    __tablename__ = "system_logs"
    __table_args__ = (
        Index("ix_system_logs_ts_level", "ts", "level"),
        Index("ix_system_logs_event_code", "event_code"),
    )

    ts: Mapped[datetime] = mapped_column(TZDateTime, nullable=False)
    level: Mapped[str] = mapped_column(String(16), nullable=False)
    logger: Mapped[str] = mapped_column(String(64), nullable=False)
    event_code: Mapped[str] = mapped_column(String(64), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[dict[str, Any] | None] = mapped_column(JSONColumn)
    trace_id: Mapped[str | None] = mapped_column(String(64))


class JobRun(Base, BigIntPK):
    """Collector / analysis job bookkeeping — powers ``GET /system/jobs``."""

    __tablename__ = "job_runs"
    __table_args__ = (Index("ix_job_runs_job_name_started_at", "job_name", "started_at"),)

    job_name: Mapped[str] = mapped_column(String(64), nullable=False)
    started_at: Mapped[datetime] = mapped_column(TZDateTime, nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(TZDateTime)
    status: Mapped[RunStatus] = mapped_column(pg_enum(RunStatus, "run_status"), nullable=False)
    items_processed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    items_failed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error: Mapped[str | None] = mapped_column(Text)
    metrics: Mapped[dict[str, Any] | None] = mapped_column(JSONColumn)


class UserSetting(Base, TimestampMixin):
    __tablename__ = "user_settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[dict[str, Any]] = mapped_column(JSONColumn, nullable=False)


class UserDrawing(Base, BigIntPK, TimestampMixin):
    """Chart drawing objects (docs/02 §2.6 — custom overlay layer)."""

    __tablename__ = "user_drawings"
    __table_args__ = (Index("ix_user_drawings_asset_id_timeframe", "asset_id", "timeframe"),)

    asset_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("assets.id"), nullable=False)
    timeframe: Mapped[Timeframe] = mapped_column(pg_enum(Timeframe, "timeframe"), nullable=False)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    geometry: Mapped[dict[str, Any]] = mapped_column(JSONColumn, nullable=False)
    style: Mapped[dict[str, Any] | None] = mapped_column(JSONColumn)

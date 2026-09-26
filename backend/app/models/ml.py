"""Model registry, metrics and predictions (continuous learning, §15)."""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    ForeignKey,
    Index,
    Integer,
    Interval,
    PrimaryKeyConstraint,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import (
    EvaluationStage,
    ModelStatus,
    ModelTask,
    PredictedDirection,
    Timeframe,
)
from app.models.base import (
    RATIO,
    Base,
    BigIntPK,
    JSONColumn,
    TimestampMixin,
    TZDateTime,
    pg_enum,
)


class ModelVersion(Base, TimestampMixin):
    __tablename__ = "model_versions"
    __table_args__ = (UniqueConstraint("name", "version", name="uq_model_versions_name_version"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    version: Mapped[str] = mapped_column(String(32), nullable=False)
    task: Mapped[ModelTask] = mapped_column(pg_enum(ModelTask, "model_task"), nullable=False)
    algo: Mapped[str] = mapped_column(String(32), nullable=False)
    trained_at: Mapped[datetime | None] = mapped_column(TZDateTime)
    train_start: Mapped[datetime | None] = mapped_column(TZDateTime)
    train_end: Mapped[datetime | None] = mapped_column(TZDateTime)
    valid_start: Mapped[datetime | None] = mapped_column(TZDateTime)
    valid_end: Mapped[datetime | None] = mapped_column(TZDateTime)
    feature_set_version: Mapped[str] = mapped_column(String(32), nullable=False)
    hyperparams: Mapped[dict[str, Any] | None] = mapped_column(JSONColumn)
    artifact_path: Mapped[str | None] = mapped_column(Text)
    status: Mapped[ModelStatus] = mapped_column(
        pg_enum(ModelStatus, "model_status"), nullable=False, default=ModelStatus.TRAINING
    )
    promoted_at: Mapped[datetime | None] = mapped_column(TZDateTime)
    retired_at: Mapped[datetime | None] = mapped_column(TZDateTime)
    parent_version_id: Mapped[int | None] = mapped_column(ForeignKey("model_versions.id"))


class ModelMetric(Base, BigIntPK):
    __tablename__ = "model_metrics"
    __table_args__ = (
        Index("ix_model_metrics_model_version_id_stage", "model_version_id", "stage"),
    )

    model_version_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("model_versions.id", ondelete="CASCADE"), nullable=False
    )
    stage: Mapped[EvaluationStage] = mapped_column(
        pg_enum(EvaluationStage, "evaluation_stage"), nullable=False
    )
    window_start: Mapped[datetime | None] = mapped_column(TZDateTime)
    window_end: Mapped[datetime | None] = mapped_column(TZDateTime)
    metric_code: Mapped[str] = mapped_column(String(32), nullable=False)
    value: Mapped[Decimal] = mapped_column(RATIO, nullable=False)
    sample_size: Mapped[int | None] = mapped_column(Integer)
    computed_at: Mapped[datetime] = mapped_column(TZDateTime, nullable=False)


class Prediction(Base):
    """Every prediction is stored and later compared with reality (§15)."""

    __tablename__ = "predictions"
    __table_args__ = (
        PrimaryKeyConstraint(
            "asset_id", "timeframe", "ts", "model_version_id", name="pk_predictions"
        ),
        # Drives the resolver job: unresolved predictions whose horizon elapsed.
        Index("ix_predictions_resolve_at_resolved_at", "resolve_at", "resolved_at"),
        Index("ix_predictions_asset_id_ts", "asset_id", "ts"),
    )

    asset_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    timeframe: Mapped[Timeframe] = mapped_column(pg_enum(Timeframe, "timeframe"), nullable=False)
    ts: Mapped[datetime] = mapped_column(TZDateTime, nullable=False)
    model_version_id: Mapped[int] = mapped_column(Integer, nullable=False)
    scoring_profile_id: Mapped[int | None] = mapped_column(Integer)
    horizon: Mapped[timedelta] = mapped_column(Interval, nullable=False)

    predicted_direction: Mapped[PredictedDirection] = mapped_column(
        pg_enum(PredictedDirection, "predicted_direction"), nullable=False
    )
    predicted_prob: Mapped[Decimal] = mapped_column(RATIO, nullable=False)
    #: Expected move expressed in ATR units — never an absolute price target.
    predicted_move_atr: Mapped[Decimal | None] = mapped_column(RATIO)
    feature_set_version: Mapped[str] = mapped_column(String(32), nullable=False)

    resolve_at: Mapped[datetime] = mapped_column(TZDateTime, nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(TZDateTime)
    actual_return: Mapped[Decimal | None] = mapped_column(RATIO)
    actual_direction: Mapped[PredictedDirection | None] = mapped_column(
        pg_enum(PredictedDirection, "predicted_direction")
    )
    is_correct: Mapped[bool | None] = mapped_column(Boolean)

"""Analytical layer: indicators, features, levels, regimes, scores, risk, signals, AI."""

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
    PrimaryKeyConstraint,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import (
    AIAnalysisStatus,
    MarketRegime,
    Recommendation,
    RegimeScope,
    SignalDirection,
    SignalStatus,
    Timeframe,
)
from app.models.base import (
    MONEY,
    RATIO,
    SCORE,
    Base,
    BigIntPK,
    JSONColumn,
    TimestampMixin,
    TZDateTime,
    pg_enum,
)


class TechnicalIndicator(Base):
    """One row per (asset, timeframe, ts, indicator, parameter set)."""

    __tablename__ = "technical_indicators"
    __table_args__ = (
        PrimaryKeyConstraint(
            "asset_id",
            "timeframe",
            "ts",
            "indicator_code",
            "params_hash",
            name="pk_technical_indicators",
        ),
        Index(
            "ix_technical_indicators_asset_id_timeframe_indicator_code_ts",
            "asset_id",
            "timeframe",
            "indicator_code",
            "ts",
        ),
        Index("ix_technical_indicators_ts", "ts"),
    )

    asset_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    timeframe: Mapped[Timeframe] = mapped_column(pg_enum(Timeframe, "timeframe"), nullable=False)
    ts: Mapped[datetime] = mapped_column(TZDateTime, nullable=False)
    indicator_code: Mapped[str] = mapped_column(String(32), nullable=False)
    #: Short hash of the parameter dict, so RSI-14 and RSI-7 can coexist.
    params_hash: Mapped[str] = mapped_column(String(16), nullable=False)
    value: Mapped[Decimal | None] = mapped_column(MONEY)
    #: Multi-output indicators (MACD, Bollinger, Ichimoku, Stochastic).
    values: Mapped[dict[str, Any] | None] = mapped_column(JSONColumn)
    engine_version: Mapped[str] = mapped_column(String(32), nullable=False)
    computed_at: Mapped[datetime] = mapped_column(TZDateTime, nullable=False)


class FeatureSnapshot(Base):
    """The single feature vector consumed by both ML and the AI analyst.

    Having one producer (``features/builder.py``) eliminates train/serve skew.
    """

    __tablename__ = "feature_snapshots"
    __table_args__ = (
        PrimaryKeyConstraint(
            "asset_id", "timeframe", "ts", "feature_set_version", name="pk_feature_snapshots"
        ),
        Index("ix_feature_snapshots_asset_id_timeframe_ts", "asset_id", "timeframe", "ts"),
    )

    asset_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    timeframe: Mapped[Timeframe] = mapped_column(pg_enum(Timeframe, "timeframe"), nullable=False)
    ts: Mapped[datetime] = mapped_column(TZDateTime, nullable=False)
    feature_set_version: Mapped[str] = mapped_column(String(32), nullable=False)
    features: Mapped[dict[str, Any]] = mapped_column(JSONColumn, nullable=False)
    #: Fraction of expected features that were actually available (0..1).
    completeness: Mapped[Decimal] = mapped_column(RATIO, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TZDateTime, nullable=False)


class SupportResistance(Base, BigIntPK):
    __tablename__ = "support_resistance"
    __table_args__ = (
        Index(
            "ix_support_resistance_asset_id_timeframe_computed_at",
            "asset_id",
            "timeframe",
            "computed_at",
        ),
    )

    asset_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    timeframe: Mapped[Timeframe] = mapped_column(pg_enum(Timeframe, "timeframe"), nullable=False)
    computed_at: Mapped[datetime] = mapped_column(TZDateTime, nullable=False)
    level: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    #: "support" or "resistance" — kept as text to allow future kinds (pivot, VWAP band).
    kind: Mapped[str] = mapped_column(String(16), nullable=False)
    strength: Mapped[Decimal | None] = mapped_column(RATIO)
    touches: Mapped[int | None] = mapped_column(Integer)
    method: Mapped[str] = mapped_column(String(32), nullable=False)
    valid_until: Mapped[datetime | None] = mapped_column(TZDateTime)


class MarketRegimeRecord(Base):
    __tablename__ = "market_regimes"
    __table_args__ = (
        PrimaryKeyConstraint("scope", "scope_ref", "ts", name="pk_market_regimes"),
        Index("ix_market_regimes_scope_ts", "scope", "ts"),
    )

    scope: Mapped[RegimeScope] = mapped_column(pg_enum(RegimeScope, "regime_scope"), nullable=False)
    #: Asset id, sector code or "" for a whole-market scope.
    scope_ref: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    ts: Mapped[datetime] = mapped_column(TZDateTime, nullable=False)
    regime: Mapped[MarketRegime] = mapped_column(
        pg_enum(MarketRegime, "market_regime"), nullable=False
    )
    confidence: Mapped[Decimal] = mapped_column(RATIO, nullable=False)
    indicators: Mapped[dict[str, Any] | None] = mapped_column(JSONColumn)
    method: Mapped[str] = mapped_column(String(32), nullable=False)


class ScoringProfile(Base, TimestampMixin):
    """Versioned weight sets. Weights are never hard-coded (§11, ADR-007)."""

    __tablename__ = "scoring_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    market_type: Mapped[str | None] = mapped_column(String(32))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    weights: Mapped[dict[str, Any]] = mapped_column(JSONColumn, nullable=False)
    thresholds: Mapped[dict[str, Any]] = mapped_column(JSONColumn, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)


class AssetScore(Base):
    __tablename__ = "asset_scores"
    __table_args__ = (
        PrimaryKeyConstraint(
            "asset_id", "timeframe", "ts", "scoring_profile_id", name="pk_asset_scores"
        ),
        Index("ix_asset_scores_ts_final_score", "ts", "final_score"),
        Index("ix_asset_scores_asset_id_timeframe_ts", "asset_id", "timeframe", "ts"),
    )

    asset_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    timeframe: Mapped[Timeframe] = mapped_column(pg_enum(Timeframe, "timeframe"), nullable=False)
    ts: Mapped[datetime] = mapped_column(TZDateTime, nullable=False)
    scoring_profile_id: Mapped[int] = mapped_column(Integer, nullable=False)

    technical: Mapped[Decimal | None] = mapped_column(SCORE)
    momentum: Mapped[Decimal | None] = mapped_column(SCORE)
    volume: Mapped[Decimal | None] = mapped_column(SCORE)
    market: Mapped[Decimal | None] = mapped_column(SCORE)
    news: Mapped[Decimal | None] = mapped_column(SCORE)
    sentiment: Mapped[Decimal | None] = mapped_column(SCORE)
    liquidity: Mapped[Decimal | None] = mapped_column(SCORE)
    ml: Mapped[Decimal | None] = mapped_column(SCORE)
    risk: Mapped[Decimal] = mapped_column(SCORE, nullable=False)
    ai_confidence: Mapped[Decimal | None] = mapped_column(SCORE)
    final_score: Mapped[Decimal] = mapped_column(SCORE, nullable=False)
    confidence: Mapped[Decimal] = mapped_column(RATIO, nullable=False)
    recommendation: Mapped[Recommendation] = mapped_column(
        pg_enum(Recommendation, "recommendation"), nullable=False
    )
    #: Full breakdown of the computation — the basis of explainability.
    components: Mapped[dict[str, Any]] = mapped_column(JSONColumn, nullable=False)
    data_completeness: Mapped[Decimal] = mapped_column(RATIO, nullable=False)


class RiskMetric(Base):
    __tablename__ = "risk_metrics"
    __table_args__ = (
        PrimaryKeyConstraint("asset_id", "timeframe", "ts", name="pk_risk_metrics"),
        Index("ix_risk_metrics_asset_id_ts", "asset_id", "ts"),
    )

    asset_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    timeframe: Mapped[Timeframe] = mapped_column(pg_enum(Timeframe, "timeframe"), nullable=False)
    ts: Mapped[datetime] = mapped_column(TZDateTime, nullable=False)

    atr: Mapped[Decimal | None] = mapped_column(MONEY)
    atr_pct: Mapped[Decimal | None] = mapped_column(RATIO)
    realized_vol_7d: Mapped[Decimal | None] = mapped_column(RATIO)
    realized_vol_30d: Mapped[Decimal | None] = mapped_column(RATIO)
    beta_vs_market: Mapped[Decimal | None] = mapped_column(RATIO)
    max_drawdown_30d: Mapped[Decimal | None] = mapped_column(RATIO)
    max_drawdown_90d: Mapped[Decimal | None] = mapped_column(RATIO)
    var_95: Mapped[Decimal | None] = mapped_column(RATIO)
    cvar_95: Mapped[Decimal | None] = mapped_column(RATIO)
    liquidity_score: Mapped[Decimal | None] = mapped_column(SCORE)
    gap_risk: Mapped[Decimal | None] = mapped_column(RATIO)
    #: Tehran-specific: order-queue / trading-halt probability.
    halt_risk: Mapped[Decimal | None] = mapped_column(RATIO)
    risk_score: Mapped[Decimal] = mapped_column(SCORE, nullable=False)


class Signal(Base, BigIntPK):
    __tablename__ = "signals"
    __table_args__ = (
        Index("ix_signals_status_created_at", "status", "created_at"),
        Index("ix_signals_asset_id_created_at", "asset_id", "created_at"),
    )

    asset_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("assets.id"), nullable=False)
    timeframe: Mapped[Timeframe] = mapped_column(pg_enum(Timeframe, "timeframe"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TZDateTime, nullable=False)
    direction: Mapped[SignalDirection] = mapped_column(
        pg_enum(SignalDirection, "signal_direction"), nullable=False
    )
    entry: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    stop_loss: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    take_profit_1: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    take_profit_2: Mapped[Decimal | None] = mapped_column(MONEY)
    rr_ratio: Mapped[Decimal] = mapped_column(RATIO, nullable=False)
    position_risk_pct: Mapped[Decimal] = mapped_column(RATIO, nullable=False)
    opportunity_score: Mapped[Decimal] = mapped_column(SCORE, nullable=False)
    risk_score: Mapped[Decimal] = mapped_column(SCORE, nullable=False)
    confidence: Mapped[Decimal] = mapped_column(RATIO, nullable=False)
    recommendation: Mapped[Recommendation] = mapped_column(
        pg_enum(Recommendation, "recommendation"), nullable=False
    )
    #: Machine-readable reasons produced by DecisionPolicy.
    reasons: Mapped[dict[str, Any]] = mapped_column(JSONColumn, nullable=False)
    rationale: Mapped[str | None] = mapped_column(Text)
    ai_analysis_id: Mapped[int | None] = mapped_column(BigInteger)
    model_version_id: Mapped[int | None] = mapped_column(Integer)
    scoring_profile_id: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[SignalStatus] = mapped_column(
        pg_enum(SignalStatus, "signal_status"), nullable=False, default=SignalStatus.ACTIVE
    )
    expires_at: Mapped[datetime | None] = mapped_column(TZDateTime)
    resolved_at: Mapped[datetime | None] = mapped_column(TZDateTime)
    outcome: Mapped[dict[str, Any] | None] = mapped_column(JSONColumn)


class AIAnalysis(Base, BigIntPK):
    __tablename__ = "ai_analysis"
    __table_args__ = (Index("ix_ai_analysis_asset_id_created_at", "asset_id", "created_at"),)

    asset_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("assets.id"), nullable=False)
    timeframe: Mapped[Timeframe] = mapped_column(pg_enum(Timeframe, "timeframe"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TZDateTime, nullable=False)
    provider: Mapped[str] = mapped_column(String(32), nullable=False)
    model: Mapped[str] = mapped_column(String(64), nullable=False)
    prompt_version: Mapped[str] = mapped_column(String(16), nullable=False)
    #: Exact payload sent to the LLM — required to reproduce past analyses.
    input_features: Mapped[dict[str, Any]] = mapped_column(JSONColumn, nullable=False)
    output: Mapped[dict[str, Any] | None] = mapped_column(JSONColumn)
    summary_fa: Mapped[str | None] = mapped_column(Text)
    contradictions: Mapped[dict[str, Any] | None] = mapped_column(JSONColumn)
    risks: Mapped[dict[str, Any] | None] = mapped_column(JSONColumn)
    ai_confidence: Mapped[Decimal | None] = mapped_column(RATIO)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    tokens_in: Mapped[int | None] = mapped_column(Integer)
    tokens_out: Mapped[int | None] = mapped_column(Integer)
    status: Mapped[AIAnalysisStatus] = mapped_column(
        pg_enum(AIAnalysisStatus, "ai_analysis_status"), nullable=False
    )
    guardrail_rejections: Mapped[dict[str, Any] | None] = mapped_column(JSONColumn)

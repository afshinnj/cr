"""Backtesting and paper trading. No real-order execution exists (ADR-014)."""

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
    BacktestMethod,
    ExitReason,
    OrderSide,
    OrderStatus,
    OrderType,
    PositionStatus,
    RunStatus,
    Timeframe,
)
from app.models.base import (
    MONEY,
    RATIO,
    Base,
    BigIntPK,
    JSONColumn,
    TimestampMixin,
    TZDateTime,
    pg_enum,
)


class Backtest(Base, BigIntPK, TimestampMixin):
    __tablename__ = "backtests"
    __table_args__ = (Index("ix_backtests_status_created_at", "status", "created_at"),)

    name: Mapped[str] = mapped_column(String(128), nullable=False)
    strategy_code: Mapped[str] = mapped_column(String(64), nullable=False)
    strategy_params: Mapped[dict[str, Any] | None] = mapped_column(JSONColumn)
    scoring_profile_id: Mapped[int | None] = mapped_column(Integer)
    model_version_id: Mapped[int | None] = mapped_column(Integer)
    universe: Mapped[dict[str, Any]] = mapped_column(JSONColumn, nullable=False)
    timeframe: Mapped[Timeframe] = mapped_column(pg_enum(Timeframe, "timeframe"), nullable=False)
    start_at: Mapped[datetime] = mapped_column(TZDateTime, nullable=False)
    end_at: Mapped[datetime] = mapped_column(TZDateTime, nullable=False)
    method: Mapped[BacktestMethod] = mapped_column(
        pg_enum(BacktestMethod, "backtest_method"), nullable=False
    )
    #: Fees, spread and slippage assumptions — without these results are fiction.
    costs: Mapped[dict[str, Any]] = mapped_column(JSONColumn, nullable=False)
    status: Mapped[RunStatus] = mapped_column(
        pg_enum(RunStatus, "run_status"), nullable=False, default=RunStatus.PENDING
    )
    finished_at: Mapped[datetime | None] = mapped_column(TZDateTime)
    metrics: Mapped[dict[str, Any] | None] = mapped_column(JSONColumn)
    equity_curve: Mapped[dict[str, Any] | None] = mapped_column(JSONColumn)
    error: Mapped[str | None] = mapped_column(Text)


class BacktestTrade(Base, BigIntPK):
    __tablename__ = "backtest_trades"
    __table_args__ = (Index("ix_backtest_trades_backtest_id_entry_ts", "backtest_id", "entry_ts"),)

    backtest_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("backtests.id", ondelete="CASCADE"), nullable=False
    )
    asset_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    side: Mapped[OrderSide] = mapped_column(pg_enum(OrderSide, "order_side"), nullable=False)
    entry_ts: Mapped[datetime] = mapped_column(TZDateTime, nullable=False)
    entry_price: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    exit_ts: Mapped[datetime | None] = mapped_column(TZDateTime)
    exit_price: Mapped[Decimal | None] = mapped_column(MONEY)
    qty: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    fees: Mapped[Decimal] = mapped_column(MONEY, nullable=False, default=0)
    pnl: Mapped[Decimal | None] = mapped_column(MONEY)
    pnl_pct: Mapped[Decimal | None] = mapped_column(RATIO)
    #: Result in units of initial risk (R-multiple).
    r_multiple: Mapped[Decimal | None] = mapped_column(RATIO)
    exit_reason: Mapped[ExitReason | None] = mapped_column(pg_enum(ExitReason, "exit_reason"))
    mae: Mapped[Decimal | None] = mapped_column(RATIO)
    mfe: Mapped[Decimal | None] = mapped_column(RATIO)
    bars_held: Mapped[int | None] = mapped_column(Integer)


class PaperAccount(Base, BigIntPK, TimestampMixin):
    __tablename__ = "paper_accounts"

    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    base_currency: Mapped[str] = mapped_column(String(16), nullable=False, default="USDT")
    initial_balance: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    current_balance: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    equity: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    scoring_profile_id: Mapped[int | None] = mapped_column(Integer)
    model_version_id: Mapped[int | None] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    #: Risk limits: max positions, risk per trade, exposure caps, loss limits.
    config: Mapped[dict[str, Any]] = mapped_column(JSONColumn, nullable=False)


class PaperOrder(Base, BigIntPK):
    __tablename__ = "paper_orders"
    __table_args__ = (Index("ix_paper_orders_account_id_created_at", "account_id", "created_at"),)

    account_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("paper_accounts.id", ondelete="CASCADE"), nullable=False
    )
    signal_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("signals.id"))
    asset_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(TZDateTime, nullable=False)
    side: Mapped[OrderSide] = mapped_column(pg_enum(OrderSide, "order_side"), nullable=False)
    type: Mapped[OrderType] = mapped_column(pg_enum(OrderType, "order_type"), nullable=False)
    qty: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    requested_price: Mapped[Decimal | None] = mapped_column(MONEY)
    fill_price: Mapped[Decimal | None] = mapped_column(MONEY)
    fill_ts: Mapped[datetime | None] = mapped_column(TZDateTime)
    status: Mapped[OrderStatus] = mapped_column(
        pg_enum(OrderStatus, "order_status"), nullable=False, default=OrderStatus.PENDING
    )
    fees: Mapped[Decimal] = mapped_column(MONEY, nullable=False, default=0)
    slippage_model: Mapped[str | None] = mapped_column(String(32))
    reject_reason: Mapped[str | None] = mapped_column(Text)


class PaperPosition(Base, BigIntPK):
    __tablename__ = "paper_positions"
    __table_args__ = (Index("ix_paper_positions_account_id_status", "account_id", "status"),)

    account_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("paper_accounts.id", ondelete="CASCADE"), nullable=False
    )
    asset_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    side: Mapped[OrderSide] = mapped_column(pg_enum(OrderSide, "order_side"), nullable=False)
    qty: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    avg_entry: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    stop_loss: Mapped[Decimal | None] = mapped_column(MONEY)
    take_profit_1: Mapped[Decimal | None] = mapped_column(MONEY)
    take_profit_2: Mapped[Decimal | None] = mapped_column(MONEY)
    opened_at: Mapped[datetime] = mapped_column(TZDateTime, nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(TZDateTime)
    realized_pnl: Mapped[Decimal] = mapped_column(MONEY, nullable=False, default=0)
    unrealized_pnl: Mapped[Decimal | None] = mapped_column(MONEY)
    status: Mapped[PositionStatus] = mapped_column(
        pg_enum(PositionStatus, "position_status"), nullable=False, default=PositionStatus.OPEN
    )
    linked_signal_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("signals.id"))
    exit_reason: Mapped[ExitReason | None] = mapped_column(pg_enum(ExitReason, "exit_reason"))


class PaperEquityPoint(Base):
    __tablename__ = "paper_equity_curve"
    __table_args__ = (PrimaryKeyConstraint("account_id", "ts", name="pk_paper_equity_curve"),)

    account_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("paper_accounts.id", ondelete="CASCADE"), nullable=False
    )
    ts: Mapped[datetime] = mapped_column(TZDateTime, nullable=False)
    equity: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    cash: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    positions_value: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    drawdown: Mapped[Decimal | None] = mapped_column(RATIO)
    open_positions_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

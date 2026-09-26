"""SQLAlchemy models.

Importing this package registers every table on :data:`app.models.base.Base`,
which Alembic's autogenerate relies on.
"""

from __future__ import annotations

from app.models.analysis import (
    AIAnalysis,
    AssetScore,
    FeatureSnapshot,
    MarketRegimeRecord,
    RiskMetric,
    ScoringProfile,
    Signal,
    SupportResistance,
    TechnicalIndicator,
)
from app.models.base import Base
from app.models.execution import (
    Backtest,
    BacktestTrade,
    PaperAccount,
    PaperEquityPoint,
    PaperOrder,
    PaperPosition,
)
from app.models.market import (
    OHLCV,
    DataQuarantine,
    MarketMetric,
    OrderBookSnapshot,
    Trade,
)
from app.models.ml import ModelMetric, ModelVersion, Prediction
from app.models.news import NewsArticle, NewsEvent, NewsEventAsset, Sentiment
from app.models.reference import (
    Asset,
    CorporateAction,
    DataSource,
    DataSourceHealth,
    Exchange,
    Sector,
    SymbolAlias,
)
from app.models.system import (
    AlertEvent,
    AlertRule,
    JobRun,
    SystemLog,
    UserDrawing,
    UserSetting,
)

__all__ = [
    "OHLCV",
    "AIAnalysis",
    "AlertEvent",
    "AlertRule",
    "Asset",
    "AssetScore",
    "Backtest",
    "BacktestTrade",
    "Base",
    "CorporateAction",
    "DataQuarantine",
    "DataSource",
    "DataSourceHealth",
    "Exchange",
    "FeatureSnapshot",
    "JobRun",
    "MarketMetric",
    "MarketRegimeRecord",
    "ModelMetric",
    "ModelVersion",
    "NewsArticle",
    "NewsEvent",
    "NewsEventAsset",
    "OrderBookSnapshot",
    "PaperAccount",
    "PaperEquityPoint",
    "PaperOrder",
    "PaperPosition",
    "Prediction",
    "RiskMetric",
    "ScoringProfile",
    "Sector",
    "Sentiment",
    "Signal",
    "SupportResistance",
    "SymbolAlias",
    "SystemLog",
    "TechnicalIndicator",
    "Trade",
    "UserDrawing",
    "UserSetting",
]

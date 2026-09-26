"""Domain enumerations shared by ORM models, schemas and engines."""

from __future__ import annotations

from enum import StrEnum


class MarketType(StrEnum):
    CRYPTO = "crypto"
    IRAN_STOCK = "iran_stock"


class AssetClass(StrEnum):
    SPOT_CRYPTO = "spot_crypto"
    PERP = "perp"
    STOCK = "stock"
    ETF = "etf"
    INDEX = "index"
    COMMODITY_FUND = "commodity_fund"


class AssetStatus(StrEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELISTED = "delisted"


class Timeframe(StrEnum):
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"
    W1 = "1w"

    @property
    def seconds(self) -> int:
        return _TIMEFRAME_SECONDS[self]


_TIMEFRAME_SECONDS: dict[Timeframe, int] = {
    Timeframe.M1: 60,
    Timeframe.M5: 300,
    Timeframe.M15: 900,
    Timeframe.M30: 1_800,
    Timeframe.H1: 3_600,
    Timeframe.H4: 14_400,
    Timeframe.D1: 86_400,
    Timeframe.W1: 604_800,
}


class DataSourceKind(StrEnum):
    MARKET = "market"
    NEWS = "news"
    ONCHAIN = "onchain"
    DERIVATIVES = "derivatives"
    REFERENCE = "reference"


class SourceStatus(StrEnum):
    UP = "up"
    DEGRADED = "degraded"
    DOWN = "down"
    UNKNOWN = "unknown"


class ValidationStatus(StrEnum):
    VALID = "valid"
    SUSPICIOUS = "suspicious"
    STALE = "stale"
    REJECTED = "rejected"


class CorporateActionType(StrEnum):
    SPLIT = "split"
    CAPITAL_INCREASE = "capital_increase"
    DIVIDEND = "dividend"
    SYMBOL_CHANGE = "symbol_change"


class RegimeScope(StrEnum):
    GLOBAL_CRYPTO = "global_crypto"
    ASSET = "asset"
    TSE_MARKET = "tse_market"
    SECTOR = "sector"


class MarketRegime(StrEnum):
    BULL = "BULL"
    BEAR = "BEAR"
    SIDEWAYS = "SIDEWAYS"
    HIGH_VOLATILITY = "HIGH_VOLATILITY"
    LOW_VOLATILITY = "LOW_VOLATILITY"


class Recommendation(StrEnum):
    BUY_CANDIDATE = "BUY_CANDIDATE"
    WATCH = "WATCH"
    HOLD = "HOLD"
    WAIT = "WAIT"
    AVOID = "AVOID"
    RESEARCH_ONLY = "RESEARCH_ONLY"
    NO_ACTION = "NO_ACTION"


class SignalDirection(StrEnum):
    LONG = "long"
    SHORT = "short"
    NONE = "none"


class SignalStatus(StrEnum):
    ACTIVE = "active"
    EXPIRED = "expired"
    INVALIDATED = "invalidated"
    HIT_TP1 = "hit_tp1"
    HIT_TP2 = "hit_tp2"
    HIT_SL = "hit_sl"


class SentimentLabel(StrEnum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class SentimentIntensity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SentimentSubject(StrEnum):
    ARTICLE = "article"
    EVENT = "event"
    ASSET_AGGREGATE = "asset_aggregate"


class NewsCategory(StrEnum):
    REGULATION = "regulation"
    HACK = "hack"
    LISTING = "listing"
    DELISTING = "delisting"
    MACRO = "macro"
    EARNINGS = "earnings"
    POLICY = "policy"
    PARTNERSHIP = "partnership"
    CORPORATE_ACTION = "corporate_action"
    OTHER = "other"


class NewsScope(StrEnum):
    GLOBAL = "global"
    MARKET = "market"
    SECTOR = "sector"
    ASSET = "asset"


class ModelTask(StrEnum):
    DIRECTION_CLF = "direction_clf"
    VOL_REG = "vol_reg"
    REGIME_CLF = "regime_clf"


class ModelStatus(StrEnum):
    TRAINING = "training"
    VALIDATED = "validated"
    BACKTESTED = "backtested"
    PAPER = "paper"
    PRODUCTION = "production"
    RETIRED = "retired"


class EvaluationStage(StrEnum):
    TRAIN = "train"
    VALIDATION = "validation"
    BACKTEST = "backtest"
    PAPER = "paper"
    LIVE = "live"


class PredictedDirection(StrEnum):
    UP = "up"
    DOWN = "down"
    NEUTRAL = "neutral"


class BacktestMethod(StrEnum):
    SIMPLE_SPLIT = "simple_split"
    WALK_FORWARD = "walk_forward"
    PURGED_KFOLD = "purged_kfold"


class RunStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"


class OrderSide(StrEnum):
    BUY = "buy"
    SELL = "sell"


class OrderType(StrEnum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"


class OrderStatus(StrEnum):
    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    REJECTED = "rejected"
    CANCELED = "canceled"


class PositionStatus(StrEnum):
    OPEN = "open"
    CLOSED = "closed"
    FROZEN = "frozen"


class ExitReason(StrEnum):
    TP1 = "tp1"
    TP2 = "tp2"
    SL = "sl"
    TIME = "time"
    SIGNAL_FLIP = "signal_flip"
    MANUAL = "manual"


class AlertConditionType(StrEnum):
    BREAKOUT = "breakout"
    VOLUME_SPIKE = "volume_spike"
    RSI_OVERBOUGHT = "rsi_overbought"
    RSI_OVERSOLD = "rsi_oversold"
    MACD_CROSS = "macd_cross"
    NEWS_IMPACT = "news_impact"
    PRICE_MOVE = "price_move"
    RISK_CHANGE = "risk_change"
    AI_SCORE_CHANGE = "ai_score_change"


class AlertScope(StrEnum):
    ASSET = "asset"
    MARKET = "market"
    GLOBAL = "global"


class AIAnalysisStatus(StrEnum):
    OK = "ok"
    INVALID_JSON = "invalid_json"
    TIMEOUT = "timeout"
    REFUSED = "refused"
    DEGRADED = "degraded"
    INSUFFICIENT_DATA = "insufficient_data"

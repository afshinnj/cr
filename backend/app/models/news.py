"""News articles, deduplicated events and sentiment."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    BigInteger,
    ForeignKey,
    Index,
    Integer,
    PrimaryKeyConstraint,
    SmallInteger,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import (
    NewsCategory,
    NewsScope,
    SentimentIntensity,
    SentimentLabel,
    SentimentSubject,
)
from app.models.base import (
    RATIO,
    SCORE,
    Base,
    BigIntPK,
    JSONColumn,
    TZDateTime,
    pg_enum,
)


class NewsEvent(Base, BigIntPK):
    """A deduplicated real-world event: many articles collapse into one row (§8)."""

    __tablename__ = "news_events"
    __table_args__ = (
        Index("ix_news_events_first_seen_at", "first_seen_at"),
        Index("ix_news_events_category_importance", "category", "importance"),
    )

    canonical_title: Mapped[str] = mapped_column(Text, nullable=False)
    first_seen_at: Mapped[datetime] = mapped_column(TZDateTime, nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(TZDateTime, nullable=False)
    article_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    #: Number of *distinct* sources — a signal of importance, not noise.
    source_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    category: Mapped[NewsCategory] = mapped_column(
        pg_enum(NewsCategory, "news_category"), nullable=False, default=NewsCategory.OTHER
    )
    scope: Mapped[NewsScope] = mapped_column(
        pg_enum(NewsScope, "news_scope"), nullable=False, default=NewsScope.ASSET
    )
    importance: Mapped[Decimal | None] = mapped_column(SCORE)
    dedup_method: Mapped[str | None] = mapped_column(String(32))
    #: Cluster centroid; stored as a JSON array until pgvector is enabled (ADR O5).
    centroid_embedding: Mapped[dict[str, Any] | None] = mapped_column(JSONColumn)


class NewsArticle(Base, BigIntPK):
    __tablename__ = "news_articles"
    __table_args__ = (
        Index("ix_news_articles_published_at", "published_at"),
        Index("ix_news_articles_event_id", "event_id"),
        Index("ix_news_articles_simhash", "simhash"),
    )

    source_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("data_sources.id"), nullable=False
    )
    external_id: Mapped[str | None] = mapped_column(String(128))
    url: Mapped[str] = mapped_column(Text, nullable=False)
    #: sha256 of the normalised URL — the L0 exact-duplicate key.
    url_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    body: Mapped[str | None] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(8), nullable=False, default="en")
    author: Mapped[str | None] = mapped_column(String(128))
    published_at: Mapped[datetime] = mapped_column(TZDateTime, nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(TZDateTime, nullable=False)
    #: 64-bit SimHash of title + lead — the L1 near-duplicate key.
    simhash: Mapped[int | None] = mapped_column(BigInteger)
    event_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("news_events.id", ondelete="SET NULL")
    )
    raw: Mapped[dict[str, Any] | None] = mapped_column(JSONColumn)


class NewsEventAsset(Base):
    """Many-to-many link between events and assets with a relevance weight."""

    __tablename__ = "news_event_assets"
    __table_args__ = (
        PrimaryKeyConstraint("event_id", "asset_id", name="pk_news_event_assets"),
        Index("ix_news_event_assets_asset_id", "asset_id"),
    )

    event_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("news_events.id", ondelete="CASCADE"), nullable=False
    )
    asset_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("assets.id", ondelete="CASCADE"), nullable=False
    )
    relevance: Mapped[Decimal] = mapped_column(RATIO, nullable=False)
    #: dictionary | ner | llm
    extraction_method: Mapped[str] = mapped_column(String(16), nullable=False)


class Sentiment(Base, BigIntPK):
    __tablename__ = "sentiments"
    __table_args__ = (
        Index("ix_sentiments_subject_type_subject_id", "subject_type", "subject_id"),
        Index("ix_sentiments_computed_at", "computed_at"),
    )

    subject_type: Mapped[SentimentSubject] = mapped_column(
        pg_enum(SentimentSubject, "sentiment_subject"), nullable=False
    )
    subject_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    label: Mapped[SentimentLabel] = mapped_column(
        pg_enum(SentimentLabel, "sentiment_label"), nullable=False
    )
    #: -1..+1
    score: Mapped[Decimal] = mapped_column(RATIO, nullable=False)
    intensity: Mapped[SentimentIntensity] = mapped_column(
        pg_enum(SentimentIntensity, "sentiment_intensity"), nullable=False
    )
    #: 0..100
    impact_score: Mapped[Decimal | None] = mapped_column(SCORE)
    confidence: Mapped[Decimal] = mapped_column(RATIO, nullable=False)
    model: Mapped[str] = mapped_column(String(64), nullable=False)
    model_version: Mapped[str | None] = mapped_column(String(32))
    computed_at: Mapped[datetime] = mapped_column(TZDateTime, nullable=False)

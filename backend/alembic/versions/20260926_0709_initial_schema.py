"""initial schema

Revision ID: 766f1fa633ff
Revises: 
Create Date: 2026-09-26 07:09:59.074712+00:00
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy import Text
from sqlalchemy.dialects import postgresql

revision: str = '766f1fa633ff'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table('asset_scores',
    sa.Column('asset_id', sa.BigInteger(), nullable=False),
    sa.Column('timeframe', sa.Enum('1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w', name='timeframe'), nullable=False),
    sa.Column('ts', sa.DateTime(timezone=True), nullable=False),
    sa.Column('scoring_profile_id', sa.Integer(), nullable=False),
    sa.Column('technical', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.Column('momentum', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.Column('volume', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.Column('market', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.Column('news', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.Column('sentiment', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.Column('liquidity', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.Column('ml', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.Column('risk', sa.Numeric(precision=5, scale=2), nullable=False),
    sa.Column('ai_confidence', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.Column('final_score', sa.Numeric(precision=5, scale=2), nullable=False),
    sa.Column('confidence', sa.Numeric(precision=10, scale=6), nullable=False),
    sa.Column('recommendation', sa.Enum('BUY_CANDIDATE', 'WATCH', 'HOLD', 'WAIT', 'AVOID', 'RESEARCH_ONLY', 'NO_ACTION', name='recommendation'), nullable=False),
    sa.Column('components', postgresql.JSONB(astext_type=Text()).with_variant(sa.JSON(), 'sqlite'), nullable=False),
    sa.Column('data_completeness', sa.Numeric(precision=10, scale=6), nullable=False),
    sa.PrimaryKeyConstraint('asset_id', 'timeframe', 'ts', 'scoring_profile_id', name='pk_asset_scores')
    )
    op.create_index('ix_asset_scores_asset_id_timeframe_ts', 'asset_scores', ['asset_id', 'timeframe', 'ts'], unique=False)
    op.create_index('ix_asset_scores_ts_final_score', 'asset_scores', ['ts', 'final_score'], unique=False)
    op.create_table('backtests',
    sa.Column('name', sa.String(length=128), nullable=False),
    sa.Column('strategy_code', sa.String(length=64), nullable=False),
    sa.Column('strategy_params', postgresql.JSONB(astext_type=Text()).with_variant(sa.JSON(), 'sqlite'), nullable=True),
    sa.Column('scoring_profile_id', sa.Integer(), nullable=True),
    sa.Column('model_version_id', sa.Integer(), nullable=True),
    sa.Column('universe', postgresql.JSONB(astext_type=Text()).with_variant(sa.JSON(), 'sqlite'), nullable=False),
    sa.Column('timeframe', sa.Enum('1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w', name='timeframe'), nullable=False),
    sa.Column('start_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('end_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('method', sa.Enum('simple_split', 'walk_forward', 'purged_kfold', name='backtest_method'), nullable=False),
    sa.Column('costs', postgresql.JSONB(astext_type=Text()).with_variant(sa.JSON(), 'sqlite'), nullable=False),
    sa.Column('status', sa.Enum('pending', 'running', 'succeeded', 'failed', 'canceled', name='run_status'), nullable=False),
    sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('metrics', postgresql.JSONB(astext_type=Text()).with_variant(sa.JSON(), 'sqlite'), nullable=True),
    sa.Column('equity_curve', postgresql.JSONB(astext_type=Text()).with_variant(sa.JSON(), 'sqlite'), nullable=True),
    sa.Column('error', sa.Text(), nullable=True),
    sa.Column('id', sa.BigInteger().with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_backtests'))
    )
    op.create_index('ix_backtests_status_created_at', 'backtests', ['status', 'created_at'], unique=False)
    op.create_table('data_sources',
    sa.Column('id', sa.SmallInteger().with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.Column('code', sa.String(length=48), nullable=False),
    sa.Column('name', sa.String(length=128), nullable=False),
    sa.Column('kind', sa.Enum('market', 'news', 'onchain', 'derivatives', 'reference', name='data_source_kind'), nullable=False),
    sa.Column('base_url', sa.Text(), nullable=True),
    sa.Column('auth_type', sa.String(length=32), nullable=True),
    sa.Column('rate_limit', postgresql.JSONB(astext_type=Text()).with_variant(sa.JSON(), 'sqlite'), nullable=True),
    sa.Column('priority', sa.SmallInteger(), nullable=False),
    sa.Column('credibility', sa.Numeric(precision=10, scale=6), nullable=True),
    sa.Column('is_enabled', sa.Boolean(), nullable=False),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_data_sources')),
    sa.UniqueConstraint('code', name=op.f('uq_data_sources_code'))
    )
    op.create_table('exchanges',
    sa.Column('id', sa.SmallInteger().with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.Column('code', sa.String(length=32), nullable=False),
    sa.Column('name', sa.String(length=128), nullable=False),
    sa.Column('market_type', sa.Enum('crypto', 'iran_stock', name='market_type'), nullable=False),
    sa.Column('timezone', sa.String(length=64), nullable=False),
    sa.Column('trading_calendar', postgresql.JSONB(astext_type=Text()).with_variant(sa.JSON(), 'sqlite'), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_exchanges')),
    sa.UniqueConstraint('code', name=op.f('uq_exchanges_code'))
    )
    op.create_table('feature_snapshots',
    sa.Column('asset_id', sa.BigInteger(), nullable=False),
    sa.Column('timeframe', sa.Enum('1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w', name='timeframe'), nullable=False),
    sa.Column('ts', sa.DateTime(timezone=True), nullable=False),
    sa.Column('feature_set_version', sa.String(length=32), nullable=False),
    sa.Column('features', postgresql.JSONB(astext_type=Text()).with_variant(sa.JSON(), 'sqlite'), nullable=False),
    sa.Column('completeness', sa.Numeric(precision=10, scale=6), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('asset_id', 'timeframe', 'ts', 'feature_set_version', name='pk_feature_snapshots')
    )
    op.create_index('ix_feature_snapshots_asset_id_timeframe_ts', 'feature_snapshots', ['asset_id', 'timeframe', 'ts'], unique=False)
    op.create_table('job_runs',
    sa.Column('job_name', sa.String(length=64), nullable=False),
    sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('status', sa.Enum('pending', 'running', 'succeeded', 'failed', 'canceled', name='run_status'), nullable=False),
    sa.Column('items_processed', sa.Integer(), nullable=False),
    sa.Column('items_failed', sa.Integer(), nullable=False),
    sa.Column('error', sa.Text(), nullable=True),
    sa.Column('metrics', postgresql.JSONB(astext_type=Text()).with_variant(sa.JSON(), 'sqlite'), nullable=True),
    sa.Column('id', sa.BigInteger().with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_job_runs'))
    )
    op.create_index('ix_job_runs_job_name_started_at', 'job_runs', ['job_name', 'started_at'], unique=False)
    op.create_table('market_metrics',
    sa.Column('asset_id', sa.BigInteger(), nullable=True),
    sa.Column('scope_ref', sa.String(length=64), nullable=False),
    sa.Column('metric_code', sa.String(length=64), nullable=False),
    sa.Column('ts', sa.DateTime(timezone=True), nullable=False),
    sa.Column('source_id', sa.SmallInteger(), nullable=False),
    sa.Column('value', sa.Numeric(precision=38, scale=12), nullable=True),
    sa.Column('meta', postgresql.JSONB(astext_type=Text()).with_variant(sa.JSON(), 'sqlite'), nullable=True),
    sa.Column('ingested_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('quality_score', sa.SmallInteger(), nullable=False),
    sa.PrimaryKeyConstraint('metric_code', 'scope_ref', 'ts', 'source_id', name='pk_market_metrics')
    )
    op.create_index('ix_market_metrics_asset_id_metric_code_ts', 'market_metrics', ['asset_id', 'metric_code', 'ts'], unique=False)
    op.create_index('ix_market_metrics_ts', 'market_metrics', ['ts'], unique=False)
    op.create_table('market_regimes',
    sa.Column('scope', sa.Enum('global_crypto', 'asset', 'tse_market', 'sector', name='regime_scope'), nullable=False),
    sa.Column('scope_ref', sa.String(length=64), nullable=False),
    sa.Column('ts', sa.DateTime(timezone=True), nullable=False),
    sa.Column('regime', sa.Enum('BULL', 'BEAR', 'SIDEWAYS', 'HIGH_VOLATILITY', 'LOW_VOLATILITY', name='market_regime'), nullable=False),
    sa.Column('confidence', sa.Numeric(precision=10, scale=6), nullable=False),
    sa.Column('indicators', postgresql.JSONB(astext_type=Text()).with_variant(sa.JSON(), 'sqlite'), nullable=True),
    sa.Column('method', sa.String(length=32), nullable=False),
    sa.PrimaryKeyConstraint('scope', 'scope_ref', 'ts', name='pk_market_regimes')
    )
    op.create_index('ix_market_regimes_scope_ts', 'market_regimes', ['scope', 'ts'], unique=False)
    op.create_table('model_versions',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('name', sa.String(length=64), nullable=False),
    sa.Column('version', sa.String(length=32), nullable=False),
    sa.Column('task', sa.Enum('direction_clf', 'vol_reg', 'regime_clf', name='model_task'), nullable=False),
    sa.Column('algo', sa.String(length=32), nullable=False),
    sa.Column('trained_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('train_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('train_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('valid_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('valid_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('feature_set_version', sa.String(length=32), nullable=False),
    sa.Column('hyperparams', postgresql.JSONB(astext_type=Text()).with_variant(sa.JSON(), 'sqlite'), nullable=True),
    sa.Column('artifact_path', sa.Text(), nullable=True),
    sa.Column('status', sa.Enum('training', 'validated', 'backtested', 'paper', 'production', 'retired', name='model_status'), nullable=False),
    sa.Column('promoted_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('retired_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('parent_version_id', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['parent_version_id'], ['model_versions.id'], name=op.f('fk_model_versions_parent_version_id_model_versions')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_model_versions')),
    sa.UniqueConstraint('name', 'version', name='uq_model_versions_name_version')
    )
    op.create_table('news_events',
    sa.Column('canonical_title', sa.Text(), nullable=False),
    sa.Column('first_seen_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('last_seen_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('article_count', sa.Integer(), nullable=False),
    sa.Column('source_count', sa.Integer(), nullable=False),
    sa.Column('category', sa.Enum('regulation', 'hack', 'listing', 'delisting', 'macro', 'earnings', 'policy', 'partnership', 'corporate_action', 'other', name='news_category'), nullable=False),
    sa.Column('scope', sa.Enum('global', 'market', 'sector', 'asset', name='news_scope'), nullable=False),
    sa.Column('importance', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.Column('dedup_method', sa.String(length=32), nullable=True),
    sa.Column('centroid_embedding', postgresql.JSONB(astext_type=Text()).with_variant(sa.JSON(), 'sqlite'), nullable=True),
    sa.Column('id', sa.BigInteger().with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_news_events'))
    )
    op.create_index('ix_news_events_category_importance', 'news_events', ['category', 'importance'], unique=False)
    op.create_index('ix_news_events_first_seen_at', 'news_events', ['first_seen_at'], unique=False)
    op.create_table('ohlcv',
    sa.Column('asset_id', sa.BigInteger(), nullable=False),
    sa.Column('timeframe', sa.Enum('1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w', name='timeframe'), nullable=False),
    sa.Column('ts', sa.DateTime(timezone=True), nullable=False),
    sa.Column('source_id', sa.SmallInteger(), nullable=False),
    sa.Column('open', sa.Numeric(precision=38, scale=12), nullable=False),
    sa.Column('high', sa.Numeric(precision=38, scale=12), nullable=False),
    sa.Column('low', sa.Numeric(precision=38, scale=12), nullable=False),
    sa.Column('close', sa.Numeric(precision=38, scale=12), nullable=False),
    sa.Column('volume', sa.Numeric(precision=38, scale=12), nullable=False),
    sa.Column('quote_volume', sa.Numeric(precision=38, scale=12), nullable=True),
    sa.Column('trade_count', sa.Integer(), nullable=True),
    sa.Column('close_adj', sa.Numeric(precision=38, scale=12), nullable=True),
    sa.Column('is_final', sa.Boolean(), nullable=False),
    sa.Column('ingested_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('quality_score', sa.SmallInteger(), nullable=False),
    sa.Column('validation_status', sa.Enum('valid', 'suspicious', 'stale', 'rejected', name='validation_status'), nullable=False),
    sa.PrimaryKeyConstraint('asset_id', 'timeframe', 'ts', 'source_id', name='pk_ohlcv')
    )
    op.create_index('ix_ohlcv_asset_id_timeframe_ts', 'ohlcv', ['asset_id', 'timeframe', 'ts'], unique=False)
    op.create_index('ix_ohlcv_ts', 'ohlcv', ['ts'], unique=False)
    op.create_table('order_book_snapshots',
    sa.Column('asset_id', sa.BigInteger(), nullable=False),
    sa.Column('ts', sa.DateTime(timezone=True), nullable=False),
    sa.Column('source_id', sa.SmallInteger(), nullable=False),
    sa.Column('bids', postgresql.JSONB(astext_type=Text()).with_variant(sa.JSON(), 'sqlite'), nullable=False),
    sa.Column('asks', postgresql.JSONB(astext_type=Text()).with_variant(sa.JSON(), 'sqlite'), nullable=False),
    sa.Column('depth_levels', sa.SmallInteger(), nullable=False),
    sa.Column('imbalance', sa.Numeric(precision=10, scale=6), nullable=True),
    sa.Column('spread', sa.Numeric(precision=38, scale=12), nullable=True),
    sa.PrimaryKeyConstraint('asset_id', 'ts', 'source_id', name='pk_order_book_snapshots')
    )
    op.create_index('ix_order_book_snapshots_asset_id_ts', 'order_book_snapshots', ['asset_id', 'ts'], unique=False)
    op.create_table('paper_accounts',
    sa.Column('name', sa.String(length=64), nullable=False),
    sa.Column('base_currency', sa.String(length=16), nullable=False),
    sa.Column('initial_balance', sa.Numeric(precision=38, scale=12), nullable=False),
    sa.Column('current_balance', sa.Numeric(precision=38, scale=12), nullable=False),
    sa.Column('equity', sa.Numeric(precision=38, scale=12), nullable=False),
    sa.Column('scoring_profile_id', sa.Integer(), nullable=True),
    sa.Column('model_version_id', sa.Integer(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('config', postgresql.JSONB(astext_type=Text()).with_variant(sa.JSON(), 'sqlite'), nullable=False),
    sa.Column('id', sa.BigInteger().with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_paper_accounts')),
    sa.UniqueConstraint('name', name=op.f('uq_paper_accounts_name'))
    )
    op.create_table('predictions',
    sa.Column('asset_id', sa.BigInteger(), nullable=False),
    sa.Column('timeframe', sa.Enum('1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w', name='timeframe'), nullable=False),
    sa.Column('ts', sa.DateTime(timezone=True), nullable=False),
    sa.Column('model_version_id', sa.Integer(), nullable=False),
    sa.Column('scoring_profile_id', sa.Integer(), nullable=True),
    sa.Column('horizon', sa.Interval(), nullable=False),
    sa.Column('predicted_direction', sa.Enum('up', 'down', 'neutral', name='predicted_direction'), nullable=False),
    sa.Column('predicted_prob', sa.Numeric(precision=10, scale=6), nullable=False),
    sa.Column('predicted_move_atr', sa.Numeric(precision=10, scale=6), nullable=True),
    sa.Column('feature_set_version', sa.String(length=32), nullable=False),
    sa.Column('resolve_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('actual_return', sa.Numeric(precision=10, scale=6), nullable=True),
    sa.Column('actual_direction', sa.Enum('up', 'down', 'neutral', name='predicted_direction'), nullable=True),
    sa.Column('is_correct', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('asset_id', 'timeframe', 'ts', 'model_version_id', name='pk_predictions')
    )
    op.create_index('ix_predictions_asset_id_ts', 'predictions', ['asset_id', 'ts'], unique=False)
    op.create_index('ix_predictions_resolve_at_resolved_at', 'predictions', ['resolve_at', 'resolved_at'], unique=False)
    op.create_table('risk_metrics',
    sa.Column('asset_id', sa.BigInteger(), nullable=False),
    sa.Column('timeframe', sa.Enum('1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w', name='timeframe'), nullable=False),
    sa.Column('ts', sa.DateTime(timezone=True), nullable=False),
    sa.Column('atr', sa.Numeric(precision=38, scale=12), nullable=True),
    sa.Column('atr_pct', sa.Numeric(precision=10, scale=6), nullable=True),
    sa.Column('realized_vol_7d', sa.Numeric(precision=10, scale=6), nullable=True),
    sa.Column('realized_vol_30d', sa.Numeric(precision=10, scale=6), nullable=True),
    sa.Column('beta_vs_market', sa.Numeric(precision=10, scale=6), nullable=True),
    sa.Column('max_drawdown_30d', sa.Numeric(precision=10, scale=6), nullable=True),
    sa.Column('max_drawdown_90d', sa.Numeric(precision=10, scale=6), nullable=True),
    sa.Column('var_95', sa.Numeric(precision=10, scale=6), nullable=True),
    sa.Column('cvar_95', sa.Numeric(precision=10, scale=6), nullable=True),
    sa.Column('liquidity_score', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.Column('gap_risk', sa.Numeric(precision=10, scale=6), nullable=True),
    sa.Column('halt_risk', sa.Numeric(precision=10, scale=6), nullable=True),
    sa.Column('risk_score', sa.Numeric(precision=5, scale=2), nullable=False),
    sa.PrimaryKeyConstraint('asset_id', 'timeframe', 'ts', name='pk_risk_metrics')
    )
    op.create_index('ix_risk_metrics_asset_id_ts', 'risk_metrics', ['asset_id', 'ts'], unique=False)
    op.create_table('scoring_profiles',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('name', sa.String(length=64), nullable=False),
    sa.Column('market_type', sa.String(length=32), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('weights', postgresql.JSONB(astext_type=Text()).with_variant(sa.JSON(), 'sqlite'), nullable=False),
    sa.Column('thresholds', postgresql.JSONB(astext_type=Text()).with_variant(sa.JSON(), 'sqlite'), nullable=False),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_scoring_profiles')),
    sa.UniqueConstraint('name', name=op.f('uq_scoring_profiles_name'))
    )
    op.create_table('sectors',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('code', sa.String(length=32), nullable=False),
    sa.Column('name_fa', sa.String(length=128), nullable=False),
    sa.Column('name_en', sa.String(length=128), nullable=True),
    sa.Column('parent_id', sa.Integer(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['parent_id'], ['sectors.id'], name=op.f('fk_sectors_parent_id_sectors')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_sectors')),
    sa.UniqueConstraint('code', name=op.f('uq_sectors_code'))
    )
    op.create_table('sentiments',
    sa.Column('subject_type', sa.Enum('article', 'event', 'asset_aggregate', name='sentiment_subject'), nullable=False),
    sa.Column('subject_id', sa.BigInteger(), nullable=False),
    sa.Column('label', sa.Enum('positive', 'negative', 'neutral', name='sentiment_label'), nullable=False),
    sa.Column('score', sa.Numeric(precision=10, scale=6), nullable=False),
    sa.Column('intensity', sa.Enum('low', 'medium', 'high', 'critical', name='sentiment_intensity'), nullable=False),
    sa.Column('impact_score', sa.Numeric(precision=5, scale=2), nullable=True),
    sa.Column('confidence', sa.Numeric(precision=10, scale=6), nullable=False),
    sa.Column('model', sa.String(length=64), nullable=False),
    sa.Column('model_version', sa.String(length=32), nullable=True),
    sa.Column('computed_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('id', sa.BigInteger().with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_sentiments'))
    )
    op.create_index('ix_sentiments_computed_at', 'sentiments', ['computed_at'], unique=False)
    op.create_index('ix_sentiments_subject_type_subject_id', 'sentiments', ['subject_type', 'subject_id'], unique=False)
    op.create_table('support_resistance',
    sa.Column('asset_id', sa.BigInteger(), nullable=False),
    sa.Column('timeframe', sa.Enum('1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w', name='timeframe'), nullable=False),
    sa.Column('computed_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('level', sa.Numeric(precision=38, scale=12), nullable=False),
    sa.Column('kind', sa.String(length=16), nullable=False),
    sa.Column('strength', sa.Numeric(precision=10, scale=6), nullable=True),
    sa.Column('touches', sa.Integer(), nullable=True),
    sa.Column('method', sa.String(length=32), nullable=False),
    sa.Column('valid_until', sa.DateTime(timezone=True), nullable=True),
    sa.Column('id', sa.BigInteger().with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_support_resistance'))
    )
    op.create_index('ix_support_resistance_asset_id_timeframe_computed_at', 'support_resistance', ['asset_id', 'timeframe', 'computed_at'], unique=False)
    op.create_table('system_logs',
    sa.Column('ts', sa.DateTime(timezone=True), nullable=False),
    sa.Column('level', sa.String(length=16), nullable=False),
    sa.Column('logger', sa.String(length=64), nullable=False),
    sa.Column('event_code', sa.String(length=64), nullable=False),
    sa.Column('message', sa.Text(), nullable=False),
    sa.Column('context', postgresql.JSONB(astext_type=Text()).with_variant(sa.JSON(), 'sqlite'), nullable=True),
    sa.Column('trace_id', sa.String(length=64), nullable=True),
    sa.Column('id', sa.BigInteger().with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_system_logs'))
    )
    op.create_index('ix_system_logs_event_code', 'system_logs', ['event_code'], unique=False)
    op.create_index('ix_system_logs_ts_level', 'system_logs', ['ts', 'level'], unique=False)
    op.create_table('technical_indicators',
    sa.Column('asset_id', sa.BigInteger(), nullable=False),
    sa.Column('timeframe', sa.Enum('1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w', name='timeframe'), nullable=False),
    sa.Column('ts', sa.DateTime(timezone=True), nullable=False),
    sa.Column('indicator_code', sa.String(length=32), nullable=False),
    sa.Column('params_hash', sa.String(length=16), nullable=False),
    sa.Column('value', sa.Numeric(precision=38, scale=12), nullable=True),
    sa.Column('values', postgresql.JSONB(astext_type=Text()).with_variant(sa.JSON(), 'sqlite'), nullable=True),
    sa.Column('engine_version', sa.String(length=32), nullable=False),
    sa.Column('computed_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('asset_id', 'timeframe', 'ts', 'indicator_code', 'params_hash', name='pk_technical_indicators')
    )
    op.create_index('ix_technical_indicators_asset_id_timeframe_indicator_code_ts', 'technical_indicators', ['asset_id', 'timeframe', 'indicator_code', 'ts'], unique=False)
    op.create_index('ix_technical_indicators_ts', 'technical_indicators', ['ts'], unique=False)
    op.create_table('trades',
    sa.Column('asset_id', sa.BigInteger(), nullable=False),
    sa.Column('ts', sa.DateTime(timezone=True), nullable=False),
    sa.Column('trade_id', sa.String(length=64), nullable=False),
    sa.Column('source_id', sa.SmallInteger(), nullable=False),
    sa.Column('price', sa.Numeric(precision=38, scale=12), nullable=False),
    sa.Column('qty', sa.Numeric(precision=38, scale=12), nullable=False),
    sa.Column('side', sa.Enum('buy', 'sell', name='order_side'), nullable=True),
    sa.PrimaryKeyConstraint('asset_id', 'ts', 'trade_id', 'source_id', name='pk_trades')
    )
    op.create_index('ix_trades_asset_id_ts', 'trades', ['asset_id', 'ts'], unique=False)
    op.create_table('user_settings',
    sa.Column('key', sa.String(length=64), nullable=False),
    sa.Column('value', postgresql.JSONB(astext_type=Text()).with_variant(sa.JSON(), 'sqlite'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.PrimaryKeyConstraint('key', name=op.f('pk_user_settings'))
    )
    op.create_table('assets',
    sa.Column('exchange_id', sa.SmallInteger(), nullable=False),
    sa.Column('symbol', sa.String(length=64), nullable=False),
    sa.Column('name_fa', sa.String(length=256), nullable=True),
    sa.Column('name_en', sa.String(length=256), nullable=True),
    sa.Column('asset_class', sa.Enum('spot_crypto', 'perp', 'stock', 'etf', 'index', 'commodity_fund', name='asset_class'), nullable=False),
    sa.Column('isin', sa.String(length=32), nullable=True),
    sa.Column('tsetmc_ins_code', sa.String(length=32), nullable=True),
    sa.Column('sector_id', sa.Integer(), nullable=True),
    sa.Column('base_currency', sa.String(length=16), nullable=True),
    sa.Column('quote_currency', sa.String(length=16), nullable=True),
    sa.Column('tick_size', sa.Numeric(precision=38, scale=12), nullable=True),
    sa.Column('lot_size', sa.Numeric(precision=38, scale=12), nullable=True),
    sa.Column('listed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('delisted_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('status', sa.Enum('active', 'suspended', 'delisted', name='asset_status'), nullable=False),
    sa.Column('is_tracked', sa.Boolean(), nullable=False),
    sa.Column('meta', postgresql.JSONB(astext_type=Text()).with_variant(sa.JSON(), 'sqlite'), nullable=True),
    sa.Column('id', sa.BigInteger().with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['exchange_id'], ['exchanges.id'], name=op.f('fk_assets_exchange_id_exchanges')),
    sa.ForeignKeyConstraint(['sector_id'], ['sectors.id'], name=op.f('fk_assets_sector_id_sectors')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_assets')),
    sa.UniqueConstraint('exchange_id', 'symbol', name='uq_assets_exchange_id_symbol'),
    sa.UniqueConstraint('tsetmc_ins_code', name=op.f('uq_assets_tsetmc_ins_code'))
    )
    op.create_index(op.f('ix_assets_exchange_id'), 'assets', ['exchange_id'], unique=False)
    op.create_index(op.f('ix_assets_isin'), 'assets', ['isin'], unique=False)
    op.create_index(op.f('ix_assets_sector_id'), 'assets', ['sector_id'], unique=False)
    op.create_index('ix_assets_status_class', 'assets', ['status', 'asset_class'], unique=False)
    op.create_table('backtest_trades',
    sa.Column('backtest_id', sa.BigInteger(), nullable=False),
    sa.Column('asset_id', sa.BigInteger(), nullable=False),
    sa.Column('side', sa.Enum('buy', 'sell', name='order_side'), nullable=False),
    sa.Column('entry_ts', sa.DateTime(timezone=True), nullable=False),
    sa.Column('entry_price', sa.Numeric(precision=38, scale=12), nullable=False),
    sa.Column('exit_ts', sa.DateTime(timezone=True), nullable=True),
    sa.Column('exit_price', sa.Numeric(precision=38, scale=12), nullable=True),
    sa.Column('qty', sa.Numeric(precision=38, scale=12), nullable=False),
    sa.Column('fees', sa.Numeric(precision=38, scale=12), nullable=False),
    sa.Column('pnl', sa.Numeric(precision=38, scale=12), nullable=True),
    sa.Column('pnl_pct', sa.Numeric(precision=10, scale=6), nullable=True),
    sa.Column('r_multiple', sa.Numeric(precision=10, scale=6), nullable=True),
    sa.Column('exit_reason', sa.Enum('tp1', 'tp2', 'sl', 'time', 'signal_flip', 'manual', name='exit_reason'), nullable=True),
    sa.Column('mae', sa.Numeric(precision=10, scale=6), nullable=True),
    sa.Column('mfe', sa.Numeric(precision=10, scale=6), nullable=True),
    sa.Column('bars_held', sa.Integer(), nullable=True),
    sa.Column('id', sa.BigInteger().with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.ForeignKeyConstraint(['backtest_id'], ['backtests.id'], name=op.f('fk_backtest_trades_backtest_id_backtests'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_backtest_trades'))
    )
    op.create_index('ix_backtest_trades_backtest_id_entry_ts', 'backtest_trades', ['backtest_id', 'entry_ts'], unique=False)
    op.create_table('data_quarantine',
    sa.Column('source_id', sa.SmallInteger(), nullable=False),
    sa.Column('table_name', sa.String(length=64), nullable=False),
    sa.Column('asset_id', sa.BigInteger(), nullable=True),
    sa.Column('reason_code', sa.String(length=64), nullable=False),
    sa.Column('reason_detail', sa.Text(), nullable=True),
    sa.Column('payload', postgresql.JSONB(astext_type=Text()).with_variant(sa.JSON(), 'sqlite'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('id', sa.BigInteger().with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.ForeignKeyConstraint(['source_id'], ['data_sources.id'], name=op.f('fk_data_quarantine_source_id_data_sources')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_data_quarantine'))
    )
    op.create_index('ix_data_quarantine_source_id_created_at', 'data_quarantine', ['source_id', 'created_at'], unique=False)
    op.create_table('data_source_health',
    sa.Column('source_id', sa.SmallInteger(), nullable=False),
    sa.Column('checked_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('status', sa.Enum('up', 'degraded', 'down', 'unknown', name='source_status'), nullable=False),
    sa.Column('latency_ms', sa.Integer(), nullable=True),
    sa.Column('error_code', sa.String(length=64), nullable=True),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('consecutive_failures', sa.Integer(), nullable=False),
    sa.Column('id', sa.BigInteger().with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.ForeignKeyConstraint(['source_id'], ['data_sources.id'], name=op.f('fk_data_source_health_source_id_data_sources')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_data_source_health'))
    )
    op.create_index('ix_data_source_health_source_id_checked_at', 'data_source_health', ['source_id', 'checked_at'], unique=False)
    op.create_table('model_metrics',
    sa.Column('model_version_id', sa.Integer(), nullable=False),
    sa.Column('stage', sa.Enum('train', 'validation', 'backtest', 'paper', 'live', name='evaluation_stage'), nullable=False),
    sa.Column('window_start', sa.DateTime(timezone=True), nullable=True),
    sa.Column('window_end', sa.DateTime(timezone=True), nullable=True),
    sa.Column('metric_code', sa.String(length=32), nullable=False),
    sa.Column('value', sa.Numeric(precision=10, scale=6), nullable=False),
    sa.Column('sample_size', sa.Integer(), nullable=True),
    sa.Column('computed_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('id', sa.BigInteger().with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.ForeignKeyConstraint(['model_version_id'], ['model_versions.id'], name=op.f('fk_model_metrics_model_version_id_model_versions'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_model_metrics'))
    )
    op.create_index('ix_model_metrics_model_version_id_stage', 'model_metrics', ['model_version_id', 'stage'], unique=False)
    op.create_table('news_articles',
    sa.Column('source_id', sa.SmallInteger(), nullable=False),
    sa.Column('external_id', sa.String(length=128), nullable=True),
    sa.Column('url', sa.Text(), nullable=False),
    sa.Column('url_hash', sa.String(length=64), nullable=False),
    sa.Column('title', sa.Text(), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('body', sa.Text(), nullable=True),
    sa.Column('language', sa.String(length=8), nullable=False),
    sa.Column('author', sa.String(length=128), nullable=True),
    sa.Column('published_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('fetched_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('simhash', sa.BigInteger(), nullable=True),
    sa.Column('event_id', sa.BigInteger(), nullable=True),
    sa.Column('raw', postgresql.JSONB(astext_type=Text()).with_variant(sa.JSON(), 'sqlite'), nullable=True),
    sa.Column('id', sa.BigInteger().with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.ForeignKeyConstraint(['event_id'], ['news_events.id'], name=op.f('fk_news_articles_event_id_news_events'), ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['source_id'], ['data_sources.id'], name=op.f('fk_news_articles_source_id_data_sources')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_news_articles')),
    sa.UniqueConstraint('url_hash', name=op.f('uq_news_articles_url_hash'))
    )
    op.create_index('ix_news_articles_event_id', 'news_articles', ['event_id'], unique=False)
    op.create_index('ix_news_articles_published_at', 'news_articles', ['published_at'], unique=False)
    op.create_index('ix_news_articles_simhash', 'news_articles', ['simhash'], unique=False)
    op.create_table('paper_equity_curve',
    sa.Column('account_id', sa.BigInteger(), nullable=False),
    sa.Column('ts', sa.DateTime(timezone=True), nullable=False),
    sa.Column('equity', sa.Numeric(precision=38, scale=12), nullable=False),
    sa.Column('cash', sa.Numeric(precision=38, scale=12), nullable=False),
    sa.Column('positions_value', sa.Numeric(precision=38, scale=12), nullable=False),
    sa.Column('drawdown', sa.Numeric(precision=10, scale=6), nullable=True),
    sa.Column('open_positions_count', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['account_id'], ['paper_accounts.id'], name=op.f('fk_paper_equity_curve_account_id_paper_accounts'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('account_id', 'ts', name='pk_paper_equity_curve')
    )
    op.create_table('ai_analysis',
    sa.Column('asset_id', sa.BigInteger(), nullable=False),
    sa.Column('timeframe', sa.Enum('1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w', name='timeframe'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('provider', sa.String(length=32), nullable=False),
    sa.Column('model', sa.String(length=64), nullable=False),
    sa.Column('prompt_version', sa.String(length=16), nullable=False),
    sa.Column('input_features', postgresql.JSONB(astext_type=Text()).with_variant(sa.JSON(), 'sqlite'), nullable=False),
    sa.Column('output', postgresql.JSONB(astext_type=Text()).with_variant(sa.JSON(), 'sqlite'), nullable=True),
    sa.Column('summary_fa', sa.Text(), nullable=True),
    sa.Column('contradictions', postgresql.JSONB(astext_type=Text()).with_variant(sa.JSON(), 'sqlite'), nullable=True),
    sa.Column('risks', postgresql.JSONB(astext_type=Text()).with_variant(sa.JSON(), 'sqlite'), nullable=True),
    sa.Column('ai_confidence', sa.Numeric(precision=10, scale=6), nullable=True),
    sa.Column('latency_ms', sa.Integer(), nullable=True),
    sa.Column('tokens_in', sa.Integer(), nullable=True),
    sa.Column('tokens_out', sa.Integer(), nullable=True),
    sa.Column('status', sa.Enum('ok', 'invalid_json', 'timeout', 'refused', 'degraded', 'insufficient_data', name='ai_analysis_status'), nullable=False),
    sa.Column('guardrail_rejections', postgresql.JSONB(astext_type=Text()).with_variant(sa.JSON(), 'sqlite'), nullable=True),
    sa.Column('id', sa.BigInteger().with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.ForeignKeyConstraint(['asset_id'], ['assets.id'], name=op.f('fk_ai_analysis_asset_id_assets')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_ai_analysis'))
    )
    op.create_index('ix_ai_analysis_asset_id_created_at', 'ai_analysis', ['asset_id', 'created_at'], unique=False)
    op.create_table('alert_rules',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('name', sa.String(length=128), nullable=False),
    sa.Column('scope', sa.Enum('asset', 'market', 'global', name='alert_scope'), nullable=False),
    sa.Column('asset_id', sa.BigInteger(), nullable=True),
    sa.Column('condition_type', sa.Enum('breakout', 'volume_spike', 'rsi_overbought', 'rsi_oversold', 'macd_cross', 'news_impact', 'price_move', 'risk_change', 'ai_score_change', name='alert_condition_type'), nullable=False),
    sa.Column('params', postgresql.JSONB(astext_type=Text()).with_variant(sa.JSON(), 'sqlite'), nullable=False),
    sa.Column('timeframe', sa.Enum('1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w', name='timeframe'), nullable=True),
    sa.Column('channels', postgresql.JSONB(astext_type=Text()).with_variant(sa.JSON(), 'sqlite'), nullable=False),
    sa.Column('cooldown_seconds', sa.Integer(), nullable=False),
    sa.Column('is_enabled', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['asset_id'], ['assets.id'], name=op.f('fk_alert_rules_asset_id_assets')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_alert_rules'))
    )
    op.create_table('corporate_actions',
    sa.Column('asset_id', sa.BigInteger(), nullable=False),
    sa.Column('type', sa.Enum('split', 'capital_increase', 'dividend', 'symbol_change', name='corporate_action_type'), nullable=False),
    sa.Column('ex_date', sa.DateTime(timezone=True), nullable=False),
    sa.Column('ratio', sa.Numeric(precision=38, scale=12), nullable=False),
    sa.Column('details', postgresql.JSONB(astext_type=Text()).with_variant(sa.JSON(), 'sqlite'), nullable=True),
    sa.Column('source_id', sa.SmallInteger(), nullable=True),
    sa.Column('id', sa.BigInteger().with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['asset_id'], ['assets.id'], name=op.f('fk_corporate_actions_asset_id_assets'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['source_id'], ['data_sources.id'], name=op.f('fk_corporate_actions_source_id_data_sources')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_corporate_actions')),
    sa.UniqueConstraint('asset_id', 'type', 'ex_date', name='uq_corporate_actions_asset_id_type_ex_date')
    )
    op.create_index('ix_corporate_actions_asset_id_ex_date', 'corporate_actions', ['asset_id', 'ex_date'], unique=False)
    op.create_table('news_event_assets',
    sa.Column('event_id', sa.BigInteger(), nullable=False),
    sa.Column('asset_id', sa.BigInteger(), nullable=False),
    sa.Column('relevance', sa.Numeric(precision=10, scale=6), nullable=False),
    sa.Column('extraction_method', sa.String(length=16), nullable=False),
    sa.ForeignKeyConstraint(['asset_id'], ['assets.id'], name=op.f('fk_news_event_assets_asset_id_assets'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['event_id'], ['news_events.id'], name=op.f('fk_news_event_assets_event_id_news_events'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('event_id', 'asset_id', name='pk_news_event_assets')
    )
    op.create_index('ix_news_event_assets_asset_id', 'news_event_assets', ['asset_id'], unique=False)
    op.create_table('signals',
    sa.Column('asset_id', sa.BigInteger(), nullable=False),
    sa.Column('timeframe', sa.Enum('1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w', name='timeframe'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('direction', sa.Enum('long', 'short', 'none', name='signal_direction'), nullable=False),
    sa.Column('entry', sa.Numeric(precision=38, scale=12), nullable=False),
    sa.Column('stop_loss', sa.Numeric(precision=38, scale=12), nullable=False),
    sa.Column('take_profit_1', sa.Numeric(precision=38, scale=12), nullable=False),
    sa.Column('take_profit_2', sa.Numeric(precision=38, scale=12), nullable=True),
    sa.Column('rr_ratio', sa.Numeric(precision=10, scale=6), nullable=False),
    sa.Column('position_risk_pct', sa.Numeric(precision=10, scale=6), nullable=False),
    sa.Column('opportunity_score', sa.Numeric(precision=5, scale=2), nullable=False),
    sa.Column('risk_score', sa.Numeric(precision=5, scale=2), nullable=False),
    sa.Column('confidence', sa.Numeric(precision=10, scale=6), nullable=False),
    sa.Column('recommendation', sa.Enum('BUY_CANDIDATE', 'WATCH', 'HOLD', 'WAIT', 'AVOID', 'RESEARCH_ONLY', 'NO_ACTION', name='recommendation'), nullable=False),
    sa.Column('reasons', postgresql.JSONB(astext_type=Text()).with_variant(sa.JSON(), 'sqlite'), nullable=False),
    sa.Column('rationale', sa.Text(), nullable=True),
    sa.Column('ai_analysis_id', sa.BigInteger(), nullable=True),
    sa.Column('model_version_id', sa.Integer(), nullable=True),
    sa.Column('scoring_profile_id', sa.Integer(), nullable=False),
    sa.Column('status', sa.Enum('active', 'expired', 'invalidated', 'hit_tp1', 'hit_tp2', 'hit_sl', name='signal_status'), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('outcome', postgresql.JSONB(astext_type=Text()).with_variant(sa.JSON(), 'sqlite'), nullable=True),
    sa.Column('id', sa.BigInteger().with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.ForeignKeyConstraint(['asset_id'], ['assets.id'], name=op.f('fk_signals_asset_id_assets')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_signals'))
    )
    op.create_index('ix_signals_asset_id_created_at', 'signals', ['asset_id', 'created_at'], unique=False)
    op.create_index('ix_signals_status_created_at', 'signals', ['status', 'created_at'], unique=False)
    op.create_table('symbol_aliases',
    sa.Column('asset_id', sa.BigInteger(), nullable=False),
    sa.Column('source_id', sa.SmallInteger(), nullable=False),
    sa.Column('external_symbol', sa.String(length=128), nullable=False),
    sa.Column('external_id', sa.String(length=128), nullable=True),
    sa.Column('id', sa.BigInteger().with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.ForeignKeyConstraint(['asset_id'], ['assets.id'], name=op.f('fk_symbol_aliases_asset_id_assets'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['source_id'], ['data_sources.id'], name=op.f('fk_symbol_aliases_source_id_data_sources')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_symbol_aliases')),
    sa.UniqueConstraint('source_id', 'external_symbol', name='uq_symbol_aliases_source_id_external_symbol')
    )
    op.create_index(op.f('ix_symbol_aliases_asset_id'), 'symbol_aliases', ['asset_id'], unique=False)
    op.create_table('user_drawings',
    sa.Column('asset_id', sa.BigInteger(), nullable=False),
    sa.Column('timeframe', sa.Enum('1m', '5m', '15m', '30m', '1h', '4h', '1d', '1w', name='timeframe'), nullable=False),
    sa.Column('kind', sa.String(length=32), nullable=False),
    sa.Column('geometry', postgresql.JSONB(astext_type=Text()).with_variant(sa.JSON(), 'sqlite'), nullable=False),
    sa.Column('style', postgresql.JSONB(astext_type=Text()).with_variant(sa.JSON(), 'sqlite'), nullable=True),
    sa.Column('id', sa.BigInteger().with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['asset_id'], ['assets.id'], name=op.f('fk_user_drawings_asset_id_assets')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_user_drawings'))
    )
    op.create_index('ix_user_drawings_asset_id_timeframe', 'user_drawings', ['asset_id', 'timeframe'], unique=False)
    op.create_table('alert_events',
    sa.Column('rule_id', sa.Integer(), nullable=False),
    sa.Column('asset_id', sa.BigInteger(), nullable=True),
    sa.Column('triggered_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('payload', postgresql.JSONB(astext_type=Text()).with_variant(sa.JSON(), 'sqlite'), nullable=False),
    sa.Column('delivery_status', postgresql.JSONB(astext_type=Text()).with_variant(sa.JSON(), 'sqlite'), nullable=True),
    sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('id', sa.BigInteger().with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.ForeignKeyConstraint(['rule_id'], ['alert_rules.id'], name=op.f('fk_alert_events_rule_id_alert_rules'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_alert_events'))
    )
    op.create_index('ix_alert_events_triggered_at', 'alert_events', ['triggered_at'], unique=False)
    op.create_table('paper_orders',
    sa.Column('account_id', sa.BigInteger(), nullable=False),
    sa.Column('signal_id', sa.BigInteger(), nullable=True),
    sa.Column('asset_id', sa.BigInteger(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('side', sa.Enum('buy', 'sell', name='order_side'), nullable=False),
    sa.Column('type', sa.Enum('market', 'limit', 'stop', name='order_type'), nullable=False),
    sa.Column('qty', sa.Numeric(precision=38, scale=12), nullable=False),
    sa.Column('requested_price', sa.Numeric(precision=38, scale=12), nullable=True),
    sa.Column('fill_price', sa.Numeric(precision=38, scale=12), nullable=True),
    sa.Column('fill_ts', sa.DateTime(timezone=True), nullable=True),
    sa.Column('status', sa.Enum('pending', 'filled', 'partially_filled', 'rejected', 'canceled', name='order_status'), nullable=False),
    sa.Column('fees', sa.Numeric(precision=38, scale=12), nullable=False),
    sa.Column('slippage_model', sa.String(length=32), nullable=True),
    sa.Column('reject_reason', sa.Text(), nullable=True),
    sa.Column('id', sa.BigInteger().with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.ForeignKeyConstraint(['account_id'], ['paper_accounts.id'], name=op.f('fk_paper_orders_account_id_paper_accounts'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['signal_id'], ['signals.id'], name=op.f('fk_paper_orders_signal_id_signals')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_paper_orders'))
    )
    op.create_index('ix_paper_orders_account_id_created_at', 'paper_orders', ['account_id', 'created_at'], unique=False)
    op.create_table('paper_positions',
    sa.Column('account_id', sa.BigInteger(), nullable=False),
    sa.Column('asset_id', sa.BigInteger(), nullable=False),
    sa.Column('side', sa.Enum('buy', 'sell', name='order_side'), nullable=False),
    sa.Column('qty', sa.Numeric(precision=38, scale=12), nullable=False),
    sa.Column('avg_entry', sa.Numeric(precision=38, scale=12), nullable=False),
    sa.Column('stop_loss', sa.Numeric(precision=38, scale=12), nullable=True),
    sa.Column('take_profit_1', sa.Numeric(precision=38, scale=12), nullable=True),
    sa.Column('take_profit_2', sa.Numeric(precision=38, scale=12), nullable=True),
    sa.Column('opened_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('realized_pnl', sa.Numeric(precision=38, scale=12), nullable=False),
    sa.Column('unrealized_pnl', sa.Numeric(precision=38, scale=12), nullable=True),
    sa.Column('status', sa.Enum('open', 'closed', 'frozen', name='position_status'), nullable=False),
    sa.Column('linked_signal_id', sa.BigInteger(), nullable=True),
    sa.Column('exit_reason', sa.Enum('tp1', 'tp2', 'sl', 'time', 'signal_flip', 'manual', name='exit_reason'), nullable=True),
    sa.Column('id', sa.BigInteger().with_variant(sa.Integer(), 'sqlite'), autoincrement=True, nullable=False),
    sa.ForeignKeyConstraint(['account_id'], ['paper_accounts.id'], name=op.f('fk_paper_positions_account_id_paper_accounts'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['linked_signal_id'], ['signals.id'], name=op.f('fk_paper_positions_linked_signal_id_signals')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_paper_positions'))
    )
    op.create_index('ix_paper_positions_account_id_status', 'paper_positions', ['account_id', 'status'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_paper_positions_account_id_status', table_name='paper_positions')
    op.drop_table('paper_positions')
    op.drop_index('ix_paper_orders_account_id_created_at', table_name='paper_orders')
    op.drop_table('paper_orders')
    op.drop_index('ix_alert_events_triggered_at', table_name='alert_events')
    op.drop_table('alert_events')
    op.drop_index('ix_user_drawings_asset_id_timeframe', table_name='user_drawings')
    op.drop_table('user_drawings')
    op.drop_index(op.f('ix_symbol_aliases_asset_id'), table_name='symbol_aliases')
    op.drop_table('symbol_aliases')
    op.drop_index('ix_signals_status_created_at', table_name='signals')
    op.drop_index('ix_signals_asset_id_created_at', table_name='signals')
    op.drop_table('signals')
    op.drop_index('ix_news_event_assets_asset_id', table_name='news_event_assets')
    op.drop_table('news_event_assets')
    op.drop_index('ix_corporate_actions_asset_id_ex_date', table_name='corporate_actions')
    op.drop_table('corporate_actions')
    op.drop_table('alert_rules')
    op.drop_index('ix_ai_analysis_asset_id_created_at', table_name='ai_analysis')
    op.drop_table('ai_analysis')
    op.drop_table('paper_equity_curve')
    op.drop_index('ix_news_articles_simhash', table_name='news_articles')
    op.drop_index('ix_news_articles_published_at', table_name='news_articles')
    op.drop_index('ix_news_articles_event_id', table_name='news_articles')
    op.drop_table('news_articles')
    op.drop_index('ix_model_metrics_model_version_id_stage', table_name='model_metrics')
    op.drop_table('model_metrics')
    op.drop_index('ix_data_source_health_source_id_checked_at', table_name='data_source_health')
    op.drop_table('data_source_health')
    op.drop_index('ix_data_quarantine_source_id_created_at', table_name='data_quarantine')
    op.drop_table('data_quarantine')
    op.drop_index('ix_backtest_trades_backtest_id_entry_ts', table_name='backtest_trades')
    op.drop_table('backtest_trades')
    op.drop_index('ix_assets_status_class', table_name='assets')
    op.drop_index(op.f('ix_assets_sector_id'), table_name='assets')
    op.drop_index(op.f('ix_assets_isin'), table_name='assets')
    op.drop_index(op.f('ix_assets_exchange_id'), table_name='assets')
    op.drop_table('assets')
    op.drop_table('user_settings')
    op.drop_index('ix_trades_asset_id_ts', table_name='trades')
    op.drop_table('trades')
    op.drop_index('ix_technical_indicators_ts', table_name='technical_indicators')
    op.drop_index('ix_technical_indicators_asset_id_timeframe_indicator_code_ts', table_name='technical_indicators')
    op.drop_table('technical_indicators')
    op.drop_index('ix_system_logs_ts_level', table_name='system_logs')
    op.drop_index('ix_system_logs_event_code', table_name='system_logs')
    op.drop_table('system_logs')
    op.drop_index('ix_support_resistance_asset_id_timeframe_computed_at', table_name='support_resistance')
    op.drop_table('support_resistance')
    op.drop_index('ix_sentiments_subject_type_subject_id', table_name='sentiments')
    op.drop_index('ix_sentiments_computed_at', table_name='sentiments')
    op.drop_table('sentiments')
    op.drop_table('sectors')
    op.drop_table('scoring_profiles')
    op.drop_index('ix_risk_metrics_asset_id_ts', table_name='risk_metrics')
    op.drop_table('risk_metrics')
    op.drop_index('ix_predictions_resolve_at_resolved_at', table_name='predictions')
    op.drop_index('ix_predictions_asset_id_ts', table_name='predictions')
    op.drop_table('predictions')
    op.drop_table('paper_accounts')
    op.drop_index('ix_order_book_snapshots_asset_id_ts', table_name='order_book_snapshots')
    op.drop_table('order_book_snapshots')
    op.drop_index('ix_ohlcv_ts', table_name='ohlcv')
    op.drop_index('ix_ohlcv_asset_id_timeframe_ts', table_name='ohlcv')
    op.drop_table('ohlcv')
    op.drop_index('ix_news_events_first_seen_at', table_name='news_events')
    op.drop_index('ix_news_events_category_importance', table_name='news_events')
    op.drop_table('news_events')
    op.drop_table('model_versions')
    op.drop_index('ix_market_regimes_scope_ts', table_name='market_regimes')
    op.drop_table('market_regimes')
    op.drop_index('ix_market_metrics_ts', table_name='market_metrics')
    op.drop_index('ix_market_metrics_asset_id_metric_code_ts', table_name='market_metrics')
    op.drop_table('market_metrics')
    op.drop_index('ix_job_runs_job_name_started_at', table_name='job_runs')
    op.drop_table('job_runs')
    op.drop_index('ix_feature_snapshots_asset_id_timeframe_ts', table_name='feature_snapshots')
    op.drop_table('feature_snapshots')
    op.drop_table('exchanges')
    op.drop_table('data_sources')
    op.drop_index('ix_backtests_status_created_at', table_name='backtests')
    op.drop_table('backtests')
    op.drop_index('ix_asset_scores_ts_final_score', table_name='asset_scores')
    op.drop_index('ix_asset_scores_asset_id_timeframe_ts', table_name='asset_scores')
    op.drop_table('asset_scores')

# ۱۰) Folder Structure

```text
ai-market-intelligence/
├── README.md
├── LICENSE
├── .gitignore                      # .env, *.db, models/, data/, logs/
├── .env.example                    # هیچ مقدار واقعی
├── docker-compose.yml
├── docker-compose.override.yml     # dev
├── Makefile                        # make up / migrate / test / lint / seed
│
├── docs/                           # همین مجموعه اسناد (منبع حقیقت معماری)
│   ├── 00-overview.md … 17-decision-log.md
│   └── adr/                        # Architecture Decision Records
│
├── backend/
│   ├── pyproject.toml              # deps + ruff + mypy + pytest config
│   ├── alembic.ini
│   ├── alembic/versions/
│   └── app/
│       ├── main.py                 # FastAPI app factory
│       ├── worker.py               # ARQ worker entrypoint
│       │
│       ├── api/
│       │   ├── deps.py             # DI: session, services, auth
│       │   ├── errors.py           # ProblemDetail handlers
│       │   └── v1/
│       │       ├── router.py
│       │       ├── assets.py  market.py  signals.py  analysis.py
│       │       ├── news.py    backtests.py  paper.py  alerts.py
│       │       ├── models.py  scoring.py    system.py
│       │       └── ws.py           # WebSocket hub
│       │
│       ├── core/
│       │   ├── config.py           # Pydantic Settings (تنها نقطه خواندن .env)
│       │   ├── logging.py          # structlog + masking
│       │   ├── security.py         # local token, secret handling
│       │   ├── errors.py           # exception hierarchy
│       │   ├── clock.py            # Clock ABC: RealClock / VirtualClock  ← کلید Backtest
│       │   ├── events.py           # Redis Streams producer/consumer
│       │   └── enums.py
│       │
│       ├── domain/                 # ★ Pure — بدون I/O، بدون ORM
│       │   ├── entities.py         # Asset, Candle, Signal, Score, Position
│       │   ├── value_objects.py    # Price, Percent, Timeframe, RiskReward
│       │   └── policies.py         # DecisionPolicy  ← تصمیم نهایی اینجاست
│       │
│       ├── models/                 # SQLAlchemy ORM
│       │   ├── base.py  asset.py  market.py  indicator.py  news.py
│       │   ├── scoring.py  ml.py  backtest.py  paper.py  system.py
│       │
│       ├── schemas/                # Pydantic (API DTOs)
│       │   ├── asset.py  market.py  analysis.py  signal.py  news.py
│       │   ├── backtest.py  paper.py  ai.py  ws.py
│       │
│       ├── database/
│       │   ├── session.py
│       │   ├── timescale.py        # hypertable / CAGG / compression helpers
│       │   └── repositories/
│       │       ├── base.py  ohlcv.py  indicator.py  news.py
│       │       ├── score.py  signal.py  prediction.py  paper.py
│       │
│       ├── providers/              # Adapters — قابل تعویض
│       │   ├── base.py             # ABCs: MarketDataProvider, NewsProvider, ...
│       │   ├── registry.py         # capability-based routing + fallback chain
│       │   ├── rate_limit.py       # token bucket (Redis)
│       │   ├── resilience.py       # retry / backoff / circuit breaker
│       │   ├── crypto/             # binance.py  coingecko.py
│       │   ├── iran/               # tsetmc.py  brsapi.py  symbols.py
│       │   ├── news/               # rss.py  cryptopanic.py  iran_news.py
│       │   └── mock/               # ⚠ TEST ONLY — گارد محیط دارد
│       │
│       ├── collectors/
│       │   ├── scheduler.py        # تعریف job ها + market calendar
│       │   ├── ohlcv_collector.py  realtime_collector.py
│       │   ├── derivatives_collector.py  iran_market_collector.py
│       │   ├── news_collector.py   backfill.py  gap_filler.py
│       │   ├── validation.py       # قواعد بخش ۵.۵
│       │   └── normalization.py    # UTC, symbols, adjusted prices
│       │
│       ├── indicators/             # ★ Pure
│       │   ├── engine.py           # Facade: compute(name, df, params)
│       │   ├── backends/           # pandas_ta.py  talib.py  native.py
│       │   ├── trend.py  momentum.py  volatility.py  volume.py
│       │   ├── levels.py           # support/resistance, breakout
│       │   └── registry.py         # نام → تابع + پارامترهای پیش‌فرض
│       │
│       ├── regime/                 # ★ Pure
│       │   ├── detector.py  crypto_regime.py  iran_regime.py  sector_regime.py
│       │
│       ├── features/
│       │   ├── builder.py          # ← تنها سازنده FeaturePayload (Live + Backtest)
│       │   ├── feature_sets.py     # نسخه‌دار: features.v3
│       │   └── selection.py
│       │
│       ├── ml/
│       │   ├── datasets.py         # triple-barrier labeling
│       │   ├── splits.py           # walk-forward, purge, embargo
│       │   ├── pipelines.py  train.py  evaluate.py  calibration.py
│       │   ├── registry.py         # model_versions lifecycle
│       │   ├── adapters/           # sklearn.py  xgboost.py  lightgbm.py(آینده)
│       │   └── drift.py
│       │
│       ├── ai/
│       │   ├── base.py             # AIProvider ABC
│       │   ├── ollama_provider.py  openai_provider.py  null_provider.py
│       │   ├── prompts/            # v1.md  v2.md  v3.md (نسخه‌دار)
│       │   ├── contracts.py        # JSON Schema ورودی/خروجی
│       │   ├── guardrails.py       # numeric grounding, banned phrases
│       │   └── cache.py
│       │
│       ├── news/
│       │   ├── pipeline.py  normalize_fa.py
│       │   ├── dedup/              # simhash.py  embeddings.py  clustering.py
│       │   ├── entity_linking.py
│       │   ├── sentiment/          # lexicon.py  model.py  aggregate.py
│       │   └── impact.py
│       │
│       ├── risk/                   # ★ Pure — بدون ایمپورت از ai/
│       │   ├── engine.py  levels.py       # entry / SL / TP1 / TP2
│       │   ├── sizing.py  metrics.py      # ATR, vol, VaR, drawdown
│       │   └── veto.py                    # قواعد رد قطعی
│       │
│       ├── scoring/                # ★ Pure
│       │   ├── engine.py  components/     # technical, momentum, volume, market,
│       │   │                              # news, sentiment, liquidity, risk, ai
│       │   ├── normalizers.py             # percentile / z-score / cross-sectional
│       │   ├── profiles.py                # بارگذاری وزن‌ها از DB/YAML
│       │   └── ranking.py
│       │
│       ├── backtesting/
│       │   ├── engine.py  data_loader.py  # PointInTimeCursor
│       │   ├── execution.py               # fees, slippage, iran queue/limits
│       │   ├── portfolio.py  metrics.py  walk_forward.py  reports.py
│       │
│       ├── paper_trading/
│       │   ├── engine.py  account.py  orders.py  positions.py
│       │   ├── execution.py  performance.py
│       │
│       ├── alerts/
│       │   ├── rules.py  evaluator.py
│       │   └── channels/           # desktop.py  telegram.py(آینده)  email.py(آینده)
│       │
│       ├── services/               # Orchestration
│       │   ├── asset_service.py  market_service.py  analysis_service.py
│       │   ├── scoring_service.py  signal_service.py  news_service.py
│       │   ├── backtest_service.py  paper_service.py  alert_service.py
│       │
│       ├── tasks/                  # تعریف jobهای ARQ
│       │   ├── collect.py  analyze.py  news.py  ai.py
│       │   ├── ml.py  resolve_predictions.py  maintenance.py
│       │
│       └── utils/
│           ├── time.py             # UTC, jalali, market calendar
│           ├── decimal.py  pandas_helpers.py  hashing.py
│
├── frontend/
│   ├── package.json  vite.config.ts  tailwind.config.ts  tsconfig.json
│   ├── electron/
│   │   ├── main.ts                 # window, tray, notifications, backend lifecycle
│   │   ├── preload.ts              # contextBridge (contextIsolation=true)
│   │   └── updater.ts
│   └── src/
│       ├── main.tsx  App.tsx
│       ├── types/api.d.ts          # ← تولید خودکار از OpenAPI
│       ├── services/               # api.ts  ws.ts  queryClient.ts
│       ├── hooks/                  # useAsset, useScores, useWsTopic, useChartSync
│       ├── store/                  # zustand: filters, chartSettings, ui
│       ├── layouts/                # RTLLayout, Sidebar, TopBar
│       ├── components/ui/          # Button, Table, Badge, ScoreGauge, Skeleton,
│       │                           # DataSourceBanner, Disclaimer
│       ├── charts/
│       │   ├── PriceChart.tsx      # Lightweight Charts
│       │   ├── overlays/           # EMA, Bollinger, S/R lines, Entry/SL/TP
│       │   ├── panes/              # RSIPane, MACDPane, ATRPane, VolumePane
│       │   └── drawing/            # canvas overlay (trendline, hline, rect)
│       ├── features/
│       │   ├── dashboard/  market-overview/  asset-list/  asset-detail/
│       │   ├── ai-panel/   news-panel/  signals/  alerts/
│       │   ├── backtest/   paper-trading/  model-performance/  settings/
│       ├── pages/
│       ├── i18n/                   # fa.ts (+ en.ts آینده)
│       └── styles/                 # tailwind.css, fonts (Vazirmatn)
│
├── docker/
│   ├── backend.Dockerfile  frontend.Dockerfile
│   ├── postgres/init.sql           # CREATE EXTENSION timescaledb, pgvector
│   └── ollama/README.md            # مدل‌ها و pull
│
├── config/
│   ├── scoring.yaml                # وزن‌های پیش‌فرض (seed پروفایل)
│   ├── indicators.yaml             # پارامترهای پیش‌فرض
│   ├── markets.yaml                # تقویم بازار، کارمزد، دامنه نوسان
│   ├── sources.yaml                # منابع، اولویت، rate limit
│   └── promotion_gates.yaml
│
├── scripts/
│   ├── seed_assets.py  backfill_history.py  train_model.py
│   └── check_architecture.py       # تست اجباری قوانین I1..I12
│
└── tests/
    ├── unit/                       # indicators (با مقادیر مرجع), scoring, risk, dedup
    ├── integration/                # DB (testcontainers), providers (VCR cassettes)
    ├── contract/                   # OpenAPI ↔ frontend types
    ├── leakage/                    # تست کندل مسموم، purge/embargo
    ├── e2e/                        # Playwright
    └── fixtures/
```

## چند نکته درباره ساختار

- **`core/clock.py`** ظاهراً کوچک است ولی کلید کل معماری Backtest است: هیچ جای کد `datetime.now()` مستقیم صدا زده نمی‌شود؛ همه از `Clock` تزریق‌شده استفاده می‌کنند. در Backtest، `VirtualClock` جایگزین می‌شود.
- **`domain/policies.py`** جایی است که AI، ML، TA و Risk با هم ترکیب و به توصیه نهایی تبدیل می‌شوند — یک نقطه، قابل تست، قابل ممیزی.
- **`features/builder.py`** تنها سازنده بردار ویژگی است تا Train/Serve Skew ممکن نباشد.
- **`scripts/check_architecture.py`** در CI اجرا می‌شود و قوانین I1..I12 را با تحلیل AST بررسی می‌کند.

# ۴) API Architecture (REST + WebSocket Contract)

## ۴.۱ اصول

- Base: `http://127.0.0.1:8787/api/v1` (نسخه در مسیر).
- همه پاسخ‌ها **Envelope** ندارند (سادگی)، اما همه خطاها قالب یکسان `ProblemDetail` دارند.
- هر پاسخ تحلیلی شامل متادیتای منبع است: `as_of`, `sources[]`, `data_completeness`, `degraded[]`.
  (اجرای بند ۲۹: کاربر همیشه می‌داند داده از کجا و از چه زمانی است.)
- Auth محلی: توکن تصادفی تولیدشده در startup، از Electron به backend پاس داده می‌شود (`X-Local-Token`). بدون آن، پورت محلی هم قابل سوءاستفاده است.
- Pagination: `?limit=&cursor=` (cursor-based برای سری‌زمانی).
- Rate limit داخلی روی endpointهای سنگین (backtest).

### قالب خطا
```json
{
  "type": "https://amip.local/errors/data-unavailable",
  "title": "Market data source unavailable",
  "status": 503,
  "code": "DATA_SOURCE_DOWN",
  "detail": "Binance klines endpoint failed after 5 retries",
  "source": "BINANCE",
  "retry_after_seconds": 30,
  "trace_id": "01J..."
}
```
> هیچ‌گاه به‌جای داده ناموجود، داده ساختگی برنمی‌گردد (بند ۲۹).

---

## ۴.۲ نقشه Endpoint ها

### System
| Method | Path | توضیح |
|---|---|---|
| GET | `/health` | liveness |
| GET | `/health/deep` | وضعیت DB, Redis, Ollama, هر Data Source |
| GET | `/system/config` | پیکربندی عمومی (بدون Secret) |
| GET | `/system/sources` | سلامت و rate-limit باقی‌مانده منابع |
| GET | `/system/jobs` | آخرین اجرای Collectorها |

### Assets
| Method | Path | توضیح |
|---|---|---|
| GET | `/assets` | فهرست با فیلتر: `market`, `sector`, `q`, `status` |
| GET | `/assets/{id}` | جزئیات نماد |
| GET | `/assets/{id}/ohlcv?timeframe=&from=&to=&limit=` | کندل‌ها |
| GET | `/assets/{id}/indicators?timeframe=&codes=rsi,macd,ema20` | اندیکاتورها |
| GET | `/assets/{id}/levels?timeframe=` | Support/Resistance |
| GET | `/assets/{id}/risk?timeframe=` | متریک‌های ریسک |
| GET | `/assets/{id}/analysis?timeframe=` | **پاسخ ترکیبی صفحه تحلیل** (بند ۲۰-۲۲) |
| GET | `/assets/{id}/news?limit=` | اخبار مرتبط |
| GET | `/assets/{id}/predictions?status=` | تاریخچه پیش‌بینی و نتیجه |

### Market & Ranking
| Method | Path | توضیح |
|---|---|---|
| GET | `/market/overview` | خلاصه دو بازار برای Dashboard |
| GET | `/market/regime?scope=global_crypto\|tse_market\|sector:فلزات` | رژیم بازار |
| GET | `/market/iran` | شاخص کل، هم‌وزن، ارزش معاملات، قدرت خریدار |
| GET | `/market/crypto` | BTC.D، Total MCap، Stablecoin، Funding aggregate |
| GET | `/rankings?type=opportunity\|risk\|momentum\|volume\|news_impact&market=&limit=` | Ranking Engine |
| GET | `/screener?filters=...` | فیلترهای ترکیبی بند ۱۹ |

### Signals & AI
| Method | Path | توضیح |
|---|---|---|
| GET | `/signals?status=active&market=&limit=` | سیگنال‌های فعال |
| GET | `/signals/{id}` | جزئیات + Entry/SL/TP/RR |
| GET | `/signals/{id}/explanation` | متن فارسی AI + شکست امتیازها |
| POST | `/ai/analyze` | درخواست تحلیل AI برای یک نماد (async → `task_id`) |
| GET | `/ai/tasks/{task_id}` | نتیجه/وضعیت |
| GET | `/ai/providers` | Providerهای در دسترس و مدل فعال |

### News
| Method | Path | توضیح |
|---|---|---|
| GET | `/news/events?from=&category=&min_importance=` | **رویدادها** (نه مقالات) |
| GET | `/news/events/{id}` | رویداد + همه مقالات خوشه + منابع |
| GET | `/news/feed?market=` | فید UI |

### Backtesting
| Method | Path | توضیح |
|---|---|---|
| POST | `/backtests` | ایجاد (async) |
| GET | `/backtests?status=` | فهرست |
| GET | `/backtests/{id}` | متریک‌ها + equity curve |
| GET | `/backtests/{id}/trades` | معاملات |
| POST | `/backtests/{id}/cancel` | |

### Paper Trading
| Method | Path | توضیح |
|---|---|---|
| GET/POST | `/paper/accounts` | |
| GET | `/paper/accounts/{id}/positions` | |
| GET | `/paper/accounts/{id}/orders` | |
| GET | `/paper/accounts/{id}/performance` | equity curve + متریک‌ها |
| POST | `/paper/accounts/{id}/reset` | |

### Alerts
| Method | Path |
|---|---|
| GET/POST/PATCH/DELETE | `/alerts/rules` |
| GET | `/alerts/events?acknowledged=false` |
| POST | `/alerts/events/{id}/ack` |

### Models
| Method | Path | توضیح |
|---|---|---|
| GET | `/models` | نسخه‌ها و وضعیت |
| GET | `/models/{id}/metrics?stage=` | |
| POST | `/models/{id}/promote` | فقط اگر Gate ها پاس شده باشند (بند ۱۵) |
| GET | `/performance/predictions?window=30d` | Accuracy/F1/WinRate واقعی |

### Scoring Profiles
| Method | Path |
|---|---|
| GET/POST | `/scoring/profiles` |
| POST | `/scoring/profiles/{id}/activate` |
| POST | `/scoring/simulate` | اعمال وزن‌های فرضی روی داده فعلی بدون ذخیره |

---

## ۴.۳ نمونه پاسخ کلیدی — `GET /assets/{id}/analysis`

```json
{
  "asset": { "id": 12, "symbol": "BTCUSDT", "name_fa": "بیت‌کوین", "market": "crypto" },
  "timeframe": "4h",
  "as_of": "2026-09-26T08:00:00Z",
  "price": { "last": "63120.5", "change_24h_pct": -1.24, "volume_24h": "18320000000" },
  "regime": { "scope": "global_crypto", "value": "BULL", "confidence": 0.68 },
  "technical": {
    "trend": "bullish",
    "rsi": 58.4, "macd": { "line": 120.3, "signal": 95.1, "hist": 25.2, "state": "positive" },
    "ema20": 61980.1, "ema50": 60110.4, "ema200": 54300.9,
    "adx": 28.6, "atr": 1240.7, "atr_pct": 1.96,
    "bb": { "upper": 65100, "mid": 62800, "lower": 60500, "width_pct": 7.3 },
    "obv_slope": 0.42, "vwap": 62730.0, "volume_change_pct": 31.4,
    "levels": { "support": [60800, 58200], "resistance": [64500, 67000] }
  },
  "scores": {
    "technical": 82, "momentum": 76, "volume": 81, "market": 73,
    "news": 88, "sentiment": 84, "liquidity": 91, "risk": 32,
    "ai_confidence": 79, "final": 84,
    "profile_id": 3,
    "components": { "technical": { "rsi_sub": 0.6, "trend_sub": 0.9, "weight": 0.25 } }
  },
  "risk": {
    "entry": "63120.5", "stop_loss": "61250.0", "take_profit_1": "66100.0",
    "take_profit_2": "68900.0", "rr_ratio": 1.59, "position_risk_pct": 1.0,
    "max_drawdown_30d_pct": 12.4, "volatility_regime": "normal",
    "veto": null
  },
  "recommendation": "WATCH",
  "ai_analysis": {
    "provider": "ollama", "model": "qwen2.5:14b-instruct", "prompt_version": "v3",
    "summary_fa": "روند کوتاه‌مدت صعودی است...",
    "contradictions": ["RSI نزدیک اشباع خرید در حالی که حجم افزایشی است"],
    "risks": ["نوسان بالاتر از میانگین ۳۰ روزه", "نزدیکی به مقاومت ۶۴٬۵۰۰"],
    "confidence": 0.79,
    "generated_at": "2026-09-26T08:00:12Z"
  },
  "data_quality": { "completeness": 0.96, "stale_fields": [], "degraded": [] },
  "sources": [
    { "code": "BINANCE", "for": ["ohlcv","funding"], "as_of": "2026-09-26T08:00:00Z" },
    { "code": "CRYPTOPANIC", "for": ["news"], "as_of": "2026-09-26T07:41:00Z" }
  ],
  "disclaimer": "تحلیل آماری است، نه پیش‌بینی قطعی."
}
```

---

## ۴.۴ WebSocket Contract — `/ws/stream`

**اتصال:** `ws://127.0.0.1:8787/ws/stream?token=...`

**Client → Server**
```json
{ "op": "subscribe", "topics": ["price:BTCUSDT", "scores:crypto", "signals:*", "alerts:*", "system:health"] }
{ "op": "unsubscribe", "topics": ["price:BTCUSDT"] }
{ "op": "ping", "ts": 1758873600 }
```

**Server → Client**
```json
{ "type": "price.tick",    "topic": "price:BTCUSDT", "ts": "...", "payload": { "last": "63120.5", "bid": "...", "ask": "..." } }
{ "type": "candle.update", "topic": "candle:BTCUSDT:1m", "payload": { "ts": "...", "o": "...", "h": "...", "l": "...", "c": "...", "v": "...", "final": false } }
{ "type": "score.updated", "topic": "scores:crypto", "payload": { "asset_id": 12, "final": 84, "delta": +3 } }
{ "type": "signal.created","topic": "signals:*", "payload": { "id": 991, "symbol": "BTCUSDT", "direction": "long", "rr": 1.59 } }
{ "type": "alert.fired",   "topic": "alerts:*", "payload": { "rule": "volume_spike", "symbol": "فملی" } }
{ "type": "ai.completed",  "topic": "ai:12", "payload": { "analysis_id": 4412 } }
{ "type": "system.degraded","topic":"system:health", "payload": { "source": "TSETMC", "status": "down", "since": "..." } }
```

**قواعد:**
- Backpressure: هر کلاینت صف محدود دارد؛ در صورت پر شدن، پیام‌های `price.tick` drop می‌شوند (coalescing) ولی `signal.created` هرگز.
- Heartbeat هر ۲۰ ثانیه؛ قطع پس از ۳ نوبت بی‌پاسخ.
- Reconnect با backoff نمایی از سمت UI و `resume_from` برای رویدادهای مهم.

---

## ۴.۵ همگام‌سازی قرارداد با Frontend

1. FastAPI → `openapi.json`
2. `openapi-typescript` → `frontend/src/types/api.d.ts`
3. تست CI: اگر schema تغییر کند و تایپ‌ها regenerate نشده باشند، build شکست می‌خورد.

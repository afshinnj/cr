# ۱۸) وضعیت Milestoneها

آخرین به‌روزرسانی: ۱۴۰۴/۰۷/۰۴ (2026-09-26)

| Milestone | وضعیت | یادداشت |
|---|---|---|
| M1 — Project Setup | ✅ تکمیل | اسکلت اجرایی، تنظیمات، لاگ، خطا، سلامت، CI، تست معماری |
| M2 — Database | ✅ تکمیل | ۴۰ جدول، ۱۰ hypertable، Migration، Repository، Seed |
| M3 — Market Data Providers | ⬜ بعدی | TSETMC مستقیم + Binance + CoinGecko |
| M4 — Technical Analysis | ⬜ | |
| M5 — Market Regime | ⬜ | |
| M6 — News Engine | ⬜ | |
| M7 — Scoring + Risk | ⬜ | |
| M8 — Backtesting | ⬜ | |
| M9 — Paper Trading | ⬜ | |
| M10 — Ollama Integration | ⬜ | |
| M11 — Electron UI | ⬜ | |
| M12 — Charts | ⬜ | |
| M13 — Alerts | ⬜ | |
| M14 — Machine Learning | ⬜ | |
| M15 — Testing & Hardening | ⬜ | |

---

## ✅ Milestone 1 — Project Setup

### تحویل‌شده
| مورد | مسیر |
|---|---|
| تنظیمات تایپ‌شده با اعتبارسنجی Production | `backend/app/core/config.py` |
| لاگ ساختاریافته با ماسک خودکار Secret | `backend/app/core/logging.py` |
| Clock تزریق‌شونده (ADR-009) | `backend/app/core/clock.py` |
| سلسله‌مراتب خطا + قالب واحد `ProblemDetail` | `backend/app/core/errors.py`, `app/api/errors.py` |
| Enumهای دامنه | `backend/app/core/enums.py` |
| بارگذار پیکربندی YAML | `backend/app/core/config_files.py` |
| اپلیکیشن FastAPI + trace id + CORS | `backend/app/main.py` |
| `/health`, `/health/deep`, `/system/config`, `/system/settings` | `backend/app/api/v1/system.py` |
| احراز هویت محلی (`X-Local-Token`) | `backend/app/api/deps.py` |
| Docker Compose (Timescale + Redis + Ollama + Backend) | `docker-compose.yml` |
| Makefile | `Makefile` |
| **اجبار قوانین معماری I1..I12** | `scripts/check_architecture.py` |
| CI (lint, mypy strict, arch, unit, integration, gitleaks) | `.github/workflows/ci.yml` |

### DoD — بررسی‌شده
- ✅ `/health` پاسخ `200`
- ✅ `/health/deep` هر مؤلفه را جدا گزارش می‌کند و با قطع Redis کد `503` و فهرست `degraded` برمی‌گرداند — بدون crash
- ✅ AI به‌عنوان `optional` علامت‌گذاری شده: قطع Ollama سیستم را پایین نمی‌آورد (ADR-005)
- ✅ درخواست بدون توکن → `401` با قالب استاندارد خطا
- ✅ `/system/settings` هیچ Secret ای را فاش نمی‌کند
- ✅ `mypy --strict` روی ۳۵ فایل: بدون خطا
- ✅ `ruff check` + `ruff format --check`: تمیز
- ✅ تست معماری: سبز

---

## ✅ Milestone 2 — Database

### تحویل‌شده
| مورد | جزئیات |
|---|---|
| مدل‌های ORM | **۴۰ جدول** در ۶ ماژول (`reference`, `market`, `analysis`, `news`, `ml`, `execution`, `system`) |
| Migration اولیه | `alembic/versions/*_initial_schema.py` |
| Migration تایم‌اسکیل | `alembic/versions/*_timescale_hypertables.py` — **۱۰ hypertable** + compression + retention |
| اعلان تایم‌اسکیل به‌صورت داده | `backend/app/database/timescale.py` |
| Session و Engine async | `backend/app/database/session.py` |
| Repository Pattern | `base`, `reference`, `market` |
| Seed تکرارپذیر | `scripts/seed_reference_data.py` |
| پیکربندی | `config/markets.yaml`, `scoring.yaml`, `sources.yaml`, `universe.yaml` |

### تصمیمات schema که بعداً اصلاحشان گران بود
1. **`corporate_actions` + `close_adj` از روز اول** (ADR-012) — بدون آن هر اندیکاتور و Backtest بورس ایران غلط است.
2. **`listed_at` / `delisted_at`** — بدون آن Backtest دچار Survivorship Bias می‌شود.
3. **`tsetmc_ins_code` یکتا** — نام نماد در بورس ایران تغییر می‌کند؛ کلید پایدار لازم است.
4. **`market_metrics` به شکل long-format** — افزودن هر معیار جدید (funding، ورود پول حقیقی، …) بدون migration.
5. **`NUMERIC(38,12)` برای همه مبالغ** — هیچ ستون `FLOAT` در کل schema وجود ندارد (تست خودکار دارد).
6. **PK ترکیبی روی `ohlcv`** — تضمین Idempotency برای Collectorها.
7. **`predictions` بدون retention policy** — مسیر ممیزی Continuous Learning هرگز حذف نمی‌شود.

### DoD — بررسی‌شده
- ✅ `alembic upgrade head` روی پایگاه داده خالی موفق
- ✅ ۴۱ جدول ساخته شد (۴۰ + `alembic_version`)
- ✅ Seed دو بار اجرا شد: بار دوم `assets_created=0` → **تکرارپذیر**
- ✅ ۶۰ دارایی، ۷ منبع داده، ۲ پروفایل امتیازدهی، ۱۰ صنعت
- ⏳ تأیید hypertableها روی TimescaleDB واقعی: در job `integration` گردش‌کار CI انجام می‌شود (در این محیط Docker در دسترس نبود)

---

## پوشش تست فعلی

```
152 passed, 8 skipped
```

| فایل تست | چه چیزی را تضمین می‌کند |
|---|---|
| `test_config.py` | `mock` در Production رد می‌شود؛ Secretها در dump فاش نمی‌شوند |
| `test_logging_masking.py` | هیچ Secret ای — حتی داخل متن آزاد — به لاگ نمی‌رسد |
| `test_clock.py` | Clock مجازی قطعی است؛ datetime بدون timezone رد می‌شود |
| `test_config_files.py` | وزن‌ها جمعشان ۱ است؛ **وزن AI هرگز بزرگ‌ترین نیست**؛ قواعد صف و دامنه نوسان ایران تعریف شده‌اند |
| `test_models_schema.py` | هیچ ستون float؛ هیچ timestamp بدون timezone؛ هیچ جدول معامله واقعی |
| `test_timescale_spec.py` | PK هر hypertable شامل ستون زمان است؛ `predictions` حذف نمی‌شود |
| `test_repositories.py` | دقت Decimal حفظ می‌شود؛ بازه نیم‌باز؛ ترتیب صحیح |
| `test_api_system.py` | قرارداد خطا، احراز هویت، عدم نشت Secret، Disclaimer دائمی |
| `test_architecture_rules.py` | **خود بررسی‌کننده معماری تست شده** — هر قانون با نمونه نقض آزمایش می‌شود |
| `integration/test_timescale_schema.py` | hypertableها، policyها، Idempotency واقعی `ON CONFLICT` |

---

## اجرا در محیط شما

```bash
cp .env.example .env
make token                 # مقدار را در LOCAL_API_TOKEN بگذارید
# POSTGRES_PASSWORD را هم تنظیم کنید
make up                    # postgres + redis + ollama + backend
make pull-model            # qwen2.5:7b-instruct  (~۵ گیگابایت دانلود)
make seed
curl localhost:8787/api/v1/health/deep
```

توسعه محلی بدون کانتینر backend:
```bash
make install && make infra && make migrate && make seed && make dev
make check                 # lint + mypy + architecture + tests
```

---

## Milestone 3 — طرح کار بعدی

1. `MarketDataProvider` ABC + Registry مبتنی بر Capability + زنجیره Fallback
2. Rate limiter توکن‌باکت روی Redis + Retry/Backoff/Circuit Breaker
3. `BinanceProvider` (REST + WebSocket) و `CoinGeckoProvider`
4. `TsetmcProvider` + **Contract Test روزانه** + resolver کد `ins_code`
5. لایه Validation (۷ قانون سند ۰۵ §۵.۵) + `data_quarantine`
6. Normalization: UTC، نگاشت نماد، قیمت تعدیل‌شده
7. Backfill تاریخی + Gap filler + `job_runs`
8. Mock providerها فقط زیر `providers/mock/` با گارد محیط

**DoD:** داده واقعی ۵ ساله روزانه در DB؛ قطع شبکه → خطای صریح و بازیابی خودکار، بدون هیچ داده ساختگی.

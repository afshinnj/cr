# ۲) Technology Stack و دلیل انتخاب هر تکنولوژی

هر ردیف شامل: **چرا انتخاب شد**، **بدیل‌ها**، و **ریسک/هزینه** آن.

## ۲.۱ Backend Core

| تکنولوژی | چرا | بدیل | ریسک |
|---|---|---|---|
| **Python 3.12+** | اکوسیستم بی‌رقیب داده/ML (pandas, sklearn, xgboost)؛ `3.12` بهبود سرعت و بهتر شدن پیام خطا | Rust/Go (سریع‌تر ولی اکوسیستم ML ضعیف) | GIL برای CPU-bound → با ProcessPool حل می‌شود |
| **FastAPI** | async native, تولید خودکار OpenAPI (قرارداد تایپ‌شده برای Frontend), وابستگی مستقیم به Pydantic | Django REST (سنگین، sync), Flask (بدون async/validation) | — |
| **Pydantic v2** | Validation در مرز سیستم (بند ۲۵/۲۶), هسته Rust → سریع, `BaseSettings` برای `.env` | dataclass + marshmallow | مهاجرت v1→v2 breaking؛ از ابتدا v2 |
| **SQLAlchemy 2.0** | ORM تایپ‌شده + امکان افت به SQL خام برای کوئری‌های سنگین Timescale | Tortoise, raw asyncpg | پیچیدگی؛ حل: Repository Pattern |
| **Alembic** | مهاجرت نسخه‌دار DB — الزامی برای تکامل schema | دستی (غیرقابل قبول) | Hypertable ها نیاز به migration دستی Timescale دارند |
| **PostgreSQL 16** | ACID، JSONB برای payload خام، partial index، window functions قوی برای تحلیل | MySQL (ضعیف‌تر در تحلیل), SQLite (بدون concurrency) | — |
| **TimescaleDB** | hypertable + chunk pruning + **continuous aggregates** (ساخت خودکار 5m/1h/1d از 1m) + compression (~۱۰x) | InfluxDB (جدا از رابطه‌ای → join سخت), ClickHouse (عالی ولی stack دوم) | افزونه؛ باید image سازگار در Docker استفاده شود |
| **Redis 7** | Cache نتایج Score، Rate-limit توکن‌باکت، **Redis Streams** به‌عنوان صف رویداد، Pub/Sub برای WebSocket fan-out | RabbitMQ (سنگین‌تر), Kafka (over-engineering) | داده in-memory → فقط داده گذرا |
| **ARQ یا Celery** | زمان‌بندی و Worker. پیشنهاد: **ARQ** (async-native، سبک، مبتنی بر Redis) | Celery (بالغ‌تر ولی sync-first و سنگین) | تصمیم در ADR-003 |
| **Pandas / NumPy / SciPy** | استاندارد داده جدولی؛ SciPy برای آزمون‌های آماری (stationarity, correlation, distribution fit) | Polars (سریع‌تر؛ گزینه بهینه‌سازی آینده) | مصرف RAM |

## ۲.۲ Technical Analysis

| تکنولوژی | چرا |
|---|---|
| **pandas-ta** (پیش‌فرض) | نصب آسان (pure python)، پوشش کامل RSI/MACD/EMA/ATR/ADX/BB/Stoch/Ichimoku/OBV/VWAP، بدون نیاز به کامپایل C |
| **TA-Lib** (اختیاری) | سریع‌تر (C)، ولی نصبش روی Windows/Docker دردسر دارد |
| **تصمیم** | لایه `IndicatorEngine` یک **Facade** است: `compute(name, df, params)`. backend آن قابل تعویض بین pandas-ta و TA-Lib است. برای اندیکاتورهای حساس (VWAP session-based, Support/Resistance, Ichimoku با تنظیمات بازار ایران) **پیاده‌سازی داخلی خودمان** با تست واحد عددی نوشته می‌شود |

> چرا پیاده‌سازی داخلی برای برخی؟ چون Support/Resistance و Breakout تعریف استاندارد ندارند و باید
> با پارامترهای قابل تنظیم و **بدون look-ahead** نوشته شوند (بند ۱۶).

## ۲.۳ Machine Learning

| تکنولوژی | چرا |
|---|---|
| **scikit-learn** | Pipeline، Preprocessing، `TimeSeriesSplit`، متریک‌ها، مدل‌های baseline (Logistic Regression به‌عنوان مرجع) |
| **XGBoost** | بهترین نسبت کارایی/دقت روی داده جدولی مالی، مقاوم به مقیاس، `feature_importance`, پشتیبانی از `sample_weight` زمانی |
| **LightGBM (آینده)** | سریع‌تر روی داده بزرگ؛ Interface مدل به‌صورت `ModelAdapter` طراحی می‌شود تا افزودنش کدصفر باشد |
| **MLflow (سبک) یا Model Registry داخلی** | نسخه‌بندی مدل، ذخیره متریک، امکان rollback (جدول `model_versions` / `model_metrics`) |
| **SHAP (اختیاری)** | توضیح‌پذیری مدل → ورودی برای متن AI Explanation |

**اصل ML:** مسئله به‌صورت **Classification احتمالاتی** تعریف می‌شود، نه Regression قیمت:
> «احتمال اینکه در H کندل آینده، بازده از آستانه k×ATR عبور کند، قبل از اینکه Stop خورده شود» — یعنی **Triple-Barrier Labeling**.
این تعریف مستقیماً با Risk Engine سازگار است و از دام «پیش‌بینی قیمت» دور می‌ماند (بند ۳۲).

## ۲.۴ Local AI

| تکنولوژی | چرا |
|---|---|
| **Ollama** | اجرای محلی، بدون هزینه، بدون ارسال داده به بیرون، REST API ساده، مدیریت مدل آسان |
| **AIProvider ABC** | `analyze(features) -> AIAnalysis`. پیاده‌سازی‌ها: `OllamaProvider`, `OpenAIProvider`, `AnthropicProvider`, `GeminiProvider`, `NullProvider` |
| **Structured Output** | استفاده از `format: json` Ollama + اعتبارسنجی با Pydantic + حداکثر ۲ بار retry؛ خروجی نامعتبر = `ai_analysis: null` (نه متن آزاد آلوده) |

## ۲.۵ Desktop Frontend

| تکنولوژی | چرا |
|---|---|
| **Electron** | نیاز به Desktop واقعی (Notification، فایل، Tray، اجرای backend محلی)؛ بسته‌بندی چندسکویی |
| **React 18 + TypeScript** | اکوسیستم، تایپ end-to-end با تولید تایپ از OpenAPI |
| **Vite** | dev server سریع، HMR، build سبک |
| **Tailwind CSS** | سرعت توسعه UI، پشتیبانی بومی از `dir="rtl"` با پلاگین logical properties |
| **RTL + فارسی** | `dir="rtl"`، فونت **Vazirmatn**، اعداد فارسی اختیاری، تاریخ **شمسی (jalaali-js)** برای بازار ایران و میلادی برای کریپتو |
| **TanStack Query** | مدیریت cache/refetch/stale برای داده سرور |
| **Zustand** | state سبک UI (فیلترها، تنظیمات چارت) |
| **Recharts/visx فقط برای چارت‌های آماری** | چارت قیمت با Lightweight Charts |

## ۲.۶ Charts

| تکنولوژی | چرا |
|---|---|
| **TradingView Lightweight Charts** | سبک (~45KB)، Canvas، عملکرد عالی روی ده‌ها هزار کندل، رایگان (Apache-2.0) |
| محدودیت مهم | Drawing Tools **داخلی ندارد**. راه‌حل: لایه Overlay سفارشی روی Canvas + ذخیره اشیای ترسیمی در DB (`user_drawings`). اگر ابزار ترسیم کامل لازم شود، بدیل `TradingView Charting Library` (نیاز به درخواست لایسنس) در ADR ثبت شده |
| Support/Resistance و Entry/SL/TP | با `createPriceLine` و سری‌های اضافی؛ سیگنال‌ها با `setMarkers` |
| RSI/MACD/ATR | چارت‌های جداگانه با محور زمانی همگام (`subscribeVisibleTimeRangeChange`) |

## ۲.۷ Communication

| تکنولوژی | چرا |
|---|---|
| **REST** | عملیات درخواست/پاسخ، صفحه‌بندی، تاریخچه |
| **WebSocket** | قیمت لحظه‌ای، به‌روزرسانی Score، Signal، Alert. پروتکل: JSON با `{type, payload, ts}` و subscribe/unsubscribe بر اساس topic |
| **OpenAPI → TS types** | تولید خودکار تایپ‌های Frontend (`openapi-typescript`) → عدم واگرایی قرارداد |

## ۲.۸ Infrastructure

| تکنولوژی | چرا |
|---|---|
| **Docker + Compose** | یک دستور برای بالا آوردن Postgres/Timescale + Redis + API + Worker + Ollama |
| **.env + Pydantic Settings** | Secrets خارج از کد و Git (بند ۲۵)؛ `.env.example` در repo |
| **Git + Conventional Commits** | تاریخچه تمیز، امکان تولید CHANGELOG |
| **Ruff + Black + mypy --strict** | کیفیت کد (بند ۲۶) |
| **pytest + pytest-asyncio + testcontainers** | تست واحد و یکپارچه روی DB واقعی |
| **ESLint + Prettier + Vitest + Playwright** | کیفیت و تست Frontend |
| **GitHub Actions** | CI: lint, type, test, architecture-tests, gitleaks |

## ۲.۹ آنچه عمداً انتخاب **نشد**

| رد شد | دلیل |
|---|---|
| Kubernetes | یک اپ Desktop تک‌کاربره است |
| Kafka | Redis Streams کافی است |
| Microservices | هزینه عملیاتی بدون سود |
| MongoDB | داده مالی رابطه‌ای و تحلیلی است |
| Deep Learning (LSTM/Transformer) روی قیمت | نسبت سیگنال به نویز پایین، خطر overfit شدید، غیرقابل توضیح. در صورت نیاز فقط پس از آنکه baselineهای Gradient Boosting به سقف رسیدند |
| Tauri به‌جای Electron | سبک‌تر، ولی اکوسیستم و پایداری کمتر برای این حجم UI (در ADR به‌عنوان گزینه آینده ثبت شد) |

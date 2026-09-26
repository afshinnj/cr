<div dir="rtl">

# AI Market Intelligence Platform

سامانه Desktop پایش، تحلیل و رتبه‌بندی بازار بورس ایران و ارزهای دیجیتال.

> **وضعیت فعلی: فاز طراحی (Design Phase) — بدون کد Production**
> مطابق بند ۳۱ سند نیازمندی، ابتدا معماری کامل ارائه شده است. پیاده‌سازی پس از تأیید، Milestone به Milestone آغاز می‌شود.

---

## هدف

تولید سه خروجی مستقل و **قابل توضیح** برای هر دارایی:

| خروجی | بازه |
|---|---|
| Opportunity Score | ۰ تا ۱۰۰ |
| Risk Score | ۰ تا ۱۰۰ |
| Confidence Score | ۰ تا ۱ |

**این سیستم قیمت را پیش‌بینی نمی‌کند.** خروجی‌ها آماری، مبتنی بر داده دارای منبع و زمان، و همراه با عملکرد تاریخی ارائه می‌شوند.

---

## مستندات معماری

| سند | موضوع |
|---|---|
| [`docs/00-overview.md`](docs/00-overview.md) | خلاصه اجرایی، اصول غیرقابل مذاکره، سؤالات باز |
| [`docs/01-architecture.md`](docs/01-architecture.md) | معماری کامل + دیاگرام‌ها |
| [`docs/02-tech-stack.md`](docs/02-tech-stack.md) | Technology Stack و دلیل هر انتخاب |
| [`docs/03-database.md`](docs/03-database.md) | ERD، جداول، TimescaleDB، برآورد حجم |
| [`docs/04-api-contract.md`](docs/04-api-contract.md) | REST + WebSocket Contract |
| [`docs/05-data-flow.md`](docs/05-data-flow.md) | جمع‌آوری، اعتبارسنجی، نرمال‌سازی |
| [`docs/06-ai-flow.md`](docs/06-ai-flow.md) | AI Flow، Prompt Contract، Guardrails |
| [`docs/07-news-flow.md`](docs/07-news-flow.md) | News Engine، Deduplication، Sentiment |
| [`docs/08-backtesting.md`](docs/08-backtesting.md) | Backtesting و Walk-Forward |
| [`docs/09-paper-trading.md`](docs/09-paper-trading.md) | Paper Trading |
| [`docs/10-folder-structure.md`](docs/10-folder-structure.md) | ساختار پوشه‌ها |
| [`docs/11-roadmap.md`](docs/11-roadmap.md) | نقشه راه ۱۵ Milestone با DoD |
| [`docs/12-risks.md`](docs/12-risks.md) | ریسک‌ها و محدودیت‌ها |
| [`docs/13-data-sources.md`](docs/13-data-sources.md) | منابع داده رایگان و محدودیت‌ها |
| [`docs/14-ollama-hardware.md`](docs/14-ollama-hardware.md) | سخت‌افزار و مدل‌های Ollama |
| [`docs/15-success-metrics.md`](docs/15-success-metrics.md) | معیارهای موفقیت |
| [`docs/16-scoring-and-risk.md`](docs/16-scoring-and-risk.md) | فرمول‌های Scoring و Risk |
| [`docs/17-decision-log.md`](docs/17-decision-log.md) | ADR — تصمیمات معماری |

---

## Stack

**Backend:** Python 3.12 · FastAPI · Pydantic v2 · SQLAlchemy 2 · Alembic · PostgreSQL + TimescaleDB · Redis
**تحلیل:** pandas · NumPy · SciPy · pandas-ta · scikit-learn · XGBoost
**AI:** Ollama (Local LLM) پشت `AIProvider` قابل تعویض
**Desktop:** Electron · React · TypeScript · Vite · Tailwind (RTL/فارسی) · TradingView Lightweight Charts
**زیرساخت:** Docker Compose · `.env`

---

## هشدار مالی

خروجی این نرم‌افزار **توصیه سرمایه‌گذاری نیست**. هیچ ادعای قطعی درباره قیمت آینده ارائه نمی‌شود.
پیش از هر استفاده واقعی، Backtest و Paper Trading الزامی است. عملکرد گذشته تضمین‌کننده آینده نیست.

</div>

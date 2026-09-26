# AI Market Intelligence Platform — سند معماری (نسخه ۰.۱ / Draft for Approval)

> وضعیت: **پیش از پیاده‌سازی**. طبق بخش ۳۱ درخواست، در این مرحله هیچ کد Production تولید نشده است.
> این سند و فایل‌های کنار آن، «قرارداد معماری» پروژه هستند. پس از تأیید شما، پیاده‌سازی Milestone به Milestone آغاز می‌شود.

---

## ۰) خلاصه اجرایی (Executive Summary)

**AI Market Intelligence Platform (کد داخلی: `AMIP`)** یک نرم‌افزار Desktop است که دو بازار
«بورس اوراق بهادار تهران» و «ارزهای دیجیتال» را به‌صورت مستمر پایش می‌کند و برای هر دارایی
سه خروجی اصلی تولید می‌کند:

| خروجی | بازه | معنا |
|---|---|---|
| `Opportunity Score` | 0..100 | میزان جذابیت نسبی فرصت در لحظه، بر اساس ترکیب وزنی سیگنال‌های مستقل |
| `Risk Score` | 0..100 | میزان ریسک ساختاری و نوسانی موقعیت (هرچه بالاتر، بدتر) |
| `Confidence Score` | 0..1 | میزان اتکاپذیری خروجی با توجه به کیفیت داده، توافق لایه‌ها و عملکرد تاریخی |

### چیزی که این سیستم هست
- یک **موتور تحلیل چندلایه و قابل توضیح (Explainable)** که هر عدد نهایی را به اجزای قابل ردیابی می‌شکند.
- یک **سیستم Evidence-based**: هر داده دارای `source` و `timestamp` و `quality` است.
- یک **حلقه بازخورد**: هر Prediction ذخیره و بعداً با نتیجه واقعی مقایسه می‌شود.

### چیزی که این سیستم **نیست**
- پیش‌بینی قطعی قیمت. هیچ خروجی به شکل «قیمت فردا X خواهد بود» تولید نمی‌شود.
- ربات معامله‌گر. در این نسخه فقط **Paper Trading** وجود دارد (بخش ۱۷ و ۳۲).
- ماشین‌حساب LLM. محاسبات عددی **هرگز** به LLM سپرده نمی‌شود (بخش ۱۳).

---

## ۱) اصول طراحی غیرقابل مذاکره (Design Invariants)

این ۱۲ قانون در CI به‌صورت تست معماری (Architecture Test) اجبار می‌شوند، نه صرفاً توصیه:

| # | قانون | نحوه اجبار |
|---|---|---|
| I1 | UI هیچ اتصال مستقیمی به DB ندارد | در `frontend/` هیچ وابستگی DB وجود ندارد؛ فقط HTTP/WS |
| I2 | Business Logic فقط در `backend/app/services` و `domain` | تست ایمپورت: `api/` نمی‌تواند `sqlalchemy` را مستقیم ایمپورت کند |
| I3 | Data Provider قابل تعویض (Interface + Registry) | همه Providerها از ABC ارث می‌برند و از طریق Factory ساخته می‌شوند |
| I4 | AI Provider قابل تعویض؛ Ollama فقط یک Implementation | `AIProvider` ABC + `OllamaProvider`, `OpenAIProvider`, `NullProvider` |
| I5 | Technical Analysis مستقل از AI | ماژول `indicators/` هیچ ایمپورتی از `ai/` ندارد (تست ایمپورت) |
| I6 | Risk Management مستقل از AI | ماژول `risk/` هیچ ایمپورتی از `ai/` ندارد |
| I7 | AI نمی‌تواند Risk Veto را override کند | تصمیم نهایی از `DecisionPolicy` می‌گذرد که AI فقط یک ورودی آن است |
| I8 | Backtesting مستقل از Live | `backtesting/` فقط از Repositoryهای read-only استفاده می‌کند |
| I9 | No Fake Data in Production | `settings.data_mode` ∈ {`live`,`mock`}؛ `mock` در Production باعث خطای startup می‌شود |
| I10 | هیچ وزن یا آستانه‌ای Hard-Code نیست | همه در `config/scoring.yaml` + جدول `scoring_profiles` |
| I11 | Secrets فقط از `.env` / Keyring | `.env` در `.gitignore`؛ اسکن `gitleaks` در CI |
| I12 | همه‌چیز Typed | `mypy --strict` روی `backend/app`، `tsc --noEmit` روی frontend |

---

## ۲) ساختار این مجموعه اسناد

| فایل | محتوا | بند درخواست |
|---|---|---|
| `01-architecture.md` | معماری کامل + دیاگرام‌ها | 1, 2 |
| `02-tech-stack.md` | تکنولوژی‌ها و دلیل انتخاب هرکدام | 3 |
| `03-database.md` | ERD + جداول + ایندکس‌ها + TimescaleDB | 4, 5 |
| `04-api-contract.md` | REST + WebSocket Contract | 6 |
| `05-data-flow.md` | جریان داده و Collection | 7 |
| `06-ai-flow.md` | AI Flow + Prompt Contract + Guardrails | 8 |
| `07-news-flow.md` | News + Deduplication + Sentiment | 9 |
| `08-backtesting.md` | معماری Backtest و Walk-Forward | 10 |
| `09-paper-trading.md` | معماری Paper Trading | 11 |
| `10-folder-structure.md` | ساختار پوشه‌ها | 12 |
| `11-roadmap.md` | نقشه راه ۱۵ Milestone با DoD | 13 |
| `12-risks.md` | ریسک‌ها و محدودیت‌ها | 14 |
| `13-data-sources.md` | منابع داده رایگان + محدودیت‌ها | 15 |
| `14-ollama-hardware.md` | سخت‌افزار + مدل‌های پیشنهادی | 16, 17 |
| `15-success-metrics.md` | معیارهای موفقیت | 18 |
| `16-scoring-and-risk.md` | فرمول‌های Scoring و Risk (جزئیات ریاضی) | 11, 12 |
| `17-decision-log.md` | ADR — تصمیمات معماری و بدیل‌ها | — |

---

## ۳) سؤالاتی که پیش از شروع Milestone 1 نیاز به پاسخ شما دارند

این موارد روی معماری اثر مستقیم دارند و در سند ADR ثبت خواهند شد:

1. **دامنه دارایی‌ها (Universe)**: چند نماد؟ پیشنهاد اولیه: Top 100 کریپتو + ~۷۰۰ نماد بورس/فرابورس. این عدد مستقیماً حجم DB و بار CPU را تعیین می‌کند (محاسبه در `03-database.md`).
2. **عمق تاریخی**: ۵ سال کریپتو (Binance رایگان) قابل انجام است؛ برای بورس ایران عمق تاریخی به منبع انتخابی وابسته است.
3. **کاربر تک‌نفره یا چندنفره؟** طراحی فعلی Single-User Desktop است (بدون Auth پیچیده، فقط Local Token).
4. **سخت‌افزار در دسترس شما** (RAM / GPU / VRAM) — تعیین‌کننده مدل Ollama (جدول در `14-ollama-hardware.md`).
5. **بودجه API**: آیا فقط منابع رایگان؟ (Free-only مسیر پیش‌فرض است و در `13-data-sources.md` محدودیت‌هایش شفاف شده.)
6. **Timeframeهای فعال در فاز اول**: پیشنهاد `15m, 1h, 4h, 1d` برای کریپتو و `1d` (+ intraday در صورت دسترسی) برای بورس ایران. فعال کردن `1m` روی همه نمادها هزینه ذخیره‌سازی را ~۶۰ برابر می‌کند.

---

## ۴) هشدار مالی (Financial Safety — بند ۳۲)

خروجی سیستم **توصیه سرمایه‌گذاری نیست**. در UI به‌صورت دائمی نمایش داده می‌شود:

> «این خروجی حاصل تحلیل آماری داده‌های تاریخی و لحظه‌ای است، نه پیش‌بینی قطعی. عملکرد گذشته تضمینی برای آینده نیست.»

هیچ Signal ای بدون `historical_performance` معتبر (حداقل N نمونه Backtest + دوره Paper Trading) در UI با برچسب «BUY CANDIDATE» ظاهر نمی‌شود؛ تا آن زمان برچسب `RESEARCH_ONLY` دارد.

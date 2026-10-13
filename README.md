# mrbiznes-trading-bot

ربات تلگرام MrBiznes — بازار، سیگنال، آلارم، ژورنال، روان‌شناسی،
تحلیل چارت PLT، رفرال، پشتیبانی و پنل ادمین.

## سریع‌ترین راه برای روشن کردن (بدون سرور)

ربات می‌تواند روی **GitHub Actions** اجرا شود (رایگان، بیرون ایران، به
تلگرام وصل می‌شود). فقط دو کار: توکن را در Secrets بگذارید و فایل
[`deploy/github-actions-telegram-bot.yml`](deploy/github-actions-telegram-bot.yml)
را در `.github/workflows/telegram-bot.yml` کپی کنید. جزئیات گام‌به‌گام:
[`SETUP_FA.md`](SETUP_FA.md) بخش «۰».

## شروع سریع (اجرای محلی)

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt   # ویندوز: .venv\Scripts\pip
cp .env.example .env                        # مقادیر را پر کنید
.venv/bin/python scripts/doctor.py          # چک کامل قبل از اجرا
.venv/bin/python main.py                    # روشن کردن ربات
```

## مستندات

| فایل | موضوع |
|---|---|
| [`SETUP_FA.md`](SETUP_FA.md) | راهنمای کامل فارسی: GitHub Actions، Railway، سرور ایران + پروکسی، عیب‌یابی |
| [`deploy/github-actions-telegram-bot.yml`](deploy/github-actions-telegram-bot.yml) | فایل اجرای ربات روی GitHub Actions (بدون سرور) |
| [`RAILWAY_SETUP.md`](RAILWAY_SETUP.md) | راه‌اندازی اسکنر PLT روی Railway (کرون) |
| [`.env.example`](.env.example) | نمونه همه‌ی متغیرهای تنظیمات |

## دستورهای داخل تلگرام

| دستور | کار |
|---|---|
| `/start` | منوی اصلی |
| `/id` | شناسه عددی تلگرام شما (برای `ADMIN_IDS`) |
| `/ping` | سرعت پاسخ‌دهی ربات |
| `/diag` | گزارش سلامت کامل (فقط ادمین) |

## ابزارهای چک

```bash
bash run_local.sh              # اجرای خودکار محلی (ویندوز: run_local.bat)
python scripts/doctor.py       # توکن، شبکه، پروکسی، دیتابیس، کاربران
python scripts/smoke_test.py   # تست import و ساخت اپلیکیشن بدون تماس با تلگرام
```

## سرورهای داخل ایران

اگر سرور داخل ایران است، دسترسی مستقیم به `api.telegram.org` بسته است.
در `.env` این را تنظیم کنید:

```
BOT_PROXY_URL=socks5://127.0.0.1:1080
```

> پروکسی باید **SOCKS5 یا HTTP** باشد؛ پروکسی MTProto تلگرام برای ربات
> کار نمی‌کند. اگر روی Railway (خارج ایران) اجرا می‌کنید، پروکسی لازم
> نیست.

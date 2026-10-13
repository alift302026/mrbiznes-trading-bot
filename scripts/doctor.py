#!/usr/bin/env python3
"""
دکتر ربات MrBiznes — چک کردن همه‌چیز قبل از روشن کردن ربات
============================================================

اجرا:

    python scripts/doctor.py

این اسکریپت هیچ پیامی به تلگرام نمی‌فرستد و هیچ‌چیز را تغییر نمی‌دهد؛
فقط وضعیت را گزارش می‌کند. برای همین می‌شود بی‌خطر روی سرور اجرا کرد.

بررسی‌ها:
    1. پایتون و پکیج‌های لازم
    2. فایل .env و متغیرهای ضروری (BOT_TOKEN, ADMIN_IDS)
    3. دسترسی مستقیم به api.telegram.org
    4. پروکسی (BOT_PROXY_URL) و تست عبور ترافیک از آن
    5. تست توکن (getMe) — مستقیم و از طریق پروکسی
    6. کلیدهای اختیاری (XT / TwelveData / OpenAI / LiveCoinWatch)
    7. دیتابیس و لیست کاربران (برای پیدا کردن شناسه تلگرام خودتان)
    8. پوشه‌های data

خروجی: 0 یعنی آماده اجرا، 1 یعنی هنوز چیزی کم است.
"""

from __future__ import annotations

import os
import platform
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

OK = "✅"
NO = "❌"
WARN = "⚠️"
INFO = "ℹ️"

problems: list[str] = []
warnings: list[str] = []


def line(title: str = "") -> None:
    if title:
        print(f"\n{title}\n" + "─" * max(24, len(title)))
    else:
        print("─" * 46)


def ok(text: str) -> None:
    print(f"  {OK} {text}")


def bad(text: str, fix: str = "") -> None:
    print(f"  {NO} {text}")
    if fix:
        print(f"     ↳ {fix}")
    problems.append(text)


def warn(text: str) -> None:
    print(f"  {WARN} {text}")
    warnings.append(text)


def info(text: str) -> None:
    print(f"  {INFO} {text}")


def mask_token(token: str) -> str:
    if not token:
        return "(خالی)"

    head, _, tail = token.partition(":")

    if not tail:
        return token[:6] + "…"

    return f"{head}:{tail[:4]}…{tail[-4:]}"


def probe(url: str, proxy: str = "", timeout: float = 6.0):
    """(موفق؟, متن, میلی‌ثانیه)"""

    try:
        import httpx
    except Exception as exc:  # pragma: no cover
        return False, f"httpx نصب نیست ({exc})", 0

    started = time.perf_counter()

    try:
        kwargs = {
            "timeout": timeout,
            "follow_redirects": True,
            "headers": {"User-Agent": "MrBiznes-Doctor"},
        }

        if proxy:
            kwargs["proxy"] = proxy

        response = httpx.get(url, **kwargs)

        elapsed = int((time.perf_counter() - started) * 1000)

        return True, f"HTTP {response.status_code}", elapsed

    except Exception as exc:
        elapsed = int((time.perf_counter() - started) * 1000)
        return False, f"{type(exc).__name__}: {str(exc)[:140]}", elapsed


def main() -> int:

    print(
        "\n"
        "==================================================\n"
        "   🩺 دکتر ربات MrBiznes — بررسی قبل از اجرا\n"
        "=================================================="
    )

    # ---------------------------------------------------------
    # 1. پایتون و پکیج‌ها
    # ---------------------------------------------------------
    line("۱) پایتون و پکیج‌های لازم")

    print(
        f"  {INFO} Python {platform.python_version()} | "
        f"{platform.system()} {platform.machine()}"
    )

    if sys.version_info < (3, 10):
        bad(
            f"نسخه پایتون قدیمی است: {platform.python_version()}",
            "پایتون 3.11 یا 3.12 نصب کنید.",
        )
    else:
        ok(f"نسخه پایتون مناسب است ({platform.python_version()})")

    required_packages = {
        "telegram": "python-telegram-bot",
        "sqlalchemy": "SQLAlchemy",
        "httpx": "httpx",
        "requests": "requests",
        "PIL": "pillow",
        "ccxt": "ccxt",
        "numpy": "numpy",
        "pandas": "pandas",
        "bs4": "beautifulsoup4",
        "jdatetime": "jdatetime",
        "hijridate": "hijridate",
        "dotenv": "python-dotenv",
    }

    missing = []

    for module, package in required_packages.items():
        try:
            __import__(module)
        except Exception:
            missing.append(package)

    if missing:
        bad(
            "این پکیج‌ها نصب نیستند: " + ", ".join(missing),
            "اجرا کنید:  pip install -r requirements.txt",
        )
    else:
        ok("همه پکیج‌های اصلی نصب هستند")

    venv = sys.prefix != getattr(sys, "base_prefix", sys.prefix)

    if venv:
        ok(f"داخل virtualenv هستید ({sys.prefix})")
    else:
        warn(
            "روی پایتون سیستم هستید، نه virtualenv. "
            "برای اجرای دائمی بهتر است از venv استفاده کنید."
        )

    # ---------------------------------------------------------
    # 2. .env و متغیرهای ضروری
    # ---------------------------------------------------------
    line("۲) فایل .env و متغیرهای ضروری")

    env_file = ROOT / ".env"

    if env_file.exists():
        ok(f"فایل .env پیدا شد ({env_file})")
    else:
        warn(
            "فایل .env وجود ندارد. "
            "از .env.example بسازید: cp .env.example .env"
        )

    try:
        from app.core.config import (  # noqa: F401
            ADMIN_IDS,
            BOT_TOKEN,
            OPENAI_API_KEY,
            OPENROUTER_API_KEY,
            REQUIRED_CHANNEL,
            TWELVE_DATA_API_KEY,
            XT_API_KEY,
            XT_SECRET_KEY,
            admin_ids_status,
            validate_bot_token,
        )
        from app.core.proxy import (
            get_proxy_url,
            mask_proxy,
            socks_support_available,
        )
        from app.models.database import DATABASE_PATH, SessionLocal
        from app.models.user import User
        from sqlalchemy import select

    except Exception as exc:
        bad(
            f"import ماژول‌های پروژه شکست خورد: {type(exc).__name__}: {exc}",
            "مطمئن شوید داخل پوشه پروژه هستید و requirements نصب است.",
        )
        line("نتیجه")
        print(f"  {NO} پروژه بالا نمی‌آید؛ خطای بالا را رفع کنید.")
        return 1

    token_ok, token_message = validate_bot_token()

    if token_ok:
        ok(f"BOT_TOKEN درست است ({mask_token(BOT_TOKEN)})")
    else:
        bad(token_message)

    admins_ok, admins_message = admin_ids_status()

    if admins_ok:
        ok(
            "ADMIN_IDS: "
            + ", ".join(str(x) for x in sorted(ADMIN_IDS))
        )
    else:
        bad(
            admins_message,
            "شناسه تلگرام خودتان را با /id در ربات یا @userinfobot بگیرید.",
        )

    info(
        f"کانال اجباری عضویت: {REQUIRED_CHANNEL or '— (غیرفعال)'}"
    )

    # ---------------------------------------------------------
    # 3. پروکسی
    # ---------------------------------------------------------
    line("۳) پروکسی (لازم برای سرورهای داخل ایران)")

    try:
        proxy_url = get_proxy_url()
    except ValueError as exc:
        proxy_url = ""
        bad(f"تنظیمات پروکسی نامعتبر: {exc}")

    if proxy_url:
        ok(f"پروکسی تنظیم شده: {mask_proxy(proxy_url)}")

        if proxy_url.lower().startswith("socks"):
            if socks_support_available():
                ok("پکیج socksio نصب است (لازم برای SOCKS5)")
            else:
                bad(
                    "پروکسی SOCKS تنظیم شده ولی socksio نصب نیست.",
                    "اجرا کنید:  pip install socksio",
                )
    else:
        info(
            "پروکسی تنظیم نشده. اگر سرور بیرون ایران است (مثل Railway) "
            "همین درست است."
        )
        info(
            "اگر سرور داخل ایران است، BOT_PROXY_URL را در .env بگذارید."
        )

    from app.core.proxy import proxy_for_all_traffic

    info(
        "اعمال پروکسی روی بازار/اخبار (BOT_PROXY_FOR_ALL): "
        + ("روشن" if proxy_for_all_traffic() else "خاموش")
    )

    # ---------------------------------------------------------
    # 4. تست شبکه + توکن
    # ---------------------------------------------------------
    line("۴) تست ارتباط با تلگرام")

    direct_ok, direct_text, direct_ms = probe(
        "https://api.telegram.org/",
        "",
        5.0,
    )

    if direct_ok:
        ok(f"اتصال مستقیم به تلگرام: {direct_text} ({direct_ms}ms)")
    else:
        print(f"  {NO} اتصال مستقیم به تلگرام: {direct_text}")
        info(
            "این طبیعی است اگر سرور داخل ایران باشد "
            "(فیلترینگ) — از پروکسی استفاده کنید."
        )

    proxy_ok = False

    if proxy_url:
        proxy_ok, proxy_text, proxy_ms = probe(
            "https://api.telegram.org/",
            proxy_url,
            8.0,
        )

        if proxy_ok:
            ok(
                f"تست پروکسی {mask_proxy(proxy_url)}: "
                f"{proxy_text} ({proxy_ms}ms)"
            )
        else:
            bad(
                f"تست پروکسی ناموفق: {proxy_text}",
                "آدرس/پورت/یوزرنیم پروکسی و روشن بودن آن را بررسی کنید.",
            )

    if token_ok:

        for label, use_proxy in (
            ("مستقیم", ""),
            ("از پروکسی", proxy_url),
        ):
            if use_proxy == "" and not direct_ok:
                continue

            if use_proxy and not proxy_ok:
                continue

            if label == "از پروکسی" and not proxy_url:
                continue

            proxy_ok_i, text, ms = probe(
                f"https://api.telegram.org/bot{BOT_TOKEN}/getMe",
                use_proxy,
                8.0,
            )

            if proxy_ok_i and "HTTP 200" in text:
                print(
                    f"  {OK} توکن سالم است ({label}) — "
                    f"{ms}ms و ربات پاسخ داد"
                )

                if not use_proxy:
                    break

            elif proxy_ok_i:
                bad(
                    f"توکن رد شد ({label}): {text}",
                    "توکن را از @BotFather دوباره بگیرید.",
                )

            else:
                print(f"  {NO} getMe {label} ناموفق: {text}")

    # ---------------------------------------------------------
    # 5. کلیدهای اختیاری
    # ---------------------------------------------------------
    line("۵) کلیدهای اختیاری (برای بخش‌های جانبی)")

    optional = [
        ("XT (صرافی/جستجوی کریپتو)", bool(XT_API_KEY and XT_SECRET_KEY)),
        ("TwelveData (فارکس)", bool(TWELVE_DATA_API_KEY)),
        ("OpenAI (تحلیل چارت PLT)", bool(OPENAI_API_KEY)),
        ("OpenRouter (مدل جایگزین PLT)", bool(OPENROUTER_API_KEY)),
        (
            "LiveCoinWatch (اسکنر PLT)",
            bool(os.getenv("LIVECOINWATCH_API_KEY", "").strip()),
        ),
    ]

    for name, present in optional:
        print(f"  {'✅' if present else '➖'} {name}: "
              + ("تنظیم شده" if present else "تنظیم نشده (اختیاری)"))

    addresses = [
        "BTC_PAYMENT_ADDRESS",
        "ETH_PAYMENT_ADDRESS",
        "TRON_PAYMENT_ADDRESS",
        "SOL_PAYMENT_ADDRESS",
        "USDT_TRC20_ADDRESS",
        "USDT_ERC20_ADDRESS",
    ]

    filled = sum(
        1 for name in addresses
        if os.getenv(name, "").strip()
    )

    print(f"  {'✅' if filled else '➖'} آدرس‌های پرداخت: "
          f"{filled} از {len(addresses)} تنظیم شده")

    # ---------------------------------------------------------
    # 6. دیتابیس و کاربران
    # ---------------------------------------------------------
    line("۶) دیتابیس")

    print(f"  {INFO} مسیر: {DATABASE_PATH}")

    if DATABASE_PATH.exists():
        ok("فایل دیتابیس موجود است")
    else:
        warn(
            "فایل دیتابیس ساخته نشده؛ با اولین اجرای ربات "
            "یا `python init_db.py` ساخته می‌شود."
        )

    try:
        from sqlalchemy import func

        with SessionLocal() as db:
            total = db.scalar(
                select(func.count(User.id))
            ) or 0

            users = list(
                db.scalars(
                    select(User)
                    .order_by(User.id.desc())
                    .limit(8)
                )
            )

        print(f"  {INFO} تعداد کاربران ثبت‌شده: {total}")
        print(f"  {INFO} آخرین کاربران:")

        if not users:
            info("هنوز کاربری ثبت نشده است.")
        else:
            for user in users:
                print(
                    f"     • id={user.telegram_id} "
                    f"@{user.username or '—'} "
                    f"({user.first_name or '—'})"
                )

            info(
                "شناسه خودتان را همین‌جا پیدا می‌کنید؛ آن را در "
                "ADMIN_IDS بگذارید."
            )

    except Exception as exc:
        text = str(exc)

        if "no such table" in text:
            info(
                "دیتابیس تازه است و هنوز جدول ندارد؛ با اولین اجرای "
                "ربات یا `python init_db.py` ساخته می‌شود."
            )
        else:
            warn(
                "خواندن دیتابیس ممکن نشد: "
                f"{type(exc).__name__}: {text[:150]}"
            )

    # ---------------------------------------------------------
    # 7. پوشه‌های داده
    # ---------------------------------------------------------
    line("۷) پوشه‌های داده")

    for relative in ("data", "data/plt_range"):
        target = ROOT / relative

        try:
            target.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            bad(
                f"ساخت پوشه {relative} ممکن نشد: {exc}",
                "دسترسی نوشتن پوشه پروژه را بررسی کنید.",
            )
            continue

        if os.access(target, os.W_OK):
            ok(f"پوشه {relative} قابل نوشتن است")
        else:
            bad(f"پوشه {relative} قابل نوشتن نیست")

    # ---------------------------------------------------------
    # نتیجه
    # ---------------------------------------------------------
    line("نتیجه")

    if problems:
        print(f"  {NO} {len(problems)} مورد باید درست شود:")
        for item in problems:
            print(f"     • {item}")
        print()
        print("  بعد از رفع موارد بالا، دوباره اجرا کنید:")
        print("     python scripts/doctor.py")
        return 1

    if warnings:
        print(f"  {WARN} {len(warnings)} هشدار (ربات کار می‌کند):")
        for item in warnings:
            print(f"     • {item}")
    else:
        print(f"  {OK} همه‌چیز مرتب است.")

    print()
    print("  🚀 اجرای ربات:")
    print("     python main.py")
    print()
    print("  📚 راهنمای کامل: SETUP_FA.md")
    print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

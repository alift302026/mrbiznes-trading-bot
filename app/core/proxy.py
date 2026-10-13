"""
شبکه و پروکسی — MrBiznes
=========================

اگر سرور ربات **داخل ایران** باشد، دسترسی مستقیم به `api.telegram.org`
فیلتر است و ربات بدون پروکسی بالا نمی‌آید.
این ماژول تنظیمات پروکسی را از محیط می‌خواند و به `python-telegram-bot`
و بقیه سرویس‌ها (که از کتابخانه `requests` استفاده می‌کنند) تحویل می‌دهد.

متغیرهای محیطی (به ترتیب اولویت):

    BOT_PROXY_URL          کامل‌ترین گزینه، مثال:
                           socks5://127.0.0.1:1080
                           socks5://user:pass@1.2.3.4:1080
                           http://127.0.0.1:8080
    BOT_UPDATES_PROXY_URL  اختیاری؛ فقط برای getUpdates (اگر جدا باشد)
    TELEGRAM_PROXY_URL     نام قدیمی/رایج
    HTTPS_PROXY            استاندارد سیستم
    ALL_PROXY              استاندارد سیستم

نکته‌های مهم
------------
1. پروکسی «MTProto» تلگرام برای **ربات** کار نمی‌کند؛ MTProto فقط برای
   خود اپلیکیشن تلگرام است. ربات به **SOCKS5** یا **HTTP/HTTPS** نیاز دارد.
2. برای SOCKS5 باید بسته `socksio` نصب باشد (در requirements.txt هست).
3. پس از تنظیم پروکسی، همان آدرس برای `requests` (تب‌های بازار، اخبار،
   PLT Range Scanner) هم در محیط ست می‌شود تا همه‌ی بخش‌ها از پروکسی رد شوند.
"""

from __future__ import annotations

import logging
import os
from typing import Optional
from urllib.parse import urlparse, urlunparse

logger = logging.getLogger(__name__)

# ترتیب اولویت خواندن آدرس پروکسی
PROXY_ENV_ORDER = (
    "BOT_PROXY_URL",
    "TELEGRAM_PROXY_URL",
    "PROXY_URL",
    "HTTPS_PROXY",
    "https_proxy",
    "ALL_PROXY",
    "all_proxy",
)

UPDATES_PROXY_ENV_ORDER = (
    "BOT_UPDATES_PROXY_URL",
    "TELEGRAM_UPDATES_PROXY_URL",
)

SOCKS_SCHEMES = {"socks5", "socks5h", "socks4", "socks4a", "socks"}


def _clean(value: Optional[str]) -> str:
    return (value or "").strip()


def _first_value(names) -> str:
    for name in names:
        value = _clean(os.getenv(name))
        if value:
            return value
    return ""


def normalize_proxy_url(raw: str) -> str:
    """
    آدرس پروکسی را یکدست می‌کند.

    - اگر پروتکل نوشته نشده باشد، `http://` اضافه می‌شود
      (مثل `127.0.0.1:8080`).
    - `mtproto://` را رد می‌کند چون برای ربات کار نمی‌کند.
    """

    value = _clean(raw)

    if not value:
        return ""

    lowered = value.lower()

    if lowered.startswith("mtproto://") or lowered.startswith("tg://"):
        raise ValueError(
            "پروکسی MTProto برای ربات کار نمی‌کند. "
            "برای ربات از SOCKS5 (socks5://host:port) یا "
            "HTTP (http://host:port) استفاده کنید."
        )

    if "://" not in value:
        value = f"http://{value}"

    parsed = urlparse(value)

    if not parsed.hostname:
        raise ValueError(
            f"آدرس پروکسی نامعتبر است: {raw!r} "
            "(نمونه صحیح: socks5://127.0.0.1:1080)"
        )

    if parsed.port is None:
        default_port = {
            "http": 8080,
            "https": 8443,
            "socks5": 1080,
            "socks5h": 1080,
            "socks4": 1080,
            "socks4a": 1080,
            "socks": 1080,
        }.get(parsed.scheme.lower())

        if default_port is None:
            raise ValueError(
                f"پورت پروکسی مشخص نیست: {raw!r} "
                "(نمونه صحیح: socks5://127.0.0.1:1080)"
            )

        parsed = parsed._replace(
            netloc=f"{parsed.hostname}:{default_port}",
        )

    return urlunparse(parsed)


def get_proxy_url() -> str:
    """آدرس پروکسی برای درخواست‌های ربات (خالی یعنی بدون پروکسی)."""

    raw = _first_value(PROXY_ENV_ORDER)

    if not raw:
        return ""

    try:
        return normalize_proxy_url(raw)
    except ValueError as exc:
        logger.error("Proxy configuration error: %s", exc)
        raise


def get_updates_proxy_url() -> str:
    """
    آدرس پروکسی مخصوص getUpdates.

    اگر جدا تنظیم نشده باشد، همان پروکسی عمومی برمی‌گردد.
    """

    raw = _first_value(UPDATES_PROXY_ENV_ORDER)

    if raw:
        try:
            return normalize_proxy_url(raw)
        except ValueError as exc:
            logger.error("Updates proxy configuration error: %s", exc)
            raise

    return get_proxy_url()


def proxy_is_configured() -> bool:
    try:
        return bool(get_proxy_url())
    except ValueError:
        return False


def proxy_scheme(url: str) -> str:
    return (urlparse(_clean(url)).scheme or "").lower()


def is_socks_proxy(url: str) -> bool:
    return proxy_scheme(url) in SOCKS_SCHEMES


def socks_support_available() -> bool:
    """آیا بسته `socksio` نصب است؟ (لازمه‌ی SOCKS5 در httpx)"""

    try:
        import socksio  # noqa: F401
    except Exception:
        return False

    return True


def verify_proxy_dependencies(url: str) -> None:
    """
    اگر پروکسی SOCKS تنظیم شده ولی پکیج لازم نصب نیست،
    با پیام واضح متوقف می‌شود (به جای خطای مبهم httpx).
    """

    if is_socks_proxy(url) and not socks_support_available():
        raise RuntimeError(
            "پروکسی SOCKS تنظیم شده ولی بسته `socksio` نصب نیست.\n"
            "اجرا کنید:  pip install socksio\n"
            "یا:          pip install -r requirements.txt"
        )


def mask_proxy(url: str) -> str:
    """آدرس پروکسی را برای لاگ/نمایش، بدون یوزرنیم و پسورد برمی‌گرداند."""

    value = _clean(url)

    if not value:
        return "بدون پروکسی"

    try:
        parsed = urlparse(value)
    except Exception:
        return "***"

    host = parsed.hostname or ""
    port = parsed.port or ""
    auth = "***@" if (parsed.username or parsed.password) else ""
    scheme = parsed.scheme or "http"

    return f"{scheme}://{auth}{host}:{port}"


def proxy_for_all_traffic() -> bool:
    """
    آیا پروکسی برای همه‌ی ترافیک (بازار، اخبار، اسکنر) هم اعمال شود؟

    پیش‌فرض: خیر.

    دلیل: بعضی از پروکسی‌ها فقط اجازه‌ی دسترسی به تلگرام را می‌دهند.
    اگر همه‌ی درخواست‌ها را به آن‌ها بفرستیم، تب‌های بازار/اخبار که
    قبلا مستقیم کار می‌کردند خراب می‌شوند. پس فقط وقتی خودتان
    مطمئن هستید پروکسی عمومی است، آن را با
    `BOT_PROXY_FOR_ALL=1` روشن کنید.
    """

    for name in (
        "BOT_PROXY_FOR_ALL",
        "BOT_PROXY_APPLY_TO_ALL",
    ):
        raw = _clean(os.getenv(name))

        if raw:
            return raw.lower() in {"1", "true", "yes", "on"}

    return False


def configure_proxy_environment() -> str:
    """
    پروکسی ربات را در محیط سیستم هم ست می‌کند (اختیاری).

    اگر `BOT_PROXY_FOR_ALL=1` باشد، سرویس‌هایی که با `requests`
    کار می‌کنند (بازار، اخبار، اسکنر PLT) هم از همان پروکسی رد
    می‌شوند.

    مقادیری که کاربر خودش ست کرده باشد بازنویسی نمی‌شوند.
    """

    try:
        url = get_proxy_url()
    except ValueError:
        return ""

    if not url:
        return ""

    verify_proxy_dependencies(url)

    if not proxy_for_all_traffic():
        logger.info(
            "پروکسی فقط برای تلگرام اعمال شد. برای اعمال روی همه‌ی "
            "درخواست‌ها (بازار/اخبار) BOT_PROXY_FOR_ALL=1 بگذارید."
        )
        return url

    for name in ("ALL_PROXY", "all_proxy", "HTTPS_PROXY", "https_proxy"):
        if not _clean(os.getenv(name)):
            os.environ[name] = url

    logger.info(
        "پروکسی برای همه‌ی درخواست‌های خروجی اعمال شد."
    )

    return url

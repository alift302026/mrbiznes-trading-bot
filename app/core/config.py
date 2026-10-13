import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")


BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

# Force override if old brand metatraid is present in env variables
raw_channel = os.getenv("REQUIRED_CHANNEL", "@MrBiznesMarket").strip()
if not raw_channel or "metatraid" in raw_channel.lower():
    REQUIRED_CHANNEL = "@MrBiznesMarket"
else:
    REQUIRED_CHANNEL = raw_channel

raw_url = os.getenv("REQUIRED_CHANNEL_URL", "https://t.me/MrBiznesMarket").strip()
if not raw_url or "metatraid" in raw_url.lower():
    REQUIRED_CHANNEL_URL = "https://t.me/MrBiznesMarket"
else:
    REQUIRED_CHANNEL_URL = raw_url


def parse_admin_ids() -> set[int]:
    output = set()

    raw = os.getenv(
        "ADMIN_IDS",
        "",
    )

    for item in raw.split(","):
        item = item.strip()

        if item.isdigit():
            output.add(int(item))

    return output


ADMIN_IDS = parse_admin_ids()

# XT Exchange Credentials
XT_API_KEY = os.getenv("XT_API_KEY", "").strip()
XT_SECRET_KEY = os.getenv("XT_SECRET_KEY", "").strip()
XT_ACCESS_KEY = os.getenv("XT_ACCESS_KEY", XT_API_KEY).strip()

# Other API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
TWELVE_DATA_API_KEY = os.getenv("TWELVE_DATA_API_KEY", "").strip()

WELCOME_IMAGE = (
    BASE_DIR
    / "assets"
    / "welcome.jpg"
)


# ============================================================
# NETWORK / PROXY  (برای سرورهای داخل ایران)
# ============================================================

from app.core.proxy import (  # noqa: E402
    configure_proxy_environment,
    get_proxy_url,
    get_updates_proxy_url,
    is_socks_proxy,
    mask_proxy,
    proxy_is_configured,
    verify_proxy_dependencies,
)


def _float_env(
    name,
    default,
):
    raw = os.getenv(
        name,
        "",
    ).strip()

    if not raw:
        return default

    try:
        value = float(raw)

    except ValueError:
        return default

    return value if value > 0 else default


# 0 یعنی مقدار پیش‌فرض کتابخانه (۵ ثانیه) استفاده شود.
# روی اینترنت ناپایدار ایران می‌توانید مثلا 20 بگذارید.
BOT_CONNECT_TIMEOUT = _float_env(
    "BOT_CONNECT_TIMEOUT",
    0,
)

BOT_READ_TIMEOUT = _float_env(
    "BOT_READ_TIMEOUT",
    0,
)

BOT_POOL_TIMEOUT = _float_env(
    "BOT_POOL_TIMEOUT",
    0,
)

BOT_DROP_PENDING_UPDATES = (
    os.getenv(
        "BOT_DROP_PENDING_UPDATES",
        "0",
    ).strip()
    == "1"
)


def validate_bot_token():
    """
    توکن ربات را بررسی می‌کند.

    برمی‌گرداند: (سالم است؟, پیام توضیحی)
    """

    token = BOT_TOKEN

    if not token:
        return (
            False,
            "متغیر BOT_TOKEN خالی است. مقدار آن را در فایل .env "
            "یا در Variables سرور (Railway/لیارا/…) تنظیم کنید.",
        )

    if ":" not in token:
        return (
            False,
            "فرمت BOT_TOKEN درست نیست (باید شبیه "
            "123456789:AA.... باشد). توکن کامل را از @BotFather بگیرید.",
        )

    head, _, tail = token.partition(":")

    if not head.isdigit() or len(tail) < 30:
        return (
            False,
            "فرمت BOT_TOKEN درست نیست (باید شبیه "
            "123456789:AA.... باشد). توکن کامل را از @BotFather بگیرید.",
        )

    return True, "BOT_TOKEN سالم است."


def admin_ids_status():
    """وضعیت ADMIN_IDS برای پیام‌های راهنما."""

    if not ADMIN_IDS:
        return (
            False,
            "ADMIN_IDS خالی است. برای دسترسی به پنل ادمین، شناسه عددی "
            "تلگرام خود را در ADMIN_IDS بگذارید (چند شناسه با کاما). "
            "شناسه را با ارسال /id به ربات یا از @userinfobot می‌گیرید.",
        )

    return True, "ADMIN_IDS تنظیم شده است."

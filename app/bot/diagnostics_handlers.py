"""
دستورهای تشخیصی ربات — MrBiznes
================================

این دستورها برای «چک کردن» ربات از داخل تلگرام ساخته شده‌اند:

    /id     → شناسه عددی تلگرام شما (برای گذاشتن در ADMIN_IDS)
    /ping   → سرعت پاسخ‌دهی ربات به تلگرام
    /diag   → گزارش کامل سلامت (فقط ادمین‌ها)

هیچ‌کدام از این دستورها داده‌ی حساسی برنمی‌گردانند؛ توکن و کلیدهای
API فقط به صورت «تنظیم شده / تنظیم نشده» گزارش می‌شوند.
"""

from __future__ import annotations

import asyncio
import logging
import os
import platform
import time
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import (
    ContextTypes,
)

from app.core.config import (
    ADMIN_IDS,
    OPENAI_API_KEY,
    OPENROUTER_API_KEY,
    REQUIRED_CHANNEL,
    REQUIRED_CHANNEL_URL,
    TWELVE_DATA_API_KEY,
    XT_API_KEY,
    XT_SECRET_KEY,
)
from app.core.proxy import (
    get_proxy_url,
    mask_proxy,
)
from app.models.database import (
    DATABASE_PATH,
    SessionLocal,
)
from app.models.user import User

logger = logging.getLogger(__name__)

TEHRAN_TZ = timezone(
    timedelta(hours=3, minutes=30)
)

STARTED_AT = time.monotonic()

TELEGRAM_API_URL = "https://api.telegram.org/"


# ============================================================
# HELPERS
# ============================================================

def _is_admin(user_id) -> bool:
    return user_id in ADMIN_IDS


def _uptime_text() -> str:

    seconds = int(
        time.monotonic() - STARTED_AT
    )

    days, rest = divmod(
        seconds,
        86400,
    )

    hours, rest = divmod(
        rest,
        3600,
    )

    minutes, secs = divmod(
        rest,
        60,
    )

    parts = []

    if days:
        parts.append(f"{days} روز")

    if hours or days:
        parts.append(f"{hours} ساعت")

    parts.append(f"{minutes} دقیقه")

    if not days:
        parts.append(f"{secs} ثانیه")

    return " و ".join(parts)


def _flag(value) -> str:
    return "✅" if value else "❌"


def _user_stats():

    try:

        with SessionLocal() as db:

            total = db.scalar(
                select(func.count(User.id))
            ) or 0

            banned = db.scalar(
                select(func.count(User.id)).where(
                    User.is_banned.is_(True)
                )
            ) or 0

        return total, banned

    except Exception as exc:

        logger.warning(
            "user stats error: %s",
            exc,
        )

        return None, None


def _probe_url(
    url,
    proxy=None,
    timeout=6.0,
):
    """
    یک درخواست HTTPS ساده به تلگرام.

    برمی‌گرداند: (موفق؟, متن نتیجه)
    """

    try:
        import httpx

    except Exception as exc:  # pragma: no cover
        return False, f"httpx نصب نیست ({exc})"

    started = time.perf_counter()

    try:

        kwargs = {
            "timeout": timeout,
            "follow_redirects": True,
            "headers": {
                "User-Agent": "MrBiznes-Doctor",
            },
        }

        if proxy:
            kwargs["proxy"] = proxy

        response = httpx.get(
            url,
            **kwargs,
        )

        elapsed = int(
            (time.perf_counter() - started) * 1000
        )

        return (
            response.status_code < 500,
            f"HTTP {response.status_code} در {elapsed}ms",
        )

    except Exception as exc:

        return False, f"{type(exc).__name__}: {str(exc)[:120]}"


async def _network_report():

    proxy = ""

    try:

        proxy = get_proxy_url()

    except ValueError as exc:

        return (
            f"⚠️ تنظیمات پروکسی نامعتبر: {exc}"
        )

    lines = []

    # اتصال مستقیم
    direct_ok, direct_text = await asyncio.to_thread(
        _probe_url,
        TELEGRAM_API_URL,
        None,
        5.0,
    )

    lines.append(
        f"{_flag(direct_ok)} اتصال مستقیم: {direct_text}"
    )

    # اتصال از پروکسی (اگر تنظیم شده)
    if proxy:

        proxy_ok, proxy_text = await asyncio.to_thread(
            _probe_url,
            TELEGRAM_API_URL,
            proxy,
            8.0,
        )

        lines.append(
            f"{_flag(proxy_ok)} پروکسی "
            f"{mask_proxy(proxy)}: {proxy_text}"
        )

    else:

        lines.append(
            "ℹ️ پروکسی تنظیم نشده (BOT_PROXY_URL خالی است)."
        )

    return "\n".join(lines)


def diag_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🔄 بروزرسانی",
                    callback_data="diag_refresh",
                ),
                InlineKeyboardButton(
                    "🏓 پینگ",
                    callback_data="diag_ping",
                ),
            ]
        ]
    )


def _diag_header():

    now = datetime.now(
        TEHRAN_TZ
    )

    return (
        "🩺 گزارش سلامت MrBiznes\n"
        "━━━━━━━━━━━━━━━━\n"
        f"🕒 زمان تهران: "
        f"{now.strftime('%Y-%m-%d %H:%M')}\n"
        f"⏱ مدت اجرا: {_uptime_text()}\n"
    )


# ============================================================
# /id
# ============================================================

async def telegram_id_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user = update.effective_user

    if user is None or update.message is None:
        return

    is_admin = _is_admin(user.id)

    lines = [
        "🆔 شناسه تلگرام شما",
        "━━━━━━━━━━━━━━━━",
        f"User ID: {user.id}",
    ]

    if user.username:
        lines.append(
            f"Username: @{user.username}"
        )

    if user.first_name:
        lines.append(
            f"Name: {user.first_name}"
        )

    if is_admin:

        lines.append("")
        lines.append(
            "✅ این شناسه در ADMIN_IDS سرور ثبت شده است؛ "
            "شما ادمین هستید (/diag را بزنید)."
        )

    else:

        lines.append("")
        lines.append(
            "⛔️ این شناسه در ADMIN_IDS سرور نیست."
        )
        lines.append(
            "برای ادمین شدن، همین عدد را در متغیر ADMIN_IDS "
            "بگذارید و ربات را ری‌استارت کنید. مثال:\n"
            f"ADMIN_IDS={user.id}"
        )

        if not ADMIN_IDS:

            lines.append("")
            lines.append(
                "ℹ️ الان ADMIN_IDS روی سرور خالی است."
            )

    await update.message.reply_text(
        "\n".join(lines)
    )


# ============================================================
# /ping
# ============================================================

async def ping_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if update.message is None:
        return

    started = time.perf_counter()

    try:

        await context.bot.get_me()

    except Exception as exc:

        await update.message.reply_text(
            "❌ ارتباط با تلگرام برقرار نشد.\n"
            f"خطا: {type(exc).__name__}: {str(exc)[:150]}"
        )

        return

    elapsed = int(
        (time.perf_counter() - started) * 1000
    )

    await update.message.reply_text(
        "🏓 Pong\n"
        f"⏱ {elapsed} میلی‌ثانیه"
    )


# ============================================================
# /diag
# ============================================================

async def diagnostics_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user = update.effective_user

    if user is None or update.message is None:
        return

    if not _is_admin(user.id):

        await update.message.reply_text(
            "⛔️ این دستور فقط برای ادمین است.\n"
            "با /id شناسه خودتان را ببینید و آن را در ADMIN_IDS "
            "سرور قرار دهید."
        )

        return

    text = await build_diagnostics(
        context,
        user,
    )

    await update.message.reply_text(
        text,
        reply_markup=diag_keyboard(),
        disable_web_page_preview=True,
    )


async def build_diagnostics(
    context,
    user,
):

    lines = [_diag_header()]

    # ---- BOT -------------------------------------------------
    bot_username = getattr(
        context.bot,
        "username",
        None,
    )

    bot_id = getattr(
        context.bot,
        "id",
        None,
    )

    started = time.perf_counter()

    api_ok = True
    api_error = ""

    try:

        me = await asyncio.wait_for(
            context.bot.get_me(),
            timeout=15,
        )

        bot_username = me.username
        bot_id = me.id

    except Exception as exc:

        api_ok = False
        api_error = (
            f"{type(exc).__name__}: {str(exc)[:120]}"
        )

    rtt = int(
        (time.perf_counter() - started) * 1000
    )

    lines.append(
        f"🤖 ربات: @{bot_username or '?'} "
        f"(id: {bot_id or '?'})"
    )

    if api_ok:
        lines.append(
            f"🌐 Telegram API: ✅ {rtt}ms"
        )
    else:
        lines.append(
            f"🌐 Telegram API: ❌ {api_error}"
        )

    # ---- PROXY ----------------------------------------------
    proxy = ""

    try:

        proxy = get_proxy_url()

    except ValueError as exc:

        lines.append(
            f"🛰 پروکسی: ⚠️ نامعتبر ({exc})"
        )

    else:

        lines.append(
            "🛰 پروکسی: "
            + (
                mask_proxy(proxy)
                if proxy
                else "— (اتصال مستقیم)"
            )
        )

    # ---- ENVIRONMENT ----------------------------------------
    lines.append(
        f"🧠 Python {platform.python_version()} | "
        f"{platform.system()} | PTB {_ptb_version()}"
    )

    lines.append(
        f"📦 نسخه پروژه: {_git_revision()}"
    )

    # ---- DATABASE -------------------------------------------
    total, banned = _user_stats()

    lines.append(
        f"🗄 دیتابیس: {DATABASE_PATH.name} | "
        f"کاربران: {total if total is not None else '؟'}"
        + (
            f" | بلاک: {banned}"
            if banned
            else ""
        )
    )

    # ---- ADMINS ---------------------------------------------
    lines.append(
        f"👤 ادمین‌ها: {len(ADMIN_IDS)} "
        f"({', '.join(str(x) for x in sorted(ADMIN_IDS)) or '—'})"
    )

    lines.append(
        f"📢 کانال اجباری: "
        f"{REQUIRED_CHANNEL or '— (غیرفعال)'}"
    )

    # ---- API KEYS -------------------------------------------
    keys = [
        ("XT", bool(XT_API_KEY and XT_SECRET_KEY)),
        ("TwelveData", bool(TWELVE_DATA_API_KEY)),
        ("OpenAI", bool(OPENAI_API_KEY)),
        ("OpenRouter", bool(OPENROUTER_API_KEY)),
        (
            "LiveCoinWatch",
            bool(
                os.getenv(
                    "LIVECOINWATCH_API_KEY",
                    "",
                ).strip()
            ),
        ),
    ]

    lines.append(
        "🔑 کلیدها: "
        + " | ".join(
            f"{name} {_flag(ok)}"
            for name, ok in keys
        )
    )

    # ---- WORKERS --------------------------------------------
    job_queue = getattr(
        context.application,
        "job_queue",
        None,
    )

    if job_queue is None:

        lines.append(
            "⏰ Job Queue: ❌ غیرفعال "
            "(python-telegram-bot[job-queue] نصب نیست)"
        )

    else:

        jobs = job_queue.jobs()

        lines.append(
            f"⏰ Job Queue: ✅ فعال ({len(jobs)} کار زمان‌بندی‌شده)"
        )

    # ---- FILES ----------------------------------------------
    data_dir = DATABASE_PATH.parent

    lines.append(
        f"📁 پوشه data: "
        f"{_flag(os.access(data_dir, os.W_OK))} "
        f"({data_dir})"
    )

    # ---- NETWORK --------------------------------------------
    lines.append("")
    lines.append("🌍 تست شبکه از خود سرور:")
    lines.append(
        await _network_report()
    )

    lines.append("")
    lines.append(
        "راهنما: SETUP_FA.md | چک قبل از اجرا: "
        "python scripts/doctor.py"
    )

    return "\n".join(lines)


def _ptb_version():

    try:

        import telegram

        return telegram.__version__

    except Exception:

        return "?"


def _git_revision():

    path = os.path.join(
        os.path.dirname(
            os.path.dirname(
                os.path.dirname(
                    os.path.abspath(__file__)
                )
            )
        ),
        ".git",
        "HEAD",
    )

    try:

        with open(
            path,
            encoding="utf-8",
        ) as handle:

            head = handle.read().strip()

        if head.startswith("ref:"):

            ref_path = os.path.join(
                os.path.dirname(path),
                head.split(
                    " ",
                    1,
                )[1].strip(),
            )

            with open(
                ref_path,
                encoding="utf-8",
            ) as handle:

                return handle.read().strip()[:7]

        return head[:7]

    except Exception:

        return "?"


async def diag_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if query is None:
        return

    if not _is_admin(query.from_user.id):

        await query.answer(
            "⛔️ فقط ادمین",
            show_alert=True,
        )

        return

    if query.data == "diag_ping":

        started = time.perf_counter()

        try:

            await context.bot.get_me()

            elapsed = int(
                (time.perf_counter() - started) * 1000
            )

            await query.answer(
                f"🏓 {elapsed}ms",
            )

        except Exception as exc:

            await query.answer(
                f"❌ {str(exc)[:180]}",
                show_alert=True,
            )

        return

    await query.answer(
        "بروزرسانی شد"
    )

    text = await build_diagnostics(
        context,
        query.from_user,
    )

    try:

        await query.edit_message_text(
            text,
            reply_markup=diag_keyboard(),
            disable_web_page_preview=True,
        )

    except Exception:

        await query.message.reply_text(
            text,
            reply_markup=diag_keyboard(),
            disable_web_page_preview=True,
        )

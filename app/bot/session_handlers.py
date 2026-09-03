import asyncio
import logging
from io import BytesIO

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    Update,
)
from telegram.ext import (
    ContextTypes,
)

from app.engines.sessions.session_engine import (
    active_sessions,
    all_sessions,
    current_overlap,
    date_center,
    next_session,
    weekly_forex_status,
)
from app.i18n.translations import t
from app.services.session_clock_renderer import render_session_clock
from app.services.user_service import (
    get_user,
    toggle_session_alerts,
)

logger = logging.getLogger(__name__)


def session_keyboard(
    telegram_id,
):
    user = get_user(telegram_id)
    enabled = user.session_alerts_enabled if user else False

    alert_label = "🔕 خاموش کردن اعلان سشن‌ها" if enabled else "🔔 فعال‌سازی اعلان سشن‌ها"

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🔄 بروزرسانی ساعت و وضعیت",
                    callback_data="session_refresh",
                )
            ],
            [
                InlineKeyboardButton(
                    alert_label,
                    callback_data="session_toggle",
                )
            ],
        ]
    )


def build_session_caption(
    telegram_id,
):
    data = date_center()
    sessions = all_sessions()
    actives = [s for s in sessions if s["is_open"]]
    weekly = weekly_forex_status()

    user = get_user(telegram_id)
    alert_status = "🔔 روشن" if (user and user.session_alerts_enabled) else "🔕 خاموش"

    active_names = " ، ".join([f"{s['flag']} {s['name']}" for s in actives]) if actives else "هیچ سشنی در حال حاضر فعال نیست"

    lines = [
        "🌍 مرکز سشن‌های معاملاتی جهانی (MrBiznes)",
        "━━━━━━━━━━━━━━━━━━━━━━",
        f"📅 تاریخ شمسی: {data['jalali']}",
        f"🌍 تاریخ میلادی: {data['gregorian']}",
        f"🇮🇷 ساعت رسمی تهران: {data['tehran_time']}",
        f"🌐 ساعت جهانی UTC: {data['utc_time']}",
        "━━━━━━━━━━━━━━━━━━━━━━",
        f"🟢 سشن‌های فعال هم‌اکنون: {active_names}",
        "",
        "⏰ ساعات فعالیت سشن‌ها به وقت تهران:",
        "• 🇦🇺 سیدنی: ۰۱:۳۰ تا ۱۰:۳۰",
        "• 🇯🇵 توکیو: ۰۳:۳۰ تا ۱۲:۳۰",
        "• 🇬🇧 لندن: ۱۱:۳۰ تا ۲۰:۳۰",
        "• 🇺🇸 نیویورک: ۱۶:۳۰ تا ۰۱:۳۰ بامداد",
        "━━━━━━━━━━━━━━━━━━━━━━",
        f"📊 وضعیت بازار هفتگی فارکس: {'🟢 باز' if weekly['market_open'] else '🔴 تعطیلات آخر هفته'}",
        f"🔔 وضعیت آلارم تغییر سشن: {alert_status}",
    ]

    return "\n".join(lines)


async def sessions_page(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    telegram_id = update.effective_user.id

    try:
        clock_img = await asyncio.to_thread(render_session_clock)
        caption = build_session_caption(telegram_id)

        await update.message.reply_photo(
            photo=clock_img,
            caption=caption,
            reply_markup=session_keyboard(telegram_id),
        )
    except Exception as exc:
        logger.warning("Session page image error: %s", exc)
        await update.message.reply_text(
            build_session_caption(telegram_id),
            reply_markup=session_keyboard(telegram_id),
        )


async def session_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    if query is None:
        return

    await query.answer()
    telegram_id = query.from_user.id

    if query.data == "session_toggle":
        toggle_session_alerts(telegram_id)

    caption = build_session_caption(telegram_id)
    try:
        clock_img = await asyncio.to_thread(render_session_clock)
        media = InputMediaPhoto(media=clock_img, caption=caption)
        await query.edit_message_media(
            media=media,
            reply_markup=session_keyboard(telegram_id),
        )
    except Exception as exc:
        logger.debug("Session edit photo fallback: %s", exc)
        try:
            await query.edit_message_caption(
                caption=caption,
                reply_markup=session_keyboard(telegram_id),
            )
        except Exception:
            pass

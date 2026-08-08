import os

from dotenv import load_dotenv

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)

from telegram.ext import ContextTypes

from app.services.user_service import (
    all_users_count,
    registered_users_count,
    vip_users_count,
)


load_dotenv()


# ============================================================
# ADMIN SECURITY
# ============================================================

def get_admin_ids() -> set[int]:

    raw = os.getenv(
        "ADMIN_IDS",
        "",
    )

    result = set()

    for item in raw.split(","):

        item = item.strip()

        if item.isdigit():

            result.add(
                int(item)
            )

    return result


def is_admin(
    telegram_id: int,
) -> bool:

    return (
        telegram_id
        in get_admin_ids()
    )


# ============================================================
# ADMIN KEYBOARD
# ============================================================

def admin_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "👥 کاربران",
                    callback_data="admin_users",
                ),

                InlineKeyboardButton(
                    "💎 VIP",
                    callback_data="admin_vip",
                ),
            ],

            [
                InlineKeyboardButton(
                    "📡 سیگنال‌ها",
                    callback_data="admin_signals",
                ),

                InlineKeyboardButton(
                    "💳 پرداخت‌ها",
                    callback_data="admin_payments",
                ),
            ],

            [
                InlineKeyboardButton(
                    "🎟 کد تخفیف",
                    callback_data="admin_discounts",
                ),

                InlineKeyboardButton(
                    "⭐ امتیازها",
                    callback_data="admin_points",
                ),
            ],

            [
                InlineKeyboardButton(
                    "📈 عملکرد ماهانه",
                    callback_data="admin_performance",
                ),
            ],

            [
                InlineKeyboardButton(
                    "📢 ارسال همگانی",
                    callback_data="admin_broadcast",
                ),
            ],

            [
                InlineKeyboardButton(
                    "⚙️ تنظیمات",
                    callback_data="admin_settings",
                ),

                InlineKeyboardButton(
                    "📊 آمار",
                    callback_data="admin_stats",
                ),
            ],
        ]
    )


# ============================================================
# ADMIN HOME
# ============================================================

async def admin_page(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    telegram_id = (
        update.effective_user.id
    )

    if not is_admin(
        telegram_id
    ):

        await update.message.reply_text(
            "⛔ دسترسی غیرمجاز."
        )

        return

    text = (
        "🛡 ALIFT ADMIN PANEL\n"
        "━━━━━━━━━━━━━━━━\n\n"
        "👑 دسترسی مدیریت تأیید شد.\n\n"
        "از این بخش می‌توانی قسمت‌های "
        "پلتفرم را مدیریت کنی."
    )

    await update.message.reply_text(
        text,
        reply_markup=admin_keyboard(),
    )


# ============================================================
# STATISTICS
# ============================================================

def statistics_text():

    users = (
        all_users_count()
    )

    registered = (
        registered_users_count()
    )

    vip = (
        vip_users_count()
    )

    normal = max(
        users - vip,
        0,
    )

    return (
        "📊 PLATFORM STATISTICS\n"
        "━━━━━━━━━━━━━━━━\n\n"

        f"👥 کل کاربران: {users}\n"
        f"✅ ثبت‌نام‌شده: {registered}\n"
        f"👤 Normal: {normal}\n"
        f"💎 VIP: {vip}"
    )


# ============================================================
# ADMIN CALLBACK ROUTER
# ============================================================

async def admin_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = (
        update.callback_query
    )

    telegram_id = (
        query.from_user.id
    )

    if not is_admin(
        telegram_id
    ):

        await query.answer(
            "⛔ Access denied",
            show_alert=True,
        )

        return

    await query.answer()

    action = (
        query.data
    )

    # --------------------------------------------------------
    # USERS
    # --------------------------------------------------------

    if action == "admin_users":

        text = (
            "👥 USER MANAGEMENT\n"
            "━━━━━━━━━━━━━━━━\n\n"

            "این بخش برای:\n\n"

            "🔎 جستجوی کاربر\n"
            "🚫 Ban / Unban\n"
            "💎 VIP Management\n"
            "⭐ Points\n"
            "📱 User Profile\n\n"

            "در مرحله مدیریت کاربران "
            "فعال می‌شود."
        )

    # --------------------------------------------------------
    # VIP
    # --------------------------------------------------------

    elif action == "admin_vip":

        text = (
            "💎 VIP MANAGEMENT\n"
            "━━━━━━━━━━━━━━━━\n\n"

            "➕ فعال‌سازی VIP\n"
            "➖ حذف VIP\n"
            "📆 تمدید اشتراک\n"
            "⏳ مشاهده انقضا"
        )

    # --------------------------------------------------------
    # SIGNALS
    # --------------------------------------------------------

    elif action == "admin_signals":

        text = (
            "📡 SIGNAL MANAGEMENT\n"
            "━━━━━━━━━━━━━━━━\n\n"

            "🆓 Free Signal\n"
            "💎 VIP Signal\n"
            "📈 Spot\n"
            "⚡ Futures\n"
            "📜 Signal History\n"
            "📊 Performance"
        )

    # --------------------------------------------------------
    # PAYMENTS
    # --------------------------------------------------------

    elif action == "admin_payments":

        text = (
            "💳 PAYMENT MANAGEMENT\n"
            "━━━━━━━━━━━━━━━━\n\n"

            "₿ Bitcoin\n"
            "Ξ Ethereum\n"
            "🔴 TRON\n"
            "◎ Solana\n"
            "₮ USDT\n\n"

            "🔎 Transaction Monitor\n"
            "✅ Confirmed\n"
            "⏳ Pending\n"
            "❌ Failed"
        )

    # --------------------------------------------------------
    # DISCOUNTS
    # --------------------------------------------------------

    elif action == "admin_discounts":

        text = (
            "🎟 DISCOUNT MANAGEMENT\n"
            "━━━━━━━━━━━━━━━━\n\n"

            "➕ ساخت کد تخفیف\n"
            "❌ غیرفعال‌سازی\n"
            "📆 تعیین تاریخ انقضا\n"
            "📊 مشاهده استفاده"
        )

    # --------------------------------------------------------
    # POINTS
    # --------------------------------------------------------

    elif action == "admin_points":

        text = (
            "⭐ POINT MANAGEMENT\n"
            "━━━━━━━━━━━━━━━━\n\n"

            "➕ افزایش امتیاز\n"
            "➖ کاهش امتیاز\n"
            "🎁 Referral Rewards\n"
            "🏆 User Levels"
        )

    # --------------------------------------------------------
    # PERFORMANCE
    # --------------------------------------------------------

    elif action == "admin_performance":

        text = (
            "📈 MONTHLY PERFORMANCE\n"
            "━━━━━━━━━━━━━━━━\n\n"

            "عملکرد فقط بر اساس "
            "سیگنال‌های بسته‌شده واقعی "
            "محاسبه خواهد شد."
        )

    # --------------------------------------------------------
    # BROADCAST
    # --------------------------------------------------------

    elif action == "admin_broadcast":

        text = (
            "📢 BROADCAST CENTER\n"
            "━━━━━━━━━━━━━━━━\n\n"

            "در این قسمت بعداً می‌توانی "
            "پیام را برای کاربران ارسال کنی.\n\n"

            "ارسال گروهی با Rate Limit "
            "و گزارش موفق/ناموفق انجام می‌شود."
        )

    # --------------------------------------------------------
    # SETTINGS
    # --------------------------------------------------------

    elif action == "admin_settings":

        text = (
            "⚙️ PLATFORM SETTINGS\n"
            "━━━━━━━━━━━━━━━━\n\n"

            "🌐 Languages\n"
            "🌍 Sessions\n"
            "📊 Market Providers\n"
            "📢 Channels\n"
            "💎 VIP Plans\n"
            "🔔 Alerts"
        )

    # --------------------------------------------------------
    # STATISTICS
    # --------------------------------------------------------

    elif action == "admin_stats":

        text = (
            statistics_text()
        )

    else:

        text = (
            "🛡 ALIFT ADMIN PANEL"
        )

    await query.edit_message_text(
        text,
        reply_markup=(
            admin_keyboard()
        ),
    )
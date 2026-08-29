from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)

from telegram.ext import (
    ContextTypes,
)


# ============================================================
# PROJECT INFO
# ============================================================

PROJECT_NAME = "MrBiznes"
PROJECT_VERSION = "0.3 Beta"


# ============================================================
# ABOUT TEXT
# ============================================================

def about_text():

    return (
        "🤝 MrBiznes\n"
        "━━━━━━━━━━━━━━━━\n\n"

        "🚀 دستیار هوشمند معامله‌گران\n\n"

        "MrBiznes یک پلتفرم در حال توسعه برای "
        "کمک به معامله‌گران بازارهای مالی است.\n\n"

        "هدف MrBiznes این است که اطلاعات مهم بازار، "
        "ابزارهای تحلیلی و هشدارهای شخصی‌سازی‌شده را "
        "در یک محیط ساده و سریع در اختیار معامله‌گر قرار دهد.\n\n"

        "━━━━━━━━━━━━━━━━\n"
        "🧩 بخش‌های MrBiznes\n\n"

        "📊 داده‌های بازار\n"
        "🔔 Smart Alerts\n"
        "📡 Trading Signals\n"
        "🌍 Market Sessions\n"
        "📰 Market News\n"
        "👁 Watchlist\n"
        "🧠 Trading Psychology\n"
        "🤖 Analysis Tools\n"
        "🎁 Referral & Points\n"
        "💎 VIP Services\n"
        "🎧 Support Center\n\n"

        "━━━━━━━━━━━━━━━━\n"
        "🌐 آینده MrBiznes\n\n"

        "Telegram Bot\n"
        "Web Platform\n"
        "Android Application\n"
        "iOS Application\n\n"

        "━━━━━━━━━━━━━━━━\n"
        "🛡 اصل مهم MrBiznes\n\n"

        "MrBiznes در نسخه فعلی یک ابزار اطلاعاتی و "
        "تحلیلی است و بدون درخواست و زیرساخت مشخص، "
        "معامله‌ای به جای کاربر اجرا نمی‌کند.\n\n"

        "⚠️ اطلاعات، تحلیل‌ها و سیگنال‌ها تضمین سود "
        "یا توصیه شخصی سرمایه‌گذاری نیستند. "
        "تصمیم نهایی و مدیریت ریسک بر عهده کاربر است.\n\n"

        f"⚙️ Version: {PROJECT_VERSION}\n\n"

        "🇮🇷 فارسی (همیشه جاویدان)\n"
        "🇬🇧 English\n"
        "🇸🇦 العربية"
    )


# ============================================================
# KEYBOARD
# ============================================================

def about_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🌐 وب‌سایت",
                    callback_data="about_website",
                ),

                InlineKeyboardButton(
                    "📱 شبکه‌های اجتماعی",
                    callback_data="about_social",
                ),
            ],

            [
                InlineKeyboardButton(
                    "🎧 پشتیبانی",
                    callback_data="about_support",
                ),

                InlineKeyboardButton(
                    "🤝 همکاری با ما",
                    callback_data="about_cooperation",
                ),
            ],

            [
                InlineKeyboardButton(
                    "🛡 حریم خصوصی",
                    callback_data="about_privacy",
                ),

                InlineKeyboardButton(
                    "📜 قوانین استفاده",
                    callback_data="about_terms",
                ),
            ],
        ]
    )


# ============================================================
# ABOUT HOME
# ============================================================

async def about_home(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    await update.message.reply_text(
        about_text(),
        reply_markup=(
            about_keyboard()
        ),
        disable_web_page_preview=True,
    )


# ============================================================
# CALLBACK
# ============================================================

async def about_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = (
        update.callback_query
    )

    if query is None:
        return

    await query.answer()

    data = (
        query.data
        or ""
    )

    if data == "about_home":

        await query.edit_message_text(
            about_text(),
            reply_markup=(
                about_keyboard()
            ),
            disable_web_page_preview=True,
        )

        return

    if data == "about_website":

        await query.edit_message_text(
            (
                "🌐 MrBiznes WEBSITE\n"
                "━━━━━━━━━━━━━━━━\n\n"

                "وب‌سایت رسمی MrBiznes در مرحله توسعه است.\n\n"

                "بعد از راه‌اندازی، حساب کاربری، "
                "Alertها، Signals، Watchlist و سایر "
                "سرویس‌ها بین Telegram، Website و "
                "اپلیکیشن‌ها هماهنگ خواهند بود."
            ),
            reply_markup=back_keyboard(),
        )

        return

    if data == "about_social":

        await query.edit_message_text(
            (
                "📱 MrBiznes SOCIAL\n"
                "━━━━━━━━━━━━━━━━\n\n"

                "کانال‌ها و شبکه‌های رسمی MrBiznes:\n\n"

                "📺 YouTube\n"
                "📸 Instagram\n"
                "𝕏 X\n"
                "💬 WhatsApp\n"
                "📢 Telegram\n\n"

                "لینک‌های رسمی پس از نهایی‌شدن "
                "از همین بخش در دسترس خواهند بود."
            ),
            reply_markup=back_keyboard(),
        )

        return

    if data == "about_support":

        await query.edit_message_text(
            (
                "🎧 MrBiznes SUPPORT\n"
                "━━━━━━━━━━━━━━━━\n\n"

                "برای ارتباط با پشتیبانی، از بخش "
                "«پشتیبانی» در منوی اصلی استفاده کن.\n\n"

                "سیستم Ticket برای پیگیری درخواست‌ها "
                "در ربات فعال است."
            ),
            reply_markup=back_keyboard(),
        )

        return

    if data == "about_cooperation":

        await query.edit_message_text(
            (
                "🤝 همکاری با MrBiznes\n"
                "━━━━━━━━━━━━━━━━\n\n"

                "زمینه‌های همکاری آینده:\n\n"

                "📊 تحلیل‌گران بازار\n"
                "📡 Signal Providers\n"
                "📰 تولیدکنندگان محتوا و خبر\n"
                "🏦 صرافی‌ها و مجموعه‌های مالی\n"
                "💻 توسعه نرم‌افزار\n"
                "📣 همکاری رسانه‌ای و تجاری\n\n"

                "فرآیند رسمی همکاری در مراحل بعد "
                "به Support Center متصل می‌شود."
            ),
            reply_markup=back_keyboard(),
        )

        return

    if data == "about_privacy":

        await query.edit_message_text(
            (
                "🛡 حریم خصوصی\n"
                "━━━━━━━━━━━━━━━━\n\n"

                "MrBiznes اصل حداقل‌سازی اطلاعات کاربران "
                "را در طراحی سیستم دنبال می‌کند.\n\n"

                "🔐 اطلاعات محرمانه و کلیدهای خصوصی "
                "کیف پول نباید از کاربران دریافت شوند.\n\n"

                "🔐 اطلاعات امنیتی سیستم نیز خارج از "
                "سورس عمومی نگهداری می‌شوند.\n\n"

                "نسخه کامل Privacy Policy همزمان با "
                "راه‌اندازی وب‌سایت منتشر خواهد شد."
            ),
            reply_markup=back_keyboard(),
        )

        return

    if data == "about_terms":

        await query.edit_message_text(
            (
                "📜 قوانین استفاده\n"
                "━━━━━━━━━━━━━━━━\n\n"

                "استفاده از MrBiznes به معنی پذیرش این است "
                "که بازارهای مالی دارای ریسک هستند.\n\n"

                "MrBiznes تضمینی درباره سود، بازده یا "
                "نتیجه معاملات ارائه نمی‌کند.\n\n"

                "کاربر مسئول تصمیم معاملاتی، مدیریت "
                "سرمایه و مدیریت ریسک خود است.\n\n"

                "نسخه کامل Terms of Service هنگام "
                "راه‌اندازی عمومی منتشر خواهد شد."
            ),
            reply_markup=back_keyboard(),
        )


# ============================================================
# BACK
# ============================================================

def back_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "⬅️ بازگشت به درباره ما",
                    callback_data="about_home",
                )
            ]
        ]
    )
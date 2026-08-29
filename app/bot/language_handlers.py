from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)

from telegram.ext import (
    ContextTypes,
)

from app.bot.navigation import (
    main_menu,
)

from app.core.config import (
    ADMIN_IDS,
)

from app.i18n.translations import (
    t,
)

from app.services.user_service import (
    set_language,
)


# ============================================================
# SUPPORTED LANGUAGES
# ============================================================

SUPPORTED_LANGUAGES = {
    "fa",
    "en",
    "ar",
}


# ============================================================
# LANGUAGE KEYBOARD
# ============================================================

def language_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🇮🇷 فارسی (همیشه جاویدان)",
                    callback_data="lang_fa",
                )
            ],
            [
                InlineKeyboardButton(
                    "🇬🇧 English",
                    callback_data="lang_en",
                ),

                InlineKeyboardButton(
                    "🇸🇦 العربية",
                    callback_data="lang_ar",
                ),
            ],
        ]
    )


# ============================================================
# LANGUAGE PAGE
# ============================================================

async def language_page(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    text = (
        "🌐 ALIFT LANGUAGE\n"
        "━━━━━━━━━━━━━━━━\n\n"

        "🇮🇷 زبان خود را انتخاب کنید\n\n"
        "🇬🇧 Select your language\n\n"
        "🇸🇦 اختر لغتك"
    )

    # Opened from a normal Telegram message
    if update.message:

        await update.message.reply_text(
            text,
            reply_markup=(
                language_keyboard()
            ),
        )

        return

    # Also support opening from an inline callback
    if update.callback_query:

        await update.callback_query.edit_message_text(
            text,
            reply_markup=(
                language_keyboard()
            ),
        )


# ============================================================
# LANGUAGE CALLBACK
# ============================================================

async def language_callback(
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

    if not data.startswith(
        "lang_"
    ):
        return

    language = data.replace(
        "lang_",
        "",
        1,
    )

    if (
        language
        not in SUPPORTED_LANGUAGES
    ):

        await query.answer(
            "Invalid language",
            show_alert=True,
        )

        return

    saved = set_language(
        query.from_user.id,
        language,
    )

    if not saved:

        await query.answer(
            "Language could not be saved.",
            show_alert=True,
        )

        return

    await query.edit_message_text(
        t(
            language,
            "language_saved",
        )
    )

    await context.bot.send_message(
        chat_id=query.from_user.id,
        text=(
            f"🚀 {t(language, 'welcome')}\n\n"
            f"{t(language, 'choose')}"
        ),
        reply_markup=(
            main_menu(
                language,
                query.from_user.id
                in ADMIN_IDS,
            )
        ),
    )
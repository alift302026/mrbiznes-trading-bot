import logging
import os

from dotenv import (
    load_dotenv,
)

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)

from telegram.constants import (
    ChatMemberStatus,
)

from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from app.models.database import (
    Base,
    engine,
)

from app.models.user import User
from app.models.payment import Payment
from app.models.discount import DiscountCode
from app.models.performance import MonthlyPerformance

from app.bot.admin_handlers import (
    admin_callback,
    admin_page,
    is_admin,
)

from app.bot.general_handlers import (
    about_page,
    news_page,
    payment_page,
    referral_page,
    send_welcome,
)

from app.bot.market_handlers import (
    market_callback,
    market_home,
)

from app.bot.navigation import (
    contact_keyboard,
    main_menu,
)

from app.i18n.translations import (
    LANGUAGES,
    t,
)

from app.services.user_service import (
    get_or_create_user,
    get_user,
    save_phone_number,
    set_language,
)


load_dotenv()

BOT_TOKEN = os.getenv(
    "BOT_TOKEN"
)

REQUIRED_CHANNEL = os.getenv(
    "REQUIRED_CHANNEL",
    "",
)

REQUIRED_CHANNEL_URL = os.getenv(
    "REQUIRED_CHANNEL_URL",
    "",
)


logging.basicConfig(
    level=logging.INFO,
)

logger = logging.getLogger(
    "alift"
)


def language_keyboard():

    codes = list(
        LANGUAGES.items()
    )

    rows = []

    for i in range(
        0,
        len(codes),
        2,
    ):

        row = []

        for code, title in (
            codes[i:i + 2]
        ):

            row.append(
                InlineKeyboardButton(
                    title,
                    callback_data=(
                        f"lang_{code}"
                    ),
                )
            )

        rows.append(
            row
        )

    return InlineKeyboardMarkup(
        rows
    )


async def language_page(
    update,
):

    await update.message.reply_text(
        "🌐 Select Language",
        reply_markup=(
            language_keyboard()
        ),
    )


async def is_channel_member(
    user_id,
    context,
):

    if not REQUIRED_CHANNEL:
        return True

    try:

        member = await (
            context.bot
            .get_chat_member(
                REQUIRED_CHANNEL,
                user_id,
            )
        )

        return member.status in {
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER,
        }

    except Exception as exc:

        logger.error(
            "Channel check: %s",
            exc,
        )

        return False


def join_keyboard():

    rows = []

    if REQUIRED_CHANNEL_URL:

        rows.append(
            [
                InlineKeyboardButton(
                    "📢 Join Channel",
                    url=(
                        REQUIRED_CHANNEL_URL
                    ),
                )
            ]
        )

    rows.append(
        [
            InlineKeyboardButton(
                "✅ Check Membership",
                callback_data=(
                    "check_membership"
                ),
            )
        ]
    )

    return InlineKeyboardMarkup(
        rows
    )


async def require_channel(
    update,
    context,
):

    if await is_channel_member(
        update.effective_user.id,
        context,
    ):

        return True

    await update.message.reply_text(
        "🔒 Channel membership required.",
        reply_markup=join_keyboard(),
    )

    return False


async def start(
    update,
    context,
):

    tg = (
        update.effective_user
    )

    referral = None

    if context.args:

        possible = (
            context.args[0]
        )

        if possible.startswith(
            "ALIFT-"
        ):

            referral = possible

    user, created = (
        get_or_create_user(
            telegram_id=tg.id,
            username=tg.username,
            first_name=tg.first_name,
            referred_by=referral,
        )
    )

    if user.is_banned:

        await update.message.reply_text(
            "⛔ Account unavailable."
        )

        return

    if not await require_channel(
        update,
        context,
    ):

        return

    if not user.phone_number:

        await send_welcome(
            update
        )

        await update.message.reply_text(
            "📱 Complete registration:",
            reply_markup=(
                contact_keyboard()
            ),
        )

        return

    lang = user.language

    await update.message.reply_text(
        (
            f"🚀 {t(lang, 'welcome')}\n\n"
            f"{t(lang, 'choose')}"
        ),
        reply_markup=(
            main_menu(
                lang,
                is_admin(tg.id),
            )
        ),
    )


async def receive_contact(
    update,
    context,
):

    contact = (
        update.message.contact
    )

    if (
        not contact
        or contact.user_id
        != update.effective_user.id
    ):

        await update.message.reply_text(
            "❌ Please share your own "
            "Telegram phone number."
        )

        return

    save_phone_number(
        update.effective_user.id,
        contact.phone_number,
    )

    await language_page(
        update
    )


async def language_callback(
    update,
    context,
):

    query = (
        update.callback_query
    )

    await query.answer()

    lang = (
        query.data
        .replace(
            "lang_",
            "",
        )
    )

    if not set_language(
        query.from_user.id,
        lang,
    ):

        return

    user = get_user(
        query.from_user.id
    )

    await query.edit_message_text(
        "✅ Language saved."
    )

    await context.bot.send_message(
        chat_id=query.from_user.id,
        text=(
            f"🚀 {t(lang, 'welcome')}\n\n"
            f"{t(lang, 'choose')}"
        ),
        reply_markup=(
            main_menu(
                lang,
                is_admin(
                    query.from_user.id
                ),
            )
        ),
    )


async def membership_callback(
    update,
    context,
):

    query = (
        update.callback_query
    )

    await query.answer()

    if not await is_channel_member(
        query.from_user.id,
        context,
    ):

        await query.answer(
            "Not confirmed.",
            show_alert=True,
        )

        return

    await query.edit_message_text(
        "✅ Membership confirmed.\n"
        "Send /start"
    )


async def router(
    update,
    context,
):

    user = get_user(
        update.effective_user.id
    )

    if not user:

        return

    lang = user.language

    text = (
        update.message.text
    )

    if text == t(
        lang,
        "markets",
    ):

        await market_home(
            update,
            context,
        )

        return

    if text == t(
        lang,
        "vip",
    ):

        await payment_page(
            update
        )

        return

    if text == t(
        lang,
        "rewards",
    ):

        await referral_page(
            update,
            context,
        )

        return

    if text == t(
        lang,
        "news",
    ):

        await news_page(
            update
        )

        return

    if text == t(
        lang,
        "about",
    ):

        await about_page(
            update
        )

        return

    if text == t(
        lang,
        "language",
    ):

        await language_page(
            update
        )

        return

    if (
        text
        == t(
            lang,
            "admin",
        )
        and is_admin(
            update.effective_user.id
        )
    ):

        await admin_page(
            update,
            context,
        )

        return

    placeholders = {
        t(lang, "signals"):
            "📡 Free / VIP Signals",

        t(lang, "alerts"):
            "🔔 Alert Engine",

        t(lang, "watchlist"):
            "👁 Daily / Weekly Watchlist",

        t(lang, "sessions"):
            "🌍 Session Engine",

        t(lang, "psychology"):
            "🧠 Psychology Engine",

        t(lang, "analysis"):
            "🤖 AI Analysis Engine",

        t(lang, "trader_bot"):
            "🤖 Trader Bot\nComing later.",

        t(lang, "exchange"):
            "🔗 Exchange Connections\n"
            "Trading access is not enabled.",

        t(lang, "education"):
            "🎓 Education Center",

        t(lang, "our_exchanges"):
            "🏦 Our Exchanges",

        t(lang, "support"):
            "🎧 Support",

        t(lang, "account"):
            (
                f"👤 Account\n\n"
                f"ID: {user.telegram_id}\n"
                f"Type: {user.membership_type}\n"
                f"Points: {user.points}"
            ),

        t(lang, "performance"):
            (
                "📈 Monthly Performance\n\n"
                "Performance will be calculated "
                "from closed signals only."
            ),
    }

    response = (
        placeholders.get(
            text
        )
    )

    if response:

        await update.message.reply_text(
            response,
            reply_markup=(
                main_menu(
                    lang,
                    is_admin(
                        user.telegram_id
                    ),
                )
            ),
        )

        return

    await update.message.reply_text(
        t(
            lang,
            "choose",
        ),
        reply_markup=(
            main_menu(
                lang,
                is_admin(
                    user.telegram_id
                ),
            )
        ),
    )


def main():

    if not BOT_TOKEN:

        raise RuntimeError(
            "BOT_TOKEN missing."
        )

    Base.metadata.create_all(
        bind=engine
    )

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    app.add_handler(
        CommandHandler(
            "start",
            start,
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            membership_callback,
            pattern="^check_membership$",
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            language_callback,
            pattern="^lang_",
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            market_callback,
            pattern="^market_",
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            admin_callback,
            pattern="^admin_",
        )
    )

    app.add_handler(
        MessageHandler(
            filters.CONTACT,
            receive_contact,
        )
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT
            & ~filters.COMMAND,
            router,
        )
    )

    print(
        "\n"
        "================================\n"
        "ALIFT TRADER PLATFORM V2\n"
        "================================\n"
        "User/Auth       : ONLINE\n"
        "i18n            : ONLINE\n"
        "Referral        : ONLINE\n"
        "Admin           : ONLINE\n"
        "Market          : ONLINE\n"
        "Payment Base    : ONLINE\n"
        "Performance Base: ONLINE\n"
        "================================\n"
    )

    app.run_polling()


if __name__ == "__main__":

    main()
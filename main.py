import logging

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)

from telegram.constants import ChatMemberStatus

from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)


# ============================================================
# CONFIG
# ============================================================

from app.core.config import (
    ADMIN_IDS,
    BOT_TOKEN,
    REQUIRED_CHANNEL,
    REQUIRED_CHANNEL_URL,
)


# ============================================================
# DATABASE
# ============================================================

from app.models.database import (
    Base,
    engine,
)

# SQLAlchemy model registration
from app.models.user import User
from app.models.payment import Payment
from app.models.discount import DiscountCode
from app.models.performance import MonthlyPerformance
from app.models.alert import MarketAlert
from app.models.psychology import (
    EndOfDayCheck,
    PsychologyAssessment,
)


# ============================================================
# BOT HANDLERS
# ============================================================

from app.bot.language_handlers import (
    language_callback,
    language_page,
)

from app.bot.market_handlers import (
    market_callback,
    market_home,
)

from app.bot.navigation import (
    main_menu,
)

from app.bot.session_handlers import (
    session_callback,
    sessions_page,
)

from app.bot.welcome_handlers import (
    send_welcome,
)

from app.bot.psychology_handlers import (
    psychology_callback,
    psychology_home,
)

from app.bot.alert_handlers import (
    alert_callback,
    alert_price_message,
    alerts_home,
)


# ============================================================
# BACKGROUND ENGINES
# ============================================================

from app.engines.sessions.alert_engine import (
    session_alert_job,
)

from app.engines.alerts.alert_worker import (
    market_alert_job,
)


# ============================================================
# SERVICES
# ============================================================

from app.services.user_service import (
    get_or_create_user,
    get_user,
)


# ============================================================
# I18N
# ============================================================

from app.i18n.translations import t


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s | "
        "%(levelname)s | "
        "%(name)s | "
        "%(message)s"
    ),
)

logger = logging.getLogger(
    "alift-trader"
)


# ============================================================
# CHANNEL KEYBOARD
# ============================================================

def join_keyboard():

    rows = []

    if REQUIRED_CHANNEL_URL:

        rows.append(
            [
                InlineKeyboardButton(
                    "📢 عضویت در کانال",
                    url=REQUIRED_CHANNEL_URL,
                )
            ]
        )

    rows.append(
        [
            InlineKeyboardButton(
                "✅ بررسی عضویت",
                callback_data=(
                    "check_membership"
                ),
            )
        ]
    )

    return InlineKeyboardMarkup(
        rows
    )


# ============================================================
# CHANNEL MEMBERSHIP
# ============================================================

async def is_channel_member(
    telegram_id,
    context,
):

    if not REQUIRED_CHANNEL:
        return True

    try:

        member = await (
            context.bot
            .get_chat_member(
                chat_id=REQUIRED_CHANNEL,
                user_id=telegram_id,
            )
        )

        return member.status in {
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER,
        }

    except Exception as exc:

        logger.exception(
            "Channel membership error: %s",
            exc,
        )

        return False


async def require_channel(
    update,
    context,
):

    telegram_user = (
        update.effective_user
    )

    if telegram_user is None:
        return False

    member = await is_channel_member(
        telegram_user.id,
        context,
    )

    if member:
        return True

    if update.message:

        await update.message.reply_text(
            (
                "🔒 برای استفاده از ALIFT TRADER "
                "ابتدا باید عضو کانال رسمی شوید.\n\n"

                "1️⃣ روی عضویت در کانال بزنید.\n"
                "2️⃣ عضو کانال شوید.\n"
                "3️⃣ بررسی عضویت را بزنید."
            ),
            reply_markup=(
                join_keyboard()
            ),
        )

    return False


# ============================================================
# START
# ============================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    telegram_user = (
        update.effective_user
    )

    if (
        telegram_user is None
        or update.message is None
    ):
        return

    # --------------------------------------------------------
    # REFERRAL
    # --------------------------------------------------------

    referral_code = None

    if context.args:

        candidate = (
            context.args[0]
            .strip()
        )

        if candidate.startswith(
            "ALIFT-"
        ):

            referral_code = candidate

    # --------------------------------------------------------
    # USER
    # --------------------------------------------------------

    user, _created = (
        get_or_create_user(
            telegram_id=telegram_user.id,
            username=telegram_user.username,
            first_name=telegram_user.first_name,
            referred_by=referral_code,
        )
    )

    # --------------------------------------------------------
    # BAN
    # --------------------------------------------------------

    if user.is_banned:

        await update.message.reply_text(
            "⛔ حساب کاربری شما در دسترس نیست."
        )

        return

    # --------------------------------------------------------
    # CHANNEL
    # --------------------------------------------------------

    if not await require_channel(
        update,
        context,
    ):
        return

    # --------------------------------------------------------
    # WELCOME PHOTO
    # --------------------------------------------------------

    await send_welcome(
        update
    )

    # --------------------------------------------------------
    # LANGUAGE
    # --------------------------------------------------------

    if not user.language:

        await language_page(
            update,
            context,
        )

        return

    language = (
        user.language
    )

    # --------------------------------------------------------
    # MAIN MENU
    # --------------------------------------------------------

    await update.message.reply_text(
        (
            "🚀 {}\n\n{}"
        ).format(
            t(
                language,
                "welcome",
            ),

            t(
                language,
                "choose",
            ),
        ),

        reply_markup=(
            main_menu(
                language,
                telegram_user.id
                in ADMIN_IDS,
            )
        ),
    )


# ============================================================
# MEMBERSHIP CALLBACK
# ============================================================

async def membership_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = (
        update.callback_query
    )

    if query is None:
        return

    await query.answer()

    member = await is_channel_member(
        query.from_user.id,
        context,
    )

    if not member:

        await query.answer(
            "❌ عضویت تأیید نشده است.",
            show_alert=True,
        )

        return

    await query.edit_message_text(
        (
            "✅ عضویت تأیید شد.\n\n"
            "دوباره /start را بزنید."
        )
    )


# ============================================================
# ACCOUNT
# ============================================================

async def account_page(
    update,
    user,
    language,
):

    username = "-"

    if user.username:

        username = (
            "@{}".format(
                user.username
            )
        )

    vip_expire = "-"

    if user.vip_expires_at:

        vip_expire = (
            user.vip_expires_at
            .strftime(
                "%Y/%m/%d"
            )
        )

    text = (
        "👤 ALIFT ACCOUNT\n"
        "━━━━━━━━━━━━━━━━\n\n"

        "🆔 Telegram ID\n"
        "{}\n\n"

        "👤 Name\n"
        "{}\n\n"

        "🔗 Username\n"
        "{}\n\n"

        "💎 Plan\n"
        "{}\n\n"

        "📆 VIP Expire\n"
        "{}\n\n"

        "⭐ Points\n"
        "{}\n\n"

        "🎁 Referral\n"
        "{}"
    ).format(
        user.telegram_id,
        user.first_name or "-",
        username,
        user.membership_type.upper(),
        vip_expire,
        user.points,
        user.referral_code or "-",
    )

    await update.message.reply_text(
        text,
        reply_markup=(
            main_menu(
                language,
                user.telegram_id
                in ADMIN_IDS,
            )
        ),
    )


# ============================================================
# TEMPORARY MODULE
# ============================================================

async def temporary_module(
    update,
    user,
    language,
    title,
):

    await update.message.reply_text(
        (
            "{}\n"
            "━━━━━━━━━━━━━━━━\n\n"
            "{}"
        ).format(
            title,

            t(
                language,
                "module_soon",
            ),
        ),

        reply_markup=(
            main_menu(
                language,
                user.telegram_id
                in ADMIN_IDS,
            )
        ),
    )


# ============================================================
# TEXT ROUTER
# ============================================================

async def menu_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if update.message is None:
        return

    if not await require_channel(
        update,
        context,
    ):
        return

    telegram_user = (
        update.effective_user
    )

    if telegram_user is None:
        return

    user = get_user(
        telegram_user.id
    )

    if user is None:

        await update.message.reply_text(
            "❌ حساب پیدا نشد. /start"
        )

        return

    if user.is_banned:

        await update.message.reply_text(
            "⛔ حساب کاربری در دسترس نیست."
        )

        return

    language = (
        user.language
        or "fa"
    )

    text = (
        update.message.text
        or ""
    )

    # ========================================================
    # ALERT PRICE INPUT
    # ========================================================

    handled = await alert_price_message(
        update,
        context,
    )

    if handled:
        return

    # ========================================================
    # MARKET
    # ========================================================

    if text == t(
        language,
        "markets",
    ):

        await market_home(
            update,
            context,
        )

        return

    # ========================================================
    # ALERT CENTER
    # ========================================================

    if text == t(
        language,
        "alerts",
    ):

        await alerts_home(
            update,
            context,
        )

        return

    # ========================================================
    # PSYCHOLOGY
    # ========================================================

    if text == t(
        language,
        "psychology",
    ):

        await psychology_home(
            update,
            context,
        )

        return

    # ========================================================
    # SESSION
    # ========================================================

    if text == t(
        language,
        "sessions",
    ):

        await sessions_page(
            update,
            context,
        )

        return

    # ========================================================
    # LANGUAGE
    # ========================================================

    if text == t(
        language,
        "language",
    ):

        await language_page(
            update,
            context,
        )

        return

    # ========================================================
    # ACCOUNT
    # ========================================================

    if text == t(
        language,
        "account",
    ):

        await account_page(
            update,
            user,
            language,
        )

        return

    # ========================================================
    # ADMIN
    # ========================================================

    if text == t(
        language,
        "admin",
    ):

        if (
            telegram_user.id
            not in ADMIN_IDS
        ):

            await update.message.reply_text(
                t(
                    language,
                    "access_denied",
                )
            )

            return

        await temporary_module(
            update,
            user,
            language,
            "🛡 ALIFT ADMIN PANEL",
        )

        return

    # ========================================================
    # MODULES NOT CONNECTED YET
    # ========================================================

    modules = {
        "signals":
            "📡 ALIFT SIGNAL CENTER",

        "watchlist":
            "👁 ALIFT WATCHLIST",

        "news":
            "📰 ALIFT NEWS CENTER",

        "analysis":
            "🤖 ALIFT ANALYSIS",

        "trader":
            "🤖 ALIFT TRADER BOT",

        "exchange":
            "🔗 EXCHANGE CONNECTION",

        "vip":
            "💎 ALIFT VIP & PAYMENT",

        "rewards":
            "🎁 REFERRAL & POINTS",

        "performance":
            "📈 MONTHLY PERFORMANCE",

        "education":
            "🎓 ALIFT EDUCATION",

        "our_exchanges":
            "🏦 OUR EXCHANGES",

        "support":
            "🎧 ALIFT SUPPORT",

        "about":
            "🤝 ABOUT ALIFT",
    }

    for key, title in (
        modules.items()
    ):

        if text == t(
            language,
            key,
        ):

            await temporary_module(
                update,
                user,
                language,
                title,
            )

            return

    # ========================================================
    # UNKNOWN
    # ========================================================

    await update.message.reply_text(
        t(
            language,
            "choose",
        ),

        reply_markup=(
            main_menu(
                language,
                telegram_user.id
                in ADMIN_IDS,
            )
        ),
    )


# ============================================================
# ERROR HANDLER
# ============================================================

async def error_handler(
    update,
    context,
):

    logger.error(
        "Unhandled Telegram error",
        exc_info=context.error,
    )


# ============================================================
# BUILD APPLICATION
# ============================================================

def build_application():

    Base.metadata.create_all(
        bind=engine
    )

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    # --------------------------------------------------------
    # CORE
    # --------------------------------------------------------

    application.add_handler(
        CommandHandler(
            "start",
            start,
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            membership_callback,
            pattern=(
                "^check_membership$"
            ),
        )
    )

    # --------------------------------------------------------
    # LANGUAGE
    # --------------------------------------------------------

    application.add_handler(
        CallbackQueryHandler(
            language_callback,
            pattern=(
                "^lang_"
            ),
        )
    )

    # --------------------------------------------------------
    # MARKET
    # --------------------------------------------------------

    application.add_handler(
        CallbackQueryHandler(
            market_callback,
            pattern=(
                "^market_"
            ),
        )
    )

    # --------------------------------------------------------
    # SESSION
    # --------------------------------------------------------

    application.add_handler(
        CallbackQueryHandler(
            session_callback,
            pattern=(
                "^session_"
            ),
        )
    )

    # --------------------------------------------------------
    # PSYCHOLOGY
    # --------------------------------------------------------

    application.add_handler(
        CallbackQueryHandler(
            psychology_callback,
            pattern=(
                "^psy_"
            ),
        )
    )

    # --------------------------------------------------------
    # ALERT CENTER
    # --------------------------------------------------------

    application.add_handler(
        CallbackQueryHandler(
            alert_callback,
            pattern=(
                "^alert_"
            ),
        )
    )

    # --------------------------------------------------------
    # TEXT
    # --------------------------------------------------------

    application.add_handler(
        MessageHandler(
            filters.TEXT
            & ~filters.COMMAND,
            menu_router,
        )
    )

    # --------------------------------------------------------
    # ERRORS
    # --------------------------------------------------------

    application.add_error_handler(
        error_handler
    )

    # --------------------------------------------------------
    # SESSION WORKER
    # --------------------------------------------------------

    if application.job_queue is not None:

        application.job_queue.run_repeating(
            session_alert_job,
            interval=30,
            first=5,
            name=(
                "session-alert-engine"
            ),
        )

        logger.info(
            "Session Alert Worker: ON"
        )

    # --------------------------------------------------------
    # MARKET ALERT WORKER
    # --------------------------------------------------------

    if application.job_queue is not None:

        application.job_queue.run_repeating(
            market_alert_job,
            interval=60,
            first=15,
            name=(
                "market-alert-worker"
            ),
        )

        logger.info(
            "Market Alert Worker: ON"
        )

    return application


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "\n"
        "========================================\n"
        "             ALIFT TRADER\n"
        "========================================\n"
        "Telegram          : STARTING\n"
        "Languages         : FA / EN / AR\n"
        "Channel           : ENABLED\n"
        "Welcome           : ENABLED\n"
        "Market            : ENABLED\n"
        "Sessions          : ENABLED\n"
        "Session Alerts    : ENABLED\n"
        "Psychology        : ENABLED\n"
        "Market Alerts     : ENABLED\n"
        "Normal Alerts     : 5\n"
        "VIP Alerts        : 50\n"
        "Admin Alerts      : UNLIMITED\n"
        "========================================\n"
    )

    application = (
        build_application()
    )

    print(
        "BOT RUNNING"
    )

    application.run_polling(
        allowed_updates=(
            Update.ALL_TYPES
        )
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()
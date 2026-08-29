import logging

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

# Register SQLAlchemy models
from app.models.user import User
from app.models.payment import Payment
from app.models.discount import DiscountCode
from app.models.performance import MonthlyPerformance
from app.models.alert import MarketAlert

from app.models.psychology import (
    EndOfDayCheck,
    PsychologyAssessment,
)

from app.models.referral import (
    PointTransaction,
    ReferralReward,
)

from app.models.support import (
    SupportMessage,
    SupportTicket,
)

from app.models.search_usage import (
    SearchUsage,
)

from app.models.admin_audit import (
    AdminAuditLog,
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

from app.bot.signal_handlers import (
    signal_center,
    signal_callback,
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

from app.bot.alert_asset_handlers import (
    asset_callback,
    asset_message,
)

from app.bot.referral_handlers import (
    referral_callback,
    referral_home,
)

from app.bot.support_handlers import (
    support_callback,
    support_home,
    support_message,
)

from app.bot.about_handlers import (
    about_callback,
    about_home,
)

from app.bot.admin_handlers import (
    admin_callback,
    admin_home,
    admin_message,
)

from app.bot.exchange_handlers import (
    exchange_callback,
    exchanges_home,
)

from app.bot.performance_handlers import (
    performance_callback,
    performance_home,
)

from app.bot.payment_handlers import (
    payment_callback,
    payment_home,
    payment_message,
)

from app.bot.admin_payment_handlers import (
    admin_payment_callback,
    admin_payments_home,
)


# ============================================================
# BACKGROUND ENGINES
# ============================================================

from app.engines.sessions.alert_engine import (
    session_alert_job,
)

from app.engines.news.arzdigital_breaking_worker import (
    arzdigital_breaking_job,
)

from app.engines.news.wallex_news_worker import (
    wallex_news_job,
)

from app.engines.news.economic_calendar_worker import (
    economic_calendar_sync_job,
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

from app.services.referral_service import (
    process_referral_reward,
)


# ============================================================
# I18N
# ============================================================

from app.i18n.translations import (
    t,
)


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
    "MrBiznes"
)


# ============================================================
# CHANNEL
# ============================================================

def join_keyboard():

    rows = []

    if REQUIRED_CHANNEL_URL:

        rows.append(
            [
                InlineKeyboardButton(
                    "ðŸ“¢ Ø¹Ø¶ÙˆÛŒØª Ø¯Ø± Ú©Ø§Ù†Ø§Ù„",
                    url=REQUIRED_CHANNEL_URL,
                )
            ]
        )

    rows.append(
        [
            InlineKeyboardButton(
                "âœ… Ø¨Ø±Ø±Ø³ÛŒ Ø¹Ø¶ÙˆÛŒØª",
                callback_data=(
                    "check_membership"
                ),
            )
        ]
    )

    return InlineKeyboardMarkup(
        rows
    )


async def is_channel_member(
    telegram_id,
    context,
):

    if not REQUIRED_CHANNEL:
        return True

    try:

        member = await (
            context.bot.get_chat_member(
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
                "ðŸ”’ Ø¨Ø±Ø§ÛŒ Ø§Ø³ØªÙØ§Ø¯Ù‡ Ø§Ø² Ù…Ø³ØªØ± Ø¨ÛŒØ²Ù†Ø³ "
                "Ø§Ø¨ØªØ¯Ø§ Ø¨Ø§ÛŒØ¯ Ø¹Ø¶Ùˆ Ú©Ø§Ù†Ø§Ù„ Ø±Ø³Ù…ÛŒ Ø´ÙˆÛŒØ¯.\n\n"

                "1ï¸âƒ£ Ø±ÙˆÛŒ Ø¹Ø¶ÙˆÛŒØª Ø¯Ø± Ú©Ø§Ù†Ø§Ù„ Ø¨Ø²Ù†ÛŒØ¯.\n"
                "2ï¸âƒ£ Ø¹Ø¶Ùˆ Ú©Ø§Ù†Ø§Ù„ Ø´ÙˆÛŒØ¯.\n"
                "3ï¸âƒ£ Ø¨Ø±Ø±Ø³ÛŒ Ø¹Ø¶ÙˆÛŒØª Ø±Ø§ Ø¨Ø²Ù†ÛŒØ¯."
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

    referral_code = None

    if context.args:

        candidate = (
            context.args[0]
            .strip()
            .upper()
        )

        if candidate.startswith(
            "MrBiznes-"
        ):

            referral_code = (
                candidate
            )

    user, created = (
        get_or_create_user(
            telegram_id=(
                telegram_user.id
            ),
            username=(
                telegram_user.username
            ),
            first_name=(
                telegram_user.first_name
            ),
            referred_by=(
                referral_code
            ),
        )
    )

    # Referral reward
    if (
        created
        and referral_code
        and user.referred_by
    ):

        try:

            rewarded = (
                process_referral_reward(
                    telegram_user.id
                )
            )

            if rewarded:

                logger.info(
                    "Referral reward processed for %s",
                    telegram_user.id,
                )

        except Exception as exc:

            logger.exception(
                "Referral reward error: %s",
                exc,
            )

    # Ban
    if user.is_banned:

        await update.message.reply_text(
            "â›” Ø­Ø³Ø§Ø¨ Ú©Ø§Ø±Ø¨Ø±ÛŒ Ø´Ù…Ø§ Ø¯Ø± Ø¯Ø³ØªØ±Ø³ Ù†ÛŒØ³Øª."
        )

        return

    # Required channel
    if not await require_channel(
        update,
        context,
    ):

        return

    # Welcome
    await send_welcome(
        update
    )

    # Language
    if not user.language:

        await language_page(
            update,
            context,
        )

        return

    language = (
        user.language
    )

    await update.message.reply_text(
        (
            "ðŸš€ {}\n\n{}"
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

    member = await is_channel_member(
        query.from_user.id,
        context,
    )

    if not member:

        await query.answer(
            "âŒ Ø¹Ø¶ÙˆÛŒØª ØªØ£ÛŒÛŒØ¯ Ù†Ø´Ø¯.",
            show_alert=True,
        )

        return

    await query.answer(
        "âœ… Ø¹Ø¶ÙˆÛŒØª ØªØ£ÛŒÛŒØ¯ Ø´Ø¯.",
        show_alert=True,
    )

    await query.edit_message_text(
        (
            "âœ… Ø¹Ø¶ÙˆÛŒØª ØªØ£ÛŒÛŒØ¯ Ø´Ø¯.\n\n"
            "Ø¯ÙˆØ¨Ø§Ø±Ù‡ /start Ø±Ø§ Ø¨Ø²Ù†ÛŒØ¯."
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

    username = (
        f"@{user.username}"
        if user.username
        else "-"
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
        "ðŸ‘¤ MrBiznes ACCOUNT\n"
        "â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n\n"

        f"ðŸ†” Telegram ID\n"
        f"{user.telegram_id}\n\n"

        f"ðŸ‘¤ Name\n"
        f"{user.first_name or '-'}\n\n"

        f"ðŸ”— Username\n"
        f"{username}\n\n"

        f"ðŸ’Ž Plan\n"
        f"{user.membership_type.upper()}\n\n"

        f"ðŸ“† VIP Expire\n"
        f"{vip_expire}\n\n"

        f"â­ Points\n"
        f"{user.points}\n\n"

        f"ðŸŽ Referral\n"
        f"{user.referral_code or '-'}"
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
            f"{title}\n"
            "â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”\n\n"
            f"{t(language, 'module_soon')}"
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

    if (
        update.message is None
        or update.effective_user
        is None
    ):
        return

    if not await require_channel(
        update,
        context,
    ):
        return

    telegram_user = (
        update.effective_user
    )

    user = get_user(
        telegram_user.id
    )

    if user is None:

        await update.message.reply_text(
            "âŒ Ø­Ø³Ø§Ø¨ Ù¾ÛŒØ¯Ø§ Ù†Ø´Ø¯. /start"
        )

        return

    if user.is_banned:

        await update.message.reply_text(
            "â›” Ø­Ø³Ø§Ø¨ Ú©Ø§Ø±Ø¨Ø±ÛŒ Ø¯Ø± Ø¯Ø³ØªØ±Ø³ Ù†ÛŒØ³Øª."
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

    # --------------------------------------------------------
    # ADMIN INPUT
    # --------------------------------------------------------

    handled = await admin_message(
        update,
        context,
    )

    if handled:
        return

    # --------------------------------------------------------
    # ASSET SEARCH
    # --------------------------------------------------------

    handled = await asset_message(
        update,
        context,
    )

    if handled:
        return

    # --------------------------------------------------------
    # ALERT INPUT
    # --------------------------------------------------------

    handled = (
        await alert_price_message(
            update,
            context,
        )
    )

    if handled:
        return

    # --------------------------------------------------------
    # PAYMENT INPUT
    # --------------------------------------------------------

    handled = await payment_message(
        update,
        context,
    )

    if handled:
        return


    # --------------------------------------------------------
    # SUPPORT INPUT
    # --------------------------------------------------------

    handled = await support_message(
        update,
        context,
    )

    if handled:
        return

    # --------------------------------------------------------
    # MARKET
    # --------------------------------------------------------

    if text == t(
        language,
        "markets",
    ):

        await market_home(
            update,
            context,
        )

        return

    # --------------------------------------------------------
    # ALERTS
    # --------------------------------------------------------

    if text == t(
        language,
        "alerts",
    ):

        await alerts_home(
            update,
            context,
        )

        return

    # --------------------------------------------------------
    # PSYCHOLOGY
    # --------------------------------------------------------

    if text == t(
        language,
        "psychology",
    ):

        await psychology_home(
            update,
            context,
        )

        return

    # --------------------------------------------------------
    # SESSIONS
    # --------------------------------------------------------

    if text == t(
        language,
        "sessions",
    ):

        await sessions_page(
            update,
            context,
        )

        return

    # --------------------------------------------------------
    # LANGUAGE
    # --------------------------------------------------------

    if text == t(
        language,
        "language",
    ):

        await language_page(
            update,
            context,
        )

        return

    # --------------------------------------------------------
    # ACCOUNT
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # REFERRAL
    # --------------------------------------------------------

    if text == t(
        language,
        "rewards",
    ):

        await referral_home(
            update,
            context,
        )

        return

    # --------------------------------------------------------
    # SUPPORT
    # --------------------------------------------------------

    if text == t(
        language,
        "support",
    ):

        await support_home(
            update,
            context,
        )

        return

    # --------------------------------------------------------
    # ABOUT
    # --------------------------------------------------------

    if text == t(
        language,
        "about",
    ):

        await about_home(
            update,
            context,
        )

        return

    # --------------------------------------------------------
    # OUR EXCHANGES
    # --------------------------------------------------------

    if text == t(
        language,
        "our_exchanges",
    ):

        await exchanges_home(
            update,
            context,
        )

        return

    # --------------------------------------------------------
    # VIP / PAYMENT
    # --------------------------------------------------------

    if text == t(
        language,
        "vip",
    ):

        await payment_home(
            update,
            context,
        )

        return


    # --------------------------------------------------------
    # PERFORMANCE
    # --------------------------------------------------------

    if text == t(
        language,
        "performance",
    ):

        await performance_home(
            update,
            context,
        )

        return

    # --------------------------------------------------------
    # ADMIN
    # --------------------------------------------------------

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

        await admin_home(
            update,
            context,
        )

        return

    # --------------------------------------------------------
    # MODULES NOT CONNECTED YET
    # --------------------------------------------------------

    modules = {
        "signals":
            "ðŸ“¡ MrBiznes SIGNAL CENTER",

        "watchlist":
            "ðŸ‘ MrBiznes WATCHLIST",

        "news":
            "ðŸ“° MrBiznes NEWS CENTER",

        "analysis":
            "ðŸ¤– MrBiznes ANALYSIS",

        "trader":
            "ðŸ¤– MrBiznes BOT",

        "exchange":
            "ðŸ”— EXCHANGE CONNECTION",
        "education":
            "ðŸŽ“ MrBiznes EDUCATION",
    }

    for key, title in (
        modules.items()
    ):

        if text == t(
            language,
            key,
        ):

            if key == "signals":
                await signal_center(
                    update,
                    context,
                )
                return

            await temporary_module(
                update,
                user,
                language,
                title,
            )

            return

    # --------------------------------------------------------
    # UNKNOWN
    # --------------------------------------------------------

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

    # START
    application.add_handler(
        CommandHandler(
            "start",
            start,
        )
    )

    # ADMIN PAYMENT COMMAND
    application.add_handler(
        CommandHandler(
            "payments",
            admin_payments_home,
        )
    )


    # MEMBERSHIP
    application.add_handler(
        CallbackQueryHandler(
            membership_callback,
            pattern="^check_membership$",
        )
    )

    # LANGUAGE
    application.add_handler(
        CallbackQueryHandler(
            language_callback,
            pattern="^lang_",
        )
    )

    # MARKET
    application.add_handler(
        CallbackQueryHandler(
            market_callback,
            pattern="^market_",
        )
    )

    # SESSIONS
    application.add_handler(
        CallbackQueryHandler(
            session_callback,
            pattern="^session_",
        )
    )

    # PSYCHOLOGY
    application.add_handler(
        CallbackQueryHandler(
            psychology_callback,
            pattern="^psy_",
        )
    )

    # ASSET SEARCH
    application.add_handler(
        CallbackQueryHandler(
            asset_callback,
            pattern="^asset_",
        )
    )

    # ALERTS
    application.add_handler(
        CallbackQueryHandler(
            alert_callback,
            pattern="^alert_",
        )
    )

    # REFERRAL
    application.add_handler(
        CallbackQueryHandler(
            referral_callback,
            pattern="^referral_",
        )
    )

    # SUPPORT
    application.add_handler(
        CallbackQueryHandler(
            support_callback,
            pattern="^support_",
        )
    )

    # ABOUT
    application.add_handler(
        CallbackQueryHandler(
            about_callback,
            pattern="^about_",
        )
    )

    # EXCHANGE HUB
    application.add_handler(
        CallbackQueryHandler(
            exchange_callback,
            pattern="^exchange_",
        )
    )

    # PERFORMANCE
    application.add_handler(
        CallbackQueryHandler(
            performance_callback,
            pattern="^performance_",
        )
    )

    # PAYMENT
    application.add_handler(
        CallbackQueryHandler(
            payment_callback,
            pattern="^payment_",
        )
    )

    # ADMIN PAYMENT
    application.add_handler(
        CallbackQueryHandler(
            admin_payment_callback,
            pattern="^adminpay_",
        )
    )


    # ADMIN
    application.add_handler(
        CallbackQueryHandler(
            admin_callback,
            pattern="^admin_",
        )
    )

    # TEXT
    application.add_handler(
        MessageHandler(
            filters.TEXT
            & ~filters.COMMAND,
            menu_router,
        )
    )

    # SIGNAL CENTER
    application.add_handler(
        CallbackQueryHandler(
            signal_callback,
            pattern=r"signal_",
        )
    )

    # ERRORS
    application.add_error_handler(
        error_handler
    )

    # SESSION WORKER
    if (
        application.job_queue
        is not None
    ):

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

    # MARKET ALERT WORKER
    if (
        application.job_queue
        is not None
    ):

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

    # ECONOMIC CALENDAR WORKER
    if application.job_queue is not None:
        application.job_queue.run_repeating(
            economic_calendar_sync_job,
            interval=900,
            first=20,
            name="economic-calendar-sync-worker",
        )

        logger.info(
            "Economic Calendar Worker: ON"
        )

    # BREAKING NEWS WORKER
    if application.job_queue is not None:
        application.job_queue.run_repeating(
            arzdigital_breaking_job,
            interval=300,
            first=30,
            name="arzdigital-breaking-news-worker",
        )

        logger.info(
            "Breaking News Worker: ON"
        )

    # WALLEX NEWS WORKER
    if application.job_queue is not None:
        application.job_queue.run_repeating(
            wallex_news_job,
            interval=900,
            first=45,
            name="wallex-news-worker",
        )

        logger.info("Wallex News Worker: ON")

    return application


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "\n"
        "========================================\n"
        "             MrBiznes\n"
        "========================================\n"
        "Languages         : FA / EN / AR\n"
        "Channel           : ENABLED\n"
        "Market            : ENABLED\n"
        "Sessions          : ENABLED\n"
        "Psychology        : ENABLED\n"
        "Crypto Alerts     : XT\n"
        "Forex Alerts      : TWELVE DATA\n"
        "Crypto Search     : ENABLED\n"
        "Forex Search      : ENABLED\n"
        "Search Quota      : NORMAL 3/MONTH\n"
        "Referral          : ENABLED\n"
        "Support           : ENABLED\n"
        "About             : ENABLED\n"
        "Exchange Hub      : ENABLED\n"
        "Performance       : ENABLED\n"
        "Admin Panel       : ENABLED\n"
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
# ENTRY
# ============================================================

if __name__ == "__main__":

    main()




import os

from pathlib import Path

from dotenv import (
    load_dotenv,
)

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)

from telegram.ext import (
    ContextTypes,
)

from app.services.user_service import (
    get_user,
    referral_stats,
)


load_dotenv()


BASE_DIR = (
    Path(__file__)
    .resolve()
    .parent
    .parent
    .parent
)

WELCOME_IMAGE = (
    BASE_DIR
    / "assets"
    / "welcome.jpg"
)


WELCOME_CAPTION = (
    "🚀 ALIFT TRADER\n\n"
    "«خوبی، تنها سرمایه‌گذاری است که "
    "هیچگاه شکست نمی‌خورد.»\n\n"
    "“Goodness is the only investment "
    "that never fails.”\n\n"
    "📊 Markets • Signals • Alerts\n"
    "📰 News • Watchlists\n"
    "🧠 Trading Psychology\n"
    "💎 Normal & VIP\n\n"
    "⚠️ Information and analysis are "
    "for informational and educational "
    "purposes."
)


async def send_welcome(
    update,
):

    if WELCOME_IMAGE.exists():

        with open(
            WELCOME_IMAGE,
            "rb",
        ) as photo:

            await update.message.reply_photo(
                photo=photo,
                caption=WELCOME_CAPTION,
            )

    else:

        await update.message.reply_text(
            WELCOME_CAPTION
        )


async def referral_page(
    update,
    context,
):

    stats = referral_stats(
        update.effective_user.id
    )

    if not stats:

        return

    me = await (
        context.bot.get_me()
    )

    link = (
        f"https://t.me/{me.username}"
        f"?start={stats['code']}"
    )

    text = (
        "🎁 REFERRAL CENTER\n"
        "━━━━━━━━━━━━━━━━\n\n"
        f"Code:\n{stats['code']}\n\n"
        f"Invites: {stats['invites']}\n"
        f"Points: {stats['points']}\n\n"
        f"🔗 Invite Link:\n{link}"
    )

    await update.message.reply_text(
        text
    )


async def payment_page(
    update,
):

    btc = os.getenv(
        "BTC_PAYMENT_ADDRESS",
        "",
    )

    eth = os.getenv(
        "ETH_PAYMENT_ADDRESS",
        "",
    )

    tron = os.getenv(
        "TRON_PAYMENT_ADDRESS",
        "",
    )

    sol = os.getenv(
        "SOL_PAYMENT_ADDRESS",
        "",
    )

    usdt_trc = os.getenv(
        "USDT_TRC20_ADDRESS",
        "",
    )

    usdt_erc = os.getenv(
        "USDT_ERC20_ADDRESS",
        "",
    )

    text = (
        "💎 VIP & CRYPTO PAYMENT\n"
        "━━━━━━━━━━━━━━━━\n\n"
        "Supported:\n\n"
        "₿ Bitcoin\n"
        "Ξ Ethereum\n"
        "🔴 TRON\n"
        "◎ Solana\n"
        "₮ USDT TRC20\n"
        "₮ USDT ERC20\n\n"
        "⚠️ Blockchain verification "
        "engine is not enabled yet.\n"
        "Do not send funds until a payment "
        "invoice is created by the bot."
    )

    await update.message.reply_text(
        text
    )


async def about_page(
    update,
):

    keyboard = []

    links = [
        (
            "🌐 Website",
            os.getenv(
                "WEBSITE_URL",
                "",
            ),
        ),
        (
            "▶️ YouTube",
            os.getenv(
                "YOUTUBE_URL",
                "",
            ),
        ),
        (
            "📸 Instagram",
            os.getenv(
                "INSTAGRAM_URL",
                "",
            ),
        ),
        (
            "𝕏 X",
            os.getenv(
                "X_URL",
                "",
            ),
        ),
        (
            "💬 WhatsApp",
            os.getenv(
                "WHATSAPP_URL",
                "",
            ),
        ),
    ]

    for title, url in links:

        if (
            url
            and url.startswith(
                (
                    "http://",
                    "https://",
                )
            )
        ):

            keyboard.append(
                [
                    InlineKeyboardButton(
                        title,
                        url=url,
                    )
                ]
            )

    await update.message.reply_text(
        "🤝 ABOUT ALIFT\n"
        "━━━━━━━━━━━━━━━━\n\n"
        "ALIFT Trader is a market "
        "information, analytics and "
        "trader-assistance platform.",
        reply_markup=(
            InlineKeyboardMarkup(
                keyboard
            )
            if keyboard
            else None
        ),
    )


async def news_page(
    update,
):

    keyboard = []

    forex = os.getenv(
        "FOREX_NEWS_CHANNEL_URL",
        "",
    )

    crypto = os.getenv(
        "CRYPTO_NEWS_CHANNEL_URL",
        "",
    )

    if forex:

        keyboard.append(
            [
                InlineKeyboardButton(
                    "💱 Forex News",
                    url=forex,
                )
            ]
        )

    if crypto:

        keyboard.append(
            [
                InlineKeyboardButton(
                    "₿ Crypto News",
                    url=crypto,
                )
            ]
        )

    await update.message.reply_text(
        "📰 ALIFT NEWS CENTER",
        reply_markup=(
            InlineKeyboardMarkup(
                keyboard
            )
            if keyboard
            else None
        ),
    )
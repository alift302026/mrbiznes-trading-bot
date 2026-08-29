from pathlib import Path

from telegram import Update


# ============================================================
# PATH
# ============================================================

PROJECT_ROOT = (
    Path(__file__)
    .resolve()
    .parent
    .parent
    .parent
)

ASSETS_DIR = (
    PROJECT_ROOT
    / "assets"
)

WELCOME_IMAGE = (
    ASSETS_DIR
    / "welcome.jpg"
)


# ============================================================
# WELCOME TEXT
# ============================================================

WELCOME_TEXT = (
    "🚀 MrBiznes\n\n"
    "«خوبی، تنها سرمایه‌گذاری است که "
    "هیچگاه شکست نمی‌خورد.»\n\n"
    "“Goodness is the only investment "
    "that never fails.”\n\n"
    "━━━━━━━━━━━━━━━━\n"
    "📊 Markets • Signals • Alerts\n"
    "📰 News • Watchlists\n"
    "🧠 Trading Psychology\n"
    "💎 Normal & VIP\n"
    "━━━━━━━━━━━━━━━━\n\n"
    "⚠️ اطلاعات و تحلیل‌های بازار "
    "جنبه آموزشی و اطلاع‌رسانی دارند."
)


# ============================================================
# SEND WELCOME
# ============================================================

async def send_welcome(
    update: Update,
):

    if not update.message:
        return

    print(
        f"WELCOME IMAGE PATH: {WELCOME_IMAGE}"
    )

    if not WELCOME_IMAGE.exists():

        print(
            "WELCOME IMAGE ERROR: "
            "welcome.jpg was not found."
        )

        await update.message.reply_text(
            WELCOME_TEXT
        )

        return

    try:

        with WELCOME_IMAGE.open(
            "rb"
        ) as photo:

            await update.message.reply_photo(
                photo=photo,
                caption=WELCOME_TEXT,
            )

        print(
            "WELCOME IMAGE: SENT"
        )

    except Exception as exc:

        print(
            "WELCOME IMAGE SEND ERROR:",
            repr(exc),
        )

        await update.message.reply_text(
            WELCOME_TEXT
        )
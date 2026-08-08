from telegram import (
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from app.i18n.translations import (
    t,
)


# ============================================================
# MAIN MENU
# ============================================================

def main_menu(
    language: str,
    is_admin: bool = False,
):

    rows = [

        [
            t(
                language,
                "markets",
            ),

            t(
                language,
                "signals",
            ),
        ],

        [
            t(
                language,
                "alerts",
            ),

            t(
                language,
                "watchlist",
            ),
        ],

        [
            t(
                language,
                "sessions",
            ),

            t(
                language,
                "news",
            ),
        ],

        [
            t(
                language,
                "psychology",
            ),

            t(
                language,
                "analysis",
            ),
        ],

        [
            t(
                language,
                "trader_bot",
            ),

            t(
                language,
                "exchange",
            ),
        ],

        [
            t(
                language,
                "vip",
            ),

            t(
                language,
                "rewards",
            ),
        ],

        [
            t(
                language,
                "performance",
            ),

            t(
                language,
                "education",
            ),
        ],

        [
            t(
                language,
                "our_exchanges",
            ),

            t(
                language,
                "support",
            ),
        ],

        [
            t(
                language,
                "about",
            ),

            t(
                language,
                "account",
            ),
        ],

        [
            t(
                language,
                "language",
            ),
        ],
    ]

    # فقط ادمین اصلی این دکمه را می‌بیند
    if is_admin:

        rows.append(
            [
                t(
                    language,
                    "admin",
                )
            ]
        )

    return ReplyKeyboardMarkup(
        rows,
        resize_keyboard=True,
        input_field_placeholder=(
            "ALIFT Trader"
        ),
    )


# ============================================================
# CONTACT KEYBOARD
# ============================================================

def contact_keyboard():

    button = KeyboardButton(
        text="📱 Share Phone / ارسال شماره",
        request_contact=True,
    )

    return ReplyKeyboardMarkup(
        [
            [button]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
from telegram import (
    ReplyKeyboardMarkup,
)

from app.i18n.translations import t


def main_menu(
    language: str = "fa",
    admin: bool = False,
):
    rows = [
        [
            t(language, "markets"),
            t(language, "signals"),
        ],
        [
            t(language, "sessions"),
            t(language, "alerts"),
        ],
        [
            t(language, "plt"),
            t(language, "journal"),
        ],
        [
            t(language, "psychology"),
            t(language, "vip"),
        ],
        [
            t(language, "rewards"),
            t(language, "performance"),
        ],
        [
            t(language, "our_exchanges"),
            t(language, "support"),
        ],
        [
            t(language, "about"),
            t(language, "account"),
        ],
    ]

    if admin:
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
    )

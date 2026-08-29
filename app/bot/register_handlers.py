from telegram.ext import (
    CallbackQueryHandler,
)

from app.bot.psychology_handlers import (
    psychology_callback,
)


def register_psychology_handlers(
    application,
):

    application.add_handler(
        CallbackQueryHandler(
            psychology_callback,
            pattern="^psy_",
        )
    )
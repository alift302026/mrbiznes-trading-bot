from app.bot.psychology_handlers import (
    psychology_home,
)

from app.bot.plt_handlers import (
    plt_entry,
)

from app.i18n.translations import (
    t,
)

from app.services.user_service import (
    get_user,
)


async def route_module(
    update,
    context,
):
    """
    مسیر‌دهی ماژول‌های مستقل.

    True:
        پیام توسط این Router پردازش شد.

    False:
        مربوط به این Router نبود.
    """

    telegram_user = (
        update.effective_user
    )

    if (
        telegram_user is None
        or update.message is None
    ):
        return False

    user = get_user(
        telegram_user.id
    )

    if user is None:
        return False

    language = (
        user.language
        or "fa"
    )

    text = (
        update.message.text
        or ""
    )

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

        return True

    # ========================================================
    # PLT - vision chart analysis
    # ========================================================

    if text == t(
        language,
        "plt",
    ):

        await plt_entry(
            update,
            context,
        )

        return True

    return False

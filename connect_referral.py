from pathlib import Path

path = Path("main.py")

text = path.read_text(
    encoding="utf-8"
)

# ------------------------------------------------------------
# 1. Import Referral Handlers
# ------------------------------------------------------------

marker = """from app.bot.alert_handlers import (
    alert_callback,
    alert_price_message,
    alerts_home,
)
"""

addition = marker + """

from app.bot.referral_handlers import (
    referral_callback,
    referral_home,
)
"""

if (
    "from app.bot.referral_handlers import"
    not in text
):

    if marker not in text:
        raise SystemExit(
            "IMPORT MARKER NOT FOUND"
        )

    text = text.replace(
        marker,
        addition,
        1,
    )


# ------------------------------------------------------------
# 2. Connect Rewards Menu
# ------------------------------------------------------------

marker = """    # ========================================================
    # ADMIN
    # ========================================================
"""

addition = """    # ========================================================
    # REFERRAL & POINTS
    # ========================================================

    if text == t(
        language,
        "rewards",
    ):

        await referral_home(
            update,
            context,
        )

        return

""" + marker

if (
    "await referral_home("
    not in text
):

    if marker not in text:
        raise SystemExit(
            "ROUTER MARKER NOT FOUND"
        )

    text = text.replace(
        marker,
        addition,
        1,
    )


# ------------------------------------------------------------
# 3. Register Referral Callback
# ------------------------------------------------------------

marker = """    # TEXT

    application.add_handler(
"""

addition = """    # REFERRAL

    application.add_handler(
        CallbackQueryHandler(
            referral_callback,
            pattern="^referral_",
        )
    )

    # TEXT

    application.add_handler(
"""

if (
    "referral_callback,"
    not in text.split(
        "# TEXT"
    )[0]
):

    if marker not in text:
        raise SystemExit(
            "CALLBACK MARKER NOT FOUND"
        )

    text = text.replace(
        marker,
        addition,
        1,
    )


path.write_text(
    text,
    encoding="utf-8",
)

print(
    "REFERRAL CONNECTED"
)
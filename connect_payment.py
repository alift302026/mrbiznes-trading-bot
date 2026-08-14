from pathlib import Path
import shutil


path = Path("main.py")

backup = Path(
    "main_before_payment_connect.py"
)


# ============================================================
# BACKUP
# ============================================================

shutil.copy2(
    path,
    backup,
)

print(
    "BACKUP CREATED:",
    backup,
)


# ============================================================
# READ
# ============================================================

text = path.read_text(
    encoding="utf-8"
)


# ============================================================
# PAYMENT IMPORTS
# ============================================================

payment_import = """
from app.bot.payment_handlers import (
    payment_callback,
    payment_home,
    payment_message,
)

from app.bot.admin_payment_handlers import (
    admin_payment_callback,
    admin_payments_home,
)
"""


marker = """
from app.bot.performance_handlers import (
    performance_callback,
    performance_home,
)
"""


if (
    "from app.bot.payment_handlers import"
    not in text
):

    if marker not in text:

        raise SystemExit(
            "PAYMENT IMPORT MARKER NOT FOUND"
        )

    text = text.replace(
        marker,
        marker
        + payment_import,
        1,
    )


# ============================================================
# PAYMENT MESSAGE INPUT
# ============================================================

input_marker = """
    # --------------------------------------------------------
    # SUPPORT INPUT
    # --------------------------------------------------------

    handled = await support_message(
        update,
        context,
    )
"""


payment_input = """
    # --------------------------------------------------------
    # PAYMENT INPUT
    # --------------------------------------------------------

    handled = await payment_message(
        update,
        context,
    )

    if handled:
        return

"""


if (
    "handled = await payment_message("
    not in text
):

    if input_marker not in text:

        raise SystemExit(
            "PAYMENT INPUT MARKER NOT FOUND"
        )

    text = text.replace(
        input_marker,
        payment_input
        + input_marker,
        1,
    )


# ============================================================
# VIP MENU ROUTE
# ============================================================

vip_marker = """
    # --------------------------------------------------------
    # PERFORMANCE
    # --------------------------------------------------------
"""


vip_route = """
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

"""


if (
    "await payment_home("
    not in text
):

    if vip_marker not in text:

        raise SystemExit(
            "VIP ROUTE MARKER NOT FOUND"
        )

    text = text.replace(
        vip_marker,
        vip_route
        + vip_marker,
        1,
    )


# ============================================================
# REMOVE VIP FROM TEMPORARY MODULES
# ============================================================

old_vip = """
        "vip":
            "💎 ALIFT VIP & PAYMENT",

"""

text = text.replace(
    old_vip,
    "",
)


# ============================================================
# PAYMENT CALLBACK
# ============================================================

callback_marker = """
    # ADMIN
    application.add_handler(
"""


payment_callback_block = """
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

"""


if (
    "pattern=\"^payment_\""
    not in text
):

    if callback_marker not in text:

        raise SystemExit(
            "PAYMENT CALLBACK MARKER NOT FOUND"
        )

    text = text.replace(
        callback_marker,
        payment_callback_block
        + callback_marker,
        1,
    )


# ============================================================
# ADMIN PAYMENTS COMMAND
# ============================================================

command_marker = """
    # MEMBERSHIP
    application.add_handler(
"""


admin_command = """
    # ADMIN PAYMENT COMMAND
    application.add_handler(
        CommandHandler(
            "payments",
            admin_payments_home,
        )
    )

"""


if (
    "\"payments\""
    not in text
):

    if command_marker not in text:

        raise SystemExit(
            "COMMAND MARKER NOT FOUND"
        )

    text = text.replace(
        command_marker,
        admin_command
        + command_marker,
        1,
    )


# ============================================================
# WRITE
# ============================================================

path.write_text(
    text,
    encoding="utf-8",
)


print(
    "PAYMENT CONNECTED TO MAIN"
)
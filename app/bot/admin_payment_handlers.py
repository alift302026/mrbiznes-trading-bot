from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)

from telegram.ext import (
    ContextTypes,
)

from app.core.config import (
    ADMIN_IDS,
)

from app.services.admin_service import (
    audit,
)

from app.services.payment_service import (
    approve_payment,
    get_payment,
    pending_payments,
    reject_payment,
)


# ============================================================
# SECURITY
# ============================================================

def is_admin(
    telegram_id,
):

    return (
        telegram_id
        in ADMIN_IDS
    )


# ============================================================
# PENDING LIST
# ============================================================

def pending_keyboard(
    items,
):

    rows = []

    for item in items:

        method = (
            "₿"
            if item.payment_method
            == "crypto"
            else "💳"
        )

        rows.append(
            [
                InlineKeyboardButton(
                    (
                        f"{method} #{item.id} "
                        f"| {item.telegram_id} "
                        f"| {item.plan_days or '-'}d"
                    ),
                    callback_data=(
                        f"adminpay_view_{item.id}"
                    ),
                )
            ]
        )

    rows.append(
        [
            InlineKeyboardButton(
                "🔄 Refresh",
                callback_data="adminpay_home",
            )
        ]
    )

    rows.append(
        [
            InlineKeyboardButton(
                "⬅️ Admin Panel",
                callback_data="admin_home",
            )
        ]
    )

    return InlineKeyboardMarkup(
        rows
    )


# ============================================================
# HOME TEXT
# ============================================================

def pending_text():

    items = pending_payments(
        100
    )

    if not items:

        return (
            "💳 ALIFT PAYMENT REVIEW\n"
            "━━━━━━━━━━━━━━━━\n\n"

            "✅ هیچ پرداخت Pending وجود ندارد."
        )

    return (
        "💳 ALIFT PAYMENT REVIEW\n"
        "━━━━━━━━━━━━━━━━\n\n"

        f"🟡 Pending: {len(items)}\n\n"

        "برای مشاهده جزئیات و تأیید/رد "
        "روی پرداخت موردنظر بزن."
    )


# ============================================================
# ADMIN PAYMENT HOME
# ============================================================

async def admin_payments_home(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user = (
        update.effective_user
    )

    if (
        user is None
        or user.id not in ADMIN_IDS
    ):

        if update.message:

            await update.message.reply_text(
                "⛔ Access denied"
            )

        return

    items = pending_payments(
        100
    )

    await update.message.reply_text(
        pending_text(),
        reply_markup=(
            pending_keyboard(
                items
            )
        ),
    )


# ============================================================
# PAYMENT DETAILS
# ============================================================

def payment_text(
    payment,
):

    reviewed = "-"

    if payment.reviewed_at:

        reviewed = (
            payment.reviewed_at
            .strftime(
                "%Y/%m/%d %H:%M"
            )
        )

    return (
        "💳 PAYMENT REVIEW\n"
        "━━━━━━━━━━━━━━━━\n\n"

        f"🆔 Payment: #{payment.id}\n"
        f"👤 User: {payment.telegram_id}\n\n"

        f"💳 Method: "
        f"{payment.payment_method or '-'}\n"

        f"💎 VIP: "
        f"{payment.plan_days or '-'} days\n"

        f"💵 Plan Price: "
        f"{payment.plan_price or '-'} USDT\n\n"

        f"🪙 Asset: {payment.asset}\n"
        f"🌐 Network: {payment.network}\n"
        f"💰 Amount: {payment.amount}\n\n"

        "🔗 TXID / Reference:\n"
        f"{payment.txid or '-'}\n\n"

        "📬 Destination:\n"
        f"{payment.destination or '-'}\n\n"

        f"📌 Status: {payment.status.upper()}\n"
        f"👮 Reviewed By: "
        f"{payment.reviewed_by or '-'}\n"
        f"🕒 Reviewed: {reviewed}"
    )


def review_keyboard(
    payment,
):

    rows = []

    if payment.status == "pending":

        rows.append(
            [
                InlineKeyboardButton(
                    "✅ APPROVE",
                    callback_data=(
                        f"adminpay_approve_{payment.id}"
                    ),
                ),

                InlineKeyboardButton(
                    "❌ REJECT",
                    callback_data=(
                        f"adminpay_reject_{payment.id}"
                    ),
                ),
            ]
        )

    rows.append(
        [
            InlineKeyboardButton(
                "⬅️ Pending Payments",
                callback_data="adminpay_home",
            )
        ]
    )

    rows.append(
        [
            InlineKeyboardButton(
                "⬅️ Admin Panel",
                callback_data="admin_home",
            )
        ]
    )

    return InlineKeyboardMarkup(
        rows
    )


# ============================================================
# CALLBACK
# ============================================================

async def admin_payment_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = (
        update.callback_query
    )

    if query is None:
        return

    admin_id = (
        query.from_user.id
    )

    if not is_admin(
        admin_id
    ):

        await query.answer(
            "⛔ Access denied",
            show_alert=True,
        )

        return

    await query.answer()

    data = (
        query.data
        or ""
    )

    # --------------------------------------------------------
    # HOME
    # --------------------------------------------------------

    if data == "adminpay_home":

        items = pending_payments(
            100
        )

        await query.edit_message_text(
            pending_text(),
            reply_markup=(
                pending_keyboard(
                    items
                )
            ),
        )

        return

    # --------------------------------------------------------
    # VIEW
    # --------------------------------------------------------

    if data.startswith(
        "adminpay_view_"
    ):

        try:

            payment_id = int(
                data.replace(
                    "adminpay_view_",
                    "",
                    1,
                )
            )

        except ValueError:
            return

        payment = get_payment(
            payment_id
        )

        if payment is None:

            await query.answer(
                "Payment not found",
                show_alert=True,
            )

            return

        await query.edit_message_text(
            payment_text(
                payment
            ),
            reply_markup=(
                review_keyboard(
                    payment
                )
            ),
        )

        return

    # --------------------------------------------------------
    # APPROVE
    # --------------------------------------------------------

    if data.startswith(
        "adminpay_approve_"
    ):

        try:

            payment_id = int(
                data.replace(
                    "adminpay_approve_",
                    "",
                    1,
                )
            )

        except ValueError:
            return

        result = approve_payment(
            payment_id,
            admin_id,
        )

        if not result:

            await query.answer(
                "Approve failed",
                show_alert=True,
            )

            return

        # The first successful approval returns
        # user information used for notification.
        if isinstance(
            result,
            dict,
        ):

            telegram_id = (
                result[
                    "telegram_id"
                ]
            )

            expiry = (
                result[
                    "vip_expires_at"
                ]
            )

            try:

                await context.bot.send_message(
                    chat_id=telegram_id,
                    text=(
                        "💎 ALIFT VIP ACTIVATED\n"
                        "━━━━━━━━━━━━━━━━\n\n"

                        "✅ پرداخت شما تأیید شد.\n\n"

                        "📅 VIP Expire:\n"
                        f"{expiry.strftime('%Y/%m/%d')}\n\n"

                        "🔔 Alert Limit: 50\n"
                        "🔎 Crypto Search: Unlimited\n\n"

                        "از همراهی شما با ALIFT "
                        "سپاسگزاریم 🚀"
                    ),
                )

            except Exception:
                pass

        audit(
            admin_id=admin_id,
            action="approve_payment",
            target_type="payment",
            target_id=payment_id,
        )

        await query.edit_message_text(
            (
                "✅ PAYMENT APPROVED\n"
                "━━━━━━━━━━━━━━━━\n\n"

                f"Payment #{payment_id}\n\n"
                "💎 VIP activated."
            ),
            reply_markup=(
                InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "⬅️ Pending Payments",
                                callback_data=(
                                    "adminpay_home"
                                ),
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                "⬅️ Admin Panel",
                                callback_data=(
                                    "admin_home"
                                ),
                            )
                        ],
                    ]
                )
            ),
        )

        return

    # --------------------------------------------------------
    # REJECT
    # --------------------------------------------------------

    if data.startswith(
        "adminpay_reject_"
    ):

        try:

            payment_id = int(
                data.replace(
                    "adminpay_reject_",
                    "",
                    1,
                )
            )

        except ValueError:
            return

        payment = get_payment(
            payment_id
        )

        if payment is None:

            await query.answer(
                "Payment not found",
                show_alert=True,
            )

            return

        success = reject_payment(
            payment_id,
            admin_id,
            reason=(
                "Rejected by admin"
            ),
        )

        if not success:

            await query.answer(
                "Reject failed",
                show_alert=True,
            )

            return

        try:

            await context.bot.send_message(
                chat_id=(
                    payment.telegram_id
                ),
                text=(
                    "❌ ALIFT PAYMENT REJECTED\n"
                    "━━━━━━━━━━━━━━━━\n\n"

                    f"Payment #{payment_id}\n\n"

                    "پرداخت تأیید نشد.\n"
                    "برای پیگیری از بخش "
                    "پشتیبانی تیکت ثبت کن."
                ),
            )

        except Exception:
            pass

        audit(
            admin_id=admin_id,
            action="reject_payment",
            target_type="payment",
            target_id=payment_id,
        )

        await query.edit_message_text(
            (
                "❌ PAYMENT REJECTED\n"
                "━━━━━━━━━━━━━━━━\n\n"

                f"Payment #{payment_id}"
            ),
            reply_markup=(
                InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "⬅️ Pending Payments",
                                callback_data=(
                                    "adminpay_home"
                                ),
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                "⬅️ Admin Panel",
                                callback_data=(
                                    "admin_home"
                                ),
                            )
                        ],
                    ]
                )
            ),
        )
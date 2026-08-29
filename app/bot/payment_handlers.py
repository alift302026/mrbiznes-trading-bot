from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)

try:
    from telegram import CopyTextButton
except ImportError:
    CopyTextButton = None

from telegram.ext import (
    ContextTypes,
)

from app.services.payment_service import (
    BANK_CARDS,
    CRYPTO_DESTINATIONS,
    VIP_PLANS,
    create_bank_payment,
    create_crypto_payment,
    user_payments,
)

from app.services.user_service import (
    get_user,
)


# ============================================================
# COPY BUTTON
# ============================================================

def copy_button(
    label,
    text,
):

    if CopyTextButton is None:
        return None

    try:

        return InlineKeyboardButton(
            label,
            copy_text=(
                CopyTextButton(
                    text=text
                )
            ),
        )

    except Exception:

        return None


# ============================================================
# HOME
# ============================================================

def payment_home_text(
    telegram_id,
):

    user = get_user(
        telegram_id
    )

    if user is None:

        plan = "NORMAL"
        expiry = "-"

    else:

        plan = (
            user.membership_type
            or "normal"
        ).upper()

        expiry = "-"

        if user.vip_expires_at:

            expiry = (
                user.vip_expires_at
                .strftime(
                    "%Y/%m/%d"
                )
            )

    return (
        "💎 MrBiznes VIP & PAYMENT\n"
        "━━━━━━━━━━━━━━━━\n\n"

        f"👤 Plan: {plan}\n"
        f"📅 VIP Expire: {expiry}\n\n"

        "🚀 MrBiznes VIP\n\n"

        "🔔 تا 50 آلارم فعال\n"
        "🔎 جستجوی نامحدود Crypto\n"
        "💎 دسترسی به امکانات VIP آینده\n\n"

        "━━━━━━━━━━━━━━━━\n"
        "💳 VIP PLANS\n\n"

        "30 روز → 10 USDT\n"
        "90 روز → 27 USDT\n"
        "180 روز → 50 USDT\n"
        "365 روز → 80 USDT\n\n"

        "روش پرداخت را پس از انتخاب پلن "
        "مشخص می‌کنی."
    )


def payment_home_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "💎 خرید / تمدید VIP",
                    callback_data=(
                        "payment_plans"
                    ),
                )
            ],

            [
                InlineKeyboardButton(
                    "📜 تاریخچه پرداخت",
                    callback_data=(
                        "payment_history"
                    ),
                )
            ],

            [
                InlineKeyboardButton(
                    "❓ راهنمای پرداخت",
                    callback_data=(
                        "payment_help"
                    ),
                )
            ],
        ]
    )


async def payment_home(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    clear_payment_flow(
        context
    )

    await update.message.reply_text(
        payment_home_text(
            update.effective_user.id
        ),
        reply_markup=(
            payment_home_keyboard()
        ),
    )


# ============================================================
# PLANS
# ============================================================

def plans_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "30 روز | 10 USDT",
                    callback_data=(
                        "payment_plan_30"
                    ),
                ),

                InlineKeyboardButton(
                    "90 روز | 27 USDT",
                    callback_data=(
                        "payment_plan_90"
                    ),
                ),
            ],

            [
                InlineKeyboardButton(
                    "180 روز | 50 USDT",
                    callback_data=(
                        "payment_plan_180"
                    ),
                ),

                InlineKeyboardButton(
                    "365 روز | 80 USDT",
                    callback_data=(
                        "payment_plan_365"
                    ),
                ),
            ],

            [
                InlineKeyboardButton(
                    "⬅️ Payment",
                    callback_data=(
                        "payment_home"
                    ),
                )
            ],
        ]
    )


# ============================================================
# METHODS
# ============================================================

def methods_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "₿ پرداخت رمزارزی",
                    callback_data=(
                        "payment_method_crypto"
                    ),
                )
            ],

            [
                InlineKeyboardButton(
                    "💳 کارت‌به‌کارت",
                    callback_data=(
                        "payment_method_bank"
                    ),
                )
            ],

            [
                InlineKeyboardButton(
                    "⬅️ پلن‌ها",
                    callback_data=(
                        "payment_plans"
                    ),
                )
            ],
        ]
    )


# ============================================================
# CRYPTO
# ============================================================

def crypto_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "💵 USDT / TRC20",
                    callback_data=(
                        "payment_crypto_usdt_trc20"
                    ),
                )
            ],

            [
                InlineKeyboardButton(
                    "₿ BTC / Bitcoin",
                    callback_data=(
                        "payment_crypto_btc"
                    ),
                ),

                InlineKeyboardButton(
                    "🟡 BNB / BEP20",
                    callback_data=(
                        "payment_crypto_bnb"
                    ),
                ),
            ],

            [
                InlineKeyboardButton(
                    "🟣 SOL / Solana",
                    callback_data=(
                        "payment_crypto_sol"
                    ),
                ),

                InlineKeyboardButton(
                    "🔴 TRX / TRON",
                    callback_data=(
                        "payment_crypto_trx"
                    ),
                ),
            ],

            [
                InlineKeyboardButton(
                    "⬅️ روش پرداخت",
                    callback_data=(
                        "payment_methods"
                    ),
                )
            ],
        ]
    )


def crypto_destination_keyboard(
    crypto_key,
):

    destination = (
        CRYPTO_DESTINATIONS[
            crypto_key
        ]
    )

    rows = []

    copy = copy_button(
        "📋 Copy Address",
        destination[
            "address"
        ],
    )

    if copy:

        rows.append(
            [copy]
        )

    rows.append(
        [
            InlineKeyboardButton(
                "✅ پرداخت کردم",
                callback_data=(
                    f"payment_crypto_paid_{crypto_key}"
                ),
            )
        ]
    )

    rows.append(
        [
            InlineKeyboardButton(
                "⬅️ Crypto",
                callback_data=(
                    "payment_method_crypto"
                ),
            )
        ]
    )

    return InlineKeyboardMarkup(
        rows
    )


# ============================================================
# BANKS
# ============================================================

def banks_keyboard():

    rows = []

    for key, data in (
        BANK_CARDS.items()
    ):

        rows.append(
            [
                InlineKeyboardButton(
                    (
                        f"💳 {data['bank']} "
                        f"| ****{data['card'][-4:]}"
                    ),
                    callback_data=(
                        f"payment_bank_{key}"
                    ),
                )
            ]
        )

    rows.append(
        [
            InlineKeyboardButton(
                "⬅️ روش پرداخت",
                callback_data=(
                    "payment_methods"
                ),
            )
        ]
    )

    return InlineKeyboardMarkup(
        rows
    )


def bank_card_keyboard(
    bank_key,
):

    bank = (
        BANK_CARDS[
            bank_key
        ]
    )

    rows = []

    copy = copy_button(
        "📋 Copy Card Number",
        bank[
            "card"
        ],
    )

    if copy:

        rows.append(
            [copy]
        )

    rows.append(
        [
            InlineKeyboardButton(
                "✅ واریز انجام شد",
                callback_data=(
                    f"payment_bank_paid_{bank_key}"
                ),
            )
        ]
    )

    rows.append(
        [
            InlineKeyboardButton(
                "⬅️ کارت‌ها",
                callback_data=(
                    "payment_method_bank"
                ),
            )
        ]
    )

    return InlineKeyboardMarkup(
        rows
    )


# ============================================================
# HISTORY
# ============================================================

def status_icon(
    status,
):

    return {
        "pending":
            "🟡",

        "confirmed":
            "🟢",

        "rejected":
            "🔴",
    }.get(
        status,
        "⚪",
    )


def payment_history_text(
    telegram_id,
):

    items = user_payments(
        telegram_id,
        20,
    )

    if not items:

        return (
            "📜 PAYMENT HISTORY\n"
            "━━━━━━━━━━━━━━━━\n\n"

            "هنوز پرداختی ثبت نشده است."
        )

    lines = [
        "📜 PAYMENT HISTORY",
        "━━━━━━━━━━━━━━━━",
        "",
    ]

    for item in items:

        lines.extend(
            [
                (
                    f"{status_icon(item.status)} "
                    f"Payment #{item.id}"
                ),

                (
                    f"💎 VIP: "
                    f"{item.plan_days or '-'} days"
                ),

                (
                    f"💳 Method: "
                    f"{item.payment_method or '-'}"
                ),

                (
                    f"💰 Asset: "
                    f"{item.asset}"
                ),

                (
                    f"📌 Status: "
                    f"{item.status.upper()}"
                ),

                "",
            ]
        )

    return "\n".join(
        lines
    )


# ============================================================
# CALLBACK
# ============================================================

async def payment_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = (
        update.callback_query
    )

    if query is None:
        return

    await query.answer()

    user_id = (
        query.from_user.id
    )

    data = (
        query.data
        or ""
    )

    # HOME

    if data == "payment_home":

        clear_payment_flow(
            context
        )

        await query.edit_message_text(
            payment_home_text(
                user_id
            ),
            reply_markup=(
                payment_home_keyboard()
            ),
        )

        return

    # HELP

    if data == "payment_help":

        await query.edit_message_text(
            (
                "❓ PAYMENT GUIDE\n"
                "━━━━━━━━━━━━━━━━\n\n"

                "1️⃣ پلن VIP را انتخاب کن.\n"
                "2️⃣ روش پرداخت را مشخص کن.\n"
                "3️⃣ فقط به آدرس/کارت نمایش‌داده‌شده "
                "پرداخت کن.\n"
                "4️⃣ TXID یا کد پیگیری را ثبت کن.\n"
                "5️⃣ پرداخت Pending می‌شود.\n"
                "6️⃣ پس از بررسی Admin، VIP فعال می‌شود.\n\n"

                "🔐 هرگز Seed Phrase، Private Key، "
                "رمز کارت یا رمز صرافی را ارسال نکن."
            ),
            reply_markup=(
                payment_home_keyboard()
            ),
        )

        return

    # HISTORY

    if data == "payment_history":

        await query.edit_message_text(
            payment_history_text(
                user_id
            ),
            reply_markup=(
                payment_home_keyboard()
            ),
        )

        return

    # PLANS

    if data == "payment_plans":

        clear_payment_flow(
            context
        )

        await query.edit_message_text(
            (
                "💎 SELECT VIP PLAN\n"
                "━━━━━━━━━━━━━━━━\n\n"

                "مدت اشتراک را انتخاب کن:"
            ),
            reply_markup=(
                plans_keyboard()
            ),
        )

        return

    # PLAN SELECT

    if data.startswith(
        "payment_plan_"
    ):

        try:

            days = int(
                data.replace(
                    "payment_plan_",
                    "",
                    1,
                )
            )

        except ValueError:
            return

        price = (
            VIP_PLANS.get(
                days
            )
        )

        if price is None:
            return

        context.user_data[
            "payment_flow"
        ] = {
            "plan_days":
                days,

            "plan_price":
                price,
        }

        await query.edit_message_text(
            (
                "💎 VIP PLAN SELECTED\n"
                "━━━━━━━━━━━━━━━━\n\n"

                f"📅 Duration: {days} days\n"
                f"💰 Price: {price:g} USDT\n\n"

                "روش پرداخت را انتخاب کن:"
            ),
            reply_markup=(
                methods_keyboard()
            ),
        )

        return

    # METHODS

    if data == "payment_methods":

        flow = get_payment_flow(
            context
        )

        if not flow:

            await query.edit_message_text(
                "❌ ابتدا پلن VIP را انتخاب کن.",
                reply_markup=(
                    plans_keyboard()
                ),
            )

            return

        await query.edit_message_text(
            (
                "💳 PAYMENT METHOD\n"
                "━━━━━━━━━━━━━━━━\n\n"

                f"Plan: {flow['plan_days']} days\n"
                f"Price: {flow['plan_price']:g} USDT"
            ),
            reply_markup=(
                methods_keyboard()
            ),
        )

        return

    # CRYPTO HOME

    if data == "payment_method_crypto":

        flow = get_payment_flow(
            context
        )

        if not flow:

            await query.edit_message_text(
                "❌ ابتدا پلن را انتخاب کن.",
                reply_markup=(
                    plans_keyboard()
                ),
            )

            return

        await query.edit_message_text(
            (
                "₿ CRYPTO PAYMENT\n"
                "━━━━━━━━━━━━━━━━\n\n"

                f"💎 {flow['plan_days']} days\n"
                f"💰 {flow['plan_price']:g} USDT\n\n"

                "شبکه پرداخت را انتخاب کن.\n\n"

                "⚠️ شبکه و آدرس باید دقیقاً "
                "با اطلاعات نمایش‌داده‌شده یکسان باشد."
            ),
            reply_markup=(
                crypto_keyboard()
            ),
        )

        return

    # CRYPTO DESTINATION

    if (
        data.startswith(
            "payment_crypto_"
        )
        and not data.startswith(
            "payment_crypto_paid_"
        )
    ):

        crypto_key = data.replace(
            "payment_crypto_",
            "",
            1,
        )

        destination = (
            CRYPTO_DESTINATIONS.get(
                crypto_key
            )
        )

        flow = get_payment_flow(
            context
        )

        if (
            destination is None
            or not flow
        ):
            return

        flow[
            "crypto_key"
        ] = crypto_key

        await query.edit_message_text(
            (
                "₿ CRYPTO PAYMENT\n"
                "━━━━━━━━━━━━━━━━\n\n"

                f"💎 Plan: {flow['plan_days']} days\n"
                f"💵 Plan Value: {flow['plan_price']:g} USDT\n\n"

                f"🪙 Asset: {destination['asset']}\n"
                f"🌐 Network: {destination['network']}\n\n"

                "📬 ADDRESS:\n"
                f"{destination['address']}\n\n"

                "⚠️ اگر دارایی انتخاب‌شده USDT نیست، "
                "مقدار معادل پلن را بر اساس قیمت زمان "
                "پرداخت ارسال کن.\n\n"

                "پس از انتقال، «پرداخت کردم» را بزن."
            ),
            reply_markup=(
                crypto_destination_keyboard(
                    crypto_key
                )
            ),
            disable_web_page_preview=True,
        )

        return

    # CRYPTO PAID

    if data.startswith(
        "payment_crypto_paid_"
    ):

        crypto_key = data.replace(
            "payment_crypto_paid_",
            "",
            1,
        )

        if (
            crypto_key
            not in CRYPTO_DESTINATIONS
        ):
            return

        flow = get_payment_flow(
            context
        )

        if not flow:
            return

        flow[
            "crypto_key"
        ] = crypto_key

        context.user_data[
            "payment_input"
        ] = {
            "mode":
                "crypto_amount",
        }

        await query.edit_message_text(
            (
                "💰 AMOUNT\n"
                "━━━━━━━━━━━━━━━━\n\n"

                "مقدار رمزارزی که واقعاً ارسال کردی "
                "را به‌صورت عدد بفرست.\n\n"

                "مثال:\n"
                "10\n"
                "یا\n"
                "0.00012"
            )
        )

        return

    # BANK HOME

    if data == "payment_method_bank":

        flow = get_payment_flow(
            context
        )

        if not flow:
            return

        await query.edit_message_text(
            (
                "💳 CARD TO CARD\n"
                "━━━━━━━━━━━━━━━━\n\n"

                f"💎 VIP: {flow['plan_days']} days\n"
                f"💵 Base Price: {flow['plan_price']:g} USDT\n\n"

                "کارت مقصد را انتخاب کن.\n\n"

                "⚠️ مبلغ ریالی باید طبق نرخ اعلامی "
                "معتبر زمان پرداخت محاسبه شود."
            ),
            reply_markup=(
                banks_keyboard()
            ),
        )

        return

    # BANK CARD

    if (
        data.startswith(
            "payment_bank_"
        )
        and not data.startswith(
            "payment_bank_paid_"
        )
    ):

        bank_key = data.replace(
            "payment_bank_",
            "",
            1,
        )

        bank = (
            BANK_CARDS.get(
                bank_key
            )
        )

        flow = get_payment_flow(
            context
        )

        if (
            bank is None
            or not flow
        ):
            return

        flow[
            "bank_key"
        ] = bank_key

        await query.edit_message_text(
            (
                "💳 CARD TO CARD\n"
                "━━━━━━━━━━━━━━━━\n\n"

                f"🏦 بانک: {bank['bank']}\n"
                f"👤 صاحب حساب: {bank['owner']}\n\n"

                "💳 شماره کارت:\n"
                f"{bank['card']}\n\n"

                f"💎 VIP: {flow['plan_days']} days\n"
                f"💵 Base Price: {flow['plan_price']:g} USDT\n\n"

                "بعد از واریز، دکمه زیر را بزن."
            ),
            reply_markup=(
                bank_card_keyboard(
                    bank_key
                )
            ),
        )

        return

    # BANK PAID

    if data.startswith(
        "payment_bank_paid_"
    ):

        bank_key = data.replace(
            "payment_bank_paid_",
            "",
            1,
        )

        if (
            bank_key
            not in BANK_CARDS
        ):
            return

        flow = get_payment_flow(
            context
        )

        if not flow:
            return

        flow[
            "bank_key"
        ] = bank_key

        context.user_data[
            "payment_input"
        ] = {
            "mode":
                "bank_amount",
        }

        await query.edit_message_text(
            (
                "💰 مبلغ واریزی\n"
                "━━━━━━━━━━━━━━━━\n\n"

                "مبلغ ریالی که واریز کردی را "
                "فقط به صورت عدد بفرست.\n\n"

                "مثال:\n"
                "8500000"
            )
        )

        return


# ============================================================
# TEXT INPUT
# ============================================================

async def payment_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if (
        update.message is None
        or update.effective_user
        is None
    ):
        return False

    pending = (
        context.user_data.get(
            "payment_input"
        )
    )

    if not pending:
        return False

    user_id = (
        update.effective_user.id
    )

    text = (
        update.message.text
        or ""
    ).strip()

    flow = get_payment_flow(
        context
    )

    if not flow:

        context.user_data.pop(
            "payment_input",
            None,
        )

        return False

    mode = (
        pending[
            "mode"
        ]
    )

    # --------------------------------------------------------
    # CRYPTO AMOUNT
    # --------------------------------------------------------

    if mode == "crypto_amount":

        try:

            amount = float(
                text.replace(
                    ",",
                    ".",
                )
            )

            if amount <= 0:
                raise ValueError

        except ValueError:

            await update.message.reply_text(
                "❌ مقدار معتبر بفرست."
            )

            return True

        flow[
            "amount"
        ] = amount

        context.user_data[
            "payment_input"
        ] = {
            "mode":
                "crypto_txid",
        }

        await update.message.reply_text(
            (
                "🔗 TXID / Transaction Hash\n"
                "━━━━━━━━━━━━━━━━\n\n"

                "TXID تراکنش را ارسال کن.\n\n"

                "⚠️ TXID تکراری پذیرفته نمی‌شود."
            )
        )

        return True

    # --------------------------------------------------------
    # CRYPTO TXID
    # --------------------------------------------------------

    if mode == "crypto_txid":

        txid = text

        if len(txid) < 6:

            await update.message.reply_text(
                "❌ TXID معتبر نیست."
            )

            return True

        try:

            item = create_crypto_payment(
                telegram_id=user_id,
                plan_days=(
                    flow[
                        "plan_days"
                    ]
                ),
                crypto_key=(
                    flow[
                        "crypto_key"
                    ]
                ),
                txid=txid,
                amount=(
                    flow[
                        "amount"
                    ]
                ),
            )

        except ValueError as exc:

            if (
                str(exc)
                == "TXID already exists"
            ):

                message = (
                    "❌ این TXID قبلاً ثبت شده است."
                )

            else:

                message = (
                    "❌ ثبت پرداخت انجام نشد."
                )

            await update.message.reply_text(
                message
            )

            return True

        clear_payment_flow(
            context
        )

        await update.message.reply_text(
            (
                "✅ PAYMENT SUBMITTED\n"
                "━━━━━━━━━━━━━━━━\n\n"

                f"Payment ID: #{item.id}\n"
                f"💎 VIP: {item.plan_days} days\n"
                f"🪙 Asset: {item.asset}\n"
                f"🌐 Network: {item.network}\n"
                f"💰 Amount: {item.amount}\n"
                "📌 Status: 🟡 PENDING\n\n"

                "پس از بررسی پرداخت توسط Admin، "
                "وضعیت به‌روزرسانی و در صورت تأیید "
                "VIP فعال می‌شود."
            ),
            reply_markup=(
                payment_home_keyboard()
            ),
        )

        return True

    # --------------------------------------------------------
    # BANK AMOUNT
    # --------------------------------------------------------

    if mode == "bank_amount":

        try:

            amount = float(
                text.replace(
                    ",",
                    "",
                )
            )

            if amount <= 0:
                raise ValueError

        except ValueError:

            await update.message.reply_text(
                "❌ مبلغ معتبر نیست."
            )

            return True

        flow[
            "amount"
        ] = amount

        context.user_data[
            "payment_input"
        ] = {
            "mode":
                "bank_tracking",
        }

        await update.message.reply_text(
            (
                "🧾 کد پیگیری\n"
                "━━━━━━━━━━━━━━━━\n\n"

                "کد پیگیری / مرجع تراکنش بانکی "
                "را ارسال کن."
            )
        )

        return True

    # --------------------------------------------------------
    # BANK TRACKING
    # --------------------------------------------------------

    if mode == "bank_tracking":

        tracking = text

        if len(
            tracking
        ) < 3:

            await update.message.reply_text(
                "❌ کد پیگیری معتبر نیست."
            )

            return True

        try:

            item = create_bank_payment(
                telegram_id=user_id,
                plan_days=(
                    flow[
                        "plan_days"
                    ]
                ),
                bank_key=(
                    flow[
                        "bank_key"
                    ]
                ),
                tracking_code=(
                    tracking
                ),
                amount=(
                    flow[
                        "amount"
                    ]
                ),
                details=(
                    "Card-to-card payment"
                ),
            )

        except ValueError as exc:

            if (
                str(exc)
                == "Tracking code already exists"
            ):

                message = (
                    "❌ این کد پیگیری قبلاً "
                    "ثبت شده است."
                )

            else:

                message = (
                    "❌ ثبت پرداخت انجام نشد."
                )

            await update.message.reply_text(
                message
            )

            return True

        clear_payment_flow(
            context
        )

        await update.message.reply_text(
            (
                "✅ BANK PAYMENT SUBMITTED\n"
                "━━━━━━━━━━━━━━━━\n\n"

                f"Payment ID: #{item.id}\n"
                f"💎 VIP: {item.plan_days} days\n"
                f"💰 Amount: {item.amount:,.0f} IRR\n"
                "📌 Status: 🟡 PENDING\n\n"

                "پرداخت برای بررسی Admin ثبت شد."
            ),
            reply_markup=(
                payment_home_keyboard()
            ),
        )

        return True

    return False


# ============================================================
# FLOW
# ============================================================

def get_payment_flow(
    context,
):

    return context.user_data.get(
        "payment_flow"
    )


def clear_payment_flow(
    context,
):

    context.user_data.pop(
        "payment_flow",
        None,
    )

    context.user_data.pop(
        "payment_input",
        None,
    )
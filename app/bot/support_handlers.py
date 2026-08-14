from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)

from telegram.ext import (
    ContextTypes,
)

from app.services.support_service import (
    close_ticket,
    create_ticket,
    get_ticket,
    ticket_messages,
    user_reply,
    user_tickets,
)


# ============================================================
# LABELS
# ============================================================

CATEGORY_LABELS = {
    "technical": "🛠 فنی",
    "payment": "💳 مالی و VIP",
    "alerts": "🔔 سیگنال و آلارم",
    "suggestion": "💡 پیشنهاد و انتقاد",
    "other": "📌 سایر",
}

STATUS_LABELS = {
    "open": "🟡 باز",
    "answered": "🟢 پاسخ داده شده",
    "closed": "⚫ بسته",
}


# ============================================================
# HOME
# ============================================================

def support_home_text():

    return (
        "🎧 ALIFT SUPPORT\n"
        "━━━━━━━━━━━━━━━━\n\n"

        "مرکز پشتیبانی ALIFT TRADER\n\n"

        "اگر سؤال، مشکل فنی، مشکل پرداخت، "
        "موضوع مربوط به آلارم‌ها یا پیشنهادی داری، "
        "از این بخش تیکت بساز.\n\n"

        "🎫 هر درخواست یک شماره تیکت اختصاصی دارد.\n"
        "📬 پاسخ پشتیبانی داخل همین ربات قابل مشاهده است.\n\n"

        "برای جلوگیری از اسپم، هر کاربر حداکثر "
        "۳ تیکت باز همزمان می‌تواند داشته باشد."
    )


def support_home_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "➕ ساخت تیکت جدید",
                    callback_data="support_new",
                )
            ],
            [
                InlineKeyboardButton(
                    "📋 تیکت‌های من",
                    callback_data="support_list",
                )
            ],
            [
                InlineKeyboardButton(
                    "🔄 بروزرسانی",
                    callback_data="support_home",
                )
            ],
        ]
    )


async def support_home(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    await update.message.reply_text(
        support_home_text(),
        reply_markup=(
            support_home_keyboard()
        ),
    )


# ============================================================
# CATEGORY
# ============================================================

def category_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    CATEGORY_LABELS[
                        "technical"
                    ],
                    callback_data=(
                        "support_category_technical"
                    ),
                ),
                InlineKeyboardButton(
                    CATEGORY_LABELS[
                        "payment"
                    ],
                    callback_data=(
                        "support_category_payment"
                    ),
                ),
            ],
            [
                InlineKeyboardButton(
                    CATEGORY_LABELS[
                        "alerts"
                    ],
                    callback_data=(
                        "support_category_alerts"
                    ),
                ),
            ],
            [
                InlineKeyboardButton(
                    CATEGORY_LABELS[
                        "suggestion"
                    ],
                    callback_data=(
                        "support_category_suggestion"
                    ),
                ),
                InlineKeyboardButton(
                    CATEGORY_LABELS[
                        "other"
                    ],
                    callback_data=(
                        "support_category_other"
                    ),
                ),
            ],
            [
                InlineKeyboardButton(
                    "⬅️ بازگشت",
                    callback_data="support_home",
                )
            ],
        ]
    )


# ============================================================
# TICKET LIST
# ============================================================

def ticket_list_keyboard(
    tickets,
):

    rows = []

    for ticket in tickets:

        icon = {
            "open": "🟡",
            "answered": "🟢",
            "closed": "⚫",
        }.get(
            ticket.status,
            "⚪",
        )

        rows.append(
            [
                InlineKeyboardButton(
                    (
                        f"{icon} Ticket #{ticket.id} "
                        f"| {CATEGORY_LABELS.get(ticket.category, ticket.category)}"
                    ),
                    callback_data=(
                        f"support_view_{ticket.id}"
                    ),
                )
            ]
        )

    rows.append(
        [
            InlineKeyboardButton(
                "➕ تیکت جدید",
                callback_data="support_new",
            )
        ]
    )

    rows.append(
        [
            InlineKeyboardButton(
                "🏠 پشتیبانی",
                callback_data="support_home",
            )
        ]
    )

    return InlineKeyboardMarkup(
        rows
    )


# ============================================================
# TICKET VIEW
# ============================================================

def ticket_text(
    ticket,
):

    messages = ticket_messages(
        ticket.id
    )

    lines = [
        f"🎫 TICKET #{ticket.id}",
        "━━━━━━━━━━━━━━━━",
        "",
        (
            "📂 دسته: "
            f"{CATEGORY_LABELS.get(ticket.category, ticket.category)}"
        ),
        (
            "📌 وضعیت: "
            f"{STATUS_LABELS.get(ticket.status, ticket.status)}"
        ),
        "",
        "💬 گفتگو:",
        "",
    ]

    if not messages:

        lines.append(
            "پیامی ثبت نشده."
        )

    for item in messages[-15:]:

        if (
            item.sender_type
            == "admin"
        ):

            sender = (
                "🛡 ALIFT SUPPORT"
            )

        else:

            sender = "👤 شما"

        text = (
            item.message
            or ""
        )

        # Prevent excessively large Telegram messages
        if len(text) > 1000:

            text = (
                text[:1000]
                + "..."
            )

        lines.append(
            f"{sender}:\n{text}\n"
        )

    return "\n".join(
        lines
    )


def ticket_keyboard(
    ticket,
):

    rows = []

    if ticket.status != "closed":

        rows.append(
            [
                InlineKeyboardButton(
                    "✍️ پاسخ به تیکت",
                    callback_data=(
                        f"support_reply_{ticket.id}"
                    ),
                )
            ]
        )

        rows.append(
            [
                InlineKeyboardButton(
                    "✅ بستن تیکت",
                    callback_data=(
                        f"support_close_{ticket.id}"
                    ),
                )
            ]
        )

    rows.append(
        [
            InlineKeyboardButton(
                "🔄 بروزرسانی",
                callback_data=(
                    f"support_view_{ticket.id}"
                ),
            )
        ]
    )

    rows.append(
        [
            InlineKeyboardButton(
                "⬅️ تیکت‌های من",
                callback_data="support_list",
            )
        ]
    )

    return InlineKeyboardMarkup(
        rows
    )


# ============================================================
# CALLBACK
# ============================================================

async def support_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = (
        update.callback_query
    )

    if query is None:
        return

    await query.answer()

    telegram_id = (
        query.from_user.id
    )

    data = (
        query.data
        or ""
    )

    # --------------------------------------------------------
    # HOME
    # --------------------------------------------------------

    if data == "support_home":

        context.user_data.pop(
            "support_input",
            None,
        )

        await query.edit_message_text(
            support_home_text(),
            reply_markup=(
                support_home_keyboard()
            ),
        )

        return

    # --------------------------------------------------------
    # NEW
    # --------------------------------------------------------

    if data == "support_new":

        context.user_data.pop(
            "support_input",
            None,
        )

        await query.edit_message_text(
            (
                "➕ تیکت جدید\n"
                "━━━━━━━━━━━━━━━━\n\n"
                "موضوع درخواستت را انتخاب کن:"
            ),
            reply_markup=(
                category_keyboard()
            ),
        )

        return

    # --------------------------------------------------------
    # CATEGORY
    # --------------------------------------------------------

    if data.startswith(
        "support_category_"
    ):

        category = data.replace(
            "support_category_",
            "",
            1,
        )

        if (
            category
            not in CATEGORY_LABELS
        ):
            return

        context.user_data[
            "support_input"
        ] = {
            "mode":
                "new",

            "category":
                category,
        }

        await query.edit_message_text(
            (
                "✍️ پیام تیکت\n"
                "━━━━━━━━━━━━━━━━\n\n"
                f"دسته: {CATEGORY_LABELS[category]}\n\n"
                "حالا پیام یا توضیح مشکلت را بفرست.\n\n"
                "حداکثر 4000 کاراکتر."
            )
        )

        return

    # --------------------------------------------------------
    # LIST
    # --------------------------------------------------------

    if data == "support_list":

        context.user_data.pop(
            "support_input",
            None,
        )

        tickets = user_tickets(
            telegram_id
        )

        if not tickets:

            text = (
                "📋 تیکت‌های من\n"
                "━━━━━━━━━━━━━━━━\n\n"
                "هنوز تیکتی ثبت نکردی."
            )

        else:

            open_count = sum(
                1
                for ticket in tickets
                if ticket.status
                != "closed"
            )

            text = (
                "📋 تیکت‌های من\n"
                "━━━━━━━━━━━━━━━━\n\n"
                f"🎫 تعداد: {len(tickets)}\n"
                f"📬 باز: {open_count}\n\n"
                "برای مشاهده روی تیکت بزن."
            )

        await query.edit_message_text(
            text,
            reply_markup=(
                ticket_list_keyboard(
                    tickets
                )
            ),
        )

        return

    # --------------------------------------------------------
    # VIEW
    # --------------------------------------------------------

    if data.startswith(
        "support_view_"
    ):

        try:

            ticket_id = int(
                data.replace(
                    "support_view_",
                    "",
                    1,
                )
            )

        except ValueError:
            return

        ticket = get_ticket(
            ticket_id,
            telegram_id,
        )

        if ticket is None:

            await query.answer(
                "تیکت پیدا نشد.",
                show_alert=True,
            )

            return

        await query.edit_message_text(
            ticket_text(
                ticket
            ),
            reply_markup=(
                ticket_keyboard(
                    ticket
                )
            ),
        )

        return

    # --------------------------------------------------------
    # REPLY
    # --------------------------------------------------------

    if data.startswith(
        "support_reply_"
    ):

        try:

            ticket_id = int(
                data.replace(
                    "support_reply_",
                    "",
                    1,
                )
            )

        except ValueError:
            return

        ticket = get_ticket(
            ticket_id,
            telegram_id,
        )

        if (
            ticket is None
            or ticket.status
            == "closed"
        ):

            await query.answer(
                "امکان پاسخ وجود ندارد.",
                show_alert=True,
            )

            return

        context.user_data[
            "support_input"
        ] = {
            "mode":
                "reply",

            "ticket_id":
                ticket_id,
        }

        await query.edit_message_text(
            (
                f"✍️ پاسخ به Ticket #{ticket_id}\n"
                "━━━━━━━━━━━━━━━━\n\n"
                "پیامت را ارسال کن."
            )
        )

        return

    # --------------------------------------------------------
    # CLOSE
    # --------------------------------------------------------

    if data.startswith(
        "support_close_"
    ):

        try:

            ticket_id = int(
                data.replace(
                    "support_close_",
                    "",
                    1,
                )
            )

        except ValueError:
            return

        success = close_ticket(
            ticket_id,
            telegram_id,
        )

        if not success:

            await query.answer(
                "تیکت پیدا نشد.",
                show_alert=True,
            )

            return

        context.user_data.pop(
            "support_input",
            None,
        )

        await query.edit_message_text(
            (
                f"✅ Ticket #{ticket_id} بسته شد."
            ),
            reply_markup=(
                InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "📋 تیکت‌های من",
                                callback_data=(
                                    "support_list"
                                ),
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                "🏠 پشتیبانی",
                                callback_data=(
                                    "support_home"
                                ),
                            )
                        ],
                    ]
                )
            ),
        )


# ============================================================
# TEXT MESSAGE HANDLER
# ============================================================

async def support_message(
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
            "support_input"
        )
    )

    if not pending:

        return False

    telegram_id = (
        update.effective_user.id
    )

    text = (
        update.message.text
        or ""
    ).strip()

    if (
        len(text) < 1
        or len(text) > 4000
    ):

        await update.message.reply_text(
            (
                "❌ پیام معتبر نیست.\n"
                "حداکثر 4000 کاراکتر."
            )
        )

        return True

    # --------------------------------------------------------
    # NEW TICKET
    # --------------------------------------------------------

    if (
        pending.get("mode")
        == "new"
    ):

        try:

            ticket = create_ticket(
                telegram_id=telegram_id,
                category=pending[
                    "category"
                ],
                message=text,
            )

        except ValueError as exc:

            if (
                str(exc)
                == "Too many open tickets"
            ):

                message = (
                    "⚠️ حداکثر ۳ تیکت باز "
                    "همزمان مجاز است.\n\n"
                    "یکی از تیکت‌های قبلی را "
                    "ببند و دوباره تلاش کن."
                )

            else:

                message = (
                    "❌ امکان ساخت تیکت وجود ندارد."
                )

            await update.message.reply_text(
                message,
                reply_markup=(
                    support_home_keyboard()
                ),
            )

            context.user_data.pop(
                "support_input",
                None,
            )

            return True

        context.user_data.pop(
            "support_input",
            None,
        )

        await update.message.reply_text(
            (
                "✅ تیکت با موفقیت ثبت شد\n"
                "━━━━━━━━━━━━━━━━\n\n"
                f"🎫 Ticket #{ticket.id}\n"
                f"📂 {CATEGORY_LABELS.get(ticket.category, ticket.category)}\n"
                "📌 وضعیت: 🟡 باز\n\n"
                "پاسخ پشتیبانی از همین بخش "
                "قابل مشاهده خواهد بود."
            ),
            reply_markup=(
                InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "🎫 مشاهده تیکت",
                                callback_data=(
                                    f"support_view_{ticket.id}"
                                ),
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                "📋 تیکت‌های من",
                                callback_data=(
                                    "support_list"
                                ),
                            )
                        ],
                    ]
                )
            ),
        )

        return True

    # --------------------------------------------------------
    # USER REPLY
    # --------------------------------------------------------

    if (
        pending.get("mode")
        == "reply"
    ):

        ticket_id = (
            pending.get(
                "ticket_id"
            )
        )

        success = user_reply(
            ticket_id=ticket_id,
            telegram_id=telegram_id,
            message=text,
        )

        context.user_data.pop(
            "support_input",
            None,
        )

        if not success:

            await update.message.reply_text(
                "❌ ارسال پاسخ انجام نشد."
            )

            return True

        await update.message.reply_text(
            (
                "✅ پاسخ ارسال شد.\n\n"
                f"Ticket #{ticket_id}"
            ),
            reply_markup=(
                InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "🎫 مشاهده تیکت",
                                callback_data=(
                                    f"support_view_{ticket_id}"
                                ),
                            )
                        ]
                    ]
                )
            ),
        )

        return True

    return False
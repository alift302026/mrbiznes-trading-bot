from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)

from telegram.ext import (
    ContextTypes,
)

from app.services.referral_service import (
    point_history,
    referral_summary,
)


def referral_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "📤 اشتراک لینک دعوت",
                    switch_inline_query="",
                )
            ],
            [
                InlineKeyboardButton(
                    "📜 تاریخچه امتیاز",
                    callback_data="referral_history",
                )
            ],
            [
                InlineKeyboardButton(
                    "🎁 پاداش‌ها",
                    callback_data="referral_rewards",
                )
            ],
            [
                InlineKeyboardButton(
                    "🔄 بروزرسانی",
                    callback_data="referral_home",
                )
            ],
        ]
    )


def referral_text(
    telegram_id,
):

    info = referral_summary(
        telegram_id
    )

    link = (
        info["link"]
        or "-"
    )

    return (
        "🎁 MrBiznes REFERRAL & POINTS\n"
        "━━━━━━━━━━━━━━━━\n\n"

        "🔗 لینک اختصاصی دعوت شما:\n"
        f"{link}\n\n"

        "👥 دعوت‌های موفق: "
        f"{info['invites']}\n"

        "⭐ امتیاز فعلی: "
        f"{info['points']}\n\n"

        "🎯 پاداش هر دعوت موفق: "
        f"+{info['reward_per_invite']} امتیاز\n\n"

        "دوستت باید برای اولین بار با لینک "
        "اختصاصی شما وارد ربات شود.\n\n"

        "🔒 هر کاربر فقط یک بار به عنوان "
        "دعوت موفق ثبت می‌شود."
    )


async def referral_home(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    telegram_id = (
        update.effective_user.id
    )

    await update.message.reply_text(
        referral_text(
            telegram_id
        ),
        reply_markup=(
            referral_keyboard()
        ),
        disable_web_page_preview=True,
    )


async def referral_callback(
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

    if data == "referral_home":

        await query.edit_message_text(
            referral_text(
                telegram_id
            ),
            reply_markup=(
                referral_keyboard()
            ),
            disable_web_page_preview=True,
        )

        return

    if data == "referral_history":

        items = point_history(
            telegram_id,
            limit=20,
        )

        if not items:

            text = (
                "📜 تاریخچه امتیاز\n"
                "━━━━━━━━━━━━━━━━\n\n"
                "هنوز تراکنش امتیازی نداری."
            )

        else:

            lines = [
                "📜 تاریخچه امتیاز",
                "━━━━━━━━━━━━━━━━",
                "",
            ]

            for item in items:

                sign = (
                    "+"
                    if item.amount > 0
                    else ""
                )

                lines.append(
                    (
                        f"{sign}{item.amount} ⭐ "
                        f"| {item.reason}"
                    )
                )

            text = "\n".join(
                lines
            )

        await query.edit_message_text(
            text,
            reply_markup=(
                InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "⬅️ بازگشت",
                                callback_data=(
                                    "referral_home"
                                ),
                            )
                        ]
                    ]
                )
            ),
        )

        return

    if data == "referral_rewards":

        await query.edit_message_text(
            (
                "🎁 MrBiznes REWARDS\n"
                "━━━━━━━━━━━━━━━━\n\n"

                "⭐ امتیازهای شما در مراحل بعد "
                "قابل استفاده برای:\n\n"

                "💎 تخفیف اشتراک VIP\n"
                "🎟 کدهای تخفیف\n"
                "🎁 کمپین‌های ویژه\n\n"

                "تبدیل امتیاز به پاداش پس از "
                "تکمیل Payment/VIP Engine فعال می‌شود."
            ),
            reply_markup=(
                InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "⬅️ بازگشت",
                                callback_data=(
                                    "referral_home"
                                ),
                            )
                        ]
                    ]
                )
            ),
        )
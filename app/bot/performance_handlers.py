from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)

from telegram.ext import (
    ContextTypes,
)

from app.services.performance_service import (
    MONTH_NAMES,
    all_time_summary,
    available_months,
    current_period,
    month_summary,
)


# ============================================================
# FORMAT
# ============================================================

def format_return(
    value,
):

    value = float(
        value or 0
    )

    if value > 0:
        return f"🟢 +{value:.2f}%"

    if value < 0:
        return f"🔴 {value:.2f}%"

    return "⚪ 0.00%"


def format_type(
    value,
):

    value = (
        value
        or "unknown"
    ).lower()

    labels = {
        "spot":
            "🟢 SPOT",

        "futures":
            "⚡ FUTURES",

        "free":
            "👤 FREE",

        "vip":
            "💎 VIP",
    }

    return labels.get(
        value,
        value.upper(),
    )


# ============================================================
# MONTH TEXT
# ============================================================

def performance_month_text(
    year,
    month,
):

    summary = month_summary(
        year,
        month,
    )

    title = (
        MONTH_NAMES.get(
            month,
            str(month),
        )
    )

    if not summary[
        "items"
    ]:

        return (
            "📈 MrBiznes MONTHLY PERFORMANCE\n"
            "━━━━━━━━━━━━━━━━\n\n"

            f"📅 {title} {year}\n\n"

            "هنوز داده عملکرد برای این ماه "
            "ثبت نشده است.\n\n"

            "پس از فعال‌شدن Signal Engine و "
            "ثبت نتایج واقعی، آمار این بخش "
            "به‌صورت شفاف نمایش داده می‌شود."
        )

    lines = [
        "📈 MrBiznes MONTHLY PERFORMANCE",
        "━━━━━━━━━━━━━━━━",
        "",
        f"📅 {title} {year}",
        "",
        f"📡 Total Signals: {summary['total']}",
        f"✅ Wins: {summary['wins']}",
        f"❌ Losses: {summary['losses']}",
        f"➖ Breakeven: {summary['breakeven']}",
        f"🎯 Win Rate: {summary['win_rate']:.2f}%",
        (
            "📊 Recorded Return: "
            f"{format_return(summary['return_percent'])}"
        ),
        "",
        "━━━━━━━━━━━━━━━━",
        "📊 Breakdown",
        "",
    ]

    for item in summary[
        "items"
    ]:

        decided = (
            (item.wins or 0)
            + (item.losses or 0)
        )

        if decided:

            win_rate = (
                (item.wins or 0)
                / decided
                * 100
            )

        else:

            win_rate = 0.0

        lines.extend(
            [
                format_type(
                    item.signal_type
                ),

                (
                    f"Signals: "
                    f"{item.total_signals or 0}"
                ),

                (
                    f"W/L/BE: "
                    f"{item.wins or 0} / "
                    f"{item.losses or 0} / "
                    f"{item.breakeven or 0}"
                ),

                (
                    f"Win Rate: "
                    f"{win_rate:.2f}%"
                ),

                (
                    "Return: "
                    f"{format_return(item.return_percent)}"
                ),

                "",
            ]
        )

    lines.extend(
        [
            "━━━━━━━━━━━━━━━━",
            "ℹ️ آمار فقط بر اساس نتایج ثبت‌شده "
            "در سیستم MrBiznes محاسبه می‌شود.",

            "",
            "⚠️ عملکرد گذشته تضمینی برای "
            "نتایج آینده نیست.",
        ]
    )

    return "\n".join(
        lines
    )


# ============================================================
# ALL TIME
# ============================================================

def all_time_text():

    data = all_time_summary()

    if data[
        "total"
    ] == 0:

        return (
            "🏆 MrBiznes ALL-TIME PERFORMANCE\n"
            "━━━━━━━━━━━━━━━━\n\n"

            "هنوز نتیجه واقعی برای محاسبه "
            "عملکرد کلی ثبت نشده است."
        )

    return (
        "🏆 MrBiznes ALL-TIME PERFORMANCE\n"
        "━━━━━━━━━━━━━━━━\n\n"

        f"📡 Signals: {data['total']}\n"
        f"✅ Wins: {data['wins']}\n"
        f"❌ Losses: {data['losses']}\n"
        f"➖ Breakeven: {data['breakeven']}\n\n"

        f"🎯 Win Rate: "
        f"{data['win_rate']:.2f}%\n"

        f"📊 Recorded Return: "
        f"{format_return(data['return_percent'])}\n\n"

        "⚠️ عملکرد گذشته تضمینی برای "
        "نتایج آینده نیست."
    )


# ============================================================
# KEYBOARDS
# ============================================================

def performance_home_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "📅 ماه جاری",
                    callback_data=(
                        "performance_current"
                    ),
                ),

                InlineKeyboardButton(
                    "🏆 All Time",
                    callback_data=(
                        "performance_all"
                    ),
                ),
            ],

            [
                InlineKeyboardButton(
                    "🗂 ماه‌های قبل",
                    callback_data=(
                        "performance_months"
                    ),
                )
            ],

            [
                InlineKeyboardButton(
                    "🔄 بروزرسانی",
                    callback_data=(
                        "performance_home"
                    ),
                )
            ],
        ]
    )


def months_keyboard():

    months = available_months(
        12
    )

    rows = []

    for year, month in months:

        name = (
            MONTH_NAMES.get(
                month,
                str(month),
            )
        )

        rows.append(
            [
                InlineKeyboardButton(
                    f"📅 {name} {year}",
                    callback_data=(
                        f"performance_view_{year}_{month}"
                    ),
                )
            ]
        )

    rows.append(
        [
            InlineKeyboardButton(
                "⬅️ Performance",
                callback_data=(
                    "performance_home"
                ),
            )
        ]
    )

    return InlineKeyboardMarkup(
        rows
    )


def back_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "⬅️ Performance",
                    callback_data=(
                        "performance_home"
                    ),
                )
            ]
        ]
    )


# ============================================================
# HOME
# ============================================================

def performance_home_text():

    year, month = (
        current_period()
    )

    month_name = (
        MONTH_NAMES.get(
            month,
            str(month),
        )
    )

    return (
        "📈 MrBiznes PERFORMANCE CENTER\n"
        "━━━━━━━━━━━━━━━━\n\n"

        "عملکرد سیگنال‌های ثبت‌شده MrBiznes "
        "در این بخش قابل مشاهده است.\n\n"

        f"📅 Current: {month_name} {year}\n\n"

        "📡 تعداد سیگنال\n"
        "✅ Win\n"
        "❌ Loss\n"
        "➖ Breakeven\n"
        "🎯 Win Rate\n"
        "📊 Recorded Return\n\n"

        "تمام آمار باید از نتایج واقعی "
        "ثبت‌شده در سیستم محاسبه شود."
    )


async def performance_home(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    await update.message.reply_text(
        performance_home_text(),
        reply_markup=(
            performance_home_keyboard()
        ),
    )


# ============================================================
# CALLBACK
# ============================================================

async def performance_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = (
        update.callback_query
    )

    if query is None:
        return

    await query.answer()

    data = (
        query.data
        or ""
    )

    if data == "performance_home":

        await query.edit_message_text(
            performance_home_text(),
            reply_markup=(
                performance_home_keyboard()
            ),
        )

        return

    if data == "performance_current":

        year, month = (
            current_period()
        )

        await query.edit_message_text(
            performance_month_text(
                year,
                month,
            ),
            reply_markup=(
                back_keyboard()
            ),
        )

        return

    if data == "performance_all":

        await query.edit_message_text(
            all_time_text(),
            reply_markup=(
                back_keyboard()
            ),
        )

        return

    if data == "performance_months":

        months = available_months(
            12
        )

        if months:

            text = (
                "🗂 PERFORMANCE HISTORY\n"
                "━━━━━━━━━━━━━━━━\n\n"
                "ماه موردنظر را انتخاب کن."
            )

        else:

            text = (
                "🗂 PERFORMANCE HISTORY\n"
                "━━━━━━━━━━━━━━━━\n\n"
                "هنوز تاریخچه‌ای ثبت نشده است."
            )

        await query.edit_message_text(
            text,
            reply_markup=(
                months_keyboard()
            ),
        )

        return

    if data.startswith(
        "performance_view_"
    ):

        payload = data.replace(
            "performance_view_",
            "",
            1,
        )

        parts = (
            payload.split(
                "_"
            )
        )

        if len(parts) != 2:
            return

        try:

            year = int(
                parts[0]
            )

            month = int(
                parts[1]
            )

        except ValueError:
            return

        if not (
            1 <= month <= 12
        ):
            return

        await query.edit_message_text(
            performance_month_text(
                year,
                month,
            ),
            reply_markup=(
                back_keyboard()
            ),
        )
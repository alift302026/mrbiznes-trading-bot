from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)

from telegram.ext import (
    ContextTypes,
)

from app.engines.market_intelligence import (
    intelligence_scan,
)


# ============================================================
# FORMAT
# ============================================================

def money(
    value,
):

    if value is None:
        return "-"

    value = float(
        value
    )

    if value >= 1_000_000_000:
        return (
            f"${value / 1_000_000_000:.2f}B"
        )

    if value >= 1_000_000:
        return (
            f"${value / 1_000_000:.2f}M"
        )

    if value >= 1_000:
        return (
            f"${value / 1_000:.2f}K"
        )

    return (
        f"${value:,.2f}"
    )


def change(
    value,
):

    if value is None:
        return "-"

    icon = (
        "🟢"
        if value > 0
        else
        "🔴"
        if value < 0
        else
        "⚪"
    )

    return (
        f"{icon} {value:+.2f}%"
    )


# ============================================================
# KEYBOARD
# ============================================================

def intelligence_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🚀 بیشترین رشد",
                    callback_data=(
                        "intel_gainers"
                    ),
                ),

                InlineKeyboardButton(
                    "🩸 بیشترین افت",
                    callback_data=(
                        "intel_losers"
                    ),
                ),
            ],

            [
                InlineKeyboardButton(
                    "🔥 بیشترین حجم",
                    callback_data=(
                        "intel_volume"
                    ),
                ),

                InlineKeyboardButton(
                    "🌡 وضعیت بازار",
                    callback_data=(
                        "intel_market"
                    ),
                ),
            ],

            [
                InlineKeyboardButton(
                    "🌊 Exchange Flow",
                    callback_data=(
                        "intel_flow"
                    ),
                )
            ],

            [
                InlineKeyboardButton(
                    "🔄 بروزرسانی",
                    callback_data=(
                        "intel_home"
                    ),
                )
            ],
        ]
    )


# ============================================================
# HOME
# ============================================================

def home_text():

    return (
        "🌊 MrBiznes MARKET INTELLIGENCE\n"
        "━━━━━━━━━━━━━━━━\n\n"

        "داده‌های زنده بازار برای شناسایی "
        "حرکت‌های مهم و تغییرات نقدینگی.\n\n"

        "🚀 Top Gainers\n"
        "🩸 Top Losers\n"
        "🔥 Volume Leaders\n"
        "🌡 Market Breadth\n"
        "🌊 Exchange Inflow / Outflow\n\n"

        "🏦 Crypto Market Source: XT\n\n"

        "⚠️ Volume با Exchange Flow متفاوت است. "
        "Inflow/Outflow فقط از داده On-chain "
        "معتبر نمایش داده خواهد شد."
    )


async def intelligence_home(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    await update.message.reply_text(
        home_text(),
        reply_markup=(
            intelligence_keyboard()
        ),
    )


# ============================================================
# CALLBACK
# ============================================================

async def intelligence_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if query is None:
        return

    await query.answer()

    data = (
        query.data
        or ""
    )

    if data == "intel_home":

        await query.edit_message_text(
            home_text(),
            reply_markup=(
                intelligence_keyboard()
            ),
        )

        return

    if data == "intel_flow":

        await query.edit_message_text(
            (
                "🌊 EXCHANGE FLOW\n"
                "━━━━━━━━━━━━━━━━\n\n"

                "این بخش برای داده واقعی:\n\n"

                "📥 Exchange Inflow\n"
                "📤 Exchange Outflow\n"
                "⚖️ Netflow\n"
                "🏦 Exchange Reserve\n"
                "🐋 Whale Transfers\n\n"

                "به Provider On-chain معتبر "
                "متصل خواهد شد.\n\n"

                "⚠️ MrBiznes هیچ عدد Inflow/Outflow "
                "را از روی Volume حدس نمی‌زند."
            ),
            reply_markup=(
                intelligence_keyboard()
            ),
        )

        return

    await query.edit_message_text(
        "⏳ در حال دریافت داده‌های XT..."
    )

    try:

        result = (
            await intelligence_scan(
                False
            )
        )

    except Exception:

        await query.edit_message_text(
            (
                "❌ دریافت Market Intelligence "
                "با خطا مواجه شد.\n\n"
                "چند لحظه بعد دوباره تلاش کن."
            ),
            reply_markup=(
                intelligence_keyboard()
            ),
        )

        return

    # MARKET

    if data == "intel_market":

        summary = result[
            "summary"
        ]

        total = max(
            1,
            summary[
                "with_change"
            ],
        )

        positive_percent = (
            summary[
                "positive"
            ]
            / total
            * 100
        )

        negative_percent = (
            summary[
                "negative"
            ]
            / total
            * 100
        )

        await query.edit_message_text(
            (
                "🌡 MARKET BREADTH\n"
                "━━━━━━━━━━━━━━━━\n\n"

                f"🪙 Assets: "
                f"{summary['assets']}\n\n"

                f"🟢 Positive: "
                f"{summary['positive']} "
                f"({positive_percent:.1f}%)\n"

                f"🔴 Negative: "
                f"{summary['negative']} "
                f"({negative_percent:.1f}%)\n"

                f"⚪ Flat: "
                f"{summary['flat']}\n\n"

                "🏦 Source: XT"
            ),
            reply_markup=(
                intelligence_keyboard()
            ),
        )

        return

    # GAINERS / LOSERS / VOLUME

    if data == "intel_gainers":

        title = (
            "🚀 TOP GAINERS — 24H"
        )

        rows = result[
            "gainers"
        ]

    elif data == "intel_losers":

        title = (
            "🩸 TOP LOSERS — 24H"
        )

        rows = result[
            "losers"
        ]

    elif data == "intel_volume":

        title = (
            "🔥 VOLUME LEADERS — 24H"
        )

        rows = result[
            "volume"
        ]

    else:

        return

    lines = [
        title,
        "━━━━━━━━━━━━━━━━",
        "",
    ]

    for index, item in enumerate(
        rows[:10],
        start=1,
    ):

        if data == "intel_volume":

            metric = money(
                item[
                    "quote_volume_24h"
                ]
            )

        else:

            metric = change(
                item[
                    "change_24h"
                ]
            )

        lines.append(
            (
                f"{index}. "
                f"{item['symbol']} "
                f"| {metric}"
            )
        )

    lines.extend(
        [
            "",
            "🏦 Source: XT",
            "🕒 Live market scan",
        ]
    )

    await query.edit_message_text(
        "\n".join(
            lines
        ),
        reply_markup=(
            intelligence_keyboard()
        ),
    )
from datetime import (
    datetime,
    timezone,
)

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)

from telegram.ext import (
    ContextTypes,
)

from app.engines.market_data.service import (
    market_service,
)


# ============================================================
# FORMAT
# ============================================================

def number(
    value,
    decimals=2,
):

    try:

        return (
            f"{float(value):,.{decimals}f}"
        )

    except (
        TypeError,
        ValueError,
    ):

        return "N/A"


def percent(
    value,
):

    try:

        value = float(
            value
        )

    except (
        TypeError,
        ValueError,
    ):

        return "N/A"

    icon = (
        "🟢"
        if value >= 0
        else "🔴"
    )

    return (
        f"{icon} "
        f"{value:+.2f}%"
    )


def utc():

    return (
        datetime.now(
            timezone.utc
        )
        .strftime(
            "%Y-%m-%d %H:%M UTC"
        )
    )


# ============================================================
# KEYBOARD
# ============================================================

def market_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "₿ Top 10 Crypto",
                    callback_data="market_crypto",
                ),
            ],

            [
                InlineKeyboardButton(
                    "💱 10 Forex",
                    callback_data="market_forex",
                ),
            ],

            [
                InlineKeyboardButton(
                    "🥇 Gold",
                    callback_data="market_gold",
                ),

                InlineKeyboardButton(
                    "🛢 Oil",
                    callback_data="market_oil",
                ),
            ],

            [
                InlineKeyboardButton(
                    "🔄 Refresh",
                    callback_data="market_home",
                ),
            ],
        ]
    )


# ============================================================
# HOME
# ============================================================

async def market_home(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    text = (
        "📊 ALIFT MARKET CENTER\n"
        "━━━━━━━━━━━━━━━━\n\n"

        "₿ Top 10 Crypto by Market Cap\n"
        "💱 10 Major Forex Pairs\n"
        "🥇 Gold\n"
        "🛢 WTI / Brent\n\n"

        "بازار موردنظر را انتخاب کنید."
    )

    if update.callback_query:

        await (
            update.callback_query
            .edit_message_text(
                text,
                reply_markup=market_keyboard(),
            )
        )

    else:

        await (
            update.message
            .reply_text(
                text,
                reply_markup=market_keyboard(),
            )
        )


# ============================================================
# CRYPTO
# ============================================================

async def crypto_page(
    query,
):

    coins = (
        await market_service
        .crypto_market()
    )

    lines = [
        "₿ TOP 10 CRYPTO",
        "━━━━━━━━━━━━━━━━",
        "",
    ]

    for index, coin in enumerate(
        coins,
        start=1,
    ):

        symbol = (
            coin
            .get(
                "symbol",
                "",
            )
            .upper()
        )

        price = number(
            coin.get(
                "current_price"
            )
        )

        change = percent(
            coin.get(
                "price_change_percentage_24h"
            )
        )

        cap = number(
            coin.get(
                "market_cap"
            ),
            0,
        )

        volume = number(
            coin.get(
                "total_volume"
            ),
            0,
        )

        lines.extend(
            [
                (
                    f"{index}. "
                    f"{symbol}"
                ),

                (
                    f"💵 ${price} "
                    f"| {change}"
                ),

                (
                    "Cap: "
                    f"${cap}"
                ),

                (
                    "Vol: "
                    f"${volume}"
                ),

                "",
            ]
        )

    lines.extend(
        [
            "Source: CoinGecko",
            f"🕒 {utc()}",
        ]
    )

    await query.edit_message_text(
        "\n".join(lines),
        reply_markup=market_keyboard(),
    )


# ============================================================
# FOREX
# ============================================================

async def forex_page(
    query,
):

    pairs = (
        await market_service
        .forex_market()
    )

    lines = [
        "💱 MAJOR FOREX PAIRS",
        "━━━━━━━━━━━━━━━━",
        "",
    ]

    for index, pair in enumerate(
        pairs,
        start=1,
    ):

        lines.append(
            (
                f"{index}. "
                f"{pair['symbol']} "
                f"= "
                f"{number(pair['price'], 5)}"
            )
        )

    lines.extend(
        [
            "",
            (
                "Source: "
                "Frankfurter / ECB"
            ),
            (
                "⚠️ Reference rates; "
                "not broker real-time quotes."
            ),
            f"🕒 {utc()}",
        ]
    )

    await query.edit_message_text(
        "\n".join(lines),
        reply_markup=market_keyboard(),
    )


# ============================================================
# GOLD
# ============================================================

async def gold_page(
    query,
):

    gold = (
        await market_service
        .gold_market()
    )

    text = (
        "🥇 GOLD\n"
        "━━━━━━━━━━━━━━━━\n\n"

        f"{gold['symbol']}\n"

        f"💵 ${number(gold['price'])}\n"

        f"24H: "
        f"{percent(gold.get('change'))}\n\n"

        f"Source: "
        f"{gold.get('source', 'N/A')}\n"

        f"🕒 {utc()}"
    )

    await query.edit_message_text(
        text,
        reply_markup=market_keyboard(),
    )


# ============================================================
# OIL
# ============================================================

async def oil_page(
    query,
):

    oils = (
        await market_service
        .oil_market()
    )

    lines = [
        "🛢 OIL MARKET",
        "━━━━━━━━━━━━━━━━",
        "",
    ]

    available = 0

    for item in oils:

        name = item.get(
            "name",
            "OIL",
        )

        if item.get(
            "error"
        ):

            lines.extend(
                [
                    f"⚠️ {name}",
                    (
                        "Data unavailable "
                        "from current provider/plan."
                    ),
                    "",
                ]
            )

            continue

        available += 1

        lines.extend(
            [
                f"🛢 {name}",

                (
                    f"💵 "
                    f"${number(item.get('price'))}"
                ),

                (
                    "Change: "
                    f"{percent(item.get('change'))}"
                ),

                "",
            ]
        )

    if available == 0:

        lines.extend(
            [
                (
                    "Twelve Data برای پلن فعلی "
                    "فید نفت قابل استفاده "
                    "برنگرداند."
                ),

                (
                    "در مرحله بعد Provider نفت "
                    "را مستقل تعویض می‌کنیم."
                ),

                "",
            ]
        )

    lines.extend(
        [
            "Source: Twelve Data",
            f"🕒 {utc()}",
        ]
    )

    await query.edit_message_text(
        "\n".join(lines),
        reply_markup=market_keyboard(),
    )


# ============================================================
# CALLBACK
# ============================================================

async def market_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = (
        update.callback_query
    )

    if not query:

        return

    await query.answer()

    action = (
        query.data
    )

    try:

        if action == "market_home":

            await market_home(
                update,
                context,
            )

            return

        if action == "market_crypto":

            await crypto_page(
                query
            )

            return

        if action == "market_forex":

            await forex_page(
                query
            )

            return

        if action == "market_gold":

            await gold_page(
                query
            )

            return

        if action == "market_oil":

            await oil_page(
                query
            )

            return

    except Exception as exc:

        await query.edit_message_text(
            (
                "⚠️ MARKET DATA ERROR\n"
                "━━━━━━━━━━━━━━━━\n\n"

                f"{type(exc).__name__}\n"

                f"{str(exc)[:800]}"
            ),
            reply_markup=market_keyboard(),
        )
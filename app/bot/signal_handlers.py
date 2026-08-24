from __future__ import annotations

import asyncio
from html import escape
from typing import Any, Dict, List

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from app.engines.signals.market_signal_scanner import (
    scan_market,
)
from app.engines.signals.top30_signal_scanner import (
    scan_top30,
)
from app.services.signal_card_renderer import (
    render_signal_card,
)


COIN_ICONS = {
    "BTC": "₿",
    "ETH": "Ξ",
    "SOL": "◎",
    "BNB": "🟡",
    "XRP": "⚫",
    "ADA": "🔵",
    "DOGE": "Ð",
    "TRX": "🔴",
    "LINK": "🔷",
    "AVAX": "🔺",
    "DOT": "⚪",
    "LTC": "Ł",
    "BCH": "🟢",
    "TON": "💎",
    "UNI": "🦄",
    "AAVE": "👻",
    "NEAR": "◉",
    "ATOM": "⚛️",
    "XLM": "✦",
    "SUI": "💧",
    "APT": "◼️",
    "INJ": "◈",
    "POL": "🟣",
    "FET": "🤖",
    "GRT": "◫",
    "PENDLE": "◐",
}


def _coin_icon(
    code: str,
) -> str:
    return COIN_ICONS.get(
        code.upper(),
        "●",
    )


def _money(
    value: Any,
) -> str:
    if value is None:
        return "—"

    value = float(value)

    if abs(value) >= 1_000_000_000:
        return (
            f"${value / 1_000_000_000:.2f}B"
        )

    if abs(value) >= 1_000_000:
        return (
            f"${value / 1_000_000:.1f}M"
        )

    if abs(value) >= 1_000:
        return (
            f"${value / 1_000:.1f}K"
        )

    return f"${value:.2f}"


def _price(
    value: Any,
) -> str:
    if value is None:
        return "—"

    value = float(value)

    if abs(value) >= 1000:
        return f"{value:,.2f}"

    if abs(value) >= 1:
        return f"{value:.4f}"

    return f"{value:.8f}"


def _percent(
    value: Any,
) -> str:
    if value is None:
        return "—"

    value = float(value)

    sign = (
        "+"
        if value > 0
        else ""
    )

    return (
        f"{sign}{value:.2f}%"
    )


def _keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🎯 برترین ستاپ‌ها",
                    callback_data=(
                        "signal_top_setups"
                    ),
                ),
            ],
            [
                InlineKeyboardButton(
                    "🟢 20 صعودی",
                    callback_data=(
                        "signal_winners"
                    ),
                ),
                InlineKeyboardButton(
                    "🔴 20 نزولی",
                    callback_data=(
                        "signal_losers"
                    ),
                ),
            ],
            [
                InlineKeyboardButton(
                    "📊 حجم 24 ساعته",
                    callback_data=(
                        "signal_volume"
                    ),
                ),
                InlineKeyboardButton(
                    "🚀 مومنتوم",
                    callback_data=(
                        "signal_momentum"
                    ),
                ),
            ],
            [
                InlineKeyboardButton(
                    "⚡ فعالیت غیرعادی",
                    callback_data=(
                        "signal_activity"
                    ),
                ),
            ],
            [
                InlineKeyboardButton(
                    "🔄 بروزرسانی",
                    callback_data=(
                        "signal_home"
                    ),
                ),
            ],
        ]
    )


async def _market_scan() -> Dict[str, Any]:
    return await asyncio.to_thread(
        scan_market,
        200,
    )


async def _top_scan(
    limit: int = 5,
) -> Dict[str, Any]:
    return await asyncio.to_thread(
        scan_top30,
        limit,
    )


def _movers_text(
    items: List[Dict[str, Any]],
    winners: bool,
) -> str:
    if winners:
        title = (
            "🟢 <b>TOP 20 GAINERS</b>"
        )
        subtitle = (
            "🚀 بیشترین رشد 24 ساعت"
        )
        arrow = "▲"
    else:
        title = (
            "🔴 <b>TOP 20 LOSERS</b>"
        )
        subtitle = (
            "🔻 بیشترین افت 24 ساعت"
        )
        arrow = "▼"

    lines = [
        title,
        subtitle,
        "",
    ]

    for index, item in enumerate(
        items[:20],
        start=1,
    ):
        code = str(
            item.get("code")
            or "?"
        ).upper()

        change = float(
            item.get(
                "change_24h_percent"
            )
            or 0
        )

        icon = _coin_icon(
            code
        )

        change_text = (
            f"+{change:.2f}%"
            if change > 0
            else f"{change:.2f}%"
        )

        lines.append(
            (
                f"{arrow} "
                f"<b>{index:02d}</b>  "
                f"{escape(icon)} "
                f"<b>{escape(code)}</b>"
            )
        )

        lines.append(
            (
                "       "
                f"<b>{change_text}</b>"
            )
        )

        if index < len(
            items[:20]
        ):
            lines.append(
                "──────────────"
            )

    lines.extend(
        [
            "",
            (
                "🛡 <b>Filter:</b> "
                "Market Cap > ارزش 1000 BTC"
            ),
            (
                "📡 <b>Source:</b> "
                "LiveCoinWatch"
            ),
        ]
    )

    return "\n".join(
        lines
    )


def _rows_text(
    items: List[Dict[str, Any]],
    mode: str,
) -> str:
    lines = []

    for index, item in enumerate(
        items[:20],
        start=1,
    ):
        code = str(
            item.get("code")
            or "?"
        ).upper()

        icon = _coin_icon(
            code
        )

        volume = _money(
            item.get(
                "volume_24h_usd"
            )
        )

        change = _percent(
            item.get(
                "change_24h_percent"
            )
        )

        if mode == "volume":
            detail = (
                f"Vol {volume} | "
                f"24H {change}"
            )

        elif mode == "momentum":
            score = float(
                item.get(
                    "momentum_score"
                )
                or 0
            )

            detail = (
                f"Score {score:.2f} | "
                f"24H {change}"
            )

        elif mode == "activity":
            ratio = (
                float(
                    item.get(
                        "volume_market_cap_ratio"
                    )
                    or 0
                )
                * 100
            )

            detail = (
                f"Vol/MCap "
                f"{ratio:.1f}% | "
                f"24H {change}"
            )

        else:
            detail = (
                f"24H {change} | "
                f"Vol {volume}"
            )

        lines.append(
            (
                f"{index:02d}. "
                f"{icon} {code}\n"
                f"     {detail}"
            )
        )

    return "\n\n".join(
        lines
    )


def _setup_caption(
    signal: Dict[str, Any],
) -> str:
    grade = signal.get(
        "grade",
        "—",
    )

    confidence = signal.get(
        "confidence",
        0,
    )

    direction = signal.get(
        "direction",
        "WATCH",
    )

    if direction == "LONG_WATCH":
        direction_fa = (
            "🟢 رصد لانگ"
        )

    elif direction == "SHORT_WATCH":
        direction_fa = (
            "🔴 رصد شورت"
        )

    else:
        direction_fa = (
            f"🟡 {direction}"
        )

    if grade in {
        "A",
        "A+",
    }:
        status = (
            "✅ کاندید سیگنال قوی"
        )
    else:
        status = (
            "👁 Watchlist — "
            "تأیید نهایی ندارد"
        )

    reasons = (
        signal.get("reasons")
        or []
    )

    risks = (
        signal.get("risks")
        or []
    )

    lines = [
        (
            "🎯 MRBIZNES "
            "SIGNAL INTELLIGENCE"
        ),
        "",
        (
            f"Asset: "
            f"{signal.get('symbol')}"
        ),
        (
            f"وضعیت: "
            f"{direction_fa}"
        ),
        (
            f"Grade: {grade} | "
            f"Score: "
            f"{confidence}/100"
        ),
        status,
        "",
        (
            "Entry Trigger: "
            + _price(
                signal.get(
                    "entry_trigger"
                )
            )
        ),
        (
            "Stop: "
            + _price(
                signal.get(
                    "stop"
                )
            )
        ),
        (
            "TP1: "
            + _price(
                signal.get(
                    "target_1"
                )
            )
        ),
        (
            "TP2: "
            + _price(
                signal.get(
                    "target_2"
                )
            )
        ),
    ]

    if reasons:
        lines.extend(
            [
                "",
                "✅ تأییدها:",
            ]
        )

        for reason in reasons[:4]:
            lines.append(
                f"• {reason}"
            )

    if risks:
        lines.extend(
            [
                "",
                "⚠️ ریسک‌ها:",
            ]
        )

        for risk in risks[:3]:
            lines.append(
                f"• {risk}"
            )

    lines.extend(
        [
            "",
            (
                "Data: "
                "XT + LiveCoinWatch"
            ),
            (
                "⚠️ جهت بازار "
                "تضمین‌شده نیست."
            ),
        ]
    )

    return "\n".join(
        lines
    )


async def signal_center(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    message = update.effective_message

    if message is None:
        return

    loading = await message.reply_text(
        "📡 در حال آماده‌سازی "
        "Signal Terminal..."
    )

    try:
        result = await _market_scan()

        text = (
            "📡 MRBIZNES SIGNAL TERMINAL\n\n"
            "🎯 تحلیل چندتایم‌فریمی\n"
            "🟢 Top 20 صعودی\n"
            "🔴 Top 20 نزولی\n"
            "📊 Volume Intelligence\n"
            "🚀 Momentum Radar\n\n"
            "🛡 Market Cap > "
            "ارزش 1000 BTC\n\n"
            f"دارایی‌های واجد شرایط: "
            f"{result['eligible_count']}\n\n"
            "Technical: XT\n"
            "Context: LiveCoinWatch"
        )

        await loading.edit_text(
            text,
            reply_markup=_keyboard(),
        )

    except Exception:
        await loading.edit_text(
            "❌ دریافت Signal Terminal "
            "ناموفق بود."
        )


async def _send_top_setup(
    query,
) -> None:
    result = await _top_scan(
        5
    )

    strong = (
        result["signals_a_plus"]
        + result["signals_a"]
    )

    if strong:
        selected = strong[0]

    elif result["watchlist_b"]:
        selected = (
            result[
                "watchlist_b"
            ][0]
        )

    else:
        selected = None

    if selected is None:
        await (
            query.message.reply_text(
                "🔎 ستاپ باکیفیت "
                "کافی پیدا نشد.\n\n"
                "سیگنال اجباری "
                "تولید نمی‌شود."
            )
        )

        return

    card = await asyncio.to_thread(
        render_signal_card,
        selected,
    )

    await query.message.reply_photo(
        photo=card,
        caption=_setup_caption(
            selected
        ),
    )


async def signal_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query

    if query is None:
        return

    await query.answer()

    action = (
        query.data
        or ""
    )

    if action in {
        "signal_winners",
        "signal_losers",
    }:
        await query.edit_message_text(
            "📊 در حال دریافت "
            "Movers..."
        )

        try:
            result = await _market_scan()

            winners = (
                action
                == "signal_winners"
            )

            items = (
                result[
                    "biggest_winners_24h"
                ]
                if winners
                else result[
                    "biggest_losers_24h"
                ]
            )

            await (
                query.message.reply_text(
                    _movers_text(
                        items,
                        winners,
                    ),
                    parse_mode=(
                        ParseMode.HTML
                    ),
                )
            )

            await (
                query.message.reply_text(
                    "📡 MRBIZNES "
                    "SIGNAL TERMINAL",
                    reply_markup=_keyboard(),
                )
            )

        except Exception:
            await (
                query.message.reply_text(
                    "❌ دریافت Movers "
                    "ناموفق بود.",
                    reply_markup=_keyboard(),
                )
            )

        return

    if action == "signal_top_setups":
        await query.edit_message_text(
            "🎯 در حال تحلیل "
            "کاندیدهای برتر...\n"
            "15m • 1h • 4h • 1w"
        )

        try:
            await _send_top_setup(
                query
            )

            await (
                query.message.reply_text(
                    "📡 MRBIZNES "
                    "SIGNAL TERMINAL",
                    reply_markup=_keyboard(),
                )
            )

        except Exception:
            await (
                query.message.reply_text(
                    "❌ تحلیل Top Setups "
                    "ناموفق بود.",
                    reply_markup=_keyboard(),
                )
            )

        return

    try:
        await query.edit_message_text(
            "📡 در حال اسکن بازار..."
        )

        result = await _market_scan()

        if action == "signal_home":
            text = (
                "📡 MRBIZNES "
                "SIGNAL TERMINAL\n\n"
                f"✅ دارایی‌های واجد "
                f"شرایط: "
                f"{result['eligible_count']}\n"
                "🛡 Market Cap > "
                "1000 BTC\n\n"
                "یک بخش را انتخاب کن."
            )

        elif action == "signal_volume":
            text = (
                "📊 24H VOLUME LEADERS\n\n"
                + _rows_text(
                    result[
                        "volume_leaders"
                    ],
                    "volume",
                )
                + "\n\n"
                "ℹ️ حجم معاملات "
                "≠ ورود خالص پول."
            )

        elif action == "signal_momentum":
            text = (
                "🚀 MOMENTUM MOVERS\n\n"
                + _rows_text(
                    result[
                        "momentum_gainers"
                    ],
                    "momentum",
                )
            )

        elif action == "signal_activity":
            text = (
                "⚡ VOLUME / MARKET CAP\n\n"
                + _rows_text(
                    result[
                        "activity_leaders"
                    ],
                    "activity",
                )
                + "\n\n"
                "⚠️ این شاخص "
                "Net Inflow نیست."
            )

        else:
            text = (
                "📡 MRBIZNES "
                "SIGNAL TERMINAL"
            )

        await query.edit_message_text(
            text,
            reply_markup=_keyboard(),
        )

    except Exception:
        await query.edit_message_text(
            "❌ خطا در اسکن بازار.",
            reply_markup=_keyboard(),
        )
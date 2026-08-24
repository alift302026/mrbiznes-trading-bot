from __future__ import annotations

import asyncio
from typing import Any, Dict, List

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import ContextTypes

from app.engines.signals.market_signal_scanner import (
    scan_market,
)


def _money(value: Any) -> str:
    if value is None:
        return "-"

    value = float(value)

    if abs(value) >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"

    if abs(value) >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"

    if abs(value) >= 1_000:
        return f"${value / 1_000:.1f}K"

    return f"${value:.2f}"


def _percent(value: Any) -> str:
    if value is None:
        return "-"

    value = float(value)

    if value > 0:
        return f"+{value:.2f}%"

    return f"{value:.2f}%"


def _keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
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
                    "🔥 برندگان 24H",
                    callback_data=(
                        "signal_winners"
                    ),
                ),
                InlineKeyboardButton(
                    "🔻 بازندگان 24H",
                    callback_data=(
                        "signal_losers"
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


async def _scan() -> Dict[str, Any]:
    return await asyncio.to_thread(
        scan_market,
        100,
    )


def _rows_text(
    items: List[Dict[str, Any]],
    mode: str,
) -> str:
    lines = []

    for index, item in enumerate(
        items[:10],
        start=1,
    ):
        code = item.get("code") or "?"

        volume = _money(
            item.get("volume_24h_usd")
        )

        change = _percent(
            item.get("change_24h_percent")
        )

        if mode == "volume":
            detail = (
                f"Vol {volume} | "
                f"24H {change}"
            )

        elif mode == "momentum":
            score = float(
                item.get("momentum_score")
                or 0
            )

            detail = (
                f"Score {score:.2f} | "
                f"24H {change}"
            )

        elif mode == "activity":
            ratio = float(
                item.get(
                    "volume_market_cap_ratio"
                )
                or 0
            ) * 100

            detail = (
                f"Vol/MCap {ratio:.1f}% | "
                f"24H {change}"
            )

        else:
            detail = (
                f"24H {change} | "
                f"Vol {volume}"
            )

        lines.append(
            f"{index}. {code} — {detail}"
        )

    return "\n".join(lines)


async def signal_center(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    message = update.effective_message

    if message is None:
        return

    loading = await message.reply_text(
        "📡 در حال دریافت داده‌های بازار..."
    )

    try:
        result = await _scan()

        text = (
            "📡 ALIFT SIGNAL CENTER\n\n"
            "هوش بازار و اسکن فرصت‌ها\n\n"
            f"✅ دارایی‌های واجد شرایط: "
            f"{result['eligible_count']}\n"
            "🛡 فیلتر Market Cap: "
            "بیشتر از ارزش 1000 BTC\n\n"
            "منبع داده: LiveCoinWatch\n\n"
            "یک بخش را انتخاب کن:\n\n"
            "⚠️ Volume به معنی "
            "Net Capital Inflow نیست."
        )

        await loading.edit_text(
            text,
            reply_markup=_keyboard(),
        )

    except Exception:
        await loading.edit_text(
            "❌ دریافت اطلاعات Signal Center "
            "ناموفق بود.\n"
            "چند لحظه دیگر دوباره امتحان کن."
        )


async def signal_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    query = update.callback_query

    if query is None:
        return

    await query.answer()

    action = query.data or ""

    try:
        await query.edit_message_text(
            "📡 در حال اسکن بازار..."
        )

        result = await _scan()

        if action == "signal_home":
            text = (
                "📡 ALIFT SIGNAL CENTER\n\n"
                "هوش بازار و اسکن فرصت‌ها\n\n"
                f"✅ دارایی‌های واجد شرایط: "
                f"{result['eligible_count']}\n"
                "🛡 Market Cap > 1000 BTC\n\n"
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
                "ℹ️ حجم معاملات ≠ ورود خالص پول."
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

        elif action == "signal_winners":
            text = (
                "🔥 BIGGEST WINNERS — 24H\n\n"
                + _rows_text(
                    result[
                        "biggest_winners_24h"
                    ],
                    "winner",
                )
            )

        elif action == "signal_losers":
            text = (
                "🔻 BIGGEST LOSERS — 24H\n\n"
                + _rows_text(
                    result[
                        "biggest_losers_24h"
                    ],
                    "loser",
                )
            )

        elif action == "signal_activity":
            text = (
                "⚡ VOLUME / MARKET CAP\n\n"
                "فعالیت معاملاتی بالا نسبت "
                "به اندازه بازار:\n\n"
                + _rows_text(
                    result[
                        "activity_leaders"
                    ],
                    "activity",
                )
                + "\n\n"
                "⚠️ این شاخص Net Inflow نیست."
            )

        else:
            text = (
                "📡 ALIFT SIGNAL CENTER"
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
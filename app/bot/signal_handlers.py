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
from app.engines.signals.setup_signal_engine import (
    analyze_setup,
)
from app.engines.signals.top30_signal_scanner import (
    scan_top30,
)
from app.services.signal_card_renderer import (
    render_signal_card,
)


def _money(
    value: Any,
) -> str:
    if value is None:
        return "—"

    number = float(value)

    if abs(number) >= 1_000_000_000:
        return (
            f"${number / 1_000_000_000:.2f}B"
        )

    if abs(number) >= 1_000_000:
        return (
            f"${number / 1_000_000:.1f}M"
        )

    if abs(number) >= 1_000:
        return (
            f"${number / 1_000:.1f}K"
        )

    return f"${number:.2f}"


def _price(
    value: Any,
) -> str:
    if value is None:
        return "—"

    number = float(value)

    if abs(number) >= 1000:
        return f"{number:,.2f}"

    if abs(number) >= 1:
        return f"{number:.4f}"

    return f"{number:.8f}"


def _percent(
    value: Any,
) -> str:
    if value is None:
        return "—"

    number = float(value)

    sign = (
        "+"
        if number > 0
        else ""
    )

    return (
        f"{sign}{number:.2f}%"
    )


def _main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🎯 برترین ستاپ‌ها",
                    callback_data=(
                        "signal_top_setups"
                    ),
                    style="primary",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🟢 20 صعودی",
                    callback_data=(
                        "signal_winners"
                    ),
                    style="success",
                ),
                InlineKeyboardButton(
                    "🔴 20 نزولی",
                    callback_data=(
                        "signal_losers"
                    ),
                    style="danger",
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


def _movers_keyboard(
    items: List[Dict[str, Any]],
    *,
    winners: bool,
) -> InlineKeyboardMarkup:
    """
    20 assets:
        left column  = 1..10
        right column = 11..20

    Each button contains rank, symbol and
    24h percentage and opens coin analysis.
    """
    visible = items[:20]

    rows = []

    style = (
        "success"
        if winners
        else "danger"
    )

    for index in range(10):
        row = []

        for item_index in (
            index,
            index + 10,
        ):
            if item_index >= len(
                visible
            ):
                continue

            item = visible[
                item_index
            ]

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

            sign = (
                "+"
                if change > 0
                else ""
            )

            text = (
                f"{item_index + 1:02d} "
                f"{code}  "
                f"{sign}{change:.2f}%"
            )

            row.append(
                InlineKeyboardButton(
                    text=text,
                    callback_data=(
                        "signal_coin_"
                        + code
                    ),
                    style=style,
                )
            )

        if row:
            rows.append(row)

    rows.append(
        [
            InlineKeyboardButton(
                "⬅️ بازگشت به Signal Terminal",
                callback_data="signal_home",
            )
        ]
    )

    return InlineKeyboardMarkup(
        rows
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


async def _coin_analysis(
    code: str,
) -> Dict[str, Any]:
    return await asyncio.to_thread(
        analyze_setup,
        f"{code}/USDT",
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
                f"{code}\n"
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
        direction_text = (
            "🟢 LONG WATCH"
        )

    elif direction == "SHORT_WATCH":
        direction_text = (
            "🔴 SHORT WATCH"
        )

    else:
        direction_text = (
            f"🟡 {direction}"
        )

    reasons = (
        signal.get("reasons")
        or []
    )

    risks = (
        signal.get("risks")
        or []
    )

    tf15 = (
        signal.get(
            "timeframes",
            {}
        ).get(
            "15m",
            {},
        )
    )

    box = (
        tf15.get("range")
        or {}
    )

    lines = [
        "🎯 MRBIZNES SIGNAL INTELLIGENCE",
        "",
        (
            f"Asset: "
            f"{signal.get('symbol')}"
        ),
        (
            f"Setup: {direction_text}"
        ),
        (
            f"Grade: {grade} | "
            f"Score: "
            f"{confidence}/100"
        ),
        "",
        "📍 TRADE MAP",
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
        "",
        "📊 15M",
        (
            f"SMA: "
            f"{tf15.get('sma_state', '—')}"
        ),
        (
            f"RSI: "
            f"{_price(tf15.get('rsi'))}"
        ),
        (
            f"Dow: "
            f"{tf15.get('dow', '—')}"
        ),
        (
            "Volume: "
            f"{(
                tf15.get('volume')
                or {}
            ).get('state', '—')}"
        ),
    ]

    if box:
        lines.extend(
            [
                (
                    f"Range: "
                    f"{box.get('length')} candles"
                ),
                (
                    "Range High: "
                    + _price(
                        box.get("high")
                    )
                ),
                (
                    "Range Low: "
                    + _price(
                        box.get("low")
                    )
                ),
            ]
        )

    if reasons:
        lines.extend(
            [
                "",
                "✅ تأییدها:",
            ]
        )

        for reason in reasons[:5]:
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
                "⚠️ WATCH/Analysis؛ "
                "توصیه قطعی معامله نیست."
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
            "🎯 Multi-Timeframe Setups\n"
            "🟢 Top 20 Gainers\n"
            "🔴 Top 20 Losers\n"
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
            reply_markup=(
                _main_keyboard()
            ),
        )

    except Exception:
        await loading.edit_text(
            "❌ دریافت Signal Terminal "
            "ناموفق بود."
        )


async def _show_movers(
    query,
    *,
    winners: bool,
) -> None:
    result = await _market_scan()

    if winners:
        items = result[
            "biggest_winners_24h"
        ]

        title = (
            "🟢 TOP 20 GAINERS • 24H\n\n"
            "روی هر کوین بزن برای تحلیل "
            "15m / 1h / 4h / 1w"
        )

    else:
        items = result[
            "biggest_losers_24h"
        ]

        title = (
            "🔴 TOP 20 LOSERS • 24H\n\n"
            "روی هر کوین بزن برای تحلیل "
            "15m / 1h / 4h / 1w"
        )

    await query.edit_message_text(
        title,
        reply_markup=(
            _movers_keyboard(
                items,
                winners=winners,
            )
        ),
    )


async def _send_signal_card(
    query,
    signal: Dict[str, Any],
) -> None:
    card = await asyncio.to_thread(
        render_signal_card,
        signal,
    )

    await query.message.reply_photo(
        photo=card,
        caption=_setup_caption(
            signal
        ),
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
            result["watchlist_b"][0]
        )

    else:
        selected = None

    if selected is None:
        await query.message.reply_text(
            "🔎 در حال حاضر "
            "ستاپ باکیفیت کافی "
            "پیدا نشد.\n\n"
            "سیگنال اجباری تولید نمی‌شود."
        )

        return

    await _send_signal_card(
        query,
        selected,
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

    if action == "signal_winners":
        try:
            await _show_movers(
                query,
                winners=True,
            )

        except Exception:
            await query.edit_message_text(
                "❌ دریافت Gainers "
                "ناموفق بود.",
                reply_markup=(
                    _main_keyboard()
                ),
            )

        return

    if action == "signal_losers":
        try:
            await _show_movers(
                query,
                winners=False,
            )

        except Exception:
            await query.edit_message_text(
                "❌ دریافت Losers "
                "ناموفق بود.",
                reply_markup=(
                    _main_keyboard()
                ),
            )

        return

    if action.startswith(
        "signal_coin_"
    ):
        code = (
            action[
                len(
                    "signal_coin_"
                ):
            ]
            .strip()
            .upper()
        )

        if not code:
            return

        await query.edit_message_text(
            (
                f"🔎 {code}/USDT\n\n"
                "در حال تحلیل:\n"
                "15m • 1h • 4h • 1w\n"
                "SMA 7/25/99 • RSI • "
                "MACD • ATR • Volume • Dow"
            )
        )

        try:
            signal = (
                await _coin_analysis(
                    code
                )
            )

            await _send_signal_card(
                query,
                signal,
            )

            await query.message.reply_text(
                "📡 MRBIZNES SIGNAL TERMINAL",
                reply_markup=(
                    _main_keyboard()
                ),
            )

        except Exception:
            await query.message.reply_text(
                (
                    f"❌ تحلیل {code} "
                    "ناموفق بود."
                ),
                reply_markup=(
                    _main_keyboard()
                ),
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

            await query.message.reply_text(
                "📡 MRBIZNES SIGNAL TERMINAL",
                reply_markup=(
                    _main_keyboard()
                ),
            )

        except Exception:
            await query.message.reply_text(
                "❌ تحلیل Top Setups "
                "ناموفق بود.",
                reply_markup=(
                    _main_keyboard()
                ),
            )

        return

    try:
        await query.edit_message_text(
            "📡 در حال اسکن بازار..."
        )

        result = await _market_scan()

        if action == "signal_home":
            text = (
                "📡 MRBIZNES SIGNAL TERMINAL\n\n"
                f"✅ دارایی‌های واجد شرایط: "
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
                "ℹ️ Volume ≠ Net Inflow."
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
                "📡 MRBIZNES SIGNAL TERMINAL"
            )

        await query.edit_message_text(
            text,
            reply_markup=(
                _main_keyboard()
            ),
        )

    except Exception:
        await query.edit_message_text(
            "❌ خطا در اسکن بازار.",
            reply_markup=(
                _main_keyboard()
            ),
        )
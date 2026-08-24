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
from app.engines.signals.top30_signal_scanner import (
    scan_top30,
)
from app.services.market_grid_renderer import (
    render_market_grid,
)
from app.services.signal_card_renderer import (
    render_signal_card,
)


def _money(value: Any) -> str:
    if value is None:
        return "—"

    value = float(value)

    if abs(value) >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"

    if abs(value) >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"

    if abs(value) >= 1_000:
        return f"${value / 1_000:.1f}K"

    return f"${value:.2f}"


def _price(value: Any) -> str:
    if value is None:
        return "—"

    value = float(value)

    if abs(value) >= 1000:
        return f"{value:,.2f}"

    if abs(value) >= 1:
        return f"{value:.4f}"

    return f"{value:.8f}"


def _percent(value: Any) -> str:
    if value is None:
        return "—"

    value = float(value)

    sign = "+" if value > 0 else ""

    return f"{sign}{value:.2f}%"


def _keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🎯 برترین ستاپ‌ها",
                    callback_data="signal_top_setups",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🟢 20 صعودی",
                    callback_data="signal_winners",
                ),
                InlineKeyboardButton(
                    "🔴 20 نزولی",
                    callback_data="signal_losers",
                ),
            ],
            [
                InlineKeyboardButton(
                    "📊 حجم 24 ساعته",
                    callback_data="signal_volume",
                ),
                InlineKeyboardButton(
                    "🚀 مومنتوم",
                    callback_data="signal_momentum",
                ),
            ],
            [
                InlineKeyboardButton(
                    "⚡ فعالیت غیرعادی",
                    callback_data="signal_activity",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🔄 بروزرسانی",
                    callback_data="signal_home",
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


def _rows_text(
    items: List[Dict[str, Any]],
    mode: str,
) -> str:
    lines = []

    for index, item in enumerate(
        items[:20],
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
        direction_fa = "🟢 رصد لانگ"

    elif direction == "SHORT_WATCH":
        direction_fa = "🔴 رصد شورت"

    else:
        direction_fa = (
            f"🟡 {direction}"
        )

    if grade in {"A", "A+"}:
        status = "✅ کاندید سیگنال قوی"

    else:
        status = (
            "👁 Watchlist — "
            "هنوز تأیید نهایی ندارد"
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
        "🎯 MRBIZNES SIGNAL INTELLIGENCE",
        "",
        f"Asset: {signal.get('symbol')}",
        f"وضعیت: {direction_fa}",
        (
            f"Grade: {grade} | "
            f"Score: {confidence}/100"
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
                signal.get("stop")
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
            "Data: XT + LiveCoinWatch",
            (
                "⚠️ تحلیل بازار است؛ "
                "جهت بازار تضمین‌شده نیست."
            ),
        ]
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
            "🛡 فیلتر بازار:\n"
            "Market Cap > ارزش 1000 BTC\n\n"
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
            "❌ دریافت اطلاعات "
            "Signal Terminal ناموفق بود."
        )


async def _send_market_grid(
    query,
    mode: str,
) -> None:
    result = await _market_scan()

    if mode == "winners":
        items = result[
            "biggest_winners_24h"
        ]

        title = (
            "🟢 20 کوین صعودی برتر "
            "در 24 ساعت اخیر"
        )

    else:
        items = result[
            "biggest_losers_24h"
        ]

        title = (
            "🔴 20 کوین نزولی برتر "
            "در 24 ساعت اخیر"
        )

    if not items:
        await query.message.reply_text(
            "داده کافی برای این بخش "
            "در حال حاضر وجود ندارد."
        )
        return

    image = await asyncio.to_thread(
        render_market_grid,
        items,
        mode=mode,
    )

    caption = (
        f"{title}\n\n"
        "🛡 Market Cap > ارزش 1000 BTC\n"
        "📡 Source: LiveCoinWatch\n\n"
        "ℹ️ Volume به معنی Net Inflow نیست."
    )

    await query.message.reply_photo(
        photo=image,
        caption=caption,
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
            "🔎 اسکن انجام شد.\n\n"
            "در حال حاضر ستاپ باکیفیت "
            "کافی پیدا نشد.\n\n"
            "سیگنال اجباری تولید نمی‌شود."
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

    if selected.get("grade") not in {
        "A",
        "A+",
    }:
        await query.message.reply_text(
            "ℹ️ این مورد فعلاً فقط "
            "Watchlist است و تأیید "
            "ورود نهایی ندارد."
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
            "🎨 در حال ساخت "
            "Market Grid..."
        )

        try:
            mode = (
                "winners"
                if action
                == "signal_winners"
                else "losers"
            )

            await _send_market_grid(
                query,
                mode,
            )

            await query.message.reply_text(
                "📡 MRBIZNES SIGNAL TERMINAL",
                reply_markup=_keyboard(),
            )

        except Exception:
            await query.message.reply_text(
                "❌ ساخت Market Grid "
                "ناموفق بود.",
                reply_markup=_keyboard(),
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
                reply_markup=_keyboard(),
            )

        except Exception:
            await query.message.reply_text(
                "❌ تحلیل Top Setups "
                "ناموفق بود.",
                reply_markup=_keyboard(),
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
                "فعالیت معاملاتی بالا "
                "نسبت به اندازه بازار:\n\n"
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
                "📡 MRBIZNES SIGNAL TERMINAL"
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
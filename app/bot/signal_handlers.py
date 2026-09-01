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

from app.services import final_signal_service as _fsvc
from app.core.config import ADMIN_IDS as _ADMIN_IDS


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
                    "⚡ سیگنال‌های نهایی S4 (خودکار ساعتی)",
                    callback_data=(
                        "signal_final_home"
                    ),
                    style="primary",
                ),
            ],
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
            {},
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

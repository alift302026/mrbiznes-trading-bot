from __future__ import annotations

from io import BytesIO
from typing import Any, Dict

from PIL import (
    Image,
    ImageDraw,
    ImageFont,
)


WIDTH = 1080
HEIGHT = 1350

BG = "#050908"
PANEL = "#0B1412"
PANEL_2 = "#101C19"
LINE = "#1D302A"

WHITE = "#F1F7F4"
MUTED = "#81938C"

GREEN = "#31E89A"
RED = "#FF6074"
CYAN = "#3DDBF2"
AMBER = "#EFC46B"


def _font(
    size: int,
    bold: bool = False,
):
    candidates = []

    if bold:
        candidates.extend(
            [
                "C:/Windows/Fonts/segoeuib.ttf",
                "C:/Windows/Fonts/arialbd.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            ]
        )
    else:
        candidates.extend(
            [
                "C:/Windows/Fonts/segoeui.ttf",
                "C:/Windows/Fonts/arial.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            ]
        )

    for path in candidates:
        try:
            return ImageFont.truetype(
                path,
                size,
            )
        except OSError:
            continue

    return ImageFont.load_default()


def _value(
    value: Any,
    decimals: int = 2,
) -> str:
    if value is None:
        return "—"

    try:
        number = float(value)

        if abs(number) >= 1000:
            return f"{number:,.{decimals}f}"

        return f"{number:.{decimals}f}"

    except (TypeError, ValueError):
        return str(value)


def _percent(
    value: Any,
) -> str:
    if value is None:
        return "—"

    try:
        number = float(value)

        sign = (
            "+"
            if number > 0
            else ""
        )

        return (
            f"{sign}{number:.2f}%"
        )

    except (TypeError, ValueError):
        return "—"


def _rounded_panel(
    draw: ImageDraw.ImageDraw,
    box,
    fill=PANEL,
):
    draw.rounded_rectangle(
        box,
        radius=22,
        fill=fill,
        outline=LINE,
        width=2,
    )


def render_signal_card(
    signal: Dict[str, Any],
) -> BytesIO:
    image = Image.new(
        "RGB",
        (
            WIDTH,
            HEIGHT,
        ),
        BG,
    )

    draw = ImageDraw.Draw(
        image
    )

    title_font = _font(
        38,
        True,
    )

    asset_font = _font(
        52,
        True,
    )

    grade_font = _font(
        70,
        True,
    )

    section_font = _font(
        25,
        True,
    )

    value_font = _font(
        28,
        True,
    )

    label_font = _font(
        22,
        False,
    )

    small_font = _font(
        18,
        False,
    )

    direction = signal.get(
        "direction",
        "WATCH",
    )

    if direction == "LONG_WATCH":
        accent = GREEN
        direction_text = (
            "LONG WATCH"
        )

    elif direction == "SHORT_WATCH":
        accent = RED
        direction_text = (
            "SHORT WATCH"
        )

    else:
        accent = AMBER
        direction_text = str(
            direction
        )

    # Header
    draw.text(
        (60, 55),
        "ALIFT TRADER",
        font=title_font,
        fill=WHITE,
    )

    draw.text(
        (60, 105),
        "SIGNAL INTELLIGENCE",
        font=small_font,
        fill=CYAN,
    )

    draw.ellipse(
        (
            945,
            65,
            965,
            85,
        ),
        fill=accent,
    )

    draw.text(
        (980, 65),
        "LIVE",
        font=small_font,
        fill=MUTED,
        anchor="lm",
    )

    # Asset panel
    _rounded_panel(
        draw,
        (
            50,
            170,
            1030,
            355,
        ),
    )

    draw.text(
        (85, 205),
        signal.get(
            "symbol",
            "UNKNOWN",
        ),
        font=asset_font,
        fill=WHITE,
    )

    draw.text(
        (87, 280),
        direction_text,
        font=section_font,
        fill=accent,
    )

    grade = signal.get(
        "grade",
        "—",
    )

    confidence = signal.get(
        "confidence",
        0,
    )

    draw.text(
        (930, 205),
        str(grade),
        font=grade_font,
        fill=accent,
        anchor="ra",
    )

    draw.text(
        (930, 290),
        f"CONFIDENCE {confidence}/100",
        font=label_font,
        fill=MUTED,
        anchor="ra",
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

    tf1h = (
        signal.get(
            "timeframes",
            {},
        ).get(
            "1h",
            {},
        )
    )

    tf4h = (
        signal.get(
            "timeframes",
            {},
        ).get(
            "4h",
            {},
        )
    )

    # Levels
    _rounded_panel(
        draw,
        (
            50,
            385,
            1030,
            610,
        ),
    )

    draw.text(
        (80, 415),
        "TRADE MAP",
        font=section_font,
        fill=CYAN,
    )

    level_items = [
        (
            "ENTRY TRIGGER",
            signal.get(
                "entry_trigger"
            ),
            accent,
        ),
        (
            "STOP",
            signal.get(
                "stop"
            ),
            RED,
        ),
        (
            "TARGET 1",
            signal.get(
                "target_1"
            ),
            GREEN,
        ),
        (
            "TARGET 2",
            signal.get(
                "target_2"
            ),
            GREEN,
        ),
    ]

    x_positions = [
        80,
        325,
        570,
        815,
    ]

    for (
        x,
        item,
    ) in zip(
        x_positions,
        level_items,
    ):
        label, value, color = item

        draw.text(
            (x, 485),
            label,
            font=small_font,
            fill=MUTED,
        )

        draw.text(
            (x, 530),
            _value(value),
            font=value_font,
            fill=color,
        )

    # Indicators
    _rounded_panel(
        draw,
        (
            50,
            640,
            1030,
            905,
        ),
    )

    draw.text(
        (80, 670),
        "15M CONFIRMATION",
        font=section_font,
        fill=CYAN,
    )

    indicators = [
        (
            "SMA 7 / 25 / 99",
            tf15.get(
                "sma_state",
                "—",
            ),
        ),
        (
            "RSI 14",
            _value(
                tf15.get("rsi")
            ),
        ),
        (
            "MACD HIST",
            _value(
                tf15.get(
                    "macd_histogram"
                )
            ),
        ),
        (
            "ATR %",
            (
                _percent(
                    tf15.get(
                        "atr_percent"
                    )
                )
            ),
        ),
        (
            "VOLUME",
            (
                tf15.get(
                    "volume",
                    {},
                ).get(
                    "state",
                    "—",
                )
            ),
        ),
        (
            "DOW",
            tf15.get(
                "dow",
                "—",
            ),
        ),
    ]

    positions = [
        (80, 735),
        (390, 735),
        (700, 735),
        (80, 825),
        (390, 825),
        (700, 825),
    ]

    for (
        position,
        item,
    ) in zip(
        positions,
        indicators,
    ):
        label, value = item

        draw.text(
            position,
            label,
            font=small_font,
            fill=MUTED,
        )

        draw.text(
            (
                position[0],
                position[1] + 34,
            ),
            str(value).upper(),
            font=value_font,
            fill=WHITE,
        )

    # Structure panel
    _rounded_panel(
        draw,
        (
            50,
            935,
            1030,
            1140,
        ),
    )

    draw.text(
        (80, 965),
        "MARKET STRUCTURE",
        font=section_font,
        fill=CYAN,
    )

    structure = [
        (
            "15M",
            tf15.get(
                "dow",
                "—",
            ),
        ),
        (
            "1H",
            tf1h.get(
                "dow",
                "—",
            ),
        ),
        (
            "4H",
            tf4h.get(
                "dow",
                "—",
            ),
        ),
    ]

    sx = [
        100,
        420,
        740,
    ]

    for (
        x,
        item,
    ) in zip(
        sx,
        structure,
    ):
        tf, state = item

        draw.text(
            (x, 1030),
            tf,
            font=small_font,
            fill=MUTED,
        )

        draw.text(
            (x, 1065),
            str(state),
            font=value_font,
            fill=WHITE,
        )

    # Footer
    market_context = (
        signal.get(
            "market_context",
            {}
        )
    )

    draw.text(
        (60, 1185),
        (
            "DATA  "
            "XT • LIVECOINWATCH"
        ),
        font=small_font,
        fill=MUTED,
    )

    relative = (
        market_context.get(
            "relative_to_btc",
            {}
        )
    )

    rel24 = relative.get(
        "24h"
    )

    draw.text(
        (60, 1230),
        (
            "RELATIVE TO BTC 24H  "
            + _percent(rel24)
        ),
        font=small_font,
        fill=(
            GREEN
            if (
                rel24 is not None
                and rel24 >= 0
            )
            else RED
        ),
    )

    draw.text(
        (1020, 1230),
        "DATA ≠ GUARANTEED DIRECTION",
        font=small_font,
        fill=MUTED,
        anchor="ra",
    )

    draw.line(
        (
            60,
            1290,
            1020,
            1290,
        ),
        fill=LINE,
        width=2,
    )

    draw.text(
        (60, 1310),
        "ALIFT MARKET INTELLIGENCE",
        font=small_font,
        fill=GREEN,
    )

    output = BytesIO()

    image.save(
        output,
        format="PNG",
        optimize=True,
    )

    output.seek(0)

    output.name = (
        "alift_signal.png"
    )

    return output
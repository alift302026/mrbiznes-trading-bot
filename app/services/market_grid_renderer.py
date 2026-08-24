from __future__ import annotations

from io import BytesIO
from typing import Any, Dict, List

from PIL import (
    Image,
    ImageDraw,
    ImageFont,
)


WIDTH = 1200
HEIGHT = 1500

BG = "#050908"
CARD = "#0C1513"
LINE = "#1C3029"

WHITE = "#F3F8F6"
MUTED = "#71837C"

GREEN = "#32E89A"
GREEN_BG = "#0C2119"

RED = "#FF6074"
RED_BG = "#241015"

CYAN = "#3CD9F1"


def _font(
    size: int,
    bold: bool = False,
):
    candidates = (
        [
            "C:/Windows/Fonts/segoeuib.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]
        if bold
        else [
            "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/arial.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
    )

    for path in candidates:
        try:
            return (
                ImageFont.truetype(
                    path,
                    size,
                )
            )
        except OSError:
            continue

    return (
        ImageFont.load_default()
    )


def _money(
    value: Any,
) -> str:
    if value is None:
        return "—"

    try:
        number = float(value)

    except (
        TypeError,
        ValueError,
    ):
        return "—"

    if abs(number) >= 1_000_000_000:
        return (
            f"${number / 1_000_000_000:.1f}B"
        )

    if abs(number) >= 1_000_000:
        return (
            f"${number / 1_000_000:.0f}M"
        )

    if abs(number) >= 1_000:
        return (
            f"${number / 1_000:.0f}K"
        )

    return f"${number:.0f}"


def _price(
    value: Any,
) -> str:
    if value is None:
        return "—"

    try:
        number = float(value)

    except (
        TypeError,
        ValueError,
    ):
        return "—"

    if number >= 1000:
        return (
            f"${number:,.0f}"
        )

    if number >= 100:
        return (
            f"${number:.2f}"
        )

    if number >= 1:
        return (
            f"${number:.3f}"
        )

    if number >= 0.01:
        return (
            f"${number:.4f}"
        )

    return (
        f"${number:.7f}"
    )


def render_market_grid(
    items: List[Dict[str, Any]],
    *,
    mode: str,
) -> BytesIO:
    mode = mode.lower()

    if mode not in {
        "winners",
        "losers",
    }:
        raise ValueError(
            "mode must be winners or losers"
        )

    bullish = (
        mode == "winners"
    )

    accent = (
        GREEN
        if bullish
        else RED
    )

    tint = (
        GREEN_BG
        if bullish
        else RED_BG
    )

    icon = (
        "▲"
        if bullish
        else "▼"
    )

    title = (
        "TOP 20 WINNERS"
        if bullish
        else "TOP 20 LOSERS"
    )

    subtitle = (
        "24H MARKET MOVERS"
    )

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
        44,
        True,
    )

    subtitle_font = _font(
        19,
        False,
    )

    coin_font = _font(
        28,
        True,
    )

    percent_font = _font(
        32,
        True,
    )

    small_font = _font(
        17,
        False,
    )

    badge_font = _font(
        20,
        True,
    )

    draw.text(
        (60, 55),
        "MRBIZNES",
        font=title_font,
        fill=WHITE,
    )

    draw.text(
        (60, 112),
        "MARKET INTELLIGENCE",
        font=subtitle_font,
        fill=CYAN,
    )

    draw.text(
        (1140, 65),
        title,
        font=_font(
            32,
            True,
        ),
        fill=accent,
        anchor="ra",
    )

    draw.text(
        (1140, 110),
        subtitle,
        font=subtitle_font,
        fill=MUTED,
        anchor="ra",
    )

    draw.line(
        (
            60,
            155,
            1140,
            155,
        ),
        fill=LINE,
        width=2,
    )

    columns = 4
    rows = 5

    left = 60
    top = 195

    gap_x = 14
    gap_y = 14

    available_width = (
        WIDTH
        - left * 2
        - gap_x
        * (columns - 1)
    )

    card_width = (
        available_width
        // columns
    )

    grid_bottom = 1320

    available_height = (
        grid_bottom
        - top
        - gap_y
        * (rows - 1)
    )

    card_height = (
        available_height
        // rows
    )

    visible_items = (
        items[:20]
    )

    for index in range(20):
        row = (
            index // columns
        )

        column = (
            index % columns
        )

        x1 = (
            left
            + column
            * (
                card_width
                + gap_x
            )
        )

        y1 = (
            top
            + row
            * (
                card_height
                + gap_y
            )
        )

        x2 = (
            x1
            + card_width
        )

        y2 = (
            y1
            + card_height
        )

        draw.rounded_rectangle(
            (
                x1,
                y1,
                x2,
                y2,
            ),
            radius=18,
            fill=CARD,
            outline=LINE,
            width=2,
        )

        if index >= len(
            visible_items
        ):
            continue

        item = visible_items[
            index
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

        price = _price(
            item.get(
                "price_usd"
            )
        )

        volume = _money(
            item.get(
                "volume_24h_usd"
            )
        )

        circle_x = (
            x1 + 43
        )

        circle_y = (
            y1 + 45
        )

        draw.ellipse(
            (
                circle_x - 24,
                circle_y - 24,
                circle_x + 24,
                circle_y + 24,
            ),
            fill=tint,
            outline=accent,
            width=2,
        )

        draw.text(
            (
                circle_x,
                circle_y - 1,
            ),
            code[:1],
            font=badge_font,
            fill=accent,
            anchor="mm",
        )

        draw.text(
            (
                x1 + 80,
                y1 + 29,
            ),
            code,
            font=coin_font,
            fill=WHITE,
        )

        sign = (
            "+"
            if change > 0
            else ""
        )

        draw.text(
            (
                x1 + 22,
                y1 + 90,
            ),
            (
                f"{icon} "
                f"{sign}"
                f"{change:.2f}%"
            ),
            font=percent_font,
            fill=accent,
        )

        draw.text(
            (
                x1 + 22,
                y1 + 139,
            ),
            price,
            font=small_font,
            fill=WHITE,
        )

        draw.text(
            (
                x2 - 22,
                y1 + 139,
            ),
            (
                "VOL "
                + volume
            ),
            font=small_font,
            fill=MUTED,
            anchor="ra",
        )

    draw.line(
        (
            60,
            1360,
            1140,
            1360,
        ),
        fill=LINE,
        width=2,
    )

    draw.text(
        (60, 1390),
        (
            "FILTER  "
            "MARKET CAP > VALUE OF 1000 BTC"
        ),
        font=subtitle_font,
        fill=MUTED,
    )

    draw.text(
        (1140, 1390),
        "SOURCE  LIVECOINWATCH",
        font=subtitle_font,
        fill=MUTED,
        anchor="ra",
    )

    draw.text(
        (60, 1435),
        (
            "24H PERFORMANCE • "
            "TRADING VOLUME ≠ NET INFLOW"
        ),
        font=subtitle_font,
        fill=accent,
    )

    output = BytesIO()

    image.save(
        output,
        format="PNG",
        optimize=True,
    )

    output.seek(0)

    output.name = (
        "mrbiznes_market_grid.png"
    )

    return output
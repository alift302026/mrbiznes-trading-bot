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

BG_DARK = "#070B0E"
CARD_BG = "#0D151D"
CARD_HOVER = "#121E2A"
BORDER_COLOR = "#1C2B3A"
BORDER_ACCENT = "#2D445D"

WHITE = "#FFFFFF"
TEXT_MUTED = "#8B9DAE"
TEXT_SUBTLE = "#5C6E80"

GREEN_NEON = "#00E676"
GREEN_BG = "#082618"

RED_NEON = "#FF5252"
RED_BG = "#2B0F13"

CYAN_NEON = "#00E5FF"
GOLD_NEON = "#FFD700"


def _font(size: int, bold: bool = False):
    candidates = (
        [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "C:/Windows/Fonts/segoeuib.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
        ]
        if bold
        else [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/arial.ttf",
        ]
    )
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _money(value: Any) -> str:
    if value is None:
        return "—"
    try:
        num = float(value)
    except (TypeError, ValueError):
        return "—"

    if abs(num) >= 1_000_000_000:
        return f"${num / 1_000_000_000:.1f}B"
    if abs(num) >= 1_000_000:
        return f"${num / 1_000_000:.1f}M"
    if abs(num) >= 1_000:
        return f"${num / 1_000:.0f}K"
    return f"${num:.0f}"


def _price(value: Any) -> str:
    if value is None:
        return "—"
    try:
        num = float(value)
    except (TypeError, ValueError):
        return "—"

    if num >= 1000:
        return f"${num:,.0f}"
    if num >= 100:
        return f"${num:.2f}"
    if num >= 1:
        return f"${num:.3f}"
    if num >= 0.01:
        return f"${num:.4f}"
    return f"${num:.7f}"


def render_market_grid(
    items: List[Dict[str, Any]],
    *,
    mode: str,
) -> BytesIO:
    mode = mode.lower()
    bullish = mode == "winners"

    accent = GREEN_NEON if bullish else RED_NEON
    tint = GREEN_BG if bullish else RED_BG
    icon = "▲" if bullish else "▼"

    title_text = "🔥 بیشترین رشد ۲۴ ساعته (TOP GAINERS)" if bullish else "❄️ بیشترین ریزش ۲۴ ساعته (TOP LOSERS)"
    subtitle_text = "پایش هوشمند بازار رمزارزها • صرافی XT و دیتابیس مستر بیزنس"

    image = Image.new("RGB", (WIDTH, HEIGHT), BG_DARK)
    draw = ImageDraw.Draw(image)

    title_font = _font(32, True)
    brand_font = _font(38, True)
    subtitle_font = _font(19, False)
    coin_font = _font(28, True)
    percent_font = _font(30, True)
    small_font = _font(17, False)
    badge_font = _font(22, True)

    # 1. Header Card
    draw.rounded_rectangle(
        (50, 35, WIDTH - 50, 150),
        radius=18,
        fill=CARD_BG,
        outline=BORDER_COLOR,
        width=2,
    )

    draw.text((80, 55), "MrBiznes MARKET INTELLIGENCE", font=brand_font, fill=WHITE)
    draw.text((80, 105), subtitle_text, font=subtitle_font, fill=TEXT_MUTED)

    # Mode Badge on Right
    draw.text((WIDTH - 80, 65), title_text, font=title_font, fill=accent, anchor="ra")

    # 2. Grid Cards (4 columns x 5 rows = 20 cards)
    columns = 4
    rows = 5
    left = 50
    top = 175
    gap_x = 16
    gap_y = 16

    available_width = WIDTH - left * 2 - gap_x * (columns - 1)
    card_width = available_width // columns

    grid_bottom = 1350
    available_height = grid_bottom - top - gap_y * (rows - 1)
    card_height = available_height // rows

    visible_items = items[:20]

    for index in range(20):
        row = index // columns
        column = index % columns

        x1 = left + column * (card_width + gap_x)
        y1 = top + row * (card_height + gap_y)
        x2 = x1 + card_width
        y2 = y1 + card_height

        draw.rounded_rectangle(
            (x1, y1, x2, y2),
            radius=16,
            fill=CARD_BG,
            outline=BORDER_COLOR,
            width=2,
        )

        if index >= len(visible_items):
            continue

        item = visible_items[index]
        code = str(item.get("code") or "?").upper()
        change = float(item.get("change_24h_percent") or 0)
        price = _price(item.get("price_usd"))
        volume = _money(item.get("volume_24h_usd"))

        # Icon Circle
        circle_x = x1 + 45
        circle_y = y1 + 45
        draw.ellipse(
            (circle_x - 24, circle_y - 24, circle_x + 24, circle_y + 24),
            fill=tint,
            outline=accent,
            width=2,
        )
        draw.text(
            (circle_x, circle_y - 1),
            code[:1],
            font=badge_font,
            fill=accent,
            anchor="mm",
        )

        # Coin Symbol
        draw.text((x1 + 82, y1 + 30), code, font=coin_font, fill=WHITE)

        # 24H Change
        sign = "+" if change > 0 else ""
        draw.text(
            (x1 + 22, y1 + 92),
            f"{icon} {sign}{change:.2f}%",
            font=percent_font,
            fill=accent,
        )

        # Price
        draw.text((x1 + 22, y1 + 144), price, font=small_font, fill=WHITE)

        # Volume
        draw.text(
            (x2 - 20, y1 + 144),
            f"حجم: {volume}",
            font=small_font,
            fill=TEXT_MUTED,
            anchor="ra",
        )

    # 3. Footer
    draw.rounded_rectangle(
        (50, 1375, WIDTH - 50, HEIGHT - 35),
        radius=16,
        fill=CARD_BG,
        outline=BORDER_COLOR,
        width=2,
    )

    draw.text((80, 1400), "مرجع داده: XT Exchange Spot • تحلیلی و آموزشی", font=subtitle_font, fill=TEXT_MUTED)
    draw.text((WIDTH - 80, 1400), "@MrBiznesMarket", font=_font(22, True), fill=GREEN_NEON, anchor="ra")

    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    output.seek(0)
    output.name = "mrbiznes_market_grid.png"
    return output

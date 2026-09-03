from __future__ import annotations

import math
from io import BytesIO
from typing import Any, Dict

from PIL import (
    Image,
    ImageDraw,
    ImageFont,
)


WIDTH = 1080
HEIGHT = 1350

BG_DARK = "#070B0E"
PANEL_BG = "#0D141C"
PANEL_INNER = "#121C26"
BORDER_COLOR = "#1C2B3A"
BORDER_HIGHLIGHT = "#2C3E52"

WHITE = "#FFFFFF"
TEXT_PRIMARY = "#F0F4F8"
TEXT_MUTED = "#8B9DAE"
TEXT_SUBTLE = "#5C6E80"

GREEN_NEON = "#00E676"
GREEN_BG = "#082618"
GREEN_BORDER = "#00E676"

RED_NEON = "#FF5252"
RED_BG = "#2B0F13"
RED_BORDER = "#FF5252"

CYAN_NEON = "#00E5FF"
GOLD_NEON = "#FFD700"
PURPLE_NEON = "#B388FF"


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


def _value(value: Any, decimals: int = 2) -> str:
    if value is None:
        return "—"
    try:
        num = float(value)
        if abs(num) >= 1000:
            return f"{num:,.{decimals}f}"
        if abs(num) < 0.001:
            return f"{num:.6f}"
        return f"{num:.{decimals}f}"
    except (TypeError, ValueError):
        return str(value)


def _percent(value: Any) -> str:
    if value is None:
        return "—"
    try:
        num = float(value)
        sign = "+" if num > 0 else ""
        return f"{sign}{num:.2f}%"
    except (TypeError, ValueError):
        return "—"


def render_signal_card(signal: Dict[str, Any]) -> BytesIO:
    image = Image.new("RGB", (WIDTH, HEIGHT), BG_DARK)
    draw = ImageDraw.Draw(image)

    # Fonts
    brand_font = _font(34, True)
    tag_font = _font(18, True)
    asset_font = _font(54, True)
    grade_font = _font(64, True)
    section_title_font = _font(22, True)
    card_value_font = _font(26, True)
    card_label_font = _font(17, False)
    small_font = _font(16, False)
    badge_font = _font(20, True)

    direction = str(signal.get("direction", "LONG")).upper()
    is_long = "LONG" in direction or "BUY" in direction
    accent = GREEN_NEON if is_long else RED_NEON
    accent_bg = GREEN_BG if is_long else RED_BG

    # 1. Header Bar
    draw.rounded_rectangle(
        (40, 35, WIDTH - 40, 115),
        radius=16,
        fill=PANEL_BG,
        outline=BORDER_COLOR,
        width=2,
    )

    draw.text((65, 55), "MrBiznes", font=brand_font, fill=WHITE)
    draw.text((245, 63), "TRADING SIGNAL", font=tag_font, fill=CYAN_NEON)

    # Live Badge
    draw.rounded_rectangle(
        (WIDTH - 210, 50, WIDTH - 65, 100),
        radius=12,
        fill=accent_bg,
        outline=accent,
        width=2,
    )
    draw.ellipse((WIDTH - 192, 70, WIDTH - 180, 82), fill=accent)
    draw.text(
        (WIDTH - 165, 64),
        "LIVE SIGNAL",
        font=badge_font,
        fill=accent,
    )

    # 2. Main Asset Card
    draw.rounded_rectangle(
        (40, 135, WIDTH - 40, 340),
        radius=20,
        fill=PANEL_BG,
        outline=BORDER_COLOR,
        width=2,
    )

    symbol = signal.get("symbol", "BTC/USDT")
    draw.text((70, 165), symbol, font=asset_font, fill=WHITE)

    # Direction Pill
    pill_text = "🟢 LONG POSITION" if is_long else "🔴 SHORT POSITION"
    draw.rounded_rectangle(
        (70, 248, 350, 305),
        radius=12,
        fill=accent_bg,
        outline=accent,
        width=2,
    )
    draw.text((88, 263), pill_text, font=badge_font, fill=accent)

    # Grade & Confidence Box
    grade = signal.get("grade", "A+")
    confidence = signal.get("confidence", 92)
    draw.text((WIDTH - 75, 160), str(grade), font=grade_font, fill=GOLD_NEON, anchor="ra")
    draw.text(
        (WIDTH - 75, 255),
        f"ستاپ تأیید شده ({confidence}/100)",
        font=badge_font,
        fill=TEXT_MUTED,
        anchor="ra",
    )

    # 3. Trade Levels Panel (ENTRY, STOP, TARGETS, R:R)
    draw.rounded_rectangle(
        (40, 360, WIDTH - 40, 600),
        radius=20,
        fill=PANEL_BG,
        outline=BORDER_COLOR,
        width=2,
    )

    draw.text((70, 385), "🎯 نقشه ورود و اهداف معامله (TRADE MAP)", font=section_title_font, fill=CYAN_NEON)

    level_boxes = [
        ("نقطه ورود (Entry)", signal.get("entry_trigger", signal.get("entry", 0)), CYAN_NEON),
        ("حد ضرر (Stop Loss)", signal.get("stop", signal.get("stop_loss", 0)), RED_NEON),
        ("تارگت اول (TP 1)", signal.get("target_1", signal.get("tp1", 0)), GREEN_NEON),
        ("تارگت دوم (TP 2)", signal.get("target_2", signal.get("tp2", 0)), GREEN_NEON),
    ]

    box_w = 215
    gap = 20
    start_x = 70
    for idx, (label, val, col) in enumerate(level_boxes):
        x1 = start_x + idx * (box_w + gap)
        y1 = 430
        x2 = x1 + box_w
        y2 = 565

        draw.rounded_rectangle(
            (x1, y1, x2, y2),
            radius=14,
            fill=PANEL_INNER,
            outline=BORDER_HIGHLIGHT,
            width=2,
        )
        draw.text((x1 + 14, y1 + 18), label, font=card_label_font, fill=TEXT_MUTED)
        draw.text((x1 + 14, y1 + 65), _value(val), font=card_value_font, fill=col)

    # 4. Multi-Timeframe Confirmation
    draw.rounded_rectangle(
        (40, 620, WIDTH - 40, 860),
        radius=20,
        fill=PANEL_BG,
        outline=BORDER_COLOR,
        width=2,
    )

    draw.text((70, 645), "📊 تاییدهای تکنیکال و اسیلاتورها (INDICATORS)", font=section_title_font, fill=CYAN_NEON)

    tf15 = signal.get("timeframes", {}).get("15m", {})
    rsi_val = _value(tf15.get("rsi", 54.2))
    macd_val = _value(tf15.get("macd_histogram", 0.15))
    atr_val = _percent(tf15.get("atr_percent", 1.8))
    vol_state = str(tf15.get("volume", {}).get("state", "High Volume")).upper()
    trend_state = str(tf15.get("sma_state", "Bullish Align")).upper()
    structure_state = str(tf15.get("dow", "BOS Bullish")).upper()

    indicator_items = [
        ("RSI (14)", rsi_val, GREEN_NEON if is_long else RED_NEON),
        ("MACD Histogram", macd_val, CYAN_NEON),
        ("ATR Volatility", atr_val, GOLD_NEON),
        ("Volume Flow", vol_state, GREEN_NEON),
        ("Trend Alignment", trend_state, accent),
        ("Structure (Dow)", structure_state, WHITE),
    ]

    col_w = 300
    row_h = 75
    for idx, (lbl, v_text, col) in enumerate(indicator_items):
        col_idx = idx % 3
        row_idx = idx // 3
        x = 70 + col_idx * (col_w + 20)
        y = 700 + row_idx * (row_h + 10)

        draw.rounded_rectangle(
            (x, y, x + col_w, y + row_h),
            radius=12,
            fill=PANEL_INNER,
            outline=BORDER_COLOR,
            width=1,
        )
        draw.text((x + 14, y + 12), lbl, font=card_label_font, fill=TEXT_MUTED)
        draw.text((x + 14, y + 38), str(v_text), font=card_value_font, fill=col)

    # 5. Market Structure & Risk Assessment
    draw.rounded_rectangle(
        (40, 880, WIDTH - 40, 1120),
        radius=20,
        fill=PANEL_BG,
        outline=BORDER_COLOR,
        width=2,
    )

    draw.text((70, 905), "🏛 ساختار بازار و تحلیل تایم‌فریم‌ها", font=section_title_font, fill=CYAN_NEON)

    tfs = [
        ("15 دقیقه (Entry)", "تثبیت و مومنتوم ورود", GREEN_NEON if is_long else RED_NEON),
        ("1 ساعته (Trend)", "روند اصلی هم‌جهت", GREEN_NEON if is_long else RED_NEON),
        ("4 ساعته (Structure)", "شکست ساختار کلیدی", CYAN_NEON),
    ]

    for idx, (tf_title, tf_desc, col) in enumerate(tfs):
        x = 70 + idx * 315
        y = 960
        draw.rounded_rectangle(
            (x, y, x + 300, y + 115),
            radius=14,
            fill=PANEL_INNER,
            outline=BORDER_HIGHLIGHT,
            width=2,
        )
        draw.text((x + 16, y + 16), tf_title, font=card_label_font, fill=TEXT_MUTED)
        draw.text((x + 16, y + 52), tf_desc, font=_font(18, True), fill=col)

    # 6. Footer & Disclaimers
    draw.rounded_rectangle(
        (40, 1140, WIDTH - 40, HEIGHT - 35),
        radius=18,
        fill=PANEL_BG,
        outline=BORDER_COLOR,
        width=2,
    )

    draw.text(
        (70, 1165),
        "بانک اطلاعات داده: XT Exchange • دیتابیس هوشمند MrBiznes",
        font=small_font,
        fill=TEXT_MUTED,
    )
    draw.text(
        (70, 1205),
        "⚠️ توجه: سیگنال‌ها جنبه تحلیلی دارند. همواره حد ضرر و مدیریت سرمایه را رعایت کنید.",
        font=small_font,
        fill=GOLD_NEON,
    )
    draw.text(
        (WIDTH - 70, 1185),
        "@MrBiznesMarket",
        font=_font(22, True),
        fill=GREEN_NEON,
        anchor="rm",
    )

    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    output.seek(0)
    output.name = "mrbiznes_signal.png"
    return output

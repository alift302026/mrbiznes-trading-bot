"""Session Clock Renderer - 24-Hour Circular Market Session Dial for MrBiznes."""
from __future__ import annotations

import math
from datetime import datetime, timezone
from io import BytesIO
from typing import Any, Dict, List
from zoneinfo import ZoneInfo

import jdatetime
from PIL import Image, ImageDraw, ImageFont

from app.engines.sessions.session_engine import (
    SESSIONS,
    TEHRAN_ZONE,
    all_sessions,
)

WIDTH = 1080
HEIGHT = 1260

BG = "#070B0E"
DIAL_BG = "#0D141C"
CARD_BG = "#0F1A24"
LINE_COLOR = "#1B2A38"
ACTIVE_GREEN = "#00E676"
ACTIVE_GLOW = "#004D28"
CLOSED_GRAY = "#22303E"
TEXT_WHITE = "#FFFFFF"
TEXT_MUTED = "#8B9DAE"
NEEDLE_CYAN = "#00E5FF"
GOLD = "#FFD700"


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


def _time_to_angle(hour: float, minute: float = 0.0) -> float:
    """
    Map 24h time to degrees on dial.
    00:00 is at top (-90 deg), progresses clockwise 360 deg in 24 hours.
    Angle = (hours + minutes/60) * (360/24) - 90
    """
    total_hours = (hour + minute / 60.0) % 24.0
    return (total_hours / 24.0) * 360.0 - 90.0


def render_session_clock() -> BytesIO:
    image = Image.new("RGB", (WIDTH, HEIGHT), BG)
    draw = ImageDraw.Draw(image)

    title_font = _font(36, True)
    subtitle_font = _font(20, False)
    badge_font = _font(18, True)
    clock_time_font = _font(38, True)
    clock_date_font = _font(19, True)
    legend_title_font = _font(22, True)
    legend_text_font = _font(19, False)
    hour_font = _font(16, True)

    now_utc = datetime.now(timezone.utc)
    tehran_now = now_utc.astimezone(TEHRAN_ZONE)
    jalali_date = jdatetime.date.fromgregorian(date=tehran_now.date())

    # Header Card
    draw.rounded_rectangle(
        (50, 40, WIDTH - 50, 130),
        radius=18,
        fill=CARD_BG,
        outline=LINE_COLOR,
        width=2,
    )

    draw.text(
        (80, 58),
        "MrBiznes | ساعت سشن‌های معاملاتی",
        font=title_font,
        fill=TEXT_WHITE,
    )
    draw.text(
        (80, 98),
        "پایش زنده ۲۴ ساعته بازار جهانی به وقت رسمی تهران 🇮🇷",
        font=subtitle_font,
        fill=TEXT_MUTED,
    )

    # Dial geometry
    center_x = WIDTH // 2
    center_y = 480
    dial_radius = 310

    # Draw outer background circle
    draw.ellipse(
        (
            center_x - dial_radius,
            center_y - dial_radius,
            center_x + dial_radius,
            center_y + dial_radius,
        ),
        fill=DIAL_BG,
        outline=LINE_COLOR,
        width=3,
    )

    # 24-hour tick marks & numbers around dial
    for h in range(24):
        angle_deg = _time_to_angle(h, 0)
        angle_rad = math.radians(angle_deg)

        # Outer tick
        tick_len = 14 if h % 6 == 0 else 8
        r_outer = dial_radius - 6
        r_inner = r_outer - tick_len
        x_out = center_x + r_outer * math.cos(angle_rad)
        y_out = center_y + r_outer * math.sin(angle_rad)
        x_in = center_x + r_inner * math.cos(angle_rad)
        y_in = center_y + r_inner * math.sin(angle_rad)

        tick_color = NEEDLE_CYAN if h % 6 == 0 else LINE_COLOR
        draw.line((x_in, y_in, x_out, y_out), fill=tick_color, width=2)

        # Hour Label for every 2 or 3 hours
        if h % 2 == 0:
            r_text = dial_radius - 32
            x_t = center_x + r_text * math.cos(angle_rad)
            y_t = center_y + r_text * math.sin(angle_rad)
            h_str = f"{h:02d}:00" if h % 6 == 0 else f"{h:02d}"
            draw.text((x_t, y_t), h_str, font=hour_font, fill=TEXT_MUTED, anchor="mm")

    # Session rings definition (Outer to inner rings)
    sessions_data = all_sessions()
    rings_config = [
        {"key": "sydney", "r_out": 265, "r_in": 235, "label": "سیدنی (Sydney)"},
        {"key": "tokyo", "r_out": 230, "r_in": 200, "label": "توکیو (Tokyo)"},
        {"key": "london", "r_out": 195, "r_in": 165, "label": "لندن (London)"},
        {"key": "new_york", "r_out": 160, "r_in": 130, "label": "نیویورک (New York)"},
    ]

    active_count = 0
    for ring in rings_config:
        item = next((s for s in sessions_data if s["key"] == ring["key"]), None)
        if not item:
            continue

        is_open = item["is_open"]
        if is_open:
            active_count += 1

        open_th = item["open_tehran"]
        close_th = item["close_tehran"]

        start_angle = _time_to_angle(open_th.hour, open_th.minute)
        end_angle = _time_to_angle(close_th.hour, close_th.minute)

        # Normalize end_angle if it wraps past 360
        if end_angle <= start_angle:
            end_angle += 360.0

        r_out = ring["r_out"]
        r_in = ring["r_in"]
        mid_r = (r_out + r_in) / 2
        width = r_out - r_in

        # Color: Glowing green if open, dark slate if closed
        arc_color = ACTIVE_GREEN if is_open else CLOSED_GRAY
        draw.arc(
            (
                center_x - mid_r,
                center_y - mid_r,
                center_x + mid_r,
                center_y + mid_r,
            ),
            start=start_angle,
            end=end_angle,
            fill=arc_color,
            width=int(width - 2),
        )

        # If active, draw bright inner highlight
        if is_open:
            draw.arc(
                (
                    center_x - mid_r,
                    center_y - mid_r,
                    center_x + mid_r,
                    center_y + mid_r,
                ),
                start=start_angle,
                end=end_angle,
                fill="#80FFB8",
                width=2,
            )

    # Current Tehran Time Needle (Hand)
    th_h = tehran_now.hour
    th_m = tehran_now.minute
    th_s = tehran_now.second
    needle_angle_deg = _time_to_angle(th_h + th_m / 60.0 + th_s / 3600.0, 0)
    needle_rad = math.radians(needle_angle_deg)

    # Draw Needle
    needle_len = dial_radius - 12
    n_x = center_x + needle_len * math.cos(needle_rad)
    n_y = center_y + needle_len * math.sin(needle_rad)
    draw.line((center_x, center_y, n_x, n_y), fill=NEEDLE_CYAN, width=3)
    draw.ellipse((n_x - 5, n_y - 5, n_x + 5, n_y + 5), fill=NEEDLE_CYAN)

    # Center Hub (Digital Clock & Jalali Date)
    center_hub_radius = 115
    draw.ellipse(
        (
            center_x - center_hub_radius,
            center_y - center_hub_radius,
            center_x + center_hub_radius,
            center_y + center_hub_radius,
        ),
        fill="#080F16",
        outline=NEEDLE_CYAN if active_count > 0 else LINE_COLOR,
        width=3,
    )

    digital_time_str = tehran_now.strftime("%H:%M:%S")
    jalali_str = f"{jalali_date.year}/{jalali_date.month:02d}/{jalali_date.day:02d}"

    draw.text(
        (center_x, center_y - 35),
        "ساعت تهران 🇮🇷",
        font=_font(14, False),
        fill=TEXT_MUTED,
        anchor="mm",
    )
    draw.text(
        (center_x, center_y - 3),
        digital_time_str,
        font=clock_time_font,
        fill=TEXT_WHITE,
        anchor="mm",
    )
    draw.text(
        (center_x, center_y + 32),
        jalali_str,
        font=clock_date_font,
        fill=GOLD,
        anchor="mm",
    )
    draw.text(
        (center_x, center_y + 60),
        f"🟢 {active_count} سشن فعال" if active_count > 0 else "🔴 بدون سشن فعال",
        font=_font(14, True),
        fill=ACTIVE_GREEN if active_count > 0 else "#FF5252",
        anchor="mm",
    )

    # Sessions Legend & Breakdown (Lower panel)
    legend_top = 825
    draw.rounded_rectangle(
        (50, legend_top, WIDTH - 50, HEIGHT - 40),
        radius=18,
        fill=CARD_BG,
        outline=LINE_COLOR,
        width=2,
    )

    draw.text(
        (80, legend_top + 22),
        "📊 وضعیت سشن‌های معاملاتی بازار جهانی (به وقت تهران):",
        font=legend_title_font,
        fill=TEXT_WHITE,
    )

    card_y = legend_top + 65
    for item in sessions_data:
        is_open = item["is_open"]
        open_th = item["open_tehran"].strftime("%H:%M")
        close_th = item["close_tehran"].strftime("%H:%M")

        # Row box
        box_bg = "#0A2016" if is_open else "#121A22"
        box_border = ACTIVE_GREEN if is_open else LINE_COLOR
        draw.rounded_rectangle(
            (75, card_y, WIDTH - 75, card_y + 65),
            radius=12,
            fill=box_bg,
            outline=box_border,
            width=2 if is_open else 1,
        )

        # Flag + Name
        name_text = f"{item['flag']} سشن {item['name']}"
        draw.text(
            (100, card_y + 32),
            name_text,
            font=_font(21, True),
            fill=TEXT_WHITE,
            anchor="lm",
        )

        # Hours
        hours_text = f"⏰ ساعت فعالیت تهران: {open_th} الی {close_th}"
        draw.text(
            (WIDTH // 2, card_y + 32),
            hours_text,
            font=legend_text_font,
            fill=TEXT_MUTED if not is_open else TEXT_WHITE,
            anchor="mm",
        )

        # Status badge
        status_text = "🟢 باز (OPEN)" if is_open else "🔴 بسته"
        status_color = ACTIVE_GREEN if is_open else "#FF6B6B"
        draw.text(
            (WIDTH - 100, card_y + 32),
            status_text,
            font=badge_font,
            fill=status_color,
            anchor="rm",
        )

        card_y += 75

    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    output.seek(0)
    output.name = "mrbiznes_session_clock.png"
    return output

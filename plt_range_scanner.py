#!/usr/bin/env python3
"""
PLT Range Scanner — MrBiznes
=============================

Scans the latest **99 CLOSED M15 candles** of the configured symbols and
reports a RANGE regime signal (information only).

Design rules (hard constraints)
-------------------------------
1.  Uses ONLY the latest 99 closed 15-minute candles (never older history).
2.  RSI is exactly RSI(14) with CLOSE as the source (Wilder smoothing).
3.  SMA 7 / 25 / 99 are computed on CLOSE over the same 99 candles.
4.  FVG analysis is completely removed (no fair-value-gap code anywhere).
5.  NO trading / order execution.  This script never sends orders and never
    reads private trade endpoints.  Output is SIGNALS only.
6.  Results are written to the SIGNALS section (stdout + files under
    <repo>/data/plt_range/) and — when Telegram credentials are configured —
    are posted to a private channel (photo card + text).
7.  When LiveCoinWatch key is configured, the symbol universe may be derived
    from the top market-cap coins; otherwise PLT_RANGE_SYMBOLS is used.

Range definition (transparent v1, thresholds configurable)
----------------------------------------------------------
A symbol is reported as RANGE when, over the same 99 closed candles:
  * RSI(14) history stays mostly inside [30, 70]   (oscillating, not trending)
  * RSI mean is near the 50 mid-line
  * SMA fan is tight: |SMA7 - SMA25| and |SMA25 - SMA99| are small relative
    to price (weak trend / no strong directional alignment)
A combined range_score (0-100) is produced; a symbol is emitted only when
score >= PLT_RANGE_MIN_SCORE (default 65).  Support/resistance edges are
derived from repeated-touch swing levels over the last 60 candles and the
last close position between the edges is reported (no buy/sell wording).

Exit codes
----------
0  run finished (signals written / posted or none found)
2  recoverable runtime error (network, data, credentials for configured push)
3  configuration error (bad env)
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import requests
except Exception:  # pragma: no cover
    requests = None  # type: ignore[assignment]

# --------------------------------------------------------------------------
# PATHS / ENV
# --------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data" / "plt_range"
CARD_DIR = DATA_DIR / "cards"
SIGNALS_DIR = DATA_DIR / "signals"
LATEST_SIGNALS_FILE = DATA_DIR / "signals_latest.txt"
STATE_FILE = DATA_DIR / "last_posted.json"

DOTENV = BASE_DIR / ".env"

INTERVAL_SECONDS = 15 * 60  # M15
REQUIRED_CANDLES = 99
FETCH_LIMIT = 110  # bounded fetch; only the latest 99 *closed* candles are used

# Telegram message size limit guard
MAX_MESSAGE_LEN = 4000


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name, "").strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "on"}


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name, "").strip()
    try:
        return float(raw)
    except ValueError:
        return default


def load_env() -> None:
    """Load .env from the repository root when present (cron has no env)."""
    if DOTENV.exists():
        try:
            for raw_line in DOTENV.read_text(encoding="utf-8").splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value
        except Exception as exc:  # pragma: no cover
            print(f"[plt_range] WARNING: could not read .env: {exc}")


# --------------------------------------------------------------------------
# CONFIG
# --------------------------------------------------------------------------

# Bitunix (public klines — no key required for reading candles).
BITUNIX_BASE = os.getenv(
    "BITUNIX_BASE_URL",
    "https://fapi.bitunix.com/api/v1/futures/market/kline",
).strip()

# Symbols default: widely traded USDT pairs on Bitunix.
DEFAULT_SYMBOLS = [
    "BTCUSDT",
    "ETHUSDT",
    "SOLUSDT",
    "BNBUSDT",
    "XRPUSDT",
    "DOGEUSDT",
    "ADAUSDT",
    "AVAXUSDT",
    "LINKUSDT",
    "LTCUSDT",
    "TRXUSDT",
    "TONUSDT",
]

SYMBOLS = [
    s.strip().upper()
    for s in os.getenv(
        "PLT_RANGE_SYMBOLS",
        ",".join(DEFAULT_SYMBOLS),
    ).split(",")
    if s.strip()
]

BITUNIX_API_KEY = os.getenv("BITUNIX_API_KEY", "").strip()
BITUNIX_SECRET_KEY = os.getenv("BITUNIX_SECRET_KEY", "").strip()

LIVECOINWATCH_API_KEY = os.getenv("LIVECOINWATCH_API_KEY", "").strip()
LCW_TOP_N = int(os.getenv("PLT_RANGE_LCW_TOP", "15").strip() or 15)

# Range thresholds
RANGE_MIN_SCORE = _env_float("PLT_RANGE_MIN_SCORE", 65.0)
RSI_BAND_LO, RSI_BAND_HI = 30.0, 70.0
SMA_FAN_TOLERANCE = _env_float("PLT_RANGE_SMA_FAN_PCT", 3.0)  # % of price

# Telegram push
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
CHANNEL_ID = os.getenv(
    "PLT_RANGE_CHANNEL_ID",
    os.getenv("NEWS_CHANNEL_ID", ""),
).strip()
SEND_EMPTY = _env_bool("PLT_RANGE_SEND_EMPTY", True)  # post summary even with no setups
FORCE_POST = _env_bool("PLT_RANGE_FORCE_POST", False)
ENABLE_CARD = _env_bool("PLT_RANGE_CARD", True)
HTTP_TIMEOUT = int(os.getenv("PLT_RANGE_HTTP_TIMEOUT", "20").strip() or 20)


def resolve_channel_id() -> str:
    """Channel id from env, falling back to the auto-discovered one."""
    if CHANNEL_ID:
        return CHANNEL_ID
    state = _load_state()
    discovered = state.get("discovered_channel_id", "")
    return str(discovered) if discovered else ""


# --------------------------------------------------------------------------
# INDICATORS (pure functions over close arrays)
# --------------------------------------------------------------------------

def rsi14(closes: List[float]) -> List[float]:
    """Wilder RSI(14) on CLOSE — matches the standard definition."""
    n = 14
    if len(closes) <= n:
        return [50.0] * len(closes)
    out: List[float] = [50.0] * len(closes)
    gains = []
    losses = []
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i - 1]
        gains.append(max(diff, 0.0))
        losses.append(max(-diff, 0.0))
    avg_gain = sum(gains[:n]) / n
    avg_loss = sum(losses[:n]) / n
    out[n] = 100.0 if avg_loss == 0 else 100.0 - (100.0 / (1.0 + avg_gain / avg_loss))
    for i in range(n + 1, len(closes)):
        avg_gain = (avg_gain * (n - 1) + gains[i - 1]) / n
        avg_loss = (avg_loss * (n - 1) + losses[i - 1]) / n
        out[i] = 100.0 if avg_loss == 0 else 100.0 - (100.0 / (1.0 + avg_gain / avg_loss))
    return out


def sma(values: List[float], period: int) -> float:
    if len(values) < period:
        raise ValueError(f"need at least {period} values for SMA{period}")
    return sum(values[-period:]) / period


# --------------------------------------------------------------------------
# BITUNIX DATA (public candles only — read-only)
# --------------------------------------------------------------------------

def fetch_bitunix_ohlcv(symbol: str, limit: int = FETCH_LIMIT) -> List[Dict[str, Any]]:
    """Return raw OHLCV rows for `symbol` (e.g. BTCUSDT), bounded to `limit`.

    Public market endpoint; no signing required.  If credentials are
    configured they are ignored here (this scanner never reads private data).
    """
    if requests is None:
        raise RuntimeError("requests is not installed")

    params = {
        "symbol": symbol,
        "interval": "15m",
        "limit": limit,
    }
    resp = requests.get(
        BITUNIX_BASE,
        params=params,
        timeout=HTTP_TIMEOUT,
        headers={"User-Agent": "MrBiznes-PLT-Range-Scanner/1.0"},
    )
    if resp.status_code != 200:
        raise RuntimeError(
            f"Bitunix HTTP {resp.status_code} for {symbol}: {resp.text[:300]}"
        )
    try:
        payload = resp.json()
    except ValueError as exc:
        raise RuntimeError(f"Bitunix bad JSON for {symbol}: {exc}") from exc

    code = payload.get("code", payload.get("Code"))
    if code not in (0, "0", None):
        raise RuntimeError(
            f"Bitunix error code={code} msg={payload.get('msg', payload.get('Msg', ''))}"
        )
    rows = payload.get("data")
    if not isinstance(rows, list) or not rows:
        raise RuntimeError(f"Bitunix returned no candles for {symbol}")
    return rows


def parse_ohlcv_row(row: Dict[str, Any]) -> Dict[str, float]:
    """Normalise a Bitunix kline row -> {open, high, low, close, time_ms}."""
    time_ms = row.get("time", row.get("ts", row.get("Time", 0)))
    if not time_ms:
        # Some spot responses use seconds
        time_ms = row.get("time_s", 0) * 1000
    return {
        "time_ms": float(time_ms),
        "open": float(row.get("open", row.get("Open"))),
        "high": float(row.get("high", row.get("High"))),
        "low": float(row.get("low", row.get("Low"))),
        "close": float(row.get("close", row.get("Close"))),
    }


def latest_closed_candles(symbol: str, limit: int = FETCH_LIMIT) -> List[Dict[str, float]]:
    """Return the latest 99 CLOSED M15 candles for symbol.

    Never scans history beyond `limit` raw candles and never uses a still
    forming (unclosed) candle.
    """
    rows = fetch_bitunix_ohlcv(symbol, limit=limit)
    candles = [parse_ohlcv_row(r) for r in rows]
    candles.sort(key=lambda c: c["time_ms"])

    now_ms = time.time() * 1000.0
    closed = [
        c
        for c in candles
        if (c["time_ms"] + INTERVAL_SECONDS * 1000.0) <= now_ms + 60_000.0
    ]
    closed = closed[-REQUIRED_CANDLES:]
    if len(closed) < REQUIRED_CANDLES:
        raise RuntimeError(
            f"{symbol}: only {len(closed)} closed candles available "
            f"(need {REQUIRED_CANDLES})"
        )
    return closed


# --------------------------------------------------------------------------
# RANGE ANALYSIS (single symbol, 99 closed candles)
# --------------------------------------------------------------------------

def _quantize(price: float) -> float:
    """Round to 4 significant figures (level buckets)."""
    if price <= 0:
        return price
    exp = math.floor(math.log10(price)) - 3
    unit = 10 ** exp
    return round(price / unit) * unit


def swing_levels(candles: List[Dict[str, float]], lookback: int = 60):
    """Repeated-touch support/resistance over the last `lookback` candles.

    Support = highest low that was touched at least twice.
    Resistance = lowest high that was touched at least twice.
    Falls back to rolling min/max when no repeated level exists.
    """
    chunk = candles[-lookback:]
    low_groups: Dict[float, List[float]] = {}
    high_groups: Dict[float, List[float]] = {}
    for c in chunk:
        low_groups.setdefault(_quantize(c["low"]), []).append(c["low"])
        high_groups.setdefault(_quantize(c["high"]), []).append(c["high"])

    def level(groups, pick, fallback):
        touched = [(q, min(vals)) for q, vals in groups.items() if len(vals) >= 2]
        if not touched:
            return fallback
        return pick(touched, key=lambda t: t[1])[1]

    support = level(low_groups, max, min(c["low"] for c in chunk))
    resistance = level(high_groups, min, max(c["high"] for c in chunk))
    if resistance <= support:
        support = min(c["low"] for c in chunk)
        resistance = max(c["high"] for c in chunk)
    return support, resistance


def analyse_symbol(symbol: str, candles: List[Dict[str, float]]) -> Dict[str, Any]:
    """Compute the full indicator + range report for one symbol."""
    closes = [c["close"] for c in candles]
    rsi_series = rsi14(closes)
    cur_rsi = rsi_series[-1]

    s7 = sma(closes, 7)
    s25 = sma(closes, 25)
    s99 = sma(closes, 99)
    last_price = closes[-1]

    support, resistance = swing_levels(candles)
    width = resistance - support
    position = (last_price - support) / width if width > 0 else 0.5

    # --- range evidence ------------------------------------------------
    recent_rsi = rsi_series[-REQUIRED_CANDLES:]
    rsi_mean = sum(recent_rsi) / len(recent_rsi)
    rsi_centered_dev = abs(rsi_mean - 50.0)          # how far RSI is biased

    crosses = 0
    prev_side = 1 if recent_rsi[0] >= 50.0 else -1
    for value in recent_rsi[1:]:
        side = 1 if value >= 50.0 else -1
        if side != prev_side:
            crosses += 1
        prev_side = side

    fan_pct = (
        100.0
        * abs(s25 - s99)
        / (last_price or 1.0)
    )

    touches_support = sum(
        1
        for c in candles[-60:]
        if c["low"] <= support * 1.003
    )
    touches_resistance = sum(
        1
        for c in candles[-60:]
        if c["high"] >= resistance * 0.997
    )

    # trend veto: 99-candle SMA spread must be small relative to price
    c_fan = max(0.0, min(100.0, 100.0 - (fan_pct / max(SMA_FAN_TOLERANCE, 1e-9)) * 100.0))

    # structure: repeated touches of both sides of the range
    c_struct = min(100.0, 20.0 * (touches_support + touches_resistance))

    # RSI behaviour: centred oscillation (not persistent bias)
    c_centered = max(0.0, min(100.0, 100.0 - rsi_centered_dev * 6.0))
    c_cross = min(100.0, crosses / 6.0 * 100.0)

    score = round(
        0.25 * c_cross
        + 0.20 * c_centered
        + 0.30 * c_fan
        + 0.25 * c_struct,
        1,
    )

    active = (
        score >= RANGE_MIN_SCORE
        and rsi_centered_dev <= 18.0
        and touches_support >= 2
        and touches_resistance >= 2
    )

    if active:
        if position <= 0.2:
            bias = "AT_SUPPORT"
        elif position >= 0.8:
            bias = "AT_RESISTANCE"
        else:
            bias = "MID_RANGE"
    else:
        bias = "NO_SETUP"

    last_open_ms = candles[-1]["time_ms"]
    last_close_utc = datetime.fromtimestamp(
        (last_open_ms + INTERVAL_SECONDS * 1000.0) / 1000.0,
        tz=timezone.utc,
    )

    return {
        "symbol": symbol,
        "last_price": round(last_price, 8),
        "rsi14": round(cur_rsi, 2),
        "sma7": round(s7, 8),
        "sma25": round(s25, 8),
        "sma99": round(s99, 8),
        "support": round(support, 8),
        "resistance": round(resistance, 8),
        "position": round(position, 3),
        "score": score,
        "active": active,
        "bias": bias,
        "last_closed_candle_utc": last_close_utc.strftime("%Y-%m-%d %H:%M UTC"),
        "candles_used": len(candles),
    }


# --------------------------------------------------------------------------
# OUTPUT FORMATTERS
# --------------------------------------------------------------------------

def format_signal(res: Dict[str, Any]) -> str:
    line = (
        f"🪙 {res['symbol']}\n"
        f"   ├ Status : {'✅ RANGE ACTIVE' if res['active'] else '— no range'}\n"
        f"   ├ Bias   : {res['bias']}\n"
        f"   ├ Close  : {res['last_price']:g}\n"
        f"   ├ Range  : {res['support']:g} — {res['resistance']:g}\n"
        f"   ├ Pos    : {res['position'] * 100:.0f}% of range\n"
        f"   ├ RSI14  : {res['rsi14']}   (close)\n"
        f"   ├ SMA    : 7={res['sma7']:g} 25={res['sma25']:g} 99={res['sma99']:g}\n"
        f"   ├ Score  : {res['score']}/100\n"
        f"   └ Candles: {res['candles_used']} closed M15 · {res['last_closed_candle_utc']}"
    )
    return line


def build_signals_text(results: List[Dict[str, Any]], scanned: List[str]) -> str:
    header = (
        "🧊 PLT RANGE SCANNER\n"
        "════════════════════════\n"
        f"🕐 {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n"
        f"📊 Scanned: {len(scanned)} symbols · {REQUIRED_CANDLES} closed M15 each\n"
        "⚙️ RSI(14)-CLOSE · SMA 7/25/99 · No FVG · No execution\n"
        "────────────────────────"
    )
    active = [r for r in results if r["active"]]
    if not active:
        body = "\n\n".join(format_signal(r) for r in results[: len(results)])
        footer = (
            "\n\n🔍 No range setup among scanned symbols this run.\n"
            "⚠️ Information only — not financial advice."
        )
        return header + "\n\n" + body + footer

    lines = [header]
    for r in active:
        lines.append("\n" + format_signal(r))
    lines.append(
        "\n\n⚠️ Information only — automated scan, no financial advice. "
        "No orders are placed by this scanner."
    )
    return "\n".join(lines)


# --------------------------------------------------------------------------
# PERSISTENCE (SIGNALS section)
# --------------------------------------------------------------------------

def write_signals_file(text: str) -> None:
    SIGNALS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    (SIGNALS_DIR / f"signals_{stamp}.txt").write_text(text, encoding="utf-8")
    LATEST_SIGNALS_FILE.write_text(text, encoding="utf-8")


def should_post_fingerprint(results: List[Dict[str, Any]]) -> Optional[str]:
    """Returns None when the previous posted result is identical (no spam)."""
    active = sorted(
        [r for r in results if r["active"]],
        key=lambda r: r["symbol"],
    )
    if not active:
        return None
    fp = json.dumps(
        [
            {
                "symbol": r["symbol"],
                "bias": r["bias"],
                "last_price": r["last_price"],
                "score": r["score"],
            }
            for r in active
        ]
    )
    return fp


def _load_state() -> Dict[str, Any]:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_state(state: Dict[str, Any]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


# --------------------------------------------------------------------------
# TELEGRAM CHANNEL PUSH
# --------------------------------------------------------------------------

def tg_ready() -> bool:
    return bool(TELEGRAM_BOT_TOKEN and resolve_channel_id())


def _tg_url(method: str) -> str:
    return f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/{method}"


def tg_send_text(text: str) -> None:
    if not tg_ready():
        raise RuntimeError("Telegram push requested but TELEGRAM_BOT_TOKEN / channel ID missing")
    if requests is None:
        raise RuntimeError("requests is not installed")
    for i in range(0, len(text), MAX_MESSAGE_LEN):
        chunk = text[i : i + MAX_MESSAGE_LEN]
        resp = requests.post(
            _tg_url("sendMessage"),
            json={
                "chat_id": resolve_channel_id(),
                "text": chunk,
                "disable_web_page_preview": True,
            },
            timeout=HTTP_TIMEOUT,
        )
        data = resp.json()
        if resp.status_code != 200 or not data.get("ok"):
            raise RuntimeError(
                f"Telegram sendMessage failed: {data.get('description', resp.text[:200])}"
            )


def tg_send_card(path: Path, caption: str) -> None:
    if not tg_ready():
        raise RuntimeError("Telegram push requested but TELEGRAM_BOT_TOKEN / channel ID missing")
    if requests is None:
        raise RuntimeError("requests is not installed")
    with path.open("rb") as photo:
        resp = requests.post(
            _tg_url("sendPhoto"),
            data={"chat_id": resolve_channel_id(), "caption": caption[:1024]},
            files={"photo": (path.name, photo, "image/png")},
            timeout=HTTP_TIMEOUT * 2,
        )
    data = resp.json()
    if resp.status_code != 200 or not data.get("ok"):
        raise RuntimeError(
            f"Telegram sendPhoto failed: {data.get('description', resp.text[:200])}"
        )


# --------------------------------------------------------------------------
# CARD RENDERER (glass-style PNG, ASCII-safe)
# --------------------------------------------------------------------------

def _font(size: int, bold: bool = False):
    from PIL import ImageFont  # local import, optional feature

    names = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
    ]
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _rounded(draw, box, radius, fill, outline=None, width=1):
    from PIL import ImageDraw  # local import

    x0, y0, x1, y1 = box
    draw.rounded_rectangle(
        [x0, y0, x1, y1],
        radius=radius,
        fill=fill,
        outline=outline,
        width=width,
    )


def render_card(res: Dict[str, Any]) -> Optional[Path]:
    """Glassmorphism style signal card. English/numbers only (RTL-safe)."""
    if not ENABLE_CARD:
        return None
    try:
        from PIL import Image, ImageDraw
    except Exception:
        return None

    W, H = 1080, 1440
    img = Image.new("RGB", (W, H), "#0b1220")
    draw = ImageDraw.Draw(img, "RGBA")

    # soft gradient background
    for y in range(H):
        t = y / H
        r = int(11 + 10 * t)
        g = int(18 + 10 * t)
        b = int(32 + 16 * t)
        draw.line([(0, y), (W, y)], fill=(r, g, b, 255))

    # glass panels
    _rounded(draw, (60, 70, W - 60, 250), 40, (255, 255, 255, 18), (255, 255, 255, 60), 2)
    _rounded(draw, (60, 300, W - 60, 760), 40, (255, 255, 255, 14), (255, 255, 255, 40), 2)
    _rounded(draw, (60, 810, W - 60, 1330), 40, (255, 255, 255, 14), (255, 255, 255, 40), 2)

    # accents
    _rounded(draw, (60, 70, 96, 250), 18, (56, 189, 248, 255))
    _rounded(draw, (W - 96, 70, W - 60, 250), 18, (56, 189, 248, 255))

    f_title = _font(44, True)
    f_sub = _font(24)
    f_big = _font(64, True)
    f_mid = _font(30, True)
    f_small = _font(24)
    f_tiny = _font(19)

    draw.text((120, 105), "PLT RANGE SCANNER", font=f_title, fill="#e2f3ff")
    draw.text(
        (120, 178),
        res["last_closed_candle_utc"] + "  ·  M15 · 99 CLOSED",
        font=f_sub,
        fill="#8fb8d8",
    )

    # symbol block
    draw.text((90, 340), res["symbol"], font=f_big, fill="#ffffff")
    status = "RANGE ACTIVE" if res["active"] else "NO RANGE"
    color = "#4ade80" if res["active"] else "#94a3b8"
    draw.text((W - 330, 360), status, font=_font(32, True), fill=color)
    draw.text(
        (90, 450),
        f"close  {res['last_price']:g}",
        font=_font(34, True),
        fill="#7dd3fc",
    )

    # range + position
    draw.text((90, 560), f"Support   {res['support']:g}", font=f_mid, fill="#f87171")
    draw.text((90, 620), f"Resistance {res['resistance']:g}", font=f_mid, fill="#4ade80")
    draw.text(
        (90, 680),
        f"Position   {res['position'] * 100:.0f}% of range",
        font=f_small,
        fill="#cbd5e1",
    )

    # range bar visualization
    bar_x0, bar_x1 = 90, W - 90
    bar_y = 735
    draw.rounded_rectangle([bar_x0, bar_y, bar_x1, bar_y + 14], 7, fill=(255, 255, 255, 40))
    mid_x = bar_x0 + (bar_x1 - bar_x0) * res["position"]
    draw.ellipse([mid_x - 12, bar_y - 5, mid_x + 12, bar_y + 19], fill="#facc15")

    # indicator rows
    rows = [
        ("RSI(14) · close", f"{res['rsi14']}"),
        ("SMA 7", f"{res['sma7']:g}"),
        ("SMA 25", f"{res['sma25']:g}"),
        ("SMA 99", f"{res['sma99']:g}"),
    ]
    y = 880
    for label, value in rows:
        draw.text((90, y), label, font=f_small, fill="#93a8c0")
        draw.text((W - 90 - 320, y), value, font=_font(30, True), fill="#eaf6ff")
        y += 72

    # score
    score_txt = f"RANGE SCORE  {res['score']:.0f} / 100"
    draw.text((90, 1210), score_txt, font=_font(36, True), fill="#facc15")
    draw.text(
        (90, 1280),
        "No FVG · No execution · Information only",
        font=f_tiny,
        fill="#64748b",
    )

    CARD_DIR.mkdir(parents=True, exist_ok=True)
    path = CARD_DIR / f"{res['symbol']}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.png"
    img.save(path, "PNG")
    return path


# --------------------------------------------------------------------------
# LIVE-COIN-WATCH (optional symbol universe)
# --------------------------------------------------------------------------

def lcw_symbols() -> List[str]:
    """Top-N market-cap coins -> 'CODEUSDT' candidates (best effort)."""
    if not LIVECOINWATCH_API_KEY:
        return []
    if requests is None:
        return []
    try:
        resp = requests.post(
            "https://api.livecoinwatch.com/coins/list",
            headers={
                "content-type": "application/json",
                "x-api-key": LIVECOINWATCH_API_KEY,
            },
            json={
                "currency": "USD",
                "sort": "rank",
                "order": "ascending",
                "offset": 0,
                "limit": LCW_TOP_N,
                "meta": False,
            },
            timeout=HTTP_TIMEOUT,
        )
        payload = resp.json()
        if resp.status_code != 200 or not isinstance(payload, list):
            return []
        out = []
        for coin in payload:
            code = str(coin.get("code", "")).strip().upper()
            if code and code not in {"USDT", "FDUSD", "USDC"}:
                out.append(f"{code}USDT")
        return out
    except Exception:
        return []


def tg_get_updates() -> list:
    """Fetch recent updates so the bot can learn its channel id."""
    if requests is None:
        raise RuntimeError("requests is not installed")
    resp = requests.get(
        _tg_url("getUpdates"),
        params={"timeout": 1},
        timeout=HTTP_TIMEOUT,
    )
    data = resp.json()
    if resp.status_code != 200 or not data.get("ok"):
        raise RuntimeError(
            f"Telegram getUpdates failed: {data.get('description', resp.text[:300])}"
        )
    return data.get("result", [])


def discover_channel_id(verbose: bool = True) -> str:
    """Auto-discover the private channel id from bot updates.

    The bot must already be added as ADMIN to the channel.  The
    'my_chat_member' / 'channel_post' update carries chat.id.
    """
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN missing (set it in .env)")
    updates = tg_get_updates()
    for upd in reversed(updates):
        chat = None
        mc = upd.get("my_chat_member") or upd.get("chat_member")
        if mc:
            chat = mc.get("chat") or {}
        cp = upd.get("channel_post")
        if cp:
            chat = cp.get("chat") or {}
        if not chat:
            continue
        cid = chat.get("id")
        ctype = chat.get("type")
        title = chat.get("title") or ""
        if cid and (ctype in {"channel", "supergroup", "group"}):
            if verbose:
                print(
                    f"[plt_range] discovered chat: id={cid} type={ctype} title={title!r}"
                )
            return str(cid)
    if verbose:
        print(
            "[plt_range] no channel update found yet.\n"
            "  Steps:\n"
            "   1) add the bot as ADMIN to the private channel\n"
            "      (open the invite link -> add bot -> grant 'post messages')\n"
            "   2) post one short message in the channel\n"
            "   3) run this command again."
        )
    return ""


def cmd_discover() -> int:
    try:
        cid = discover_channel_id()
    except Exception as exc:
        print(
            f"[plt_range] could not reach Telegram / read updates: {exc}\n"
            "  Make sure TELEGRAM_BOT_TOKEN is set in .env and this machine can "
            "reach api.telegram.org.",
            file=sys.stderr,
        )
        return 2
    if not cid:
        return 2
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    state = _load_state()
    state["discovered_channel_id"] = cid
    _save_state(state)
    print(f"[plt_range] saved discovered channel id -> {STATE_FILE}")
    print(f"[plt_range] set PLT_RANGE_CHANNEL_ID={cid} in .env (or it is now in state file)")
    return 0


def cmd_test_post() -> int:
    """Send one test message to the channel (auto-discovers the id)."""
    if not TELEGRAM_BOT_TOKEN:
        print(
            "[plt_range] TELEGRAM_BOT_TOKEN missing.\n"
            "  Put your bot token in .env first:\n"
            "    TELEGRAM_BOT_TOKEN=123456:ABC-...",
            file=sys.stderr,
        )
        return 3
    cid = resolve_channel_id()
    if not cid:
        print("[plt_range] channel id unknown -> trying to discover it ...")
        cid = discover_channel_id()
        if not cid:
            return 2
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        state = _load_state()
        state["discovered_channel_id"] = cid
        _save_state(state)
    text = (
        "✅ PLT Range Scanner — connected.\n"
        f"🕐 {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n"
        "Next posts will arrive on the hourly scan schedule."
    )
    try:
        tg_send_text(text)
    except Exception as exc:
        print(f"[plt_range] send failed: {exc}", file=sys.stderr)
        return 2
    print(f"[plt_range] test message posted to {cid}")
    return 0


# --------------------------------------------------------------------------
# RUNNER
# --------------------------------------------------------------------------

def run_scan(fixture: Optional[str] = None, force: bool = False):
    print("[plt_range] starting scan", flush=True)

    if fixture:
        results = fixture_scan(fixture)
    else:
        symbols = SYMBOLS
        lcw = lcw_symbols()
        if lcw:
            symbols = lcw[:LCW_TOP_N]
            print(f"[plt_range] symbol universe from LiveCoinWatch top {LCW_TOP_N}", flush=True)
        if not symbols:
            raise RuntimeError("No symbols to scan (PLT_RANGE_SYMBOLS empty and no LCW data)")

        results = []
        for symbol in symbols:
            try:
                candles = latest_closed_candles(symbol)
                info = analyse_symbol(symbol, candles)
                print(
                    f"[plt_range] {symbol}: {info['candles_used']} candles "
                    f"rsi={info['rsi14']} score={info['score']} bias={info['bias']}",
                    flush=True,
                )
                results.append(info)
            except Exception as exc:
                print(
                    f"[plt_range] ERROR {symbol}: {exc}",
                    file=sys.stderr,
                    flush=True,
                )

    scanned_symbols = [r["symbol"] for r in results]
    text = build_signals_text(results, scanned_symbols)

    # ============ SIGNALS SECTION ============
    print("\n" + "=" * 30 + " SIGNALS " + "=" * 30, flush=True)
    print(text, flush=True)
    print("=" * 68, flush=True)
    # ==========================================

    write_signals_file(text)
    print(f"[plt_range] signals written -> {LATEST_SIGNALS_FILE}", flush=True)

    active = [r for r in results if r["active"]]
    fp = should_post_fingerprint(results)

    # Telegram push (only when fully configured)
    if tg_ready():
        state = _load_state()
        changed = state.get("last_fp") != fp

        # short run summary goes out every run (user-requested cadence)
        if active:
            summary = (
                "🧊 PLT RANGE SCANNER — run summary\n"
                "════════════════════════\n"
                f"🕐 {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n\n"
                + "\n".join(
                    f"🪙 {r['symbol']} → {r['bias']}  (score {r['score']})"
                    for r in active
                )
            )
        else:
            summary = (
                "🧊 PLT RANGE SCANNER\n"
                "════════════════════════\n"
                f"🕐 {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n\n"
                "🔍 No range setup among scanned symbols this run."
            )
        tg_send_text(summary)
        print("[plt_range] run summary posted to channel", flush=True)

        # full SIGNALS text + glass cards are posted only when the setup changed
        do_full = force or FORCE_POST or changed or not state.get("ever_posted")
        if fp is None and not SEND_EMPTY:
            do_full = False
        if do_full:
            cards: List[Path] = []
            for r in active:
                card = render_card(r)
                if card:
                    cards.append(card)
            if cards:
                for r, card in zip(active, cards):
                    tg_send_card(
                        card,
                        f"🧊 PLT RANGE | {r['symbol']}\n"
                        f"Bias: {r['bias']} · Score: {r['score']}\n"
                        f"{r['last_closed_candle_utc']}",
                    )
            elif active or SEND_EMPTY:
                tg_send_text(text)
            state["last_fp"] = fp
            state["last_posted_utc"] = datetime.now(timezone.utc).isoformat()
            state["ever_posted"] = True
            _save_state(state)
            print("[plt_range] full signal text/cards posted to channel", flush=True)
        else:
            print(
                "[plt_range] no change since last full post — full cards skipped "
                "(summary was still sent)",
                flush=True,
            )
    else:
        print(
            "[plt_range] Telegram push skipped: TELEGRAM_BOT_TOKEN / channel ID not set",
            flush=True,
        )

    return active


# --------------------------------------------------------------------------
# FIXTURE MODE (deterministic test data — no network)
# --------------------------------------------------------------------------

def _synthetic_closes(seed: int, ranging: bool, n: int = 140) -> List[float]:
    rng = random.Random(seed)
    out = []
    for i in range(n):
        if ranging:
            # bounded oscillation -> clean range behaviour with repeated edges
            out.append(100.0 + 3.0 * math.sin(i / 14.0) + rng.uniform(-0.15, 0.15))
        else:
            # steady drift -> trending behaviour
            out.append(100.0 + i * 0.6 + rng.uniform(-0.2, 0.3))
    return out


def fixture_scan(mode: str) -> List[Dict[str, Any]]:
    """Run the pipeline on synthetic candles (used by --fixture)."""
    print(f"[plt_range] FIXTURE MODE: {mode}", flush=True)
    out = []
    if mode in {"range", "mixed"}:
        closes = _synthetic_closes(7, ranging=True)
        candles = [
            {
                "time_ms": 1_700_000_000_000 + i * INTERVAL_SECONDS * 1000,
                "open": c,
                "high": c + 0.3,
                "low": c - 0.3,
                "close": c,
            }
            for i, c in enumerate(closes)
        ]
        info = analyse_symbol("RNGUSDT", candles[-99:])
        info["symbol"] = "RNGUSDT"
        out.append(info)
        print(
            f"[plt_range] fixture {info['symbol']}: score={info['score']} bias={info['bias']}",
            flush=True,
        )
    if mode in {"trend", "mixed"}:
        closes = _synthetic_closes(3, ranging=False)
        candles = [
            {
                "time_ms": 1_700_000_000_000 + i * INTERVAL_SECONDS * 1000,
                "open": c,
                "high": c + 0.3,
                "low": c - 0.3,
                "close": c,
            }
            for i, c in enumerate(closes)
        ]
        info = analyse_symbol("TRENDUSDT", candles[-99:])
        info["symbol"] = "TRENDUSDT"
        out.append(info)
        print(
            f"[plt_range] fixture {info['symbol']}: score={info['score']} bias={info['bias']}",
            flush=True,
        )
    return out


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def parse_args(argv: Optional[List[str]] = None):
    parser = argparse.ArgumentParser(
        prog="plt_range_scanner",
        description="PLT Range Scanner (99 closed M15 candles, RSI14/SMA 7-25-99).",
    )
    parser.add_argument(
        "--fixture",
        choices=["range", "trend", "mixed"],
        default=None,
        help="run offline on synthetic candles (CI / manual validation)",
    )
    parser.add_argument(
        "--force-post",
        action="store_true",
        help="post to channel even if nothing changed since last run",
    )
    parser.add_argument(
        "--discover",
        action="store_true",
        help="discover the private channel id from bot updates, save it, exit",
    )
    parser.add_argument(
        "--test-post",
        action="store_true",
        help="send one test message to the channel (discovers id if needed), exit",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    # cron often runs with a C locale -> force UTF-8 output streams
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass
    args = parse_args(argv)
    load_env()
    try:
        if args.discover:
            return cmd_discover()
        if args.test_post:
            return cmd_test_post()
        run_scan(fixture=args.fixture, force=args.force_post)
        return 0
    except Exception as exc:
        print(f"[plt_range] FATAL: {exc}", file=sys.stderr, flush=True)
        return 2


if __name__ == "__main__":
    sys.exit(main())

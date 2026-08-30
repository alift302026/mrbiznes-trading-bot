"""Final signal service: scan, store, caption. Human approval only — the
bot never places orders; this only renders suggestion cards."""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

DATA_DIR = Path(os.getenv("SIGNAL_DATA_DIR", "data"))
STORE_PATH = DATA_DIR / "latest_signals.json"

DEFAULT_SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "BNBUSDT", "DOGEUSDT",
    "ADAUSDT", "LINKUSDT", "AVAXUSDT", "DOTUSDT", "TRXUSDT", "LTCUSDT",
]


def watchlist() -> List[str]:
    raw = os.getenv("FINAL_SIGNAL_SYMBOLS", "")
    if raw.strip():
        return [s.strip().upper() for s in raw.split(",") if s.strip()]
    return list(DEFAULT_SYMBOLS)


def push_enabled() -> bool:
    return os.getenv("FINAL_SIGNALS_PUSH", "0") == "1"


def _load_store() -> Dict[str, Any]:
    try:
        return json.loads(STORE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {"signals": []}


def load_latest(limit: int = 10) -> List[Dict[str, Any]]:
    return list(_load_store().get("signals", []))[:limit]


def save_signals(signals: List[Dict[str, Any]]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    existing = _load_store().get("signals", [])
    seen = {f"{s['symbol']}|{s['direction']}|{s.get('decision_time')}" for s in existing}
    fresh = [
        s for s in signals
        if f"{s['symbol']}|{s['direction']}|{s.get('decision_time')}" not in seen
    ]
    merged = fresh + existing
    STORE_PATH.write_text(
        json.dumps({"signals": merged[:50]}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return fresh


def scan_all(timeout_note: bool = True) -> List[Dict[str, Any]]:
    """Run the engine over the whole watchlist (sync, network)."""
    from app.engines.signals.final_setup_engine import analyze_symbol_online

    out: List[Dict[str, Any]] = []
    for sym in watchlist():
        try:
            sig = analyze_symbol_online(sym)
            if sig:
                out.append(sig)
                logger.info("final-signal: %s %s score=%s", sym, sig["direction"], sig["confidence"])
        except Exception as exc:  # noqa: BLE001
            logger.warning("final-signal scan failed for %s: %s", sym, exc)
    return out


def _price(v: Any) -> str:
    try:
        x = float(v)
    except (TypeError, ValueError):
        return "—"
    if abs(x) >= 1000:
        return f"{x:,.2f}"
    if abs(x) >= 1:
        return f"{x:,.4f}"
    return f"{x:.6f}"


def build_caption_fa(signal: Dict[str, Any]) -> str:
    """Persian caption with WHY lines + honest risk framing (same style as
    the bot's signal section cards)."""
    emoji = "🟢" if signal.get("direction") == "LONG" else "🔴"
    pos_risk = signal.get("position_risk", "۱٪")
    lines = [
        "🎯 سیگنال نهایی مستر بیزنس — S4 Breakout & Retest",
        "",
        f"{emoji} {signal.get('direction', '—')}  |  🪙 {signal.get('symbol', '—')}",
        f"🏅 Grade: {signal.get('grade', '—')}  |  امتیاز: {signal.get('confidence', 0)}/100",
        "",
        "📍 نقشه معامله",
        f"ورود: {_price(signal.get('entry'))}",
        f"حد ضرر: {_price(signal.get('stop'))}",
        f"TP1: {_price(signal.get('target_1'))}  (۵۰٪، سپس حد ضرر روی سربه‌سر)",
        f"TP2: {_price(signal.get('target_2'))}",
        f"TP3: {_price(signal.get('target_3'))}  (اختیاری، برای رانر)",
        f"اهرم پیشنهادی: {signal.get('leverage', '—')} (ریسک هر معامله ≈ {pos_risk} سرمایه)",
        "",
        "✅ چرا این سیگنال؟",
    ]
    for r in (signal.get("reasons") or [])[:5]:
        lines.append(f"• {r}")
    lines.append("")
    lines.append("⚠️ ریسک‌ها")
    for r in (signal.get("risks") or [])[:3]:
        lines.append(f"• {r}")
    lines.extend(
        [
            "",
            f"⏱ زمان تریگر (UTC): {signal.get('decision_time', '—')}",
            "Data: XT Exchange",
            "",
            "هشدار: این صرفاً تحلیل و پیشنهاد است؛ باز/بستن معامله همیشه با خود شماست.",
        ]
    )
    return "\n".join(lines)


def render_card(signal: Dict[str, Any]):
    """Render the same graphical card used by the bot's signal section."""
    from app.services.signal_card_renderer import render_signal_card

    return render_signal_card(signal)

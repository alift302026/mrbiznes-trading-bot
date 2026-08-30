"""MrBiznes FINAL setup engine (S4 breakout-retest, research-validated).

Pipeline (per project rules):
MARKET DATA -> INDICATORS -> SETUP DETECTION -> CONFIRMATION
-> RISK ENGINE -> SIGNAL (dict) -> HUMAN APPROVAL (never auto-orders).

Research provenance: S4 breakout-retest was the strongest family in the
May-Jul 2026 xt 15m study (4 majors, fees+slippage, chrono walk-forward):
~65% OOS entry win-rate with rr1/rr2 = 1R/2R exits. Regime gating and
trailing exits were tested in v2/v3 and NOT adopted (no OOS improvement).
The engine ships in paper-tracking mode; forward validation comes first.

Pure pandas/numpy. Data inputs are DataFrames so the engine is fully
testable offline (research zips) and identical logic runs live on XT.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

# ----------------------------- indicators ---------------------------------


def _ema(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(span=n, adjust=False).mean()


def _atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    h, l, c = df["high"], df["low"], df["close"]
    tr = pd.concat(
        [(h - l), (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1
    ).max(axis=1)
    return tr.ewm(alpha=1 / n, adjust=False).mean()


def _adx(df: pd.DataFrame, n: int = 14) -> pd.Series:
    h, l, c = df["high"], df["low"], df["close"]
    up = h.diff()
    dn = -l.diff()
    plus_dm = np.where((up > dn) & (up > 0), up, 0.0)
    minus_dm = np.where((dn > up) & (dn > 0), dn, 0.0)
    tr = pd.concat(
        [(h - l), (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1
    ).max(axis=1)
    atr_ = tr.ewm(alpha=1 / n, adjust=False).mean()
    plus_di = 100 * pd.Series(plus_dm, index=df.index).ewm(
        alpha=1 / n, adjust=False
    ).mean() / atr_
    minus_di = 100 * pd.Series(minus_dm, index=df.index).ewm(
        alpha=1 / n, adjust=False
    ).mean() / atr_
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di + 1e-12)
    return dx.ewm(alpha=1 / n, adjust=False).mean()


def _rsi(s: pd.Series, n: int = 9) -> pd.Series:
    d = s.diff()
    gain = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    loss = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    rs = gain / (loss + 1e-12)
    return 100 - 100 / (1 + rs)


def _ut_bot(df: pd.DataFrame, key: float = 1.0, atr_n: int = 10) -> pd.Series:
    """UT Bot trailing-stop position (+1 long / -1 short), user's Pine spec."""
    src = df["close"]
    atr_ = _atr(df, atr_n) * key
    trail = np.zeros(len(df))
    pos = np.zeros(len(df))
    prev_trail = 0.0
    prev_pos = 0
    for i in range(len(df)):
        s = src.iloc[i]
        a = atr_.iloc[i]
        if np.isnan(a):
            trail[i] = s
            continue
        pc = src.iloc[i - 1] if i else s
        if s > prev_trail and pc > prev_trail:
            t = max(prev_trail, s - a)
        elif s < prev_trail and pc < prev_trail:
            t = min(prev_trail, s + a)
        elif s > prev_trail:
            t = s - a
        else:
            t = s + a
        if prev_pos <= 0 and s > t:
            p = 1
        elif prev_pos >= 0 and s < t:
            p = -1
        else:
            p = prev_pos
        trail[i] = t
        pos[i] = p
        prev_trail = t
        prev_pos = p
    return pd.Series(pos, index=df.index)


# ----------------------------- engine -------------------------------------

LEVEL_BARS = 40
RETEST_BARS = 8
BODY_MIN = 0.6
RELVOL_MIN = 1.2
ADX15_MIN = 16.0
ADXTREND_MIN = 18.0
RR1, RR2, RR3 = 1.0, 2.0, 3.0
FRESH_WITHIN = 6  # only emit signal if trigger inside last N bars


def _prepare(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["atr"] = _atr(out)
    out["relvol"] = out["volume"] / (out["volume"].rolling(100).mean() + 1e-12)
    out["adx"] = _adx(out)
    out["rsi9"] = _rsi(out["close"], 9)
    out["rsi14"] = _rsi(out["close"], 14)
    macd = _ema(out["close"], 12) - _ema(out["close"], 26)
    out["macd_hist"] = macd - _ema(macd, 9)
    out["ut"] = _ut_bot(out)
    return out


def analyze_candles(
    symbol: str,
    df15: pd.DataFrame,
    df1h: pd.DataFrame,
    df4h: pd.DataFrame,
) -> Optional[Dict[str, Any]]:
    """Detect the latest S4 LONG/SHORT signal. None if nothing fresh."""
    if len(df15) < LEVEL_BARS + RETEST_BARS + 15 or len(df4h) < 55:
        return None
    d15 = _prepare(df15)
    dxa = _adx(df4h)
    ema20 = _ema(df4h["close"], 20)
    ema50 = _ema(df4h["close"], 50)
    u1h = _ut_bot(df1h) if len(df1h) >= 15 else None

    c = d15["close"].values
    o = d15["open"].values
    hi = d15["high"].values
    lo = d15["low"].values
    rv = d15["relvol"].values
    a = d15["atr"].values
    ax = d15["adx"].values

    best: Optional[Dict[str, Any]] = None
    n = len(d15)
    scan_from = max(LEVEL_BARS + 5, n - 200)
    for b in range(scan_from, n - RETEST_BARS - 1):
        if np.isnan(a[b]) or rv[b] < RELVOL_MIN or ax[b] < ADX15_MIN:
            continue
        lvl_hi = hi[b - LEVEL_BARS : b].max()
        lvl_lo = lo[b - LEVEL_BARS : b].min()
        rng = max(hi[b] - lo[b], 1e-12)
        body = abs(c[b] - o[b])
        if body < BODY_MIN * rng:
            continue
        side = 0
        if c[b] > lvl_hi:
            side = 1
        elif c[b] < lvl_lo:
            side = -1
        if side == 0:
            continue
        level = lvl_hi if side == 1 else lvl_lo
        for r in range(b + 1, min(b + 1 + RETEST_BARS, n - 1)):
            touched = lo[r] <= level + 0.3 * a[r] if side == 1 else hi[r] >= level - 0.3 * a[r]
            held = c[r] > level if side == 1 else c[r] < level
            if not (touched and held):
                continue
            entry = c[r]
            if side == 1:
                sl = min(lo[b : r + 1]) - 0.5 * a[r]
            else:
                sl = max(hi[b : r + 1]) + 0.5 * a[r]
            risk = abs(entry - sl)
            if risk <= 0 or risk / entry > 0.05:
                break
            best = {
                "side": side,
                "decision_i": r,
                "break_i": b,
                "level": float(level),
                "entry": float(entry),
                "sl": float(sl),
                "atr": float(a[r]),
            }
            break

    if best is None:
        return None
    if best["decision_i"] < n - 1 - FRESH_WITHIN:
        return None  # stale: never emit

    side = best["side"]
    entry, sl = best["entry"], best["sl"]
    risk = abs(entry - sl)
    tp1 = entry + side * RR1 * risk
    tp2 = entry + side * RR2 * risk
    tp3 = entry + side * RR3 * risk

    # ---- confluence scoring (0-100, explainable) ----
    t4h_trend = 1 if ema20.iloc[-1] > ema50.iloc[-1] and df4h["close"].iloc[-1] > ema50.iloc[-1] else (
        -1 if ema20.iloc[-1] < ema50.iloc[-1] and df4h["close"].iloc[-1] < ema50.iloc[-1] else 0
    )
    adx4 = float(dxa.iloc[-1])
    adx15 = float(ax[best["decision_i"]])
    relv = float(rv[best["break_i"]])
    rsi15 = float(d15["rsi9"].iloc[best["decision_i"]])
    ut15 = int(d15["ut"].iloc[best["decision_i"]])
    ut1h = int(u1h.iloc[-1]) if u1h is not None and len(u1h) else 0
    body_pct = body = float(
        abs(c[best["break_i"]] - o[best["break_i"]])
        / max(hi[best["break_i"]] - lo[best["break_i"]], 1e-12)
    )

    score = 0
    parts: Dict[str, int] = {}
    parts["structure_4h"] = 25 if t4h_trend == side else (10 if t4h_trend == 0 else 0)
    parts["confirm_ut"] = 20 if (ut15 == side and ut1h == side) else (12 if ut15 == side else 0)
    parts["volume"] = 15 if relv >= 1.8 else (10 if relv >= 1.4 else 6)
    parts["adx"] = 15 if (adx4 >= ADXTREND_MIN and adx15 >= 22) else (9 if adx15 >= 22 else 4)
    parts["breakout_quality"] = 15 if body_pct >= 0.75 else (10 if body_pct >= 0.65 else 6)
    parts["rsi_context"] = 10 if (side == 1 and rsi15 > 50 or side == -1 and rsi15 < 50) else 4
    score = int(sum(parts.values()))
    if score < 60:
        return None  # no forced signals

    grade = "A+" if score >= 85 else ("A" if score >= 75 else "A-")
    direction = "LONG" if side == 1 else "SHORT"

    sl_pct = risk / entry
    lev = int(np.clip(round(0.012 / max(sl_pct, 1e-6)), 2, 10))
    lev_lo = max(2, lev - 2)
    lev_txt = f"{lev}x" if lev == lev_lo else f"{lev_lo}x–{lev}x"
    dd = d15.index[best["decision_i"]]

    reasons: List[str] = []
    if t4h_trend == side:
        if side == 1:
            reasons.append("ساختار ۴ ساعته هم‌جهت است (EMA20 بالای EMA50 و قیمت بالای EMA50)")
        else:
            reasons.append("ساختار ۴ ساعته هم‌جهت است (EMA20 زیر EMA50 و قیمت زیر EMA50)")
    if ut15 == side and ut1h == side:
        reasons.append("تأیید UT Bot در ۱۵ دقیقه و ۱ ساعته")
    elif ut15 == side:
        reasons.append("تأیید UT Bot در ۱۵ دقیقه")
    reasons.append(f"شکست سطح {best['level']:.6g} با بدنه {body_pct*100:.0f}% و حجم {relv:.1f} برابر میانگین")
    if adx4 >= ADXTREND_MIN:
        reasons.append(f"روند فعال است (ADX 4H = {adx4:.0f})")
    reasons.append("ورود پس از ریتست موفق سطح شکسته (تأیید نگه‌داشت)")

    risks: List[str] = [
        "کلوز ۱۵ دقیقه‌ای پشت سطح شکسته، کل ستاپ را باطل می‌کند.",
        "بک‌تست ۳ ماه: ورود حدود ۶۵٪ برد جهت‌دار داشته؛ معامله همیشه تصمیم شماست.",
    ]
    if t4h_trend != side:
        risks.append("روند ۴ ساعته تأیید کامل نمی‌کند — با حجم کمتر.")

    return {
        "symbol": symbol,
        "direction": direction,
        "grade": grade,
        "confidence": score,
        "score_parts": parts,
        "entry_trigger": "BREAK-RETEST",
        "entry": float(entry),
        "stop": float(sl),
        "target_1": float(tp1),
        "target_2": float(tp2),
        "target_3": float(tp3),
        "leverage": lev_txt,
        "timeframes": {
            "15m": {
                "sma_state": "UP" if t4h_trend == 1 else ("DOWN" if t4h_trend == -1 else "FLAT"),
                "rsi": round(float(d15["rsi14"].iloc[best["decision_i"]]), 1),
                "macd_histogram": round(float(d15["macd_hist"].iloc[best["decision_i"]]), 4),
                "atr_percent": round(best["atr"] / entry * 100, 2),
                "dow": "UT-LONG" if ut15 == 1 else "UT-SHORT",
                "volume": {"state": f"{relv:.1f}x avg"},
            },
            "1h": {"dow": "UP" if ut1h == 1 else ("DOWN" if ut1h == -1 else "—")},
            "4h": {"dow": "UP" if t4h_trend == 1 else ("DOWN" if t4h_trend == -1 else "FLAT")},
        },
        "reasons": reasons,
        "risks": risks,
        "setup": "S4_BREAKOUT_RETEST",
        "decision_time": str(dd),
        "atr": best["atr"],
    }


def resample_df(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    agg = {
        "open": "first", "high": "max", "low": "min",
        "close": "last", "volume": "sum",
    }
    return df.resample(rule).agg(agg).dropna()


def analyze_symbol_online(symbol: str) -> Optional[Dict[str, Any]]:
    """Live path: fetch closed candles from XT and analyze."""
    from app.engines.signals.xt_signal_provider import fetch_candles

    def _to_df(candles):
        rows = {
            "open": [float(x["open"]) for x in candles],
            "high": [float(x["high"]) for x in candles],
            "low": [float(x["low"]) for x in candles],
            "close": [float(x["close"]) for x in candles],
            "volume": [float(x.get("volume", x.get("q", 0)) or 0) for x in candles],
        }
        idx = pd.to_datetime([x["time"] for x in candles], unit="ms", utc=True)
        df = pd.DataFrame(rows, index=idx).sort_index()
        return df

    df15 = _to_df(fetch_candles(symbol, "15m", limit=320))
    df1h = _to_df(fetch_candles(symbol, "1h", limit=60))
    df4h = _to_df(fetch_candles(symbol, "4h", limit=80))
    return analyze_candles(symbol, df15, df1h, df4h)

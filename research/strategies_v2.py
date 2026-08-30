"""V2: S4 & S2 with quality filters (session/swing/fvg-dedup)."""
import numpy as np
import pandas as pd
from ind import rel_volume, atr
from features import detect_fvgs, fvg_state_at, swing_points

SESSION_HOURS = set(range(12, 21))  # 12:00-20:00 UTC (London/NY)


def _sess_ok(df, i):
    h = df.index[i].hour
    return h in SESSION_HOURS


def s4_v2(df, p):
    sigs = []
    c = df["close"].values; o = df["open"].values
    lo = df["low"].values; hi = df["high"].values
    rv = df["relvol"].values; a = df["atr"].values; adxv = df["adx"].values
    N, RETEST = 40, 8
    for b in range(N + 5, len(df) - RETEST - 1):
        if np.isnan(a[b]) or rv[b] < p["relvol"]:
            continue
        lvl_hi = hi[b - N: b].max(); lvl_lo = lo[b - N: b].min()
        # level must be a real swing extreme (structure, not noise)
        sw_hi = swing_points(pd.Series(hi[: b]), 3, "high")
        sw_lo = swing_points(pd.Series(lo[: b]), 3, "low")
        rng = max(hi[b] - lo[b], 1e-12); body = abs(c[b] - o[b])
        if c[b] > lvl_hi and body >= 0.6 * rng and adxv[b] >= 16:
            if not (len(sw_hi) and abs(hi[sw_hi[-1]] - lvl_hi) < 0.25 * a[b]):
                continue
            for r in range(b + 1, min(b + 1 + RETEST, len(df) - 1)):
                if not _sess_ok(df, r):
                    continue
                if lo[r] <= lvl_hi + 0.3 * a[r] and c[r] > lvl_hi:
                    entry = c[r]
                    sl = min(lo[b: r + 1]) - 0.5 * a[r]
                    rr = abs(entry - sl)
                    if rr <= 0: continue
                    sigs.append({"decision_i": r, "side": 1, "entry_mode": "next_open",
                                 "limit_price": None, "fill_deadline": None,
                                 "sl": sl, "tp1": entry + 1.0 * rr, "tp2": entry + 3.0 * rr,
                                 "strategy": "S4_V2", "note": "v2: سطح سوئینگ + سشن + تریل"})
                    break
        elif c[b] < lvl_lo and body >= 0.6 * rng and adxv[b] >= 16:
            if not (len(sw_lo) and abs(lo[sw_lo[-1]] - lvl_lo) < 0.25 * a[b]):
                continue
            for r in range(b + 1, min(b + 1 + RETEST, len(df) - 1)):
                if not _sess_ok(df, r):
                    continue
                if hi[r] >= lvl_lo - 0.3 * a[r] and c[r] < lvl_lo:
                    entry = c[r]
                    sl = max(hi[b: r + 1]) + 0.5 * a[r]
                    rr = abs(sl - entry)
                    if rr <= 0: continue
                    sigs.append({"decision_i": r, "side": -1, "entry_mode": "next_open",
                                 "limit_price": None, "fill_deadline": None,
                                 "sl": sl, "tp1": entry - 1.0 * rr, "tp2": entry - 3.0 * rr,
                                 "strategy": "S4_V2", "note": "v2: سطح سوئینگ + سشن + تریل"})
                    break
    return sigs


def s2_v2(df, p):
    sigs = []
    fvgs = detect_fvgs(df)
    c = df["close"].values; cf = df["cf1h"].values
    st = df["st4h"].values; a = df["atr"].values; rv = df["relvol"].values
    used = set()
    for i in range(60, len(df) - 13):
        if st[i] == 0 or np.isnan(a[i]) or not _sess_ok(df, i):
            continue
        bull, bear = fvg_state_at(df, fvgs, i, max_age=24)
        f = bull if st[i] == 1 else bear
        if f is None or cf[i] != st[i] or f["bar"] in used:
            continue
        gap = f["top"] - f["bottom"]
        if gap < 0.25 * a[i]:  # meaningful gap only
            continue
        if rv[f["bar"]] < p["relvol"]:
            continue
        side = st[i]
        mid = (f["top"] + f["bottom"]) / 2.0
        sl = (f["bottom"] - 0.5 * a[i]) if side == 1 else (f["top"] + 0.5 * a[i])
        r = abs(mid - sl)
        if r <= 0:
            continue
        used.add(f["bar"])
        sigs.append({"decision_i": i, "side": side, "entry_mode": "limit",
                     "limit_price": (f["top"] * 0.65 + f["bottom"] * 0.35) if side == -1 else (f["bottom"] * 0.65 + f["top"] * 0.35),
                     "fill_deadline": i + 12,
                     "sl": sl, "tp1": mid + side * 1.0 * r, "tp2": mid + side * 3.0 * r,
                     "strategy": "S2_V2", "note": "v2: گپ معنادار + تازه + یکبارگراستفاده + سشن"})
    return sigs


STRATS_V2 = {"S2_V2": s2_v2, "S4_V2": s4_v2}

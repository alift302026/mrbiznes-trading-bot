"""The 5 candidate 15m setups. All decisions use bar i CLOSE only.
Signal dict: decision_i, side(+1 long/-1 short), entry_mode
('next_open'|'limit'), limit_price, fill_deadline, sl, tp1, tp2,
strategy, note."""
import numpy as np
import pandas as pd

from ind import (
    adx, atr, ema, macd, rel_volume, rsi, stoch_rsi,
    supertrend, ut_bot,
)
from features import (
    detect_fvgs, fvg_state_at, htf_trend_state, range_state,
    resample_ohlcv,
)


def prepare(df15: pd.DataFrame) -> pd.DataFrame:
    df = df15.copy()
    df["atr"] = atr(df, 14)
    df["ema20"] = ema(df["close"], 20)
    df["ema50"] = ema(df["close"], 50)
    df["ema200"] = ema(df["close"], 200)
    df["adx"] = adx(df, 14)
    df["rsi"] = rsi(df["close"], 14)
    df["relvol"] = rel_volume(df, 20)
    m, s, h = macd(df["close"])
    df["macdh"] = h
    k, d = stoch_rsi(df["close"])
    df["stk"] = k
    ub, us, upos = ut_bot(df)
    df["ut_buy"] = ub
    df["ut_sell"] = us

    df4h = resample_ohlcv(df, "4h")
    state4h = htf_trend_state(df4h)
    df["st4h"] = state4h.reindex(df.index, method="ffill").fillna(0)

    df1h = resample_ohlcv(df, "1h")
    e1h = ema(df1h["close"], 20)
    c1h = df1h["close"]
    conf1h = np.sign(c1h - e1h).fillna(0)
    df["cf1h"] = conf1h.reindex(df.index, method="ffill").fillna(0)
    return df


PARAMS = {
    "atr_mul": 1.5,
    "rr1": 1.0,
    "rr2": 2.0,
    "relvol": 1.3,
    "adx_min": 22,
}

GRID = {
    "atr_mul": [1.25, 1.5, 2.0],
    "rr2": [2.0, 3.0],
    "relvol": [1.2, 1.5],
}


def _sig(i, side, sl, tp1, tp2, strategy, note,
         entry_mode="next_open", limit_price=None,
         fill_deadline=None):
    return {
        "decision_i": i,
        "side": side,
        "entry_mode": entry_mode,
        "limit_price": limit_price,
        "fill_deadline": fill_deadline,
        "sl": sl,
        "tp1": tp1,
        "tp2": tp2,
        "strategy": strategy,
        "note": note,
    }


def _risk_ok(entry, sl, tp2, side, min_rr=1.5):
    r = abs(entry - sl)
    if r <= 0:
        return False
    reward = (tp2 - entry) * side
    return reward / r >= min_rr * 0.999  # to TP2 at least ~min_rr


def s1_trend_pullback(df, p):
    sigs = []
    c = df["close"].values
    o = df["open"].values
    lo = df["low"].values
    hi = df["high"].values
    e20 = df["ema20"].values
    e50 = df["ema50"].values
    e200 = df["ema200"].values
    adxv = df["adx"].values
    rsiv = df["rsi"].values
    rv = df["relvol"].values
    a = df["atr"].values
    st = df["st4h"].values
    utb = df["ut_buy"].values
    uts = df["ut_sell"].values
    for i in range(50, len(df) - 1):
        if np.isnan(a[i]) or adxv[i] < p["adx_min"]:
            continue
        if rv[i] < p["relvol"]:
            continue
        r = p["atr_mul"] * a[i]
        if st[i] == 1 and c[i] > e200[i] and e20[i] > e50[i]:
            pulled = lo[i] <= e20[i] and c[i] > e50[i]
            if pulled and utb[i] and 40 <= rsiv[i] <= 68:
                sl = c[i] - r
                sigs.append(
                    _sig(i, 1, sl, c[i] + p["rr1"] * r,
                         c[i] + p["rr2"] * r, "S1_TREND_PB",
                         "پول‌بک به EMA20/50 در روند صعودی + تریگر UT")
                )
        elif st[i] == -1 and c[i] < e200[i] and e20[i] < e50[i]:
            pulled = hi[i] >= e20[i] and c[i] < e50[i]
            if pulled and uts[i] and 32 <= rsiv[i] <= 60:
                sl = c[i] + r
                sigs.append(
                    _sig(i, -1, sl, c[i] - p["rr1"] * r,
                         c[i] - p["rr2"] * r, "S1_TREND_PB",
                         "پول‌بک به EMA20/50 در روند نزولی + تریگر UT")
                )
    return sigs


def s2_fvg_continuation(df, p):
    sigs = []
    fvgs = detect_fvgs(df)
    c = df["close"].values
    cf = df["cf1h"].values
    st = df["st4h"].values
    a = df["atr"].values
    rv = df["relvol"].values
    upos = df["ut_sell"].values  # noqa
    for i in range(60, len(df) - 13):
        if st[i] == 0 or np.isnan(a[i]):
            continue
        bull, bear = fvg_state_at(df, fvgs, i)
        f = bull if st[i] == 1 else bear
        if f is None or cf[i] != st[i]:
            continue
        if rv[f["bar"]] < p["relvol"]:
            continue
        mid = (f["top"] + f["bottom"]) / 2.0
        side = st[i]
        buf = 0.5 * a[i]
        if side == 1:
            sl = f["bottom"] - buf
            entry = mid
        else:
            sl = f["top"] + buf
            entry = mid
        r = abs(entry - sl)
        tp1 = entry + side * p["rr1"] * r
        tp2 = entry + side * max(p["rr2"], 1.5) * r
        if not _risk_ok(entry, sl, tp2, side):
            continue
        sigs.append(
            _sig(i, side, sl, tp1, tp2, "S2_FVG_CONT",
                 "ورود از میانه FVG هم‌جهت با ساختار 4H",
                 entry_mode="limit",
                 limit_price=entry,
                 fill_deadline=i + 12)
        )
    return sigs


def s3_range_reversal(df, p):
    sigs = []
    c = df["close"].values
    o = df["open"].values
    lo = df["low"].values
    hi = df["high"].values
    k = df["stk"].values
    adxv = df["adx"].values
    a = df["atr"].values
    for i in range(90, len(df) - 1):
        if np.isnan(a[i]) or adxv[i] >= 25:
            continue
        is_r, rlo, rhi, decay = range_state(df, i)
        if not is_r or decay > 1.05:
            continue
        width = rhi - rlo
        zone = 0.2 * width
        mid = (rhi + rlo) / 2.0
        rebound_up = c[i] >= lo[i] + 0.5 * (hi[i] - lo[i])
        rebound_dn = c[i] <= hi[i] - 0.5 * (hi[i] - lo[i])
        if lo[i] <= rlo + zone and rebound_up and k[i] < 25:
            entry = c[i]
            sl = rlo - 0.5 * a[i]
            tp2 = rhi - 0.15 * width
            tp1 = mid
            if _risk_ok(entry, sl, tp2, 1, min_rr=1.2):
                sigs.append(
                    _sig(i, 1, sl, tp1, tp2, "S3_RANGE_REV",
                         "برگشت از کف رنج با کاهش حجم"))
        elif hi[i] >= rhi - zone and rebound_dn and k[i] > 75:
            entry = c[i]
            sl = rhi + 0.5 * a[i]
            tp2 = rlo + 0.15 * width
            tp1 = mid
            if _risk_ok(entry, sl, tp2, -1, min_rr=1.2):
                sigs.append(
                    _sig(i, -1, sl, tp1, tp2, "S3_RANGE_REV",
                         "برگشت از سقف رنج با کاهش حجم"))
    return sigs


def s4_breakout_retest(df, p):
    sigs = []
    c = df["close"].values
    o = df["open"].values
    lo = df["low"].values
    hi = df["high"].values
    rv = df["relvol"].values
    a = df["atr"].values
    adxv = df["adx"].values
    N, RETEST = 40, 8
    for b in range(N + 5, len(df) - RETEST - 1):
        if np.isnan(a[b]) or rv[b] < p["relvol"]:
            continue
        lvl_hi = hi[b - N: b].max()
        lvl_lo = lo[b - N: b].min()
        rng = max(hi[b] - lo[b], 1e-12)
        body = abs(c[b] - o[b])
        if c[b] > lvl_hi and body >= 0.6 * rng and adxv[b] >= 16:
            for r in range(b + 1, min(b + 1 + RETEST, len(df) - 1)):
                if lo[r] <= lvl_hi + 0.3 * a[r] and c[r] > lvl_hi:
                    entry = c[r]
                    sl = min(lo[b: r + 1]) - 0.5 * a[r]
                    rr = abs(entry - sl)
                    tp1 = entry + 1.5 * rr
                    tp2 = entry + max(p["rr2"], 3.0) * rr
                    if _risk_ok(entry, sl, tp2, 1):
                        sigs.append(
                            _sig(r, 1, sl, tp1, tp2, "S4_BRK_RETEST",
                                 "شکست + ریتست موفق سقف"))
                    break
        elif c[b] < lvl_lo and body >= 0.6 * rng and adxv[b] >= 16:
            for r in range(b + 1, min(b + 1 + RETEST, len(df) - 1)):
                if hi[r] >= lvl_lo - 0.3 * a[r] and c[r] < lvl_lo:
                    entry = c[r]
                    sl = max(hi[b: r + 1]) + 0.5 * a[r]
                    rr = abs(sl - entry)
                    tp1 = entry - 1.5 * rr
                    tp2 = entry - max(p["rr2"], 3.0) * rr
                    if _risk_ok(entry, sl, tp2, -1):
                        sigs.append(
                            _sig(r, -1, sl, tp1, tp2, "S4_BRK_RETEST",
                                 "شکست + ریتست موفق کف"))
                    break
    return sigs


def s5_momentum_flip(df, p):
    sigs = []
    c = df["close"].values
    e200 = df["ema200"].values
    mh = df["macdh"].values
    rsiv = df["rsi"].values
    adxv = df["adx"].values
    a = df["atr"].values
    st = df["st4h"].values
    df4h = resample_ohlcv(df, "4h")
    d4, _ = supertrend(df4h)
    st_dir = d4.reindex(df.index, method="ffill").fillna(0).values
    for i in range(50, len(df) - 1):
        if np.isnan(a[i]) or adxv[i] < 20:
            continue
        cross_up = mh[i] > 0 and mh[i - 1] <= 0
        cross_dn = mh[i] < 0 and mh[i - 1] >= 0
        r = p["atr_mul"] * a[i]
        if (cross_up and st_dir[i] == 1 and st[i] != -1
                and rsiv[i] > 50 and c[i] > e200[i]):
            sigs.append(
                _sig(i, 1, c[i] - r, c[i] + p["rr1"] * r,
                     c[i] + p["rr2"] * r, "S5_MOM_FLIP",
                     "کراس MACD هم‌جهت Supertrend 4H"))
        elif (cross_dn and st_dir[i] == -1 and st[i] != 1
                and rsiv[i] < 50 and c[i] < e200[i]):
            sigs.append(
                _sig(i, -1, c[i] + r, c[i] - p["rr1"] * r,
                     c[i] - p["rr2"] * r, "S5_MOM_FLIP",
                     "کراس MACD نزولی هم‌جهت Supertrend 4H"))
    return sigs


STRATEGIES = {
    "S1_TREND_PB": s1_trend_pullback,
    "S2_FVG_CONT": s2_fvg_continuation,
    "S3_RANGE_REV": s3_range_reversal,
    "S4_BRK_RETEST": s4_breakout_retest,
    "S5_MOM_FLIP": s5_momentum_flip,
}

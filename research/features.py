"""Market-structure features: resampling, swings, FVG, range detection."""
import numpy as np
import pandas as pd


def resample_ohlcv(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    agg = {
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "volume": "sum",
    }
    out = (
        df.resample(rule).agg(agg).dropna(subset=["close"]).copy()
    )
    return out


def swing_points(s: pd.Series, k: int = 3, kind: str = "high"):
    """Confirmed swing points (need k bars on each side).
    Returns index positions of confirmed swings."""
    v = s.values
    n = len(v)
    idx = []
    for i in range(k, n - k):
        w = v[i - k: i + k + 1]
        if kind == "high" and v[i] == w.max() and (w < v[i]).sum() == 2 * k:
            idx.append(i)
        if kind == "low" and v[i] == w.min() and (w > v[i]).sum() == 2 * k:
            idx.append(i)
    return np.array(idx, dtype=int)


def htf_trend_state(df4h: pd.DataFrame, lookback_swings: int = 6, k: int = 3):
    """Bullish if recent confirmed swings make HH+HL; bearish LH+LL;
    else 0. Computed per-bar using only past confirmed swings."""
    dir_arr = np.zeros(len(df4h), dtype=int)
    highs = df4h["high"].values
    lows = df4h["low"].values
    for i in range(2 * k + 2, len(df4h)):
        hh = swing_points(pd.Series(highs[: i - k + 1]), k, "high")
        ll = swing_points(pd.Series(lows[: i - k + 1]), k, "low")
        state = 0
        if len(hh) >= 2 and len(ll) >= 2:
            h1, h2 = highs[hh[-2]], highs[hh[-1]]
            l1, l2 = lows[ll[-2]], lows[ll[-1]]
            need = lookback_swings
            if h2 > h1 and l2 > l1:
                state = 1
            elif h2 < h1 and l2 < l1:
                state = -1
            dir_arr[i] = state if need else state
    return pd.Series(dir_arr, index=df4h.index)


def detect_fvgs(df: pd.DataFrame):
    """Return list of dicts for every FVG. Bullish: low[i] > high[i-2];
    gap zone = (high[i-2], low[i]); confirmed when candle i closes.
    index i = creation bar (3rd candle). zone uses completed candles only."""
    highs = df["high"].values
    lows = df["low"].values
    fvgs = []
    for i in range(2, len(df)):
        if lows[i] > highs[i - 2]:
            fvgs.append(
                {
                    "bar": i,
                    "side": 1,
                    "top": lows[i],
                    "bottom": highs[i - 2],
                }
            )
        elif highs[i] < lows[i - 2]:
            fvgs.append(
                {
                    "bar": i,
                    "side": -1,
                    "top": lows[i - 2],
                    "bottom": highs[i],
                }
            )
    return fvgs


def fvg_state_at(df, fvgs, i, max_age=60):
    """For decision bar i: most recent unmitigated FVG per side
    created at bar <= i. Mitigation = price traded fully through zone."""
    best = {1: None, -1: None}
    for f in reversed(fvgs):
        b = f["bar"]
        if b > i:
            continue
        if i - b > max_age:
            break  # list is ascending; older ones all too old
        if best[1] is not None and best[-1] is not None:
            break
        lows = df["low"].values
        highs = df["high"].values
        filled = False
        for j in range(b + 1, i + 1):
            if f["side"] == 1 and lows[j] <= f["bottom"]:
                filled = True
                break
            if f["side"] == -1 and highs[j] >= f["top"]:
                filled = True
                break
        if not filled:
            if (
                best[f["side"]] is None
                or b > best[f["side"]]["bar"]
            ):
                best[f["side"]] = f
    return best[1], best[-1]


def range_state(df, i, window=60, max_width_atr=6.0, touch_tol=0.35):
    """Detect ranging regime at bar i using last `window` closed bars.
    Returns (is_range, low, high, vol_decay) or (False,...).
    Range: several touches both sides + width not huge + volume decay."""
    if i < window + 20:
        return False, np.nan, np.nan, 1.0
    w = df.iloc[i - window: i + 1]
    hi = w["high"].max()
    lo = w["low"].min()
    mid = (hi + lo) / 2.0
    atr_now = w["atr"].iloc[-1]
    if np.isnan(atr_now) or atr_now <= 0:
        return False, np.nan, np.nan, 1.0
    width = (hi - lo)
    if width > max_width_atr * atr_now:
        return False, np.nan, np.nan, 1.0
    tol = touch_tol * width
    highs = w["high"].values
    lows = w["low"].values
    touch_hi = int((highs >= hi - tol).sum())
    touch_lo = int((lows <= lo + tol).sum())
    if touch_hi < 3 or touch_lo < 3:
        return False, np.nan, np.nan, 1.0
    vol = w["volume"].values
    half = len(vol) // 2
    vol_decay = (
        vol[half:].mean() / vol[:half].mean()
        if vol[:half].mean() > 0
        else 1.0
    )
    return True, float(lo), float(hi), float(vol_decay)

"""Indicator library (no look-ahead; values at bar i use bars <= i)."""
import numpy as np
import pandas as pd


def ema(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(span=n, adjust=False, min_periods=n).mean()


def sma(s: pd.Series, n: int) -> pd.Series:
    return s.rolling(n, min_periods=n).mean()


def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    """Wilder ATR."""
    h, l, c = df["high"], df["low"], df["close"]
    pc = c.shift(1)
    tr = pd.concat(
        [(h - l), (h - pc).abs(), (l - pc).abs()], axis=1
    ).max(axis=1)
    return tr.ewm(alpha=1.0 / n, adjust=False, min_periods=n).mean()


def rsi(s: pd.Series, n: int = 14) -> pd.Series:
    """Wilder RSI."""
    d = s.diff()
    up = d.clip(lower=0.0)
    dn = (-d).clip(lower=0.0)
    ru = up.ewm(alpha=1.0 / n, adjust=False, min_periods=n).mean()
    rd = dn.ewm(alpha=1.0 / n, adjust=False, min_periods=n).mean()
    rs = ru / rd.replace(0.0, np.nan)
    return (100.0 - 100.0 / (1.0 + rs)).fillna(100.0)


def macd(s: pd.Series, fast=12, slow=26, sig=9):
    m = ema(s, fast) - ema(s, slow)
    signal = ema(m, sig)
    return m, signal, m - signal


def adx(df: pd.DataFrame, n: int = 14) -> pd.Series:
    h, l, c = df["high"], df["low"], df["close"]
    up = h.diff()
    dn = -l.diff()
    pdm = np.where((up > dn) & (up > 0), up, 0.0)
    ndm = np.where((dn > up) & (dn > 0), dn, 0.0)
    a = atr(df, n)
    pdi = 100 * pd.Series(pdm, index=df.index).ewm(
        alpha=1.0 / n, adjust=False, min_periods=n
    ).mean() / a
    ndi = 100 * pd.Series(ndm, index=df.index).ewm(
        alpha=1.0 / n, adjust=False, min_periods=n
    ).mean() / a
    dx = 100 * (pdi - ndi).abs() / (pdi + ndi).replace(0, np.nan)
    return dx.ewm(alpha=1.0 / n, adjust=False, min_periods=n).mean()


def stoch_rsi(s: pd.Series, n=14, k=3, d=3):
    r = rsi(s, n)
    lo = r.rolling(n, min_periods=n).min()
    hi = r.rolling(n, min_periods=n).max()
    st = (r - lo) / (hi - lo).replace(0, np.nan)
    k_line = st.rolling(k, min_periods=k).mean() * 100
    d_line = k_line.rolling(d, min_periods=d).mean()
    return k_line, d_line


def supertrend(df, n=10, mult=3.0):
    """Returns (direction, st_line). direction: 1=bull, -1=bear."""
    a = atr(df, n)
    hl2 = (df["high"] + df["low"]) / 2.0
    up = hl2 + mult * a
    dn = hl2 - mult * a
    close = df["close"].values
    up = up.values
    dn = dn.values
    final_up = np.full(len(df), np.nan)
    final_dn = np.full(len(df), np.nan)
    direction = np.zeros(len(df), dtype=int)
    for i in range(1, len(df)):
        final_up[i] = (
            up[i]
            if (up[i] < final_up[i - 1] or close[i - 1] > final_up[i - 1])
            else final_up[i - 1]
        ) if not np.isnan(up[i]) else np.nan
        final_dn[i] = (
            dn[i]
            if (dn[i] > final_dn[i - 1] or close[i - 1] < final_dn[i - 1])
            else final_dn[i - 1]
        ) if not np.isnan(dn[i]) else np.nan
        if close[i] > (final_up[i - 1] if not np.isnan(final_up[i - 1]) else -np.inf):
            direction[i] = 1
        elif close[i] < (final_dn[i - 1] if not np.isnan(final_dn[i - 1]) else np.inf):
            direction[i] = -1
        else:
            direction[i] = direction[i - 1]
    return (
        pd.Series(direction, index=df.index),
        pd.Series(
            np.where(direction == 1, final_dn, final_up), index=df.index
        ),
    )


def ut_bot(df, key=1.0, atr_n=10):
    """UT Bot Alerts port (Pine v4, Heikin Ashi off, closed candles).
    Returns (buy_flip, sell_flip, pos) boolean Series + position."""
    src = df["close"].values
    nloss = (key * atr(df, atr_n)).values
    n = len(df)
    stop = np.zeros(n)
    pos = np.zeros(n, dtype=int)
    for i in range(1, n):
        prev = stop[i - 1]
        if src[i] > prev and src[i - 1] > prev:
            stop[i] = max(prev, src[i] - nloss[i])
        elif src[i] < prev and src[i - 1] < prev:
            stop[i] = min(prev, src[i] + nloss[i])
        else:
            stop[i] = src[i] - nloss[i] if src[i] > prev else src[i] + nloss[i]
        if src[i - 1] < prev and src[i] > prev:
            pos[i] = 1
        elif src[i - 1] > prev and src[i] < prev:
            pos[i] = -1
        else:
            pos[i] = pos[i - 1]
    pos_s = pd.Series(pos, index=df.index)
    buy = (pos_s == 1) & (pos_s.shift(1) != 1)
    sell = (pos_s == -1) & (pos_s.shift(1) != -1)
    return buy.fillna(False), sell.fillna(False), pos_s


def rel_volume(df, n=20) -> pd.Series:
    v = df["volume"]
    return v / v.rolling(n, min_periods=n).mean()

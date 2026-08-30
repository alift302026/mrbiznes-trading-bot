"""Event-driven backtester: closed-candle decisions, next-open entries,
conservative intrabar SL-first rule, fees+slippage, partial TP exits."""
import numpy as np
import pandas as pd

FEE_SIDE = 0.001       # 0.10% per side
SLIP_SIDE = 0.0003     # 0.03% slippage per side


def simulate(df, signals):
    """Return list of trade dicts with r_multiple."""
    o = df["open"].values
    hi = df["high"].values
    lo = df["low"].values
    c = df["close"].values
    n = len(df)
    trades = []
    for s in signals:
        side = s["side"]
        if s["entry_mode"] == "next_open":
            ei = s["decision_i"] + 1
            if ei >= n:
                continue
            entry = o[ei]
        else:  # limit fill
            entry = s["limit_price"]
            ei = None
            for j in range(s["decision_i"] + 1,
                           min(s["fill_deadline"] + 1, n)):
                touched = lo[j] <= entry <= hi[j]
                if touched:
                    ei = j
                    break
                # invalidation if SL crossed before fill
                if side == 1 and lo[j] <= s["sl"]:
                    break
                if side == -1 and hi[j] >= s["sl"]:
                    break
            if ei is None:
                continue  # never filled -> no trade
        sl = s["sl"]
        risk = abs(entry - sl)
        if risk <= 0:
            continue
        tp1, tp2 = s["tp1"], s["tp2"]
        r_total = 0.0
        frac = 1.0
        be = False
        exit_i = None
        for j in range(ei, n):
            # entry-bar conservatism: SL checked before TP
            sl_eff = entry if be else sl
            hit_sl = (lo[j] <= sl_eff) if side == 1 else (hi[j] >= sl_eff)
            hit_tp1 = (hi[j] >= tp1) if side == 1 else (lo[j] <= tp1)
            hit_tp2 = (hi[j] >= tp2) if side == 1 else (lo[j] <= tp2)
            if frac == 1.0 and hit_sl:
                r_total -= 1.0
                exit_i = j
                break
            if frac == 1.0 and hit_tp1:
                r_partial = frac * 0.5
                r_total += 0.5 * (abs(tp1 - entry) / risk)
                frac = 0.5
                be = True
                if hit_tp2:  # same bar also tp2
                    r_total += 0.5 * (abs(tp2 - entry) / risk)
                    exit_i = j
                    frac = 0.0
                    break
                continue
            if frac == 0.5:
                if hit_sl:
                    exit_i = j
                    frac = 0.0
                    break  # BE -> 0R on remainder
                if hit_tp2:
                    r_total += 0.5 * (abs(tp2 - entry) / risk)
                    exit_i = j
                    frac = 0.0
                    break
        if frac > 0:  # end of data: close at last close
            r_total += frac * ((c[n - 1] - entry) * side / risk)
            exit_i = n - 1
        # costs in R terms
        cost_r = (2 * (FEE_SIDE + SLIP_SIDE) * entry) / risk
        r_net = r_total - cost_r
        trades.append({
            "strategy": s["strategy"],
            "side": side,
            "entry_i": ei,
            "exit_i": exit_i,
            "r": r_net,
            "note": s["note"],
        })
    return trades


def metrics(trades):
    if not trades:
        return {"trades": 0}
    r = np.array([t["r"] for t in trades], dtype=float)
    wins = r[r > 0]
    losses = r[r <= 0]
    pf = (wins.sum() / abs(losses.sum())) if losses.size and losses.sum() != 0 else (
        float("inf") if wins.size else 0.0)
    cum = np.cumsum(r)
    peak = np.maximum.accumulate(cum) if len(cum) else np.array([0])
    dd = (peak - cum)
    maxdd = float(dd.max()) if len(dd) else 0.0
    std = r.std(ddof=1) if len(r) > 1 else 0.0
    downside = r[r < 0]
    dstd = downside.std(ddof=1) if len(downside) > 1 else 0.0
    longs = r[[t["side"] == 1 for t in trades]]
    shorts = r[[t["side"] == -1 for t in trades]]

    def wr(x):
        return float((x > 0).mean() * 100) if len(x) else None

    return {
        "trades": int(len(r)),
        "win_rate": wr(r),
        "profit_factor": float(pf) if pf != float("inf") else 999.0,
        "expectancy_r": float(r.mean()),
        "avg_r": float(r.mean()),
        "max_dd_r": maxdd,
        "sharpe_like": float(r.mean() / std * np.sqrt(len(r))) if std > 0 else 0.0,
        "sortino_like": float(r.mean() / dstd * np.sqrt(len(r))) if dstd > 0 else 0.0,
        "long_wr": wr(longs),
        "short_wr": wr(shorts),
        "total_r": float(r.sum()),
    }


def split_chrono(trades, df_len, ratios=(0.6, 0.2, 0.2)):
    b1 = int(df_len * ratios[0])
    b2 = int(df_len * (ratios[0] + ratios[1]))
    out = {"train": [], "val": [], "oos": []}
    for t in trades:
        i = t["entry_i"]
        if i is None:
            continue
        if i < b1:
            out["train"].append(t)
        elif i < b2:
            out["val"].append(t)
        else:
            out["oos"].append(t)
    return out


def walk_forward(trades, df_len, folds=3):
    """Anchored folds: each fold tests on the next chronological slice."""
    res = []
    bounds = np.linspace(0, df_len, folds * 2 + 1).astype(int)
    for f in range(folds):
        lo_b = bounds[2 * f + 1]
        hi_b = bounds[2 * f + 2]
        seg = [t for t in trades
               if t["entry_i"] is not None and lo_b <= t["entry_i"] < hi_b]
        m = metrics(seg)
        res.append({"fold": f + 1, **m})
    return res

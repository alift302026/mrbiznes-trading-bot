"""V2 exit engine: 70% out at TP1 (1R), 30% chandelier-trail toward TP2."""
import numpy as np
from backtest import FEE_SIDE, SLIP_SIDE

def simulate_v2(df, signals):
    o = df["open"].values; hi = df["high"].values
    lo = df["low"].values; c = df["close"].values
    av = df["atr"].values if "atr" in df.columns else None
    n = len(df); trades = []
    for s in signals:
        side = s["side"]
        if s["entry_mode"] == "next_open":
            ei = s["decision_i"] + 1
            if ei >= n: continue
            entry = o[ei]
        else:
            entry = s["limit_price"]; ei = None
            for j in range(s["decision_i"] + 1, min(s["fill_deadline"] + 1, n)):
                if lo[j] <= entry <= hi[j]:
                    ei = j; break
                if side == 1 and lo[j] <= s["sl"]: break
                if side == -1 and hi[j] >= s["sl"]: break
            if ei is None: continue
        sl = s["sl"]; risk = abs(entry - sl)
        if risk <= 0: continue
        tp1, tp2 = s["tp1"], s["tp2"]
        r_total = 0.0; frac = 1.0; be_trail = None; peak = entry; done = False
        exit_i = None
        for j in range(ei, n):
            sl_eff = sl if be_trail is None else max(sl, be_trail) if side == 1 else min(sl, be_trail)
            hit_sl = (lo[j] <= sl_eff) if side == 1 else (hi[j] >= sl_eff)
            hit_tp1 = (hi[j] >= tp1) if side == 1 else (lo[j] <= tp1)
            hit_tp2 = (hi[j] >= tp2) if side == 1 else (lo[j] <= tp2)
            if frac == 1.0 and hit_sl:
                r_total = -1.0; exit_i = j; done = True; break
            if frac == 1.0 and hit_tp1:
                r_total += 0.7 * (abs(tp1 - entry) / risk)
                frac = 0.3
                peak = hi[j] if side == 1 else lo[j]
                if hit_tp2:
                    r_total += 0.3 * (abs(tp2 - entry) / risk); exit_i = j; frac = 0.0; done = True; break
                continue
            if frac == 0.3:
                a = av[j] if av is not None and not np.isnan(av[j]) else risk
                if side == 1:
                    peak = max(peak, hi[j]); be_trail = peak - 1.0 * a
                    if lo[j] <= max(entry, be_trail):
                        exit_i = j; frac = 0.0; done = True; break
                    if hit_tp2:
                        r_total += 0.3 * 3.0; exit_i = j; frac = 0.0; done = True; break
                else:
                    peak = min(peak, lo[j]); be_trail = peak + 1.0 * a
                    if hi[j] >= min(entry, be_trail):
                        exit_i = j; frac = 0.0; done = True; break
                    if hit_tp2:
                        r_total += 0.3 * 3.0; exit_i = j; frac = 0.0; done = True; break
        if frac > 0:
            r_total += frac * ((c[n - 1] - entry) * side / risk)
            exit_i = n - 1
        cost_r = (2 * (FEE_SIDE + SLIP_SIDE) * entry) / risk
        trades.append({"strategy": s["strategy"], "side": side,
                       "entry_i": ei, "exit_i": exit_i, "r": r_total - cost_r,
                       "note": s["note"]})
    return trades

import json, sys
sys.path.insert(0, "/home/user/research")
from run_research import load_klines, PARAMS
from strategies import prepare, s4_breakout_retest, s2_fvg_continuation
from strategies_v2 import SESSION_HOURS
from backtest_v2 import simulate_v2
from backtest import metrics, split_chrono, walk_forward

def session_only(sigs, df):
    return [s for s in sigs if df.index[s["decision_i"]].hour in SESSION_HOURS]

data = load_klines()
res = {}
for sid, fn in [("S4_classic_v2exit", s4_breakout_retest), ("S2_classic_v2exit", s2_fvg_continuation)]:
    tot_n = 0; wsum = 0.0; esum = 0.0
    for sym, df in data.items():
        dfp = prepare(df)
        sigs = session_only(fn(dfp, PARAMS), dfp)
        tr = simulate_v2(dfp, sigs)
        parts = split_chrono(tr, len(dfp))
        o = metrics(parts["oos"])
        t0 = metrics(parts["train"])
        print(f"{sid} {sym}: sig={len(sigs)} trainN={t0.get('trades')} trainWR={t0.get('win_rate')} oosN={o.get('trades')} oosWR={o.get('win_rate')} oosEXP={o.get('expectancy_r')} oosPF={o.get('profit_factor')}")
        if o.get("trades"):
            tot_n += o["trades"]; wsum += o["win_rate"]*o["trades"]; esum += o["expectancy_r"]*o["trades"]
    if tot_n:
        print(f">>> {sid} AGG: n={tot_n} WR={wsum/tot_n:.1f}% EXP={esum/tot_n:+.3f}R")

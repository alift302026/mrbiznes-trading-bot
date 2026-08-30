import json, os, sys
sys.path.insert(0, "/home/user/research")
from run_research import load_klines, PARAMS
from strategies import prepare
from strategies_v2 import STRATS_V2
from backtest_v2 import simulate_v2
from backtest import metrics, split_chrono, walk_forward

data = load_klines()
out = {}
for sym, df in data.items():
    dfp = prepare(df)
    for sid, fn in STRATS_V2.items():
        sigs = fn(dfp, PARAMS)
        tr = simulate_v2(dfp, sigs)
        parts = split_chrono(tr, len(dfp))
        agg = {}
        row = {"signals": len(sigs),
               "train": metrics(parts["train"]),
               "oos": metrics(parts["oos"]),
               "wf": walk_forward(tr, len(dfp))}
        out.setdefault(sid, {})[sym] = row
        o = row["oos"]
        print(f"{sid} {sym}: sig={len(sigs)} oosN={o.get('trades')} oosWR={o.get('win_rate')} oosEXP={o.get('expectancy_r')} oosPF={o.get('profit_factor')}")
json.dump(out, open("/home/user/research/out/metrics_v2.json", "w"), default=str, indent=2)
print("WROTE metrics_v2.json")

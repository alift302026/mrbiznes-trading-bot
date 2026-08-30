"""MrBiznes 15M research runner.
Reads kline CSV/ZIPs from /home/user/uploads (or ./data), then:
- prepares features per symbol
- runs 5 strategies with tiny param grids tuned ONLY on train split
- evaluates val + OOS once, walk-forward, sensitivity
- writes out/report_fa.md, out/metrics.json, out/strategies_spec.json
"""
import itertools
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backtest import metrics, simulate, split_chrono, walk_forward
from strategies import GRID, PARAMS, STRATEGIES, prepare

DATA_DIRS = ["/home/user/uploads", "/home/user/research/data"]
OUT = "/home/user/research/out"


def load_klines():
    """Load binance-format monthly kline zips/csvs. Returns
    {symbol: 15m DataFrame(tz-utc index)}."""
    frames = {}
    for d in DATA_DIRS:
        if not os.path.isdir(d):
            continue
        for fn in sorted(os.listdir(d)):
            if not ("15m" in fn and (fn.endswith(".zip") or fn.endswith(".csv"))):
                continue
            path = os.path.join(d, fn)
            sym = fn.split("-")[0]
            try:
                tmp = pd.read_csv(
                    path, header=None,
                    names=["open_time", "open", "high", "low", "close",
                           "volume", "close_time", "qv", "trades",
                           "tbv", "tqv", "ignore"],
                    usecols=[0, 1, 2, 3, 4, 5],
                )
                if not np.issubdtype(tmp["open"].dtype, np.number):
                    tmp = pd.read_csv(path, usecols=[0, 1, 2, 3, 4, 5])
                    tmp.columns = ["open_time", "open", "high", "low",
                                   "close", "volume"]
                raw = tmp["open_time"].astype("int64")
                unit = "us" if int(raw.iloc[0]) > 10 ** 14 else "ms"
                tmp["ts"] = pd.to_datetime(raw, unit=unit, utc=True)
                tmp = tmp.set_index("ts")[["open", "high", "low",
                                           "close", "volume"]].astype(float)
                tmp = tmp[~tmp.index.duplicated(keep="first")]
                frames.setdefault(sym, []).append(tmp)
                print(f"loaded {fn}: {len(tmp)} rows")
            except Exception as e:  # noqa
                print(f"skip {fn}: {e}")
    out = {}
    for sym, parts in frames.items():
        df = pd.concat(parts).sort_index()
        df = df[~df.index.duplicated(keep="first")]
        out[sym] = df
    return out


def grid_iter(grid):
    keys = sorted(grid.keys())
    for combo in itertools.product(*(grid[k] for k in keys)):
        yield dict(zip(keys, combo))


def evaluate_symbol(df, sigs_all_train_mode):
    """Returns trades list for full series."""
    return simulate(df, sigs_all_train_mode)


def main():
    os.makedirs(OUT, exist_ok=True)
    data = load_klines()
    if not data:
        print("WAITING_FOR_DATA: put *15m* kline zips in /home/user/uploads")
        sys.exit(2)

    report = {"symbols": {}, "strategies": {}}
    for sym, df in data.items():
        print(f"\n=== {sym}: {len(df)} 15m bars "
              f"({df.index[0]} .. {df.index[-1]}) ===")
        dfp = prepare(df)
        report["symbols"][sym] = {
            "bars": int(len(df)),
            "from": str(df.index[0]),
            "to": str(df.index[-1]),
        }
        for sid, fn in STRATEGIES.items():
            best = None
            # ---- tune on TRAIN only ----
            for p in grid_iter(GRID):
                params = {**PARAMS, **p}
                sigs = fn(dfp, params)
                tr = simulate(dfp, sigs)
                parts = split_chrono(tr, len(dfp))
                mt = metrics(parts["train"])
                if mt["trades"] < 8:
                    continue
                score = mt["profit_factor"] * min(mt["trades"], 60)
                if best is None or score > best[0]:
                    best = (score, params, sigs, tr)
            if best is None:
                report["strategies"].setdefault(sid, {})[sym] = {
                    "status": "NO_VALID_PARAMS_ON_TRAIN"}
                continue
            _, params, sigs, trades = best
            parts = split_chrono(trades, len(dfp))
            row = {
                "params": params,
                "signals": len(sigs),
                "train": metrics(parts["train"]),
                "val": metrics(parts["val"]),
                "oos": metrics(parts["oos"]),
                "walk_forward": walk_forward(trades, len(dfp)),
            }
            # sensitivity: bump each tuned param one step, re-run once
            sens = {}
            for k in GRID:
                vals = GRID[k]
                cur = vals.index(params[k]) if params[k] in vals else -1
                if cur == -1:
                    continue
                nb = vals[min(cur + 1, len(vals) - 1)]
                if nb == params[k]:
                    continue
                p2 = {**params, k: nb}
                tr2 = simulate(dfp, fn(dfp, p2))
                parts2 = split_chrono(tr2, len(dfp))
                sens[k] = metrics(parts2["train"]).get("profit_factor")
            row["sensitivity_train_pf"] = sens
            report["strategies"].setdefault(sid, {})[sym] = row
            o = row["oos"]
            print(f"{sid}: p={params} sig={len(sigs)} "
                  f"trainPF={row['train'].get('profit_factor')} "
                  f"oosN={o.get('trades')} oosWR={o.get('win_rate')}")

    with open(os.path.join(OUT, "metrics.json"), "w") as f:
        json.dump(report, f, ensure_ascii=False, indent=2,
                  default=str)
    print("\nwrote out/metrics.json")


if __name__ == "__main__":
    main()

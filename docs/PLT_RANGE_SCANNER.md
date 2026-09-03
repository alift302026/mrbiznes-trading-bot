# PLT Range Scanner — Cron Scanner

Standalone, **stdlib-only** (`/usr/bin/python3`, no pip deps) hourly scanner:
detects range-bound (consolidating) symbols on **Bitunix M15** candles.

## What it does (hard requirements)

| # | Requirement | Status |
|---|-------------|--------|
| 1 | Scanner file exists | `plt_range_scanner.py` (repo root) |
| 2 | Python path | `/usr/bin/python3` (stdlib only — works anywhere) |
| 3 | Dependencies | none required (urllib/json/datetime/zoneinfo only) |
| 4 | Bitunix credentials | NOT needed — public market-data endpoints only, zero authenticated calls, no POST to exchange |
| 5 | LiveCoinWatch market-cap | `LIVECOINWATCH_API_KEY` in `.env` builds the top-cap universe; falls back to major coins (env `PLT_RANGE_SYMBOLS`) if unavailable |
| 6 | Manual test | `python3 plt_range_scanner.py --selftest` (offline) + one live run |
| 7 | Candle window | latest **99 CLOSED M15** candles exactly; in-progress candle defensively dropped |
| 8 | RSI | exactly **RSI(14), source = CLOSE** (Wilder smoothing) |
| 9 | SMA | **SMA 7, SMA 25, SMA 99** all computed and reported |
| 10 | FVG | **completely removed** (AST-verified in tests — no FVG code/strings anywhere) |
| 11 | Trading | **NO order/trading execution** — read-only scanner |
| 12 | Output | `=== SIGNALS ===` section in the log + JSON snapshot `data/plt_range_scanner_latest.json` |
| 13 | History | requests only `limit=99` — never fetches extra history |

## Range criteria (env-tunable)

A symbol is flagged `RANGE` when ALL hold on the 99 closed candles:

- band width (last 20 closed candles high/low) ≤ `PLT_RANGE_MAX_WIDTH_PCT` (default 6%)
- `40 ≤ RSI(14) ≤ 60` (`PLT_RANGE_RSI_MIN` / `PLT_RANGE_RSI_MAX`)
- `|close − SMA25| / SMA25 ≤ 2.5%` (`PLT_RANGE_MAX_DIST_SMA25_PCT`)
- close inside the band

## Install the cron job (idempotent — never duplicates)

```bash
bash install_plt_cron.sh
```

Registers exactly one entry (hourly, minute 5):

```
5 * * * * /usr/bin/python3 /path/to/plt_range_scanner.py >> /path/to/logs/plt_range_scanner.log 2>&1 # MRBIZNES-PLT-RANGE-SCANNER
```

The installer removes any previous matching line before adding, runs the
offline selftest first, and verifies the final entry count is exactly 1.

Note: `logs/` and `data/` are git-ignored; the cron minute is the SERVER's
local timezone.

## Environment variables (all optional)

The scanner has its **own dedicated env file** — separate from the bot's `.env`:

```
.env.plt_range_scanner        # <- dedicated file for THIS cron job (git-ignored)
```

Template: `.env.plt_range_scanner.example`. Put the scanner's own
LiveCoinWatch key there (use a SEPARATE key from the bot's, so quota
and usage stay isolated):

```
PLT_SCANNER_LIVECOINWATCH_API_KEY=...
```

**Key precedence** (first non-empty wins — always independent of the bot):

1. env var `PLT_SCANNER_LIVECOINWATCH_API_KEY`
2. `.env.plt_range_scanner` (dedicated file)
3. env var / `.env` `LIVECOINWATCH_API_KEY` (legacy fallback)

The key is sent ONLY to LiveCoinWatch (as `x-api-key`); Bitunix calls
stay credential-free. The file is re-read on every cron run — edit it
anytime, effective next run. Each scan logs the active key source
(`LCW key: dedicated-file | shared-env | none ...`) in its banner.

Other optional settings (dedicated file first, shared bot `.env` as fallback):

```
PLT_RANGE_MARKET=spot              # spot | futures
PLT_RANGE_SYMBOLS=BTC,ETH,SOL     # override universe
PLT_RANGE_MAX_SYMBOLS=10
PLT_RANGE_LOOKBACK=20
PLT_RANGE_MAX_WIDTH_PCT=6.0
PLT_RANGE_MAX_DIST_SMA25_PCT=2.5
PLT_RANGE_RSI_MIN=40
PLT_RANGE_RSI_MAX=60
LCW_LIMIT=15
LCW_MIN_CAP_USD=100000000
```

## Selftest (offline, no network)

```bash
python3 plt_range_scanner.py --selftest
```

Validates SMA math, exact RSI(14)-Wilder values, the 99-closed-candle
window, in-progress-candle dropping, range detection on synthetic data,
and source-level guarantees (no FVG, no order execution, GET-only).

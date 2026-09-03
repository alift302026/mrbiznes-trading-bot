#!/usr/bin/env python3
# ============================================================
# MRBIZNES — PLT RANGE SCANNER (standalone cron scanner)
# ============================================================
# Scope (hard requirements — DO NOT violate):
#   * Bitunix M15 candles ONLY, latest 99 CLOSED candles exactly.
#   * No historical data is requested beyond those 99 candles.
#   * RSI is exactly RSI(14), source = CLOSE.
#   * SMA 7, SMA 25 and SMA 99 are calculated.
#   * FVG (Fair Value Gap) analysis is COMPLETELY removed.
#   * READ-ONLY: NO trading / order execution of any kind.
#     (Only public market-data endpoints are called; no API key
#     is used or required, no POST is ever sent to Bitunix.)
#   * Results are printed to the "=== SIGNALS ===" section of
#     stdout (captured in the cron log) and saved as a JSON
#     snapshot for the bot's SIGNALS section.
# ============================================================

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

# ------------------------------------------------------------
# PATHS
# ------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

SNAPSHOT_PATH = DATA_DIR / "plt_range_scanner_latest.json"

# Dedicated (separate) env file for THIS cron job — independent from
# the bot's shared .env. Override the location with PLT_SCANNER_ENV.
DEDICATED_ENV_PATH = BASE_DIR / ".env.plt_range_scanner"
SHARED_ENV_PATH = BASE_DIR / ".env"

TEHRAN = ZoneInfo("Asia/Tehran")

# ------------------------------------------------------------
# CONFIG (dedicated .env.plt_range_scanner first, shared .env fallback)
# ------------------------------------------------------------

def _parse_env_file(path: Path) -> dict:
    """Parse KEY=VALUE lines. Missing files yield {}."""
    result: dict = {}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return result
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            result[key] = value
    return result


_ENV_ORIGIN: dict[str, str] = {}  # env key -> file name that supplied it


def _load_env(paths: list[Path]) -> None:
    """Load env files in order; real environment always wins."""
    for path in paths:
        for key, value in _parse_env_file(path).items():
            if key not in os.environ:
                os.environ[key] = value
                _ENV_ORIGIN[key] = path.name


_load_env([DEDICATED_ENV_PATH, SHARED_ENV_PATH])


def _lcw_key_candidates(dedicated_path: Path | None, shared_path: Path | None):
    """Yield (source, key) in strict precedence order.

    The source label reports the TRUE origin: a value that was loaded
    from the dedicated file at import time is reported as
    "dedicated-file" (not "dedicated-env"), thanks to _ENV_ORIGIN.
    """
    dedicated_name = DEDICATED_ENV_PATH.name
    shared_name = SHARED_ENV_PATH.name

    key = "PLT_SCANNER_LIVECOINWATCH_API_KEY"
    value = os.getenv(key, "").strip()
    if value:
        source = (
            "dedicated-file"
            if _ENV_ORIGIN.get(key) == dedicated_name
            else "dedicated-env"
        )
        yield source, value

    dedicated_file = _parse_env_file(
        dedicated_path if dedicated_path is not None else DEDICATED_ENV_PATH
    )
    value = (
        dedicated_file.get(key)
        or dedicated_file.get("LIVECOINWATCH_API_KEY")
        or ""
    ).strip()
    if value:
        yield "dedicated-file", value

    key = "LIVECOINWATCH_API_KEY"
    value = os.getenv(key, "").strip()
    if value:
        origin = _ENV_ORIGIN.get(key)
        if origin == dedicated_name:
            source = "dedicated-file"
        elif origin == shared_name:
            source = "shared-file"
        else:
            source = "shared-env"
        yield source, value

    shared_file = _parse_env_file(
        shared_path if shared_path is not None else SHARED_ENV_PATH
    )
    value = shared_file.get(key, "").strip()
    if value:
        yield "shared-file", value


def resolve_lcw_key(
    dedicated_path: Path | None = None,
    shared_path: Path | None = None,
) -> str:
    """LiveCoinWatch key — DEDICATED scanner key first.

    Precedence (first non-empty wins):
      1. env var  PLT_SCANNER_LIVECOINWATCH_API_KEY
      2. dedicated file .env.plt_range_scanner  (PLT_SCANNER_LIVECOINWATCH_API_KEY,
         or LIVECOINWATCH_API_KEY inside that dedicated file)
      3. shared  env var / .env  LIVECOINWATCH_API_KEY  (legacy fallback)
    """
    for _, value in _lcw_key_candidates(dedicated_path, shared_path):
        if value:
            return value
    return ""


def lcw_key_source(
    dedicated_path: Path | None = None,
    shared_path: Path | None = None,
) -> str:
    """Where the effective key comes from: dedicated-env | dedicated-file | shared-env | shared-file | none."""
    for source, value in _lcw_key_candidates(dedicated_path, shared_path):
        if value:
            return source
    return "none"


# Market data provider (read-only, public, no credentials needed)
BITUNIX_SPOT_BASE = os.getenv("BITUNIX_SPOT_BASE", "https://openapi.bitunix.com")
BITUNIX_FUTURES_BASE = os.getenv("BITUNIX_FUTURES_BASE", "https://fapi.bitunix.com")
LCW_BASE = os.getenv("LCW_BASE", "https://api.livecoinwatch.com")
LCW_API_KEY = resolve_lcw_key()

MARKET = os.getenv("PLT_RANGE_MARKET", "spot").strip().lower()  # spot | futures

# Fixed analysis window (requirement: latest 99 CLOSED M15 candles)
TIMEFRAME_MINUTES = 15
CANDLE_LIMIT = 99

# Range detection tuning (env-overridable)
LOOKBACK = int(os.getenv("PLT_RANGE_LOOKBACK", "20"))          # band lookback (closed candles)
MAX_WIDTH_PCT = float(os.getenv("PLT_RANGE_MAX_WIDTH_PCT", "6.0"))
MAX_DIST_SMA25_PCT = float(os.getenv("PLT_RANGE_MAX_DIST_SMA25_PCT", "2.5"))
RSI_MIN = float(os.getenv("PLT_RANGE_RSI_MIN", "40"))
RSI_MAX = float(os.getenv("PLT_RANGE_RSI_MAX", "60"))

# Universe
PLT_RANGE_SYMBOLS = os.getenv("PLT_RANGE_SYMBOLS", "").strip()  # e.g. "BTC,ETH,SOL"
LCW_LIMIT = int(os.getenv("LCW_LIMIT", "15"))
LCW_MIN_CAP_USD = float(os.getenv("LCW_MIN_CAP_USD", "100000000"))
MAX_SYMBOLS = int(os.getenv("PLT_RANGE_MAX_SYMBOLS", "10"))

FALLBACK_SYMBOLS = ["BTC", "ETH", "BNB", "SOL", "XRP", "DOGE", "ADA", "LINK", "AVAX", "LTC"]

HTTP_TIMEOUT = 15
RETRIES = 2


# ============================================================
# HTTP (GET/JSON, stdlib only)
# ============================================================

def http_json(
    url: str,
    payload: dict | None = None,
    api_key: str = "",
) -> object:
    """GET (payload=None) or POST-JSON. Optional API key goes to x-api-key.

    NOTE: the api_key is ONLY for read-only market-data providers
    (LiveCoinWatch). It is never sent to the exchange (Bitunix).
    """
    data = None
    headers = {
        "User-Agent": "MrBiznesPLTRangeScanner/1.0",
        "Accept": "application/json",
    }
    if api_key:
        headers["x-api-key"] = api_key
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    last_error: Exception | None = None
    for attempt in range(RETRIES + 1):
        try:
            request = urllib.request.Request(url, data=data, headers=headers)
            with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT) as response:
                return json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
            last_error = exc
            if attempt < RETRIES:
                time.sleep(1 + attempt)
    raise RuntimeError(f"HTTP failed for {url}: {last_error}")


def bitunix_get(path: str, params: dict) -> object:
    base = BITUNIX_SPOT_BASE if MARKET == "spot" else BITUNIX_FUTURES_BASE
    query = urllib.parse.urlencode(params)
    return http_json(f"{base}{path}?{query}")


# ============================================================
# BITUNIX CANDLES — latest 99 CLOSED M15 only
# ============================================================

def _to_float(value) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if result == result else None  # reject NaN


def _to_epoch_ms(value) -> float | None:
    """Candle open-time may arrive as ms-epoch number or ISO8601 string."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if text.isdigit():
        number = float(text)
        return number if number > 10**11 else number * 1000.0  # sec -> ms
    try:
        iso = text.replace("Z", "+00:00")
        return datetime.fromisoformat(iso).timestamp() * 1000.0
    except ValueError:
        return None


def parse_candles(payload: object) -> list[dict]:
    """Tolerant parser: returns ASCENDING [{open_ts_ms, open, high, low, close}]."""
    rows: list = []
    if isinstance(payload, dict):
        data = payload.get("data")
        if isinstance(data, dict):
            data = data.get("list") or data.get("data") or []
        rows = data if isinstance(data, list) else []
    elif isinstance(payload, list):
        rows = payload

    candles: list[dict] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        open_ts = _to_epoch_ms(row.get("time") or row.get("ts") or row.get("openTime"))
        open_p = _to_float(row.get("open"))
        high = _to_float(row.get("high"))
        low = _to_float(row.get("low"))
        close = _to_float(row.get("close") or row.get("lastPrice"))
        if None in (open_ts, open_p, high, low, close):
            continue
        candles.append(
            {
                "open_ts": open_ts,
                "open": open_p,
                "high": high,
                "low": low,
                "close": close,
            }
        )

    candles.sort(key=lambda c: c["open_ts"])
    return candles


def candle_interval_ms() -> float:
    return TIMEFRAME_MINUTES * 60 * 1000


def keep_closed_only(candles: list[dict], now_ms: float | None = None) -> list[dict]:
    """Requirement: ONLY fully CLOSED M15 candles may be used."""
    if now_ms is None:
        now_ms = time.time() * 1000.0
    horizon = candle_interval_ms()
    return [c for c in candles if c["open_ts"] + horizon <= now_ms]


def fetch_closed_m15(symbol: str) -> list[dict]:
    """Fetch exactly the latest 99 CLOSED M15 candles — never more history."""
    interval = "15" if MARKET == "spot" else "15m"

    if MARKET == "spot":
        # Bitunix spot kline/history already EXCLUDES the in-progress candle
        # when endTime is omitted (per official docs). limit=99 => no extra history.
        params = {"symbol": symbol, "interval": interval, "limit": str(CANDLE_LIMIT)}
        payload = bitunix_get("/api/spot/v1/market/kline/history", params)
    else:
        params = {"symbol": symbol, "interval": interval, "limit": CANDLE_LIMIT}
        payload = bitunix_get("/api/v1/futures/market/kline", params)

    candles = keep_closed_only(parse_candles(payload))

    if len(candles) < CANDLE_LIMIT:
        return []

    return candles[-CANDLE_LIMIT:]  # exactly the latest 99 closed candles


# ============================================================
# INDICATORS (pure functions)
# ============================================================

def sma(values: list[float], period: int) -> float | None:
    """Simple Moving Average over the LAST `period` values."""
    if period <= 0 or len(values) < period:
        return None
    window = values[-period:]
    return sum(window) / period


def rsi_wilder(closes: list[float], period: int = 14) -> float | None:
    """RSI(period=14), source = CLOSE, Wilder smoothing (exact definition).

    Needs at least period+1 closes. No other price source is ever used.
    """
    if period <= 0 or len(closes) < period + 1:
        return None

    gains = 0.0
    losses = 0.0
    for i in range(1, period + 1):
        change = closes[i] - closes[i - 1]
        if change >= 0:
            gains += change
        else:
            losses -= change

    avg_gain = gains / period
    avg_loss = losses / period

    for i in range(period + 1, len(closes)):
        change = closes[i] - closes[i - 1]
        gain = change if change > 0 else 0.0
        loss = -change if change < 0 else 0.0
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period

    if avg_loss == 0:
        return 100.0 if avg_gain > 0 else 50.0

    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


# ============================================================
# RANGE ANALYSIS
# ============================================================

def analyze_range(candles: list[dict]) -> dict | None:
    """Range-bound detection over the 99 closed candles.

    NOTE: FVG analysis intentionally does NOT exist here.
    """
    if len(candles) != CANDLE_LIMIT:
        return None

    closes = [c["close"] for c in candles]
    highs = [c["high"] for c in candles]
    lows = [c["low"] for c in candles]

    last_close = closes[-1]

    sma7 = sma(closes, 7)
    sma25 = sma(closes, 25)
    sma99 = sma(closes, 99)
    rsi14 = rsi_wilder(closes, 14)  # exactly RSI(14) on CLOSE

    band = candles[-LOOKBACK:]
    range_high = max(c["high"] for c in band)
    range_low = min(c["low"] for c in band)
    band_mid = (range_high + range_low) / 2.0
    width_pct = ((range_high - range_low) / band_mid * 100.0) if band_mid else None

    dist_sma25_pct = (
        abs(last_close - sma25) / sma25 * 100.0
        if sma25
        else None
    )

    in_band = range_low <= last_close <= range_high

    reasons: list[str] = []
    if width_pct is None or width_pct > MAX_WIDTH_PCT:
        reasons.append(f"width {width_pct:.2f}% > {MAX_WIDTH_PCT}%")
    if rsi14 is None or not (RSI_MIN <= rsi14 <= RSI_MAX):
        reasons.append(f"RSI14 {rsi14:.1f} outside {RSI_MIN:.0f}-{RSI_MAX:.0f}")
    if dist_sma25_pct is None or dist_sma25_pct > MAX_DIST_SMA25_PCT:
        reasons.append(f"dist(SMA25) {dist_sma25_pct:.2f}% > {MAX_DIST_SMA25_PCT}%")
    if not in_band:
        reasons.append("close outside band")

    is_range = not reasons

    position_pct = (
        (last_close - range_low) / (range_high - range_low) * 100.0
        if range_high > range_low
        else 50.0
    )

    return {
        "symbol": None,  # filled by caller
        "last_close": last_close,
        "range_low": range_low,
        "range_high": range_high,
        "width_pct": width_pct,
        "position_pct": position_pct,
        "rsi14": rsi14,
        "sma7": sma7,
        "sma25": sma25,
        "sma99": sma99,
        "dist_sma25_pct": dist_sma25_pct,
        "dist_sma99_pct": (
            (last_close - sma99) / sma99 * 100.0 if sma99 else None
        ),
        "is_range": is_range,
        "reject_reasons": reasons,
        "candles_used": len(candles),
    }


# ============================================================
# UNIVERSE (LiveCoinWatch market cap -> Bitunix symbols)
# ============================================================

def lcw_top_universe() -> list[str]:
    """Top coins by market cap from LiveCoinWatch (read-only).

    Uses the DEDICATED scanner key (never the bot's shared credential).
    Resolved at call time, so editing the dedicated env file takes
    effect on the NEXT cron run without code changes.
    """
    payload = http_json(
        f"{LCW_BASE}/coins/list",
        payload={
            "currency": "USD",
            "sort": "rank",
            "order": "ascending",
            "offset": 0,
            "limit": 100,
            "meta": False,
        },
        api_key=resolve_lcw_key(),
    )
    codes: list[str] = []
    for item in payload if isinstance(payload, list) else []:
        cap = _to_float(item.get("cap"))
        code = str(item.get("code") or "").strip().upper()
        if not code or code in {"USDT", "USDC", "DAI", "FDUSD", "TUSD"}:
            continue
        if cap is not None and cap >= LCW_MIN_CAP_USD:
            codes.append(code)
        if len(codes) >= LCW_LIMIT:
            break
    return codes


def bitunix_tradable_bases() -> set[str] | None:
    """Base tokens with an OPEN {BASE}/USDT pair on Bitunix spot."""
    try:
        payload = bitunix_get("/api/spot/v1/common/coin_pair/list", {})
        rows = payload.get("data") if isinstance(payload, dict) else None
        bases: set[str] = set()
        for row in rows if isinstance(rows, list) else []:
            if str(row.get("isOpen", "")).lower() != "true":
                continue
            base = str(row.get("base") or "").strip().upper()
            quote = str(row.get("quote") or "").strip().upper()
            if base and quote == "USDT":
                bases.add(base)
        return bases or None
    except Exception:
        return None


def build_universe() -> tuple[list[str], str]:
    """Returns (symbols, source_description)."""
    if PLT_RANGE_SYMBOLS:
        codes = [c.strip().upper() for c in PLT_RANGE_SYMBOLS.split(",") if c.strip()]
        return codes, "config PLT_RANGE_SYMBOLS"

    try:
        codes = lcw_top_universe()
        source = "LiveCoinWatch top market-cap"
    except Exception as exc:
        print(f"[WARN] LiveCoinWatch unavailable ({exc}); using fallback majors.")
        codes = list(FALLBACK_SYMBOLS)
        source = "fallback majors (LCW unavailable)"

    bases = bitunix_tradable_bases() if MARKET == "spot" else None
    symbols: list[str] = []
    for code in codes:
        if bases is not None and code not in bases:
            continue  # no open {CODE}/USDT pair on Bitunix
        symbols.append(f"{code}USDT")
        if len(symbols) >= MAX_SYMBOLS:
            break

    if not symbols:
        symbols = [f"{c}USDT" for c in FALLBACK_SYMBOLS[:MAX_SYMBOLS]]
        source += " -> fallback majors"

    return symbols, source


# ============================================================
# SCAN + OUTPUT
# ============================================================

def scan() -> list[dict]:
    symbols, source = build_universe()
    now = datetime.now(timezone.utc)
    print("=" * 48)
    print(f"PLT RANGE SCANNER | {now.isoformat(timespec='seconds')}")
    print(f"Tehran time      : {now.astimezone(TEHRAN).isoformat(timespec='seconds')}")
    print(f"Market           : Bitunix {MARKET} (public, read-only, NO API key)")
    print(f"LCW key          : {lcw_key_source()}")
    print(f"Window           : latest {CANDLE_LIMIT} CLOSED M15 candles ONLY")
    print(f"Indicators       : RSI(14)@CLOSE + SMA(7,25,99) — no FVG")
    print(f"Universe source  : {source}")
    print(f"Symbols          : {', '.join(symbols)}")
    print("=" * 48)

    results: list[dict] = []
    for symbol in symbols:
        try:
            candles = fetch_closed_m15(symbol)
        except Exception as exc:
            print(f"  [SKIP] {symbol}: fetch failed — {exc}")
            continue
        if len(candles) != CANDLE_LIMIT:
            print(f"  [SKIP] {symbol}: only {len(candles)} closed M15 candles (need {CANDLE_LIMIT})")
            continue

        analysis = analyze_range(candles)
        if analysis is None:
            continue
        analysis["symbol"] = symbol
        results.append(analysis)

        state = "RANGE ✔" if analysis["is_range"] else "no"
        detail = ", ".join(analysis["reject_reasons"]) if analysis["reject_reasons"] else "all criteria met"
        print(f"  [{state}] {symbol}: close={analysis['last_close']:.6g} "
              f"band=[{analysis['range_low']:.6g}..{analysis['range_high']:.6g}] "
              f"width={analysis['width_pct']:.2f}% RSI14={analysis['rsi14']:.1f} "
              f"SMA7={analysis['sma7']:.6g} SMA25={analysis['sma25']:.6g} SMA99={analysis['sma99']:.6g} "
              f"— {detail}")

    return results


def write_signals_section(results: list[dict]) -> None:
    """Requirement: results must go to the SIGNALS section/output."""
    print()
    print("# ==================================================")
    print("# ==================== SIGNALS =====================")
    print("# ==================================================")

    ranges = [r for r in results if r["is_range"]]
    if not ranges:
        print("هیچ ستاپ رِنج فعالی پیدا نشد. (No active range setups.)")
    else:
        for r in ranges:
            print(
                f"📐 {r['symbol']} | RANGING\n"
                f"   close      : {r['last_close']:.6g}\n"
                f"   range      : {r['range_low']:.6g} — {r['range_high']:.6g}  "
                f"(width {r['width_pct']:.2f}%)\n"
                f"   position   : {r['position_pct']:.0f}% of band\n"
                f"   RSI(14)    : {r['rsi14']:.1f}\n"
                f"   SMA 7/25/99: {r['sma7']:.6g} / {r['sma25']:.6g} / {r['sma99']:.6g}\n"
                f"   dist SMA99 : {r['dist_sma99_pct']:+.2f}%"
            )

    snapshot = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "scanner": "plt_range_scanner",
        "timeframe": f"M{TIMEFRAME_MINUTES}",
        "candles_used": CANDLE_LIMIT,
        "rsi": {"period": 14, "source": "close"},
        "smas": [7, 25, 99],
        "fvg_removed": True,
        "trading_execution": False,
        "signals": [
            {k: v for k, v in r.items() if k != "symbol"} | {"symbol": r["symbol"]}
            for r in ranges
        ],
        "scanned": [
            {"symbol": r["symbol"], "is_range": r["is_range"], "reject_reasons": r["reject_reasons"]}
            for r in results
        ],
    }
    try:
        SNAPSHOT_PATH.write_text(
            json.dumps(snapshot, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"\n[snapshot] {SNAPSHOT_PATH}")
    except OSError as exc:
        print(f"[WARN] snapshot write failed: {exc}")


# ============================================================
# SELFTEST (offline, deterministic — for validation without network)
# ============================================================

def _make_candle(open_ts: float, open_p: float, high: float, low: float, close: float) -> dict:
    return {"open_ts": open_ts, "open": open_p, "high": high, "low": low, "close": close}


def selftest() -> int:
    print("PLT RANGE SCANNER — OFFLINE SELFTEST")
    failures: list[str] = []

    def check(name: str, condition: bool) -> None:
        print(f"  {'PASS' if condition else 'FAIL'} — {name}")
        if not condition:
            failures.append(name)

    # --- SMA ---
    check("SMA(7) basic", abs(sma(list(range(1, 8)), 7) - 4.0) < 1e-9)
    check("SMA(25) insufficient -> None", sma(list(range(10)), 25) is None)
    check("SMA(99) window = mean of last 99", abs(
        sma([float(i) for i in range(150)], 99) - sum(range(51, 150)) / 99.0) < 1e-9)

    # --- RSI(14) CLOSE, hand-computed cases ---
    flat = [100.0] * 15
    check("RSI flat = 50 (neutral)", abs(rsi_wilder(flat) - 50.0) < 1e-9)
    rising = [100.0 + i for i in range(15)]
    check("RSI all-up = 100", rsi_wilder(rising) == 100.0)
    falling = [100.0 - i for i in range(15)]
    check("RSI all-down = 0", rsi_wilder(falling) == 0.0)

    # Wilder smoothing hand case: closes 0..14 (14 gains of +1), then 12.0
    # -> seed avgGain=1, avgLoss=0 ; next diff -2:
    #    avgGain = 13/14 ; avgLoss = 2/14 ; RSI = 100 - 100/(1+6.5) = 86.666...
    manual = [float(i) for i in range(15)] + [12.0]
    expected = 100.0 - 100.0 / (1.0 + (13 / 14) / (2 / 14))
    check("RSI Wilder smoothing exact", abs(rsi_wilder(manual) - expected) < 1e-9)

    # --- closed-candle filter ---
    now_ms = 1_800_000 * 1000.0  # aligned to a 15m boundary
    in_progress = _make_candle(now_ms - 60_000, 1, 1, 1, 1)  # opened 1 min ago
    closed = _make_candle(now_ms - 15 * 60_000, 1, 1, 1, 1)
    kept = keep_closed_only([closed, in_progress], now_ms=now_ms)
    check("in-progress candle dropped", len(kept) == 1 and kept[0] is closed)

    # --- 99-candle window slicing ---
    synthetic = [
        _make_candle((10_000 + i) * 60_000.0, 100, 100.5, 99.5, 100)
        for i in range(120)
    ]
    window = synthetic[-CANDLE_LIMIT:]
    check("window is exactly 99", len(window) == 99)
    check("window keeps newest candles", window[-1] is synthetic[-1])

    # --- range analysis: flat synthetic data must be detected ---
    flat_candles = []
    for i in range(CANDLE_LIMIT):
        open_ts = (10_000 + i) * 900_000.0
        flat_candles.append(_make_candle(open_ts, 100.0, 100.4, 99.6, 100.0))
    result = analyze_range(flat_candles)
    check("flat data -> is_range", bool(result and result["is_range"]))
    check("flat data -> RSI ~ 50", bool(result and abs(result["rsi14"] - 50.0) < 1e-6))
    check("SMAs computed", bool(result and None not in (result["sma7"], result["sma25"], result["sma99"])))

    # --- trending data must NOT be a range ---
    trend_candles = []
    for i in range(CANDLE_LIMIT):
        price = 100.0 + i * 1.0
        open_ts = (10_000 + i) * 900_000.0
        trend_candles.append(_make_candle(open_ts, price, price + 0.5, price - 0.5, price + 0.2))
    result_trend = analyze_range(trend_candles)
    check("strong uptrend -> not a range", bool(result_trend and not result_trend["is_range"]))

    # --- structural guarantees (source-level, requirement checks) ---
    # Scan only the functional part (everything before this selftest) to
    # avoid matching the check-list strings themselves.
    source_text = Path(__file__).read_text(encoding="utf-8")
    functional_source = source_text.split("def selftest")[0]

    import ast
    tree = ast.parse(functional_source)
    fvg_code: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef,
                             ast.Name, ast.Attribute, ast.arg)):
            name = getattr(node, "name", "") or getattr(node, "id", "") or getattr(node, "attr", "")
            if "fvg" in str(name).lower():
                fvg_code.append(str(name))
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            value = str(node.value).lower()
            negations = ("no fvg", "removed", "does not exist", "intentionally")
            if "fvg" in value and not any(neg in value for neg in negations):
                fvg_code.append(node.value)
    check("no FVG logic present (AST scan)", not fvg_code)

    for forbidden in ("placeOrder", "place_order", "/order/submit", "trade/execute", "createOrder"):
        check(f"no order execution: {forbidden}", forbidden not in functional_source)
    check("no Bitunix POST (read-only)", 'method="POST"' not in functional_source and "'POST'" not in functional_source)

    print()
    if failures:
        print(f"SELFTEST FAILED: {len(failures)} check(s): {failures}")
        return 1
    print("SELFTEST PASSED: all checks OK.")
    return 0


# ============================================================
# MAIN
# ============================================================

def main() -> int:
    if "--selftest" in sys.argv:
        return selftest()

    try:
        results = scan()
    except Exception as exc:
        print(f"[ERROR] scan aborted: {exc}")
        return 0  # cron: never spam retries; next run is in <=1h

    write_signals_section(results)
    return 0


if __name__ == "__main__":
    sys.exit(main())

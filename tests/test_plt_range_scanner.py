"""Unit tests for the standalone PLT Range Scanner (offline, no network).

Loads plt_range_scanner.py from the repo root via importlib.
Validates the user's hard requirements:
- window = latest 99 CLOSED M15 candles, nothing more
- RSI is exactly RSI(14) on CLOSE
- SMA 7 / 25 / 99 computed
- FVG analysis completely absent
- NO trading/order execution (no POST to exchange, no order calls)
"""

import importlib.util
import math
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCANNER_PATH = REPO_ROOT / "plt_range_scanner.py"

spec = importlib.util.spec_from_file_location("plt_range_scanner", SCANNER_PATH)
scanner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scanner)


def _candle(i, open_p, high, low, close, ts=None):
    return {
        "open_ts": ts if ts is not None else (10_000 + i) * 900_000.0,
        "open": open_p,
        "high": high,
        "low": low,
        "close": close,
    }


def _flat_candles(n=99, center=100.0, spread=0.4):
    return [
        _candle(i, center, center + spread, center - spread, center)
        for i in range(n)
    ]


# ============================================================
# indicators
# ============================================================

def test_sma_7_basic():
    assert abs(scanner.sma([1, 2, 3, 4, 5, 6, 7], 7) - 4.0) < 1e-9


def test_sma_uses_last_window_only():
    values = [float(i) for i in range(150)]
    expected = sum(range(51, 150)) / 99.0
    assert abs(scanner.sma(values, 99) - expected) < 1e-9


def test_sma_insufficient_data_returns_none():
    assert scanner.sma([1.0] * 98, 99) is None


def test_all_three_smas_computed_on_99_candles():
    result = scanner.analyze_range(_flat_candles())
    assert result is not None
    assert result["sma7"] == pytest.approx(100.0)
    assert result["sma25"] == pytest.approx(100.0)
    assert result["sma99"] == pytest.approx(100.0)


def test_rsi_14_flat_is_neutral_50():
    closes = [100.0] * 15
    assert scanner.rsi_wilder(closes) == pytest.approx(50.0)


def test_rsi_14_all_gains_is_100():
    closes = [100.0 + i for i in range(15)]
    assert scanner.rsi_wilder(closes) == 100.0


def test_rsi_14_all_losses_is_0():
    closes = [100.0 - i for i in range(15)]
    assert scanner.rsi_wilder(closes) == 0.0


def test_rsi_wilder_smoothing_exact_value():
    # closes 0..14 (14 gains of +1), then 12.0 -> one final diff of -2
    # seed avgGain=1, avgLoss=0 ; Wilder step: avgGain=13/14, avgLoss=2/14
    # RSI = 100 - 100/(1+6.5) = 86.666...
    closes = [float(i) for i in range(15)] + [12.0]
    expected = 100.0 - 100.0 / (1.0 + (13 / 14) / (2 / 14))
    assert scanner.rsi_wilder(closes) == pytest.approx(expected, rel=1e-12)


def test_rsi_14_is_default_and_close_sourced():
    import inspect
    signature = inspect.signature(scanner.rsi_wilder)
    assert signature.parameters["period"].default == 14
    source = inspect.getsource(scanner.rsi_wilder)
    assert "closes[i]" in source  # source is the CLOSE series only


# ============================================================
# closed-candle window (requirement 7 & 13)
# ============================================================

def test_in_progress_candle_is_dropped():
    now_ms = time.time() * 1000
    open_candle = _candle(0, 1, 1, 1, 1, ts=now_ms - 60_000)      # opened 1 min ago
    closed_candle = _candle(1, 1, 1, 1, 1, ts=now_ms - 15 * 60_000)
    kept = scanner.keep_closed_only([open_candle, closed_candle])
    assert kept == [closed_candle]


def test_window_is_capped_to_latest_99():
    candles = _flat_candles(150)
    result = scanner.analyze_range(candles)
    assert result is None  # analyze_range only accepts exactly 99

    sliced = candles[-99:]
    result = scanner.analyze_range(sliced)
    assert result is not None
    assert result["candles_used"] == 99


def test_fetch_requests_exactly_99_candles():
    import inspect
    source = inspect.getsource(scanner.fetch_closed_m15)
    assert "CANDLE_LIMIT" in source
    assert scanner.CANDLE_LIMIT == 99
    # no pagination / no extra history requests
    assert "startTime" not in source
    assert "while" not in source


def test_parse_candles_ascending_and_tolerant():
    payload = {
        "code": 0,
        "data": [
            {"time": 2000, "open": "2", "high": "3", "low": "1", "close": "2.5"},
            {"time": 1000, "open": "1", "high": "2", "low": "0.5", "close": "1.5"},
            {"bad": "row"},
        ],
    }
    candles = scanner.parse_candles(payload)
    assert [c["open_ts"] for c in candles] == [1000.0, 2000.0]
    assert candles[0]["close"] == 1.5


def test_parse_candles_accepts_iso8601_ts():
    payload = {"data": [{"ts": "2026-01-01T00:00:00Z", "open": 1, "high": 1, "low": 1, "close": 1}]}
    candles = scanner.parse_candles(payload)
    assert candles and candles[0]["open_ts"] > 1_600_000_000_000


# ============================================================
# range logic
# ============================================================

def test_flat_market_detected_as_range():
    result = scanner.analyze_range(_flat_candles())
    assert result is not None
    assert result["is_range"] is True
    assert result["rsi14"] == pytest.approx(50.0)
    assert result["range_low"] == pytest.approx(99.6)
    assert result["range_high"] == pytest.approx(100.4)


def test_strong_trend_not_a_range():
    candles = []
    for i in range(99):
        price = 100.0 + i
        candles.append(_candle(i, price, price + 0.5, price - 0.5, price + 0.2))
    result = scanner.analyze_range(candles)
    assert result is not None
    assert result["is_range"] is False
    assert result["reject_reasons"]  # must explain why


def test_analyze_rejects_wrong_window_size():
    assert scanner.analyze_range(_flat_candles(98)) is None
    assert scanner.analyze_range(_flat_candles(100)) is None


# ============================================================
# structural guarantees (requirements 10, 11, 12)
# ============================================================

def _functional_source() -> str:
    """Scanner source without the selftest block (avoids self-matching)."""
    return SCANNER_PATH.read_text(encoding="utf-8").split("def selftest")[0]


def test_no_fvg_logic_anywhere_in_ast():
    import ast
    tree = ast.parse(_functional_source())
    offenders = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef,
                             ast.Name, ast.Attribute, ast.arg)):
            name = getattr(node, "name", "") or getattr(node, "id", "") or getattr(node, "attr", "")
            if "fvg" in str(name).lower():
                offenders.append(f"code symbol: {name}")
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            value = str(node.value).lower()
            negations = ("no fvg", "removed", "does not exist", "intentionally")
            if "fvg" in value and not any(neg in value for neg in negations):
                offenders.append(f"string: {node.value!r}")
    assert not offenders, f"FVG logic present: {offenders}"


@pytest.mark.parametrize("fragment", [
    "placeOrder", "place_order", "createOrder", "create_order",
    "/order/submit", "trade/execute", "privateKey",
])
def test_no_trading_or_signed_calls(fragment):
    # functional code only — the selftest's own check-list literals are excluded
    source = _functional_source()
    assert fragment not in source


def test_bitunix_calls_are_get_only():
    source = _functional_source()
    assert 'method="POST"' not in source
    assert "'POST'" not in source
    # LCW coins/list POST is a read-only market-data query, allowed:
    assert "coins/list" in source
    assert "/api/spot/v1" in source  # public spot endpoints only


def test_signals_section_is_written():
    import inspect
    source = inspect.getsource(scanner.write_signals_section)
    assert "==================== SIGNALS ====================" in source
    assert "SNAPSHOT_PATH" in source


def test_scanner_uses_only_stdlib():
    source = SCANNER_PATH.read_text(encoding="utf-8")
    for banned in ("import requests", "import ccxt", "import pandas", "import numpy"):
        assert banned not in source


# ============================================================
# math sanity for range metrics
# ============================================================

def test_position_in_band_math():
    result = scanner.analyze_range(_flat_candles(center=100.0, spread=1.0))
    assert result is not None
    assert 0.0 <= result["position_pct"] <= 100.0
    assert result["width_pct"] == pytest.approx(2.0 / 100.0 * 100.0)


def test_selftest_script_passes():
    import subprocess
    import sys
    proc = subprocess.run(
        [sys.executable, str(SCANNER_PATH), "--selftest"],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "SELFTEST PASSED" in proc.stdout

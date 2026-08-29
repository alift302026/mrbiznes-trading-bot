from __future__ import annotations

from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed,
)
from typing import Any, Dict, List

from app.engines.signals.livecoinwatch_provider import (
    get_coin,
    list_coins,
)
from app.engines.signals.setup_signal_engine import (
    analyze_setup,
)


STABLECOINS = {
    "USDT",
    "USDC",
    "DAI",
    "FDUSD",
    "TUSD",
    "USDE",
    "USDS",
    "PYUSD",
    "FRAX",
    "USD1",
    "USDD",
    "BUSD",
}

MAX_WORKERS = 4


def _eligible(
    item: Dict[str, Any],
    minimum_cap: float,
) -> bool:
    code = str(
        item.get("code") or ""
    ).upper()

    if not code:
        return False

    if code.startswith("_"):
        return False

    if code in STABLECOINS:
        return False

    cap = item.get(
        "market_cap_usd"
    )

    volume = item.get(
        "volume_24h_usd"
    )

    if cap is None:
        return False

    if cap < minimum_cap:
        return False

    if volume is None:
        return False

    if volume <= 0:
        return False

    return True


def _relative_to_btc(
    item: Dict[str, Any],
    btc: Dict[str, Any],
) -> Dict[str, float]:
    code = str(
        item.get("code") or ""
    ).upper()

    if code == "BTC":
        return {
            "1h": 0.0,
            "24h": 0.0,
            "7d": 0.0,
        }

    result = {}

    for key, output_key in (
        (
            "change_1h_percent",
            "1h",
        ),
        (
            "change_24h_percent",
            "24h",
        ),
        (
            "change_7d_percent",
            "7d",
        ),
    ):
        coin_value = float(
            item.get(key)
            or 0.0
        )

        btc_value = float(
            btc.get(key)
            or 0.0
        )

        result[
            output_key
        ] = (
            coin_value
            - btc_value
        )

    return result


def _grade(
    confidence: int,
) -> str:
    if confidence >= 85:
        return "A+"

    if confidence >= 75:
        return "A"

    if confidence >= 65:
        return "B"

    return "NO_SIGNAL"


def _adjust_signal(
    signal: Dict[str, Any],
    item: Dict[str, Any],
    btc: Dict[str, Any],
) -> Dict[str, Any]:
    result = dict(signal)

    confidence = int(
        result.get(
            "confidence",
            0,
        )
    )

    direction = result.get(
        "direction"
    )

    weekly = (
        result.get(
            "weekly_context"
        )
        or {}
    )

    weekly_sma = weekly.get(
        "sma_state"
    )

    weekly_dow = weekly.get(
        "dow"
    )

    risks = list(
        result.get("risks")
        or []
    )

    reasons = list(
        result.get("reasons")
        or []
    )

    relative = _relative_to_btc(
        item,
        btc,
    )

    # Weekly context
    if (
        direction == "LONG_WATCH"
        and (
            weekly_sma == "bearish"
            or weekly_dow == "LH_LL"
        )
    ):
        confidence -= 8

        risks.append(
            "Weekly structure conflicts "
            "with long setup"
        )

    elif (
        direction == "SHORT_WATCH"
        and (
            weekly_sma == "bullish"
            or weekly_dow == "HH_HL"
        )
    ):
        confidence -= 8

        risks.append(
            "Weekly structure conflicts "
            "with short setup"
        )

    elif (
        direction == "LONG_WATCH"
        and weekly_sma == "bullish"
        and weekly_dow == "HH_HL"
    ):
        confidence += 5

        reasons.append(
            "Weekly trend confirms long"
        )

    elif (
        direction == "SHORT_WATCH"
        and weekly_sma == "bearish"
        and weekly_dow == "LH_LL"
    ):
        confidence += 5

        reasons.append(
            "Weekly trend confirms short"
        )

    # Relative strength vs BTC
    if item.get("code") != "BTC":

        if (
            direction == "LONG_WATCH"
            and relative["24h"] > 1
            and relative["7d"] > 0
        ):
            confidence += 5

            reasons.append(
                "Asset outperforming BTC"
            )

        elif (
            direction == "LONG_WATCH"
            and relative["24h"] < -2
        ):
            confidence -= 5

            risks.append(
                "Asset underperforming BTC"
            )

        elif (
            direction == "SHORT_WATCH"
            and relative["24h"] < -1
            and relative["7d"] < 0
        ):
            confidence += 5

            reasons.append(
                "Asset weaker than BTC"
            )

        elif (
            direction == "SHORT_WATCH"
            and relative["24h"] > 2
        ):
            confidence -= 5

            risks.append(
                "Asset outperforming BTC "
                "against short setup"
            )

    confidence = max(
        0,
        min(confidence, 100),
    )

    result[
        "confidence"
    ] = confidence

    result[
        "grade"
    ] = _grade(
        confidence
    )

    result[
        "reasons"
    ] = reasons[:8]

    result[
        "risks"
    ] = risks[:6]

    result[
        "market_context"
    ] = {
        "rank": item.get(
            "rank"
        ),

        "market_cap_usd": (
            item.get(
                "market_cap_usd"
            )
        ),

        "volume_24h_usd": (
            item.get(
                "volume_24h_usd"
            )
        ),

        "change_1h_percent": (
            item.get(
                "change_1h_percent"
            )
        ),

        "change_24h_percent": (
            item.get(
                "change_24h_percent"
            )
        ),

        "change_7d_percent": (
            item.get(
                "change_7d_percent"
            )
        ),

        "relative_to_btc": (
            relative
        ),
    }

    return result


def _analyze_one(
    item: Dict[str, Any],
) -> Dict[str, Any]:
    code = item["code"]

    signal = analyze_setup(
        f"{code}/USDT"
    )

    return {
        "item": item,
        "signal": signal,
    }


def scan_top30(
    deep_limit: int = 30,
) -> Dict[str, Any]:
    btc = get_coin(
        "BTC",
        meta=False,
    )

    btc_price = btc.get(
        "price_usd"
    )

    if not btc_price:
        raise RuntimeError(
            "BTC price unavailable"
        )

    minimum_cap = (
        float(btc_price)
        * 1000
    )

    raw = list_coins(
        sort="cap",
        order="descending",
        limit=100,
    )

    eligible = [
        item
        for item in raw
        if _eligible(
            item,
            minimum_cap,
        )
    ]

    limit = max(
        1,
        min(
            int(deep_limit),
            30,
        ),
    )

    universe = eligible[:limit]

    analyzed: List[
        Dict[str, Any]
    ] = []

    failures: List[str] = []

    with ThreadPoolExecutor(
        max_workers=MAX_WORKERS
    ) as executor:

        futures = {
            executor.submit(
                _analyze_one,
                item,
            ): item
            for item in universe
        }

        for future in as_completed(
            futures
        ):
            item = futures[
                future
            ]

            try:
                result = (
                    future.result()
                )

                signal = (
                    _adjust_signal(
                        result[
                            "signal"
                        ],
                        result[
                            "item"
                        ],
                        btc,
                    )
                )

                analyzed.append(
                    signal
                )

            except Exception:
                failures.append(
                    str(
                        item.get(
                            "code"
                        )
                    )
                )

    analyzed.sort(
        key=lambda item: (
            item.get(
                "confidence",
                0,
            )
        ),
        reverse=True,
    )

    grade_a_plus = [
        item
        for item in analyzed
        if item.get("grade")
        == "A+"
    ]

    grade_a = [
        item
        for item in analyzed
        if item.get("grade")
        == "A"
    ]

    grade_b = [
        item
        for item in analyzed
        if item.get("grade")
        == "B"
    ]

    no_signal = [
        item
        for item in analyzed
        if item.get("grade")
        == "NO_SIGNAL"
    ]

    return {
        "provider": {
            "market_context": (
                "LiveCoinWatch"
            ),
            "ohlcv": "XT",
        },

        "btc": btc,

        "minimum_market_cap_usd": (
            minimum_cap
        ),

        "universe_count": len(
            universe
        ),

        "analyzed_count": len(
            analyzed
        ),

        "failures": failures,

        "signals_a_plus": (
            grade_a_plus
        ),

        "signals_a": (
            grade_a
        ),

        "watchlist_b": (
            grade_b
        ),

        "no_signal": (
            no_signal
        ),

        "all_results": (
            analyzed
        ),

        "publish_candidates": (
            grade_a_plus
            + grade_a
        )[:10],

        "note": (
            "Only A/A+ qualify as "
            "high-priority candidates. "
            "Thresholds remain experimental "
            "until validated by backtesting."
        ),
    }
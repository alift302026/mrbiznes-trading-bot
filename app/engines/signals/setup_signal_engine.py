from __future__ import annotations

from datetime import (
    datetime,
    timedelta,
    timezone,
)
from typing import (
    Any,
    Dict,
    List,
    Optional,
)

from app.engines.signals.technical_signal_analyzer import (
    analyze_timeframe,
    swing_points,
)
from app.engines.signals.xt_signal_provider import (
    fetch_multi_timeframe,
)


def _closed(
    candles: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Keep only fully closed candles.

    XT may return the candle that is currently forming.
    Confirmed signal calculations must not use it.
    """
    if not candles:
        return []

    timeframe = candles[-1].get(
        "timeframe"
    )

    durations = {
        "15m": timedelta(
            minutes=15
        ),
        "1h": timedelta(
            hours=1
        ),
        "4h": timedelta(
            hours=4
        ),
        "1w": timedelta(
            days=7
        ),
    }

    duration = durations.get(
        timeframe
    )

    if duration is None:
        return candles

    now = datetime.now(
        timezone.utc
    )

    result = []

    for candle in candles:
        candle_time = candle.get(
            "time"
        )

        if not isinstance(
            candle_time,
            datetime,
        ):
            continue

        if candle_time.tzinfo is None:
            candle_time = (
                candle_time.replace(
                    tzinfo=timezone.utc
                )
            )
        else:
            candle_time = (
                candle_time.astimezone(
                    timezone.utc
                )
            )

        candle_close_time = (
            candle_time
            + duration
        )

        if candle_close_time <= now:
            result.append(candle)

    return result


def _last_swing_low(
    candles: List[Dict[str, Any]],
) -> Optional[float]:
    swings = swing_points(
        candles[-80:]
    )

    lows = swings["lows"]

    if not lows:
        return None

    return float(
        lows[-1]["price"]
    )


def _last_swing_high(
    candles: List[Dict[str, Any]],
) -> Optional[float]:
    swings = swing_points(
        candles[-80:]
    )

    highs = swings["highs"]

    if not highs:
        return None

    return float(
        highs[-1]["price"]
    )


def _long_score(
    tf15: Dict[str, Any],
    tf1h: Dict[str, Any],
    tf4h: Dict[str, Any],
) -> Dict[str, Any]:
    score = 0

    reasons: List[str] = []
    risks: List[str] = []

    if (
        tf15["sma_state"]
        == "bullish"
    ):
        score += 15

        reasons.append(
            "SMA 7/25/99 bullish on 15m"
        )

    if (
        tf1h["sma_state"]
        == "bullish"
    ):
        score += 12

        reasons.append(
            "1h SMA structure supports long"
        )

    if (
        tf4h["sma_state"]
        == "bullish"
    ):
        score += 8

        reasons.append(
            "4h higher-timeframe trend supports long"
        )

    if tf15["dow"] == "HH_HL":
        score += 15

        reasons.append(
            "15m Dow structure is HH/HL"
        )

    if tf1h["dow"] == "HH_HL":
        score += 12

        reasons.append(
            "1h Dow structure is HH/HL"
        )

    rsi = tf15.get("rsi")

    if rsi is not None:

        if 50 <= rsi <= 65:
            score += 10

            reasons.append(
                "15m RSI supports bullish momentum"
            )

        elif 65 < rsi < 70:
            score += 5

            risks.append(
                "RSI approaching overbought zone"
            )

        elif rsi >= 70:
            score -= 10

            risks.append(
                "RSI is overbought"
            )

        elif rsi < 45:
            score -= 10

            risks.append(
                "RSI does not support long momentum"
            )

    histogram = tf15.get(
        "macd_histogram"
    )

    if histogram is not None:

        if histogram > 0:
            score += 8

            reasons.append(
                "MACD histogram positive"
            )

        else:
            score -= 5

            risks.append(
                "MACD momentum is negative"
            )

    volume = (
        tf15.get("volume")
        or {}
    )

    if (
        volume.get("state")
        == "contraction"
    ):
        score += 6

        reasons.append(
            "Volume contraction detected"
        )

    box = tf15.get("range")

    if box:

        position = box.get(
            "position",
            0.5,
        )

        if position >= 0.70:
            score += 8

            reasons.append(
                "Price is near upper range boundary"
            )

        if (
            box.get("length", 0)
            >= 10
        ):
            score += 6

            reasons.append(
                f"{box['length']}-candle range detected"
            )

    score = max(
        0,
        min(score, 100),
    )

    return {
        "score": score,
        "reasons": reasons,
        "risks": risks,
    }


def _short_score(
    tf15: Dict[str, Any],
    tf1h: Dict[str, Any],
    tf4h: Dict[str, Any],
) -> Dict[str, Any]:
    score = 0

    reasons: List[str] = []
    risks: List[str] = []

    if (
        tf15["sma_state"]
        == "bearish"
    ):
        score += 15

        reasons.append(
            "SMA 7/25/99 bearish on 15m"
        )

    if (
        tf1h["sma_state"]
        == "bearish"
    ):
        score += 12

        reasons.append(
            "1h SMA structure supports short"
        )

    if (
        tf4h["sma_state"]
        == "bearish"
    ):
        score += 8

        reasons.append(
            "4h higher-timeframe trend supports short"
        )

    if tf15["dow"] == "LH_LL":
        score += 15

        reasons.append(
            "15m Dow structure is LH/LL"
        )

    if tf1h["dow"] == "LH_LL":
        score += 12

        reasons.append(
            "1h Dow structure is LH/LL"
        )

    rsi = tf15.get("rsi")

    if rsi is not None:

        if 35 <= rsi <= 50:
            score += 10

            reasons.append(
                "15m RSI supports bearish momentum"
            )

        elif 30 < rsi < 35:
            score += 5

            risks.append(
                "RSI approaching oversold zone"
            )

        elif rsi <= 30:
            score -= 10

            risks.append(
                "RSI is oversold"
            )

        elif rsi > 55:
            score -= 10

            risks.append(
                "RSI does not support short momentum"
            )

    histogram = tf15.get(
        "macd_histogram"
    )

    if histogram is not None:

        if histogram < 0:
            score += 8

            reasons.append(
                "MACD histogram negative"
            )

        else:
            score -= 5

            risks.append(
                "MACD momentum is positive"
            )

    volume = (
        tf15.get("volume")
        or {}
    )

    if (
        volume.get("state")
        == "contraction"
    ):
        score += 6

        reasons.append(
            "Volume contraction detected"
        )

    box = tf15.get("range")

    if box:

        position = box.get(
            "position",
            0.5,
        )

        if position <= 0.30:
            score += 8

            reasons.append(
                "Price is near lower range boundary"
            )

        if (
            box.get("length", 0)
            >= 10
        ):
            score += 6

            reasons.append(
                f"{box['length']}-candle range detected"
            )

    score = max(
        0,
        min(score, 100),
    )

    return {
        "score": score,
        "reasons": reasons,
        "risks": risks,
    }


def _grade(
    score: int,
) -> str:
    """
    Experimental quality classification.

    These thresholds must later be calibrated
    using backtests and real recorded results.
    """
    if score >= 85:
        return "A+"

    if score >= 75:
        return "A"

    if score >= 65:
        return "B"

    return "NO_SIGNAL"


def _calculate_levels(
    direction: str,
    tf15: Dict[str, Any],
    candles: List[Dict[str, Any]],
) -> Dict[str, Optional[float]]:
    box = tf15.get("range")
    atr_value = tf15.get("atr")

    entry = None
    stop = None

    if box:

        if direction == "LONG_WATCH":
            entry = float(
                box["high"]
            )

        else:
            entry = float(
                box["low"]
            )

    if direction == "LONG_WATCH":

        swing = _last_swing_low(
            candles
        )

        if (
            swing is not None
            and atr_value is not None
        ):
            stop = (
                swing
                - atr_value * 0.15
            )

    else:

        swing = _last_swing_high(
            candles
        )

        if (
            swing is not None
            and atr_value is not None
        ):
            stop = (
                swing
                + atr_value * 0.15
            )

    target_1 = None
    target_2 = None

    if (
        entry is not None
        and stop is not None
    ):
        risk = abs(
            entry - stop
        )

        if risk > 0:

            if (
                direction
                == "LONG_WATCH"
            ):
                target_1 = (
                    entry
                    + risk * 1.5
                )

                target_2 = (
                    entry
                    + risk * 2.0
                )

            else:
                target_1 = (
                    entry
                    - risk * 1.5
                )

                target_2 = (
                    entry
                    - risk * 2.0
                )

    return {
        "entry": entry,
        "stop": stop,
        "target_1": target_1,
        "target_2": target_2,
    }


def analyze_setup(
    symbol: str,
) -> Dict[str, Any]:
    raw = fetch_multi_timeframe(
        symbol=symbol,
        limit=150,
    )

    closed: Dict[
        str,
        List[Dict[str, Any]],
    ] = {}

    for (
        timeframe,
        candles,
    ) in raw.items():

        confirmed = _closed(
            candles
        )

        if len(confirmed) < 100:
            raise RuntimeError(
                "Not enough closed candles "
                f"for {symbol} {timeframe}"
            )

        closed[
            timeframe
        ] = confirmed

    analysis = {
        timeframe: analyze_timeframe(
            candles
        )
        for (
            timeframe,
            candles,
        ) in closed.items()
    }

    tf15 = analysis["15m"]
    tf1h = analysis["1h"]
    tf4h = analysis["4h"]
    tf1w = analysis["1w"]

    long_result = _long_score(
        tf15,
        tf1h,
        tf4h,
    )

    short_result = _short_score(
        tf15,
        tf1h,
        tf4h,
    )

    if (
        long_result["score"]
        >= short_result["score"]
    ):
        direction = "LONG_WATCH"
        selected = long_result

    else:
        direction = "SHORT_WATCH"
        selected = short_result

    grade = _grade(
        selected["score"]
    )

    levels = _calculate_levels(
        direction=direction,
        tf15=tf15,
        candles=closed["15m"],
    )

    return {
        "symbol": symbol.upper(),

        "direction": direction,

        "grade": grade,

        "confidence": (
            selected["score"]
        ),

        "entry_trigger": (
            levels["entry"]
        ),

        "stop": (
            levels["stop"]
        ),

        "target_1": (
            levels["target_1"]
        ),

        "target_2": (
            levels["target_2"]
        ),

        "reasons": (
            selected[
                "reasons"
            ][:8]
        ),

        "risks": (
            selected[
                "risks"
            ][:5]
        ),

        "timeframes": analysis,

        "weekly_context": {
            "sma_state": (
                tf1w["sma_state"]
            ),
            "dow": tf1w["dow"],
            "rsi": tf1w["rsi"],
        },

        "closed_candle_time": (
            closed["15m"][-1][
                "time"
            ]
        ),

        "closed_candle_count": {
            timeframe: len(
                candles
            )
            for (
                timeframe,
                candles,
            ) in closed.items()
        },

        "execution_note": (
            "WATCH only. Entry requires "
            "a confirmed closed-candle trigger. "
            "MrBiznes does not execute a trade."
        ),
    }
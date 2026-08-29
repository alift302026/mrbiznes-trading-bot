from __future__ import annotations

from statistics import mean
from typing import Any, Dict, List, Optional


Candle = Dict[str, Any]


def sma(
    values: List[float],
    period: int,
) -> Optional[float]:
    if len(values) < period:
        return None

    return mean(values[-period:])


def ema_series(
    values: List[float],
    period: int,
) -> List[float]:
    if len(values) < period:
        return []

    multiplier = 2 / (period + 1)

    result = [
        mean(values[:period])
    ]

    for value in values[period:]:
        result.append(
            (
                value - result[-1]
            )
            * multiplier
            + result[-1]
        )

    return result


def rsi(
    values: List[float],
    period: int = 14,
) -> Optional[float]:
    if len(values) <= period:
        return None

    changes = [
        values[index]
        - values[index - 1]
        for index in range(
            1,
            len(values),
        )
    ]

    gains = [
        max(change, 0)
        for change in changes
    ]

    losses = [
        abs(min(change, 0))
        for change in changes
    ]

    avg_gain = mean(
        gains[:period]
    )

    avg_loss = mean(
        losses[:period]
    )

    for index in range(
        period,
        len(gains),
    ):
        avg_gain = (
            avg_gain
            * (period - 1)
            + gains[index]
        ) / period

        avg_loss = (
            avg_loss
            * (period - 1)
            + losses[index]
        ) / period

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss

    return 100 - (
        100 / (1 + rs)
    )


def macd(
    values: List[float],
) -> Dict[str, Optional[float]]:
    fast = ema_series(
        values,
        12,
    )

    slow = ema_series(
        values,
        26,
    )

    if not fast or not slow:
        return {
            "macd": None,
            "signal": None,
            "histogram": None,
        }

    # Align EMA series by their ending values.
    offset = len(fast) - len(slow)

    aligned_fast = (
        fast[offset:]
        if offset >= 0
        else fast
    )

    aligned_slow = (
        slow
        if offset >= 0
        else slow[-len(fast):]
    )

    macd_line = [
        fast_value - slow_value
        for fast_value, slow_value
        in zip(
            aligned_fast,
            aligned_slow,
        )
    ]

    signal_line = ema_series(
        macd_line,
        9,
    )

    if not signal_line:
        return {
            "macd": macd_line[-1],
            "signal": None,
            "histogram": None,
        }

    current_macd = macd_line[-1]
    current_signal = signal_line[-1]

    return {
        "macd": current_macd,
        "signal": current_signal,
        "histogram": (
            current_macd
            - current_signal
        ),
    }


def atr(
    candles: List[Candle],
    period: int = 14,
) -> Optional[float]:
    if len(candles) <= period:
        return None

    true_ranges = []

    for index in range(
        1,
        len(candles),
    ):
        current = candles[index]
        previous = candles[
            index - 1
        ]

        tr = max(
            current["high"]
            - current["low"],
            abs(
                current["high"]
                - previous["close"]
            ),
            abs(
                current["low"]
                - previous["close"]
            ),
        )

        true_ranges.append(tr)

    if len(true_ranges) < period:
        return None

    value = mean(
        true_ranges[:period]
    )

    for tr in true_ranges[
        period:
    ]:
        value = (
            value
            * (period - 1)
            + tr
        ) / period

    return value


def volume_state(
    candles: List[Candle],
    period: int = 20,
) -> Dict[str, Any]:
    if len(candles) < period + 1:
        return {
            "ratio": None,
            "state": "unknown",
        }

    volumes = [
        candle["volume_base"]
        for candle in candles
    ]

    current = volumes[-1]

    average = mean(
        volumes[-period - 1:-1]
    )

    if average <= 0:
        return {
            "ratio": None,
            "state": "unknown",
        }

    ratio = current / average

    if ratio >= 1.5:
        state = "expansion"
    elif ratio <= 0.7:
        state = "contraction"
    else:
        state = "normal"

    return {
        "current": current,
        "average": average,
        "ratio": ratio,
        "state": state,
    }


def detect_range(
    candles: List[Candle],
) -> Optional[Dict[str, Any]]:
    """
    Search the most recent 10-20 candles
    for a compact range.

    ATR is used to avoid calling every
    sideways-looking sequence a range.
    """

    current_atr = atr(
        candles,
        14,
    )

    if current_atr is None:
        return None

    close = candles[-1][
        "close"
    ]

    best = None

    for length in range(
        20,
        9,
        -1,
    ):
        if len(candles) < length:
            continue

        box = candles[-length:]

        high = max(
            candle["high"]
            for candle in box
        )

        low = min(
            candle["low"]
            for candle in box
        )

        width = high - low

        if width <= 0:
            continue

        width_atr = (
            width / current_atr
        )

        # Reject excessively wide structures.
        if width_atr > 6:
            continue

        tolerance = max(
            current_atr * 0.35,
            width * 0.08,
        )

        high_touches = sum(
            1
            for candle in box
            if (
                high
                - candle["high"]
            ) <= tolerance
        )

        low_touches = sum(
            1
            for candle in box
            if (
                candle["low"]
                - low
            ) <= tolerance
        )

        if (
            high_touches < 2
            or low_touches < 2
        ):
            continue

        position = (
            (close - low) / width
        )

        best = {
            "length": length,
            "high": high,
            "low": low,
            "mid": (
                high + low
            ) / 2,
            "width": width,
            "width_atr": width_atr,
            "high_touches": (
                high_touches
            ),
            "low_touches": (
                low_touches
            ),
            "position": position,
        }

        break

    return best


def swing_points(
    candles: List[Candle],
    window: int = 2,
) -> Dict[str, List[Dict[str, Any]]]:
    highs = []
    lows = []

    for index in range(
        window,
        len(candles) - window,
    ):
        current = candles[index]

        neighbours = candles[
            index - window:
            index + window + 1
        ]

        if current["high"] == max(
            item["high"]
            for item in neighbours
        ):
            highs.append(
                {
                    "index": index,
                    "price": (
                        current["high"]
                    ),
                }
            )

        if current["low"] == min(
            item["low"]
            for item in neighbours
        ):
            lows.append(
                {
                    "index": index,
                    "price": (
                        current["low"]
                    ),
                }
            )

    return {
        "highs": highs,
        "lows": lows,
    }


def dow_structure(
    candles: List[Candle],
) -> str:
    swings = swing_points(
        candles[-80:],
    )

    highs = swings["highs"]
    lows = swings["lows"]

    if (
        len(highs) < 2
        or len(lows) < 2
    ):
        return "UNCONFIRMED"

    previous_high = highs[-2][
        "price"
    ]
    current_high = highs[-1][
        "price"
    ]

    previous_low = lows[-2][
        "price"
    ]
    current_low = lows[-1][
        "price"
    ]

    if (
        current_high
        > previous_high
        and current_low
        > previous_low
    ):
        return "HH_HL"

    if (
        current_high
        < previous_high
        and current_low
        < previous_low
    ):
        return "LH_LL"

    return "MIXED_RANGE"


def candle_setup(
    candles: List[Candle],
) -> List[str]:
    if len(candles) < 3:
        return []

    current = candles[-1]
    previous = candles[-2]

    signals = []

    current_body = abs(
        current["close"]
        - current["open"]
    )

    previous_body = abs(
        previous["close"]
        - previous["open"]
    )

    bullish_engulfing = (
        previous["close"]
        < previous["open"]
        and current["close"]
        > current["open"]
        and current["open"]
        <= previous["close"]
        and current["close"]
        >= previous["open"]
    )

    bearish_engulfing = (
        previous["close"]
        > previous["open"]
        and current["close"]
        < current["open"]
        and current["open"]
        >= previous["close"]
        and current["close"]
        <= previous["open"]
    )

    if bullish_engulfing:
        signals.append(
            "bullish_engulfing"
        )

    if bearish_engulfing:
        signals.append(
            "bearish_engulfing"
        )

    if current_body > (
        previous_body * 2
    ):
        signals.append(
            "large_body"
        )

    upper_wick = (
        current["high"]
        - max(
            current["open"],
            current["close"],
        )
    )

    lower_wick = (
        min(
            current["open"],
            current["close"],
        )
        - current["low"]
    )

    if (
        lower_wick
        > max(
            current_body * 1.5,
            0,
        )
    ):
        signals.append(
            "lower_wick_rejection"
        )

    if (
        upper_wick
        > max(
            current_body * 1.5,
            0,
        )
    ):
        signals.append(
            "upper_wick_rejection"
        )

    return signals


def analyze_timeframe(
    candles: List[Candle],
) -> Dict[str, Any]:
    closes = [
        candle["close"]
        for candle in candles
    ]

    current_price = closes[-1]

    sma7 = sma(
        closes,
        7,
    )

    sma25 = sma(
        closes,
        25,
    )

    sma99 = sma(
        closes,
        99,
    )

    current_rsi = rsi(
        closes,
        14,
    )

    macd_data = macd(
        closes
    )

    current_atr = atr(
        candles,
        14,
    )

    atr_percent = (
        (
            current_atr
            / current_price
        )
        * 100
        if current_atr
        and current_price
        else None
    )

    if (
        sma7 is not None
        and sma25 is not None
        and sma99 is not None
    ):
        if (
            sma7
            > sma25
            > sma99
        ):
            sma_state = (
                "bullish"
            )
        elif (
            sma7
            < sma25
            < sma99
        ):
            sma_state = (
                "bearish"
            )
        else:
            sma_state = (
                "compression"
            )
    else:
        sma_state = "unknown"

    return {
        "price": current_price,

        "sma7": sma7,
        "sma25": sma25,
        "sma99": sma99,
        "sma_state": sma_state,

        "rsi": current_rsi,

        "macd": (
            macd_data["macd"]
        ),
        "macd_signal": (
            macd_data["signal"]
        ),
        "macd_histogram": (
            macd_data[
                "histogram"
            ]
        ),

        "atr": current_atr,
        "atr_percent": (
            atr_percent
        ),

        "volume": volume_state(
            candles
        ),

        "range": detect_range(
            candles
        ),

        "dow": dow_structure(
            candles
        ),

        "candles": candle_setup(
            candles
        ),
    }
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
    atr,
)
from app.engines.signals.xt_signal_provider import (
    fetch_candles,
)


def _closed_15m(
    candles: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    now = datetime.now(
        timezone.utc
    )

    duration = timedelta(
        minutes=15
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

        if (
            candle_time
            + duration
            <= now
        ):
            result.append(
                candle
            )

    return result


def detect_sharp_move(
    symbol: str,
) -> Optional[Dict[str, Any]]:
    """
    Detect unusual confirmed 15m movement.

    Detection uses:
    - closed-candle return
    - movement normalized by ATR
    - volume relative to recent average

    This produces an anomaly alert,
    not a trading entry signal.
    """

    candles = fetch_candles(
        symbol=symbol,
        timeframe="15m",
        limit=80,
    )

    closed = _closed_15m(
        candles
    )

    if len(closed) < 25:
        return None

    current = closed[-1]
    previous = closed[-2]

    previous_close = float(
        previous["close"]
    )

    current_close = float(
        current["close"]
    )

    if previous_close <= 0:
        return None

    change_percent = (
        (
            current_close
            - previous_close
        )
        / previous_close
        * 100
    )

    current_atr = atr(
        closed,
        14,
    )

    if (
        current_atr is None
        or current_atr <= 0
    ):
        return None

    price_move = abs(
        current_close
        - previous_close
    )

    atr_multiple = (
        price_move
        / current_atr
    )

    previous_volumes = [
        float(
            candle[
                "volume_base"
            ]
        )
        for candle in closed[
            -21:-1
        ]
    ]

    if not previous_volumes:
        return None

    average_volume = (
        sum(previous_volumes)
        / len(previous_volumes)
    )

    current_volume = float(
        current["volume_base"]
    )

    if average_volume <= 0:
        return None

    volume_ratio = (
        current_volume
        / average_volume
    )

    qualifies = (
        (
            atr_multiple >= 1.5
            and volume_ratio >= 1.8
        )
        or (
            abs(change_percent) >= 3.0
            and volume_ratio >= 1.5
        )
    )

    if not qualifies:
        return None

    if change_percent > 0:
        move_type = (
            "SHARP_PUMP"
        )
    else:
        move_type = (
            "SHARP_DUMP"
        )

    severity = "HIGH"

    if (
        atr_multiple >= 2.5
        and volume_ratio >= 2.5
    ):
        severity = "CRITICAL"

    return {
        "symbol": symbol.upper(),

        "type": move_type,

        "severity": severity,

        "timeframe": "15m",

        "change_percent": (
            change_percent
        ),

        "atr_multiple": (
            atr_multiple
        ),

        "volume_ratio": (
            volume_ratio
        ),

        "open": float(
            current["open"]
        ),

        "high": float(
            current["high"]
        ),

        "low": float(
            current["low"]
        ),

        "close": (
            current_close
        ),

        "candle_time": (
            current["time"]
        ),

        "provider": "XT",

        "note": (
            "Confirmed sharp-move alert. "
            "This is not an entry signal."
        ),
    }
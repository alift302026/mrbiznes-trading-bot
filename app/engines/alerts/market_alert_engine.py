import json
import math

import ccxt.async_support as ccxt
import pandas as pd


SUPPORTED_SYMBOLS = {
    "btc": "BTC/USDT",
    "eth": "ETH/USDT",
    "bnb": "BNB/USDT",
    "sol": "SOL/USDT",
    "xrp": "XRP/USDT",
    "doge": "DOGE/USDT",
    "ada": "ADA/USDT",
    "trx": "TRX/USDT",
    "link": "LINK/USDT",
    "avax": "AVAX/USDT",
}


SUPPORTED_TIMEFRAMES = {
    "15m",
    "1h",
    "4h",
    "1d",
}


# ============================================================
# PARAMETERS
# ============================================================

def get_parameters(alert):
    raw = getattr(
        alert,
        "parameters",
        None,
    )

    if not raw:
        return {}

    if isinstance(raw, dict):
        return raw

    try:
        result = json.loads(raw)

        if isinstance(result, dict):
            return result

    except (
        TypeError,
        ValueError,
        json.JSONDecodeError,
    ):
        pass

    return {}


def safe_int(
    value,
    default,
    minimum=1,
    maximum=500,
):
    try:
        value = int(value)
    except (TypeError, ValueError):
        return default

    return max(
        minimum,
        min(
            value,
            maximum,
        ),
    )


def safe_float(
    value,
    default,
):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return default

    if not math.isfinite(value):
        return default

    return value


# ============================================================
# INDICATORS
# ============================================================

def ema(
    series,
    period,
):
    return series.ewm(
        span=period,
        adjust=False,
    ).mean()


def calculate_rsi(
    series,
    period=14,
):
    delta = series.diff()

    gain = delta.clip(
        lower=0,
    )

    loss = (
        -delta.clip(
            upper=0,
        )
    )

    avg_gain = gain.ewm(
        alpha=1 / period,
        adjust=False,
        min_periods=period,
    ).mean()

    avg_loss = loss.ewm(
        alpha=1 / period,
        adjust=False,
        min_periods=period,
    ).mean()

    rs = (
        avg_gain
        / avg_loss.replace(
            0,
            float("nan"),
        )
    )

    result = (
        100
        - (
            100
            / (1 + rs)
        )
    )

    return result.fillna(50.0)


def calculate_macd(
    series,
    fast=12,
    slow=26,
    signal=9,
):
    fast_line = ema(
        series,
        fast,
    )

    slow_line = ema(
        series,
        slow,
    )

    macd_line = (
        fast_line
        - slow_line
    )

    signal_line = ema(
        macd_line,
        signal,
    )

    return (
        macd_line,
        signal_line,
    )


def calculate_atr(
    df,
    period=14,
):
    previous_close = (
        df["close"].shift(1)
    )

    high_low = (
        df["high"]
        - df["low"]
    )

    high_close = (
        df["high"]
        - previous_close
    ).abs()

    low_close = (
        df["low"]
        - previous_close
    ).abs()

    true_range = pd.concat(
        [
            high_low,
            high_close,
            low_close,
        ],
        axis=1,
    ).max(axis=1)

    return true_range.ewm(
        alpha=1 / period,
        adjust=False,
        min_periods=period,
    ).mean()


# ============================================================
# MARKET DATA
# ============================================================

async def fetch_market_snapshot(
    symbol,
    timeframe="1h",
    parameters=None,
):
    if symbol not in SUPPORTED_SYMBOLS.values():
        raise ValueError(
            "Unsupported symbol"
        )

    if timeframe not in SUPPORTED_TIMEFRAMES:
        raise ValueError(
            "Unsupported timeframe"
        )

    parameters = parameters or {}

    rsi_period = safe_int(
        parameters.get(
            "rsi_period",
            parameters.get(
                "period",
                14,
            ),
        ),
        14,
        2,
        100,
    )

    ema_fast = safe_int(
        parameters.get(
            "ema_fast",
            parameters.get(
                "fast",
                20,
            ),
        ),
        20,
        2,
        300,
    )

    ema_slow = safe_int(
        parameters.get(
            "ema_slow",
            parameters.get(
                "slow",
                50,
            ),
        ),
        50,
        2,
        500,
    )

    atr_period = safe_int(
        parameters.get(
            "atr_period",
            parameters.get(
                "period",
                14,
            ),
        ),
        14,
        2,
        100,
    )

    volume_period = safe_int(
        parameters.get(
            "volume_period",
            20,
        ),
        20,
        2,
        200,
    )

    required_limit = max(
        220,
        ema_fast + 30,
        ema_slow + 30,
        rsi_period + 30,
        atr_period + 30,
        volume_period + 30,
    )

    required_limit = min(
        required_limit,
        1000,
    )

    exchange = ccxt.binance(
        {
            "enableRateLimit": True,
            "timeout": 20000,
        }
    )

    try:
        candles = await exchange.fetch_ohlcv(
            symbol,
            timeframe=timeframe,
            limit=required_limit,
        )

    finally:
        await exchange.close()

    if len(candles) < 60:
        raise RuntimeError(
            "Not enough market data"
        )

    df = pd.DataFrame(
        candles,
        columns=[
            "timestamp",
            "open",
            "high",
            "low",
            "close",
            "volume",
        ],
    )

    for column in [
        "open",
        "high",
        "low",
        "close",
        "volume",
    ]:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    df = df.dropna(
        subset=[
            "high",
            "low",
            "close",
            "volume",
        ]
    ).reset_index(drop=True)

    if len(df) < 60:
        raise RuntimeError(
            "Not enough valid market data"
        )

    df["ema_fast"] = ema(
        df["close"],
        ema_fast,
    )

    df["ema_slow"] = ema(
        df["close"],
        ema_slow,
    )

    df["rsi"] = calculate_rsi(
        df["close"],
        rsi_period,
    )

    (
        df["macd"],
        df["macd_signal"],
    ) = calculate_macd(
        df["close"],
    )

    df["atr"] = calculate_atr(
        df,
        atr_period,
    )

    df["atr_percent"] = (
        df["atr"]
        / df["close"]
        * 100
    )

    df["volume_average"] = (
        df["volume"]
        .rolling(
            volume_period
        )
        .mean()
    )

    current = df.iloc[-1]
    previous = df.iloc[-2]

    return {
        "price": float(
            current["close"]
        ),

        "ema_fast": float(
            current["ema_fast"]
        ),

        "ema_slow": float(
            current["ema_slow"]
        ),

        "previous_ema_fast": float(
            previous["ema_fast"]
        ),

        "previous_ema_slow": float(
            previous["ema_slow"]
        ),

        # Backward compatibility
        "ema20": float(
            current["ema_fast"]
        ),

        "ema50": float(
            current["ema_slow"]
        ),

        "previous_ema20": float(
            previous["ema_fast"]
        ),

        "previous_ema50": float(
            previous["ema_slow"]
        ),

        "rsi": float(
            current["rsi"]
        ),

        "macd": float(
            current["macd"]
        ),

        "macd_signal": float(
            current["macd_signal"]
        ),

        "previous_macd": float(
            previous["macd"]
        ),

        "previous_macd_signal": float(
            previous["macd_signal"]
        ),

        "atr": float(
            current["atr"]
        ),

        "atr_percent": float(
            current["atr_percent"]
        ),

        "volume": float(
            current["volume"]
        ),

        "volume_average": float(
            current["volume_average"]
        ),

        "settings": {
            "rsi_period":
                rsi_period,

            "ema_fast":
                ema_fast,

            "ema_slow":
                ema_slow,

            "atr_period":
                atr_period,

            "volume_period":
                volume_period,
        },
    }


# ============================================================
# ALERT EVALUATION
# ============================================================

def evaluate_alert(
    alert,
    snapshot,
):
    alert_type = (
        alert.alert_type
    )

    params = get_parameters(
        alert
    )

    # --------------------------------------------------------
    # PRICE
    # --------------------------------------------------------

    if alert_type == "price_above":
        target = safe_float(
            alert.target_value,
            0.0,
        )

        triggered = (
            snapshot["price"]
            >= target
        )

        return (
            triggered,
            "above"
            if triggered
            else "below",
        )

    if alert_type == "price_below":
        target = safe_float(
            alert.target_value,
            0.0,
        )

        triggered = (
            snapshot["price"]
            <= target
        )

        return (
            triggered,
            "below"
            if triggered
            else "above",
        )

    # --------------------------------------------------------
    # EMA CROSS
    # --------------------------------------------------------

    if alert_type == "ema_bull":
        triggered = (
            snapshot[
                "previous_ema_fast"
            ]
            <= snapshot[
                "previous_ema_slow"
            ]
            and
            snapshot["ema_fast"]
            > snapshot["ema_slow"]
        )

        state = (
            "bull"
            if snapshot["ema_fast"]
            > snapshot["ema_slow"]
            else "bear"
        )

        return triggered, state

    if alert_type == "ema_bear":
        triggered = (
            snapshot[
                "previous_ema_fast"
            ]
            >= snapshot[
                "previous_ema_slow"
            ]
            and
            snapshot["ema_fast"]
            < snapshot["ema_slow"]
        )

        state = (
            "bear"
            if snapshot["ema_fast"]
            < snapshot["ema_slow"]
            else "bull"
        )

        return triggered, state

    # --------------------------------------------------------
    # RSI
    # --------------------------------------------------------

    if alert_type in {
        "rsi_high",
        "rsi_above",
    }:
        threshold = safe_float(
            params.get(
                "value",
                alert.target_value
                if alert.target_value
                is not None
                else 70,
            ),
            70.0,
        )

        triggered = (
            snapshot["rsi"]
            >= threshold
        )

        return (
            triggered,
            "above"
            if triggered
            else "below",
        )

    if alert_type in {
        "rsi_low",
        "rsi_below",
    }:
        threshold = safe_float(
            params.get(
                "value",
                alert.target_value
                if alert.target_value
                is not None
                else 30,
            ),
            30.0,
        )

        triggered = (
            snapshot["rsi"]
            <= threshold
        )

        return (
            triggered,
            "below"
            if triggered
            else "above",
        )

    # --------------------------------------------------------
    # MACD
    # --------------------------------------------------------

    if alert_type == "macd_bull":
        triggered = (
            snapshot["previous_macd"]
            <= snapshot[
                "previous_macd_signal"
            ]
            and
            snapshot["macd"]
            > snapshot["macd_signal"]
        )

        state = (
            "bull"
            if snapshot["macd"]
            > snapshot["macd_signal"]
            else "bear"
        )

        return triggered, state

    if alert_type == "macd_bear":
        triggered = (
            snapshot["previous_macd"]
            >= snapshot[
                "previous_macd_signal"
            ]
            and
            snapshot["macd"]
            < snapshot["macd_signal"]
        )

        state = (
            "bear"
            if snapshot["macd"]
            < snapshot["macd_signal"]
            else "bull"
        )

        return triggered, state

    # --------------------------------------------------------
    # VOLUME
    # --------------------------------------------------------

    if alert_type == "volume_spike":
        average = (
            snapshot[
                "volume_average"
            ]
        )

        if (
            not math.isfinite(average)
            or average <= 0
        ):
            return False, "normal"

        ratio = (
            snapshot["volume"]
            / average
        )

        multiplier = safe_float(
            params.get(
                "multiplier",
                alert.target_value
                if alert.target_value
                is not None
                else 1.8,
            ),
            1.8,
        )

        triggered = (
            ratio >= multiplier
        )

        return (
            triggered,
            "spike"
            if triggered
            else "normal",
        )

    # --------------------------------------------------------
    # ATR RAW
    # --------------------------------------------------------

    if alert_type == "atr_above":
        threshold = safe_float(
            params.get(
                "value",
                alert.target_value,
            ),
            1.0,
        )

        triggered = (
            snapshot["atr"]
            >= threshold
        )

        return (
            triggered,
            "above"
            if triggered
            else "below",
        )

    if alert_type == "atr_below":
        threshold = safe_float(
            params.get(
                "value",
                alert.target_value,
            ),
            1.0,
        )

        triggered = (
            snapshot["atr"]
            <= threshold
        )

        return (
            triggered,
            "below"
            if triggered
            else "above",
        )

    # --------------------------------------------------------
    # ATR PERCENT
    # --------------------------------------------------------

    if alert_type == "atr_percent_above":
        threshold = safe_float(
            params.get(
                "value",
                alert.target_value,
            ),
            1.0,
        )

        triggered = (
            snapshot[
                "atr_percent"
            ]
            >= threshold
        )

        return (
            triggered,
            "above"
            if triggered
            else "below",
        )

    if alert_type == "atr_percent_below":
        threshold = safe_float(
            params.get(
                "value",
                alert.target_value,
            ),
            1.0,
        )

        triggered = (
            snapshot[
                "atr_percent"
            ]
            <= threshold
        )

        return (
            triggered,
            "below"
            if triggered
            else "above",
        )

    return False, "unknown"
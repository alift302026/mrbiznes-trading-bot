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
        lower=0
    )

    loss = (
        -delta.clip(
            upper=0
        )
    )

    avg_gain = gain.ewm(
        alpha=1 / period,
        adjust=False,
    ).mean()

    avg_loss = loss.ewm(
        alpha=1 / period,
        adjust=False,
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

    return result.fillna(50)


def calculate_macd(
    series,
):
    fast = ema(
        series,
        12,
    )

    slow = ema(
        series,
        26,
    )

    macd_line = (
        fast - slow
    )

    signal_line = ema(
        macd_line,
        9,
    )

    return (
        macd_line,
        signal_line,
    )


async def fetch_market_snapshot(
    symbol,
    timeframe="1h",
):
    if (
        symbol
        not in SUPPORTED_SYMBOLS.values()
    ):
        raise ValueError(
            "Unsupported symbol"
        )

    if (
        timeframe
        not in SUPPORTED_TIMEFRAMES
    ):
        raise ValueError(
            "Unsupported timeframe"
        )

    exchange = ccxt.binance(
        {
            "enableRateLimit": True,
            "timeout": 20000,
        }
    )

    try:
        candles = (
            await exchange.fetch_ohlcv(
                symbol,
                timeframe=timeframe,
                limit=220,
            )
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

    numeric_columns = [
        "open",
        "high",
        "low",
        "close",
        "volume",
    ]

    for column in numeric_columns:
        df[column] = pd.to_numeric(
            df[column],
            errors="coerce",
        )

    df["ema20"] = ema(
        df["close"],
        20,
    )

    df["ema50"] = ema(
        df["close"],
        50,
    )

    df["rsi"] = calculate_rsi(
        df["close"],
    )

    (
        df["macd"],
        df["macd_signal"],
    ) = calculate_macd(
        df["close"]
    )

    df["volume_average"] = (
        df["volume"]
        .rolling(20)
        .mean()
    )

    current = df.iloc[-1]
    previous = df.iloc[-2]

    return {
        "price":
            float(
                current["close"]
            ),

        "ema20":
            float(
                current["ema20"]
            ),

        "ema50":
            float(
                current["ema50"]
            ),

        "previous_ema20":
            float(
                previous["ema20"]
            ),

        "previous_ema50":
            float(
                previous["ema50"]
            ),

        "rsi":
            float(
                current["rsi"]
            ),

        "macd":
            float(
                current["macd"]
            ),

        "macd_signal":
            float(
                current[
                    "macd_signal"
                ]
            ),

        "previous_macd":
            float(
                previous["macd"]
            ),

        "previous_macd_signal":
            float(
                previous[
                    "macd_signal"
                ]
            ),

        "volume":
            float(
                current["volume"]
            ),

        "volume_average":
            float(
                current[
                    "volume_average"
                ]
            ),
    }


def evaluate_alert(
    alert,
    snapshot,
):
    alert_type = (
        alert.alert_type
    )

    if alert_type == "price_above":
        triggered = (
            snapshot["price"]
            >= alert.target_value
        )

        state = (
            "above"
            if triggered
            else "below"
        )

        return triggered, state

    if alert_type == "price_below":
        triggered = (
            snapshot["price"]
            <= alert.target_value
        )

        state = (
            "below"
            if triggered
            else "above"
        )

        return triggered, state

    if alert_type == "ema_bull":
        triggered = (
            snapshot["previous_ema20"]
            <= snapshot["previous_ema50"]
            and
            snapshot["ema20"]
            > snapshot["ema50"]
        )

        state = (
            "bull"
            if snapshot["ema20"]
            > snapshot["ema50"]
            else "bear"
        )

        return triggered, state

    if alert_type == "ema_bear":
        triggered = (
            snapshot["previous_ema20"]
            >= snapshot["previous_ema50"]
            and
            snapshot["ema20"]
            < snapshot["ema50"]
        )

        state = (
            "bear"
            if snapshot["ema20"]
            < snapshot["ema50"]
            else "bull"
        )

        return triggered, state

    if alert_type == "rsi_high":
        triggered = (
            snapshot["rsi"]
            >= 70
        )

        state = (
            "high"
            if triggered
            else "normal"
        )

        return triggered, state

    if alert_type == "rsi_low":
        triggered = (
            snapshot["rsi"]
            <= 30
        )

        state = (
            "low"
            if triggered
            else "normal"
        )

        return triggered, state

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

    if alert_type == "volume_spike":
        average = (
            snapshot[
                "volume_average"
            ]
        )

        if average <= 0:
            return False, "normal"

        ratio = (
            snapshot["volume"]
            / average
        )

        triggered = (
            ratio >= 1.8
        )

        state = (
            "spike"
            if triggered
            else "normal"
        )

        return triggered, state

    return False, "unknown"
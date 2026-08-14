import os

import httpx
import pandas as pd

from dotenv import (
    load_dotenv,
)


load_dotenv()


TWELVE_DATA_API_KEY = os.getenv(
    "TWELVE_DATA_API_KEY"
)


TWELVE_DATA_URL = (
    "https://api.twelvedata.com"
)


SUPPORTED_FOREX_TIMEFRAMES = {
    "15m": "15min",
    "1h": "1h",
    "4h": "4h",
    "1d": "1day",
}


POPULAR_FOREX = {
    "eurusd": "EUR/USD",
    "gbpusd": "GBP/USD",
    "usdjpy": "USD/JPY",
    "audusd": "AUD/USD",
    "usdcad": "USD/CAD",
    "usdchf": "USD/CHF",
    "nzdusd": "NZD/USD",
    "eurjpy": "EUR/JPY",
    "gbpjpy": "GBP/JPY",
    "eurgbp": "EUR/GBP",
}


# ============================================================
# KEY
# ============================================================

def check_key():

    if not TWELVE_DATA_API_KEY:

        raise RuntimeError(
            "TWELVE_DATA_API_KEY is missing"
        )


# ============================================================
# NORMALIZE
# ============================================================

def normalize_forex_symbol(
    value,
):

    value = (
        value
        .strip()
        .upper()
        .replace(" ", "")
        .replace("-", "/")
        .replace("_", "/")
    )

    if not value:
        return None

    # EURUSD -> EUR/USD
    if "/" not in value:

        if len(value) == 6:

            value = (
                value[:3]
                + "/"
                + value[3:]
            )

        else:

            return None

    parts = value.split("/")

    if len(parts) != 2:
        return None

    base = parts[0]
    quote = parts[1]

    if (
        len(base) != 3
        or len(quote) != 3
        or not base.isalpha()
        or not quote.isalpha()
    ):

        return None

    return (
        f"{base}/{quote}"
    )


# ============================================================
# REQUEST
# ============================================================

async def twelve_request(
    endpoint,
    params,
):

    check_key()

    request_params = dict(
        params
    )

    request_params[
        "apikey"
    ] = TWELVE_DATA_API_KEY

    async with httpx.AsyncClient(
        timeout=20.0
    ) as client:

        response = await client.get(
            (
                f"{TWELVE_DATA_URL}"
                f"/{endpoint}"
            ),
            params=request_params,
        )

        response.raise_for_status()

        data = response.json()

    if (
        isinstance(data, dict)
        and data.get("status")
        == "error"
    ):

        raise RuntimeError(
            data.get(
                "message",
                "Twelve Data error",
            )
        )

    return data


# ============================================================
# VALIDATE FOREX
# ============================================================

async def validate_forex_symbol(
    value,
):

    symbol = normalize_forex_symbol(
        value
    )

    if not symbol:
        return None

    try:

        data = await twelve_request(
            "quote",
            {
                "symbol":
                    symbol,
            },
        )

    except Exception:

        return None

    if not isinstance(
        data,
        dict,
    ):

        return None

    if not (
        data.get("close")
        or data.get("price")
    ):

        return None

    return symbol


# ============================================================
# QUOTE
# ============================================================

async def forex_quote(
    symbol,
):

    symbol = normalize_forex_symbol(
        symbol
    )

    if not symbol:

        raise ValueError(
            "Invalid forex symbol"
        )

    data = await twelve_request(
        "quote",
        {
            "symbol":
                symbol,
        },
    )

    price = (
        data.get("close")
        or data.get("price")
    )

    if price is None:

        raise RuntimeError(
            "Forex price unavailable"
        )

    return {
        "symbol":
            symbol,

        "price":
            float(price),

        "provider":
            "Twelve Data",
    }


# ============================================================
# CANDLES
# ============================================================

async def forex_candles(
    symbol,
    timeframe="1h",
    outputsize=250,
):

    symbol = normalize_forex_symbol(
        symbol
    )

    if not symbol:

        raise ValueError(
            "Invalid forex symbol"
        )

    if (
        timeframe
        not in SUPPORTED_FOREX_TIMEFRAMES
    ):

        raise ValueError(
            "Unsupported forex timeframe"
        )

    outputsize = max(
        60,
        min(
            int(outputsize),
            5000,
        ),
    )

    data = await twelve_request(
        "time_series",
        {
            "symbol":
                symbol,

            "interval":
                SUPPORTED_FOREX_TIMEFRAMES[
                    timeframe
                ],

            "outputsize":
                outputsize,

            "order":
                "ASC",
        },
    )

    values = (
        data.get("values")
        or []
    )

    if len(values) < 60:

        raise RuntimeError(
            "Not enough forex candles"
        )

    df = pd.DataFrame(
        values
    )

    required = {
        "open",
        "high",
        "low",
        "close",
    }

    if not required.issubset(
        df.columns
    ):

        raise RuntimeError(
            "Invalid Twelve Data candles"
        )

    for column in [
        "open",
        "high",
        "low",
        "close",
    ]:

        df[column] = (
            pd.to_numeric(
                df[column],
                errors="coerce",
            )
        )

    if "volume" in df.columns:

        df["volume"] = (
            pd.to_numeric(
                df["volume"],
                errors="coerce",
            )
        )

    else:

        # Spot Forex often has no centralized volume.
        df["volume"] = float("nan")

    df = (
        df.dropna(
            subset=[
                "open",
                "high",
                "low",
                "close",
            ]
        )
        .reset_index(
            drop=True
        )
    )

    if len(df) < 60:

        raise RuntimeError(
            "Not enough valid forex candles"
        )

    return df
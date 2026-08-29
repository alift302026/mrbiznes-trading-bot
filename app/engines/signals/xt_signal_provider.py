from __future__ import annotations

import threading
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


BASE_URL = "https://sapi.xt.com/v4/public/kline"
TIMEOUT = 20
CACHE_TTL_SECONDS = 60

TIMEFRAMES = {
    "15m": "15m",
    "1h": "1h",
    "4h": "4h",
    "1w": "1w",
}


class XTSignalProviderError(RuntimeError):
    pass


_CACHE: Dict[
    Tuple[str, str, int],
    Tuple[float, List[Dict[str, Any]]],
] = {}

_CACHE_LOCK = threading.Lock()


def _build_session() -> requests.Session:
    session = requests.Session()

    retry = Retry(
        total=2,
        connect=2,
        read=2,
        status=2,
        backoff_factor=0.4,
        status_forcelist=(
            429,
            500,
            502,
            503,
            504,
        ),
        allowed_methods=frozenset(
            {"GET"}
        ),
        raise_on_status=False,
    )

    adapter = HTTPAdapter(
        max_retries=retry,
        pool_connections=20,
        pool_maxsize=20,
    )

    session.mount(
        "https://",
        adapter,
    )

    session.headers.update(
        {
            "Accept": "application/json",
            "User-Agent": (
                "MrBiznes/1.0"
            ),
        }
    )

    return session


_SESSION = _build_session()


def normalize_symbol(
    symbol: str,
) -> str:
    value = str(
        symbol or ""
    ).strip().lower()

    if "/" in value:
        base, quote = value.split(
            "/",
            1,
        )

        value = (
            f"{base}_{quote}"
        )

    elif "_" not in value:

        if value.endswith(
            "usdt"
        ):
            value = (
                value[:-4]
                + "_usdt"
            )

        else:
            value = (
                value
                + "_usdt"
            )

    if not value:
        raise ValueError(
            "XT symbol is required"
        )

    return value


def _float(
    value: Any,
) -> float:
    try:
        return float(value)

    except (
        TypeError,
        ValueError,
    ) as exc:
        raise XTSignalProviderError(
            "Invalid XT numeric value: "
            f"{value}"
        ) from exc


def _copy_candles(
    candles: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    return [
        dict(candle)
        for candle in candles
    ]


def _cache_get(
    key: Tuple[str, str, int],
) -> List[Dict[str, Any]] | None:
    now = time.monotonic()

    with _CACHE_LOCK:
        cached = _CACHE.get(key)

        if cached is None:
            return None

        created_at, candles = cached

        if (
            now - created_at
            > CACHE_TTL_SECONDS
        ):
            _CACHE.pop(
                key,
                None,
            )

            return None

        return _copy_candles(
            candles
        )


def _cache_set(
    key: Tuple[str, str, int],
    candles: List[Dict[str, Any]],
) -> None:
    with _CACHE_LOCK:
        _CACHE[key] = (
            time.monotonic(),
            _copy_candles(
                candles
            ),
        )


def clear_cache() -> None:
    with _CACHE_LOCK:
        _CACHE.clear()


def fetch_candles(
    symbol: str,
    timeframe: str = "15m",
    limit: int = 150,
    *,
    use_cache: bool = True,
) -> List[Dict[str, Any]]:
    if timeframe not in TIMEFRAMES:
        raise ValueError(
            "Unsupported timeframe: "
            f"{timeframe}"
        )

    limit = max(
        20,
        min(
            int(limit),
            500,
        ),
    )

    normalized_symbol = (
        normalize_symbol(
            symbol
        )
    )

    key = (
        normalized_symbol,
        timeframe,
        limit,
    )

    if use_cache:
        cached = _cache_get(
            key
        )

        if cached is not None:
            return cached

    params = {
        "symbol": (
            normalized_symbol
        ),
        "interval": (
            TIMEFRAMES[
                timeframe
            ]
        ),
        "limit": limit,
    }

    try:
        response = _SESSION.get(
            BASE_URL,
            params=params,
            timeout=TIMEOUT,
        )

    except requests.RequestException as exc:
        raise XTSignalProviderError(
            "XT request failed: "
            f"{exc}"
        ) from exc

    if response.status_code != 200:
        raise XTSignalProviderError(
            "XT HTTP "
            f"{response.status_code}: "
            f"{response.text[:300]}"
        )

    try:
        payload = response.json()

    except ValueError as exc:
        raise XTSignalProviderError(
            "XT returned invalid JSON"
        ) from exc

    if payload.get("rc") != 0:
        raise XTSignalProviderError(
            "XT API error: "
            f"{payload}"
        )

    result = payload.get(
        "result"
    )

    if not isinstance(
        result,
        list,
    ):
        raise XTSignalProviderError(
            "XT kline result "
            "is not a list"
        )

    candles: List[
        Dict[str, Any]
    ] = []

    for item in result:
        if not isinstance(
            item,
            dict,
        ):
            continue

        try:
            timestamp = int(
                item["t"]
            )

            candle = {
                "timestamp": (
                    timestamp
                ),

                "time": (
                    datetime.fromtimestamp(
                        timestamp
                        / 1000,
                        tz=timezone.utc,
                    )
                ),

                "open": _float(
                    item["o"]
                ),

                "high": _float(
                    item["h"]
                ),

                "low": _float(
                    item["l"]
                ),

                "close": _float(
                    item["c"]
                ),

                "volume_base": (
                    _float(
                        item.get(
                            "q",
                            0,
                        )
                    )
                ),

                "volume_quote": (
                    _float(
                        item.get(
                            "v",
                            0,
                        )
                    )
                ),

                "provider": "XT",

                "symbol": (
                    normalized_symbol
                ),

                "timeframe": (
                    timeframe
                ),
            }

            candles.append(
                candle
            )

        except (
            KeyError,
            TypeError,
            ValueError,
            XTSignalProviderError,
        ):
            continue

    if len(candles) < 20:
        raise XTSignalProviderError(
            "XT returned too few "
            "valid candles"
        )

    # XT response is observed newest-first.
    # Indicators require chronological order.
    candles.sort(
        key=lambda item: (
            item["timestamp"]
        )
    )

    if use_cache:
        _cache_set(
            key,
            candles,
        )

    return _copy_candles(
        candles
    )


def fetch_multi_timeframe(
    symbol: str,
    limit: int = 150,
    *,
    use_cache: bool = True,
) -> Dict[
    str,
    List[Dict[str, Any]],
]:
    result: Dict[
        str,
        List[Dict[str, Any]],
    ] = {}

    for timeframe in (
        "15m",
        "1h",
        "4h",
        "1w",
    ):
        result[
            timeframe
        ] = fetch_candles(
            symbol=symbol,
            timeframe=timeframe,
            limit=limit,
            use_cache=use_cache,
        )

    return result
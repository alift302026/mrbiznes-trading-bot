import os
from typing import Any, Dict, Iterable, List, Optional

import requests


BASE_URL = "https://api.livecoinwatch.com"
TIMEOUT = 20


class LiveCoinWatchError(RuntimeError):
    """Raised when LiveCoinWatch cannot provide valid market data."""


def _api_key() -> str:
    key = os.getenv("LIVECOINWATCH_API_KEY", "").strip()

    if not key:
        raise LiveCoinWatchError(
            "LIVECOINWATCH_API_KEY is missing"
        )

    return key


def _headers() -> Dict[str, str]:
    return {
        "content-type": "application/json",
        "x-api-key": _api_key(),
    }


def _post(endpoint: str, payload: Dict[str, Any]) -> Any:
    url = f"{BASE_URL}{endpoint}"

    try:
        response = requests.post(
            url,
            headers=_headers(),
            json=payload,
            timeout=TIMEOUT,
        )
    except requests.RequestException as exc:
        raise LiveCoinWatchError(
            f"LiveCoinWatch request failed: {exc}"
        ) from exc

    if response.status_code != 200:
        message = response.text[:500]

        raise LiveCoinWatchError(
            f"LiveCoinWatch HTTP {response.status_code}: {message}"
        )

    try:
        return response.json()
    except ValueError as exc:
        raise LiveCoinWatchError(
            "LiveCoinWatch returned invalid JSON"
        ) from exc


def _normalize_code(code: str) -> str:
    value = str(code or "").strip().upper()

    if "/" in value:
        value = value.split("/", 1)[0]

    if value.endswith("USDT") and "/" not in str(code):
        value = value[:-4]

    if not value:
        raise ValueError("Coin code is required")

    return value


def _delta_percent(value: Any) -> Optional[float]:
    """
    LiveCoinWatch delta values are multipliers.

    Example:
        1.05 -> +5%
        0.97 -> -3%
    """
    if value is None:
        return None

    try:
        return (float(value) - 1.0) * 100.0
    except (TypeError, ValueError):
        return None


def _number(value: Any) -> Optional[float]:
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalize_coin(
    data: Dict[str, Any],
    fallback_code: Optional[str] = None,
) -> Dict[str, Any]:
    delta = data.get("delta") or {}

    code = data.get("code") or fallback_code

    return {
        "provider": "livecoinwatch",
        "code": _normalize_code(code) if code else None,
        "name": data.get("name"),
        "rank": data.get("rank"),
        "price_usd": _number(data.get("rate")),
        "volume_24h_usd": _number(data.get("volume")),
        "market_cap_usd": _number(data.get("cap")),
        "liquidity_usd": _number(data.get("liquidity")),
        "circulating_supply": _number(
            data.get("circulatingSupply")
        ),
        "total_supply": _number(data.get("totalSupply")),
        "max_supply": _number(data.get("maxSupply")),
        "ath_usd": _number(data.get("allTimeHighUSD")),
        "exchanges": data.get("exchanges"),
        "markets": data.get("markets"),
        "pairs": data.get("pairs"),
        "change_1h_percent": _delta_percent(
            delta.get("hour")
        ),
        "change_24h_percent": _delta_percent(
            delta.get("day")
        ),
        "change_7d_percent": _delta_percent(
            delta.get("week")
        ),
        "change_30d_percent": _delta_percent(
            delta.get("month")
        ),
        "change_90d_percent": _delta_percent(
            delta.get("quarter")
        ),
        "change_1y_percent": _delta_percent(
            delta.get("year")
        ),
    }


def get_coin(
    code: str,
    meta: bool = True,
) -> Dict[str, Any]:
    """
    Fetch detailed LiveCoinWatch context for one crypto asset.
    """
    normalized_code = _normalize_code(code)

    data = _post(
        "/coins/single",
        {
            "currency": "USD",
            "code": normalized_code,
            "meta": bool(meta),
        },
    )

    if not isinstance(data, dict):
        raise LiveCoinWatchError(
            "Unexpected response for single coin"
        )

    return _normalize_coin(
        data,
        fallback_code=normalized_code,
    )


def get_coins(
    codes: Iterable[str],
) -> List[Dict[str, Any]]:
    """
    Fetch multiple assets in one request.

    Intended for signal scanning to avoid one API request per coin.
    """
    normalized_codes: List[str] = []

    for code in codes:
        normalized = _normalize_code(code)

        if normalized not in normalized_codes:
            normalized_codes.append(normalized)

    if not normalized_codes:
        return []

    data = _post(
        "/coins/map",
        {
            "currency": "USD",
            "codes": normalized_codes,
            "sort": "rank",
            "order": "ascending",
            "offset": 0,
            "limit": len(normalized_codes),
            "meta": False,
        },
    )

    if not isinstance(data, list):
        raise LiveCoinWatchError(
            "Unexpected response for coin map"
        )

    result = []

    for item in data:
        if isinstance(item, dict):
            result.append(_normalize_coin(item))

    return result
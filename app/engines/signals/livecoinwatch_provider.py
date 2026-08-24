from __future__ import annotations

import os
from typing import Any, Dict, Iterable, List, Optional

import requests


BASE_URL = "https://api.livecoinwatch.com"
TIMEOUT = 20


class LiveCoinWatchError(RuntimeError):
    pass


def _api_key() -> str:
    key = os.getenv(
        "LIVECOINWATCH_API_KEY",
        "",
    ).strip()

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


def _post(
    endpoint: str,
    payload: Dict[str, Any],
) -> Any:
    try:
        response = requests.post(
            f"{BASE_URL}{endpoint}",
            headers=_headers(),
            json=payload,
            timeout=TIMEOUT,
        )
    except requests.RequestException as exc:
        raise LiveCoinWatchError(
            f"LiveCoinWatch request failed: {exc}"
        ) from exc

    if response.status_code != 200:
        raise LiveCoinWatchError(
            "LiveCoinWatch HTTP "
            f"{response.status_code}: "
            f"{response.text[:500]}"
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
    elif value.endswith("USDT"):
        value = value[:-4]

    if not value:
        raise ValueError(
            "Coin code is required"
        )

    return value


def _number(value: Any) -> Optional[float]:
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _delta_percent(
    value: Any,
) -> Optional[float]:
    value = _number(value)

    if value is None:
        return None

    # LiveCoinWatch delta is a multiplier.
    # 1.05 = +5%, 0.97 = -3%.
    return (value - 1.0) * 100.0


def _normalize_coin(
    data: Dict[str, Any],
    fallback_code: Optional[str] = None,
) -> Dict[str, Any]:
    delta = data.get("delta") or {}

    code = (
        data.get("code")
        or fallback_code
    )

    return {
        "provider": "livecoinwatch",
        "code": (
            _normalize_code(code)
            if code
            else None
        ),
        "name": data.get("name"),
        "rank": data.get("rank"),
        "price_usd": _number(
            data.get("rate")
        ),
        "volume_24h_usd": _number(
            data.get("volume")
        ),
        "market_cap_usd": _number(
            data.get("cap")
        ),
        "liquidity_usd": _number(
            data.get("liquidity")
        ),
        "circulating_supply": _number(
            data.get("circulatingSupply")
        ),
        "total_supply": _number(
            data.get("totalSupply")
        ),
        "max_supply": _number(
            data.get("maxSupply")
        ),
        "ath_usd": _number(
            data.get("allTimeHighUSD")
        ),
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
    normalized = _normalize_code(code)

    data = _post(
        "/coins/single",
        {
            "currency": "USD",
            "code": normalized,
            "meta": bool(meta),
        },
    )

    if not isinstance(data, dict):
        raise LiveCoinWatchError(
            "Unexpected single coin response"
        )

    return _normalize_coin(
        data,
        fallback_code=normalized,
    )


def get_coins(
    codes: Iterable[str],
) -> List[Dict[str, Any]]:
    normalized_codes: List[str] = []

    for code in codes:
        value = _normalize_code(code)

        if value not in normalized_codes:
            normalized_codes.append(value)

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
            "Unexpected coin map response"
        )

    result = []

    for item in data:
        if not isinstance(item, dict):
            continue

        if not item.get("code"):
            continue

        try:
            result.append(_normalize_coin(item))
        except (TypeError, ValueError):
            continue

    return result


def list_coins(
    *,
    sort: str = "volume",
    order: str = "descending",
    offset: int = 0,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """
    Market scanner endpoint.

    Useful for:
    - volume leaders
    - biggest movers
    - momentum scanning
    - market-cap filtering
    """

    limit = max(
        1,
        min(int(limit), 200),
    )

    offset = max(
        0,
        int(offset),
    )

    allowed_sort = {
        "rank",
        "price",
        "volume",
        "cap",
    }

    if sort not in allowed_sort:
        raise ValueError(
            f"Unsupported sort: {sort}"
        )

    if order not in {
        "ascending",
        "descending",
    }:
        raise ValueError(
            "order must be ascending "
            "or descending"
        )

    data = _post(
        "/coins/list",
        {
            "currency": "USD",
            "sort": sort,
            "order": order,
            "offset": offset,
            "limit": limit,
            "meta": False,
        },
    )

    if not isinstance(data, list):
        raise LiveCoinWatchError(
            "Unexpected coin list response"
        )

    result = []

    for item in data:
        if not isinstance(item, dict):
            continue

        if not item.get("code"):
            continue

        try:
            result.append(_normalize_coin(item))
        except (TypeError, ValueError):
            continue

    return result
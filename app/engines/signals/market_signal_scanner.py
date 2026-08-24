from __future__ import annotations

from typing import Any, Dict, List

from app.engines.signals.livecoinwatch_provider import (
    get_coin,
    list_coins,
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


def _valid_coin(
    coin: Dict[str, Any],
    minimum_cap: float,
) -> bool:
    code = str(
        coin.get("code") or ""
    ).upper()

    cap = coin.get("market_cap_usd")
    volume = coin.get("volume_24h_usd")

    if not code:
        return False

    if code in STABLECOINS:
        return False

    if code.startswith("_"):
        return False

    if cap is None:
        return False

    if cap < minimum_cap:
        return False

    if volume is None or volume <= 0:
        return False

    return True


def _activity_ratio(
    coin: Dict[str, Any],
) -> float:
    volume = (
        coin.get("volume_24h_usd")
        or 0.0
    )

    cap = (
        coin.get("market_cap_usd")
        or 0.0
    )

    if cap <= 0:
        return 0.0

    return volume / cap


def _momentum_score(
    coin: Dict[str, Any],
) -> float:
    change_1h = (
        coin.get("change_1h_percent")
        or 0.0
    )

    change_24h = (
        coin.get("change_24h_percent")
        or 0.0
    )

    change_7d = (
        coin.get("change_7d_percent")
        or 0.0
    )

    return (
        change_1h * 0.45
        + change_24h * 0.35
        + change_7d * 0.20
    )


def scan_market(
    limit: int = 100,
) -> Dict[str, Any]:
    """
    Scan LiveCoinWatch market data.

    Filter:
        market cap >= value of 1000 BTC

    Important:
        trading volume is NOT net capital inflow.
    """

    btc = get_coin(
        "BTC",
        meta=False,
    )

    btc_price = btc.get("price_usd")

    if btc_price is None or btc_price <= 0:
        raise RuntimeError(
            "Unable to determine BTC price"
        )

    minimum_cap = btc_price * 1000.0

    raw_coins = list_coins(
        sort="volume",
        order="descending",
        limit=limit,
    )

    coins: List[Dict[str, Any]] = []

    for coin in raw_coins:
        if not _valid_coin(
            coin,
            minimum_cap,
        ):
            continue

        enriched = dict(coin)

        enriched[
            "volume_market_cap_ratio"
        ] = _activity_ratio(coin)

        enriched[
            "momentum_score"
        ] = _momentum_score(coin)

        coins.append(enriched)

    volume_leaders = sorted(
        coins,
        key=lambda item: (
            item.get("volume_24h_usd")
            or 0.0
        ),
        reverse=True,
    )

    activity_leaders = sorted(
        coins,
        key=lambda item: (
            item["volume_market_cap_ratio"]
        ),
        reverse=True,
    )

    momentum_gainers = sorted(
        coins,
        key=lambda item: (
            item["momentum_score"]
        ),
        reverse=True,
    )

    momentum_losers = sorted(
        coins,
        key=lambda item: (
            item["momentum_score"]
        ),
    )

    biggest_winners = sorted(
        coins,
        key=lambda item: (
            item.get("change_24h_percent")
            or 0.0
        ),
        reverse=True,
    )

    biggest_losers = sorted(
        coins,
        key=lambda item: (
            item.get("change_24h_percent")
            or 0.0
        ),
    )

    return {
        "provider": "livecoinwatch",
        "btc_price_usd": btc_price,
        "minimum_market_cap_usd": minimum_cap,
        "eligible_count": len(coins),

        "volume_leaders": (
            volume_leaders[:10]
        ),

        "activity_leaders": (
            activity_leaders[:10]
        ),

        "momentum_gainers": (
            momentum_gainers[:10]
        ),

        "momentum_losers": (
            momentum_losers[:10]
        ),

        "biggest_winners_24h": (
            biggest_winners[:10]
        ),

        "biggest_losers_24h": (
            biggest_losers[:10]
        ),

        "data_note": (
            "Volume is trading activity, "
            "not net capital inflow."
        ),
    }
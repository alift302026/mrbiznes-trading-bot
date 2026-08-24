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

RESULT_LIMIT = 20


def _valid_coin(
    coin: Dict[str, Any],
    minimum_cap: float,
) -> bool:
    code = str(
        coin.get("code") or ""
    ).upper()

    cap = coin.get(
        "market_cap_usd"
    )

    volume = coin.get(
        "volume_24h_usd"
    )

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

    if volume is None:
        return False

    if volume <= 0:
        return False

    return True


def _activity_ratio(
    coin: Dict[str, Any],
) -> float:
    volume = float(
        coin.get(
            "volume_24h_usd"
        )
        or 0
    )

    cap = float(
        coin.get(
            "market_cap_usd"
        )
        or 0
    )

    if cap <= 0:
        return 0.0

    return volume / cap


def _momentum_score(
    coin: Dict[str, Any],
) -> float:
    change_1h = float(
        coin.get(
            "change_1h_percent"
        )
        or 0
    )

    change_24h = float(
        coin.get(
            "change_24h_percent"
        )
        or 0
    )

    change_7d = float(
        coin.get(
            "change_7d_percent"
        )
        or 0
    )

    return (
        change_1h * 0.45
        + change_24h * 0.35
        + change_7d * 0.20
    )


def scan_market(
    limit: int = 200,
) -> Dict[str, Any]:
    """
    Broad LiveCoinWatch market scan.

    Quality filter:
        Market Cap >= current value of 1000 BTC.

    Stablecoins and malformed/no-cap assets
    are excluded.

    The output provides up to 20 assets for
    each visual Signal Center category.

    Trading volume is NOT net capital inflow.
    """

    btc = get_coin(
        "BTC",
        meta=False,
    )

    btc_price = btc.get(
        "price_usd"
    )

    if (
        btc_price is None
        or btc_price <= 0
    ):
        raise RuntimeError(
            "Unable to determine BTC price"
        )

    minimum_cap = (
        float(btc_price)
        * 1000.0
    )

    raw_coins = list_coins(
        sort="volume",
        order="descending",
        limit=max(
            50,
            min(
                int(limit),
                200,
            ),
        ),
    )

    coins: List[
        Dict[str, Any]
    ] = []

    for coin in raw_coins:
        if not _valid_coin(
            coin,
            minimum_cap,
        ):
            continue

        enriched = dict(
            coin
        )

        enriched[
            "volume_market_cap_ratio"
        ] = _activity_ratio(
            coin
        )

        enriched[
            "momentum_score"
        ] = _momentum_score(
            coin
        )

        coins.append(
            enriched
        )

    volume_leaders = sorted(
        coins,
        key=lambda item: (
            item.get(
                "volume_24h_usd"
            )
            or 0
        ),
        reverse=True,
    )

    activity_leaders = sorted(
        coins,
        key=lambda item: (
            item.get(
                "volume_market_cap_ratio"
            )
            or 0
        ),
        reverse=True,
    )

    momentum_gainers = sorted(
        coins,
        key=lambda item: (
            item.get(
                "momentum_score"
            )
            or 0
        ),
        reverse=True,
    )

    momentum_losers = sorted(
        coins,
        key=lambda item: (
            item.get(
                "momentum_score"
            )
            or 0
        ),
    )

    biggest_winners = sorted(
        coins,
        key=lambda item: (
            item.get(
                "change_24h_percent"
            )
            or 0
        ),
        reverse=True,
    )

    biggest_losers = sorted(
        coins,
        key=lambda item: (
            item.get(
                "change_24h_percent"
            )
            or 0
        ),
    )

    # Ensure winners are actually positive
    # and losers are actually negative.
    biggest_winners = [
        item
        for item in biggest_winners
        if (
            item.get(
                "change_24h_percent"
            )
            is not None
            and item[
                "change_24h_percent"
            ] > 0
        )
    ]

    biggest_losers = [
        item
        for item in biggest_losers
        if (
            item.get(
                "change_24h_percent"
            )
            is not None
            and item[
                "change_24h_percent"
            ] < 0
        )
    ]

    return {
        "provider": (
            "livecoinwatch"
        ),

        "btc_price_usd": (
            btc_price
        ),

        "minimum_market_cap_usd": (
            minimum_cap
        ),

        "eligible_count": (
            len(coins)
        ),

        "volume_leaders": (
            volume_leaders[
                :RESULT_LIMIT
            ]
        ),

        "activity_leaders": (
            activity_leaders[
                :RESULT_LIMIT
            ]
        ),

        "momentum_gainers": (
            momentum_gainers[
                :RESULT_LIMIT
            ]
        ),

        "momentum_losers": (
            momentum_losers[
                :RESULT_LIMIT
            ]
        ),

        "biggest_winners_24h": (
            biggest_winners[
                :RESULT_LIMIT
            ]
        ),

        "biggest_losers_24h": (
            biggest_losers[
                :RESULT_LIMIT
            ]
        ),

        "result_limit": (
            RESULT_LIMIT
        ),

        "data_note": (
            "Volume represents trading activity "
            "and must not be interpreted as "
            "net capital inflow."
        ),
    }
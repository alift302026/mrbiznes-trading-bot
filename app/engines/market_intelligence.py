import asyncio
from datetime import datetime

import ccxt.async_support as ccxt

from app.models.database import (
    SessionLocal,
)

from app.models.market_intelligence import (
    AssetMarketSnapshot,
)


EXCHANGE_ID = "xt"


# ============================================================
# EXCHANGE
# ============================================================

def create_exchange():

    exchange_class = getattr(
        ccxt,
        EXCHANGE_ID,
    )

    return exchange_class(
        {
            "enableRateLimit": True,
            "timeout": 25000,
        }
    )


# ============================================================
# SAFE FLOAT
# ============================================================

def safe_float(
    value,
):

    try:

        value = float(
            value
        )

    except (
        TypeError,
        ValueError,
    ):

        return None

    return value


# ============================================================
# SCAN XT SPOT / USDT
# ============================================================

async def scan_xt_market():

    exchange = create_exchange()

    try:

        markets = (
            await exchange.load_markets()
        )

        tickers = (
            await exchange.fetch_tickers()
        )

    finally:

        await exchange.close()

    rows = []

    now = datetime.utcnow()

    for symbol, market in (
        markets.items()
    ):

        if not market.get(
            "spot",
            False,
        ):
            continue

        if (
            market.get("active")
            is False
        ):
            continue

        if (
            str(
                market.get(
                    "quote",
                    "",
                )
            ).upper()
            != "USDT"
        ):
            continue

        ticker = tickers.get(
            symbol
        )

        if not ticker:
            continue

        last = safe_float(
            ticker.get(
                "last"
            )
        )

        percentage = safe_float(
            ticker.get(
                "percentage"
            )
        )

        base_volume = safe_float(
            ticker.get(
                "baseVolume"
            )
        )

        quote_volume = safe_float(
            ticker.get(
                "quoteVolume"
            )
        )

        if last is None:
            continue

        rows.append(
            {
                "symbol":
                    symbol,

                "price":
                    last,

                "change_24h":
                    percentage,

                "volume_24h":
                    base_volume,

                "quote_volume_24h":
                    quote_volume,

                "source":
                    "XT",

                "captured_at":
                    now,
            }
        )

    return rows


# ============================================================
# STORE SNAPSHOT
# ============================================================

def save_market_snapshot(
    rows,
):

    if not rows:
        return 0

    with SessionLocal() as db:

        for row in rows:

            item = AssetMarketSnapshot(
                symbol=row[
                    "symbol"
                ],
                market="crypto",
                price=row[
                    "price"
                ],
                change_24h=row[
                    "change_24h"
                ],
                volume_24h=row[
                    "volume_24h"
                ],
                quote_volume_24h=row[
                    "quote_volume_24h"
                ],
                source=row[
                    "source"
                ],
                captured_at=row[
                    "captured_at"
                ],
            )

            db.add(
                item
            )

        db.commit()

    return len(
        rows
    )


# ============================================================
# TOP GAINERS
# ============================================================

def top_gainers(
    rows,
    limit=10,
):

    valid = [
        row
        for row in rows
        if row[
            "change_24h"
        ] is not None
    ]

    valid.sort(
        key=lambda row: (
            row[
                "change_24h"
            ]
        ),
        reverse=True,
    )

    return valid[
        :limit
    ]


# ============================================================
# TOP LOSERS
# ============================================================

def top_losers(
    rows,
    limit=10,
):

    valid = [
        row
        for row in rows
        if row[
            "change_24h"
        ] is not None
    ]

    valid.sort(
        key=lambda row: (
            row[
                "change_24h"
            ]
        )
    )

    return valid[
        :limit
    ]


# ============================================================
# VOLUME LEADERS
# ============================================================

def volume_leaders(
    rows,
    limit=10,
):

    valid = [
        row
        for row in rows
        if (
            row[
                "quote_volume_24h"
            ]
            is not None
            and row[
                "quote_volume_24h"
            ] > 0
        )
    ]

    valid.sort(
        key=lambda row: (
            row[
                "quote_volume_24h"
            ]
        ),
        reverse=True,
    )

    return valid[
        :limit
    ]


# ============================================================
# MARKET SUMMARY
# ============================================================

def market_summary(
    rows,
):

    changes = [
        row[
            "change_24h"
        ]
        for row in rows
        if row[
            "change_24h"
        ] is not None
    ]

    positive = sum(
        1
        for value in changes
        if value > 0
    )

    negative = sum(
        1
        for value in changes
        if value < 0
    )

    flat = sum(
        1
        for value in changes
        if value == 0
    )

    return {
        "assets":
            len(rows),

        "with_change":
            len(changes),

        "positive":
            positive,

        "negative":
            negative,

        "flat":
            flat,
    }


# ============================================================
# FULL SCAN
# ============================================================

async def intelligence_scan(
    save=False,
):

    rows = (
        await scan_xt_market()
    )

    if save:

        save_market_snapshot(
            rows
        )

    return {
        "summary":
            market_summary(
                rows
            ),

        "gainers":
            top_gainers(
                rows
            ),

        "losers":
            top_losers(
                rows
            ),

        "volume":
            volume_leaders(
                rows
            ),

        "rows":
            rows,
    }
import ccxt.async_support as ccxt


# ============================================================
# NORMALIZE CRYPTO SYMBOL
# ============================================================

def normalize_crypto_symbol(
    value,
):

    value = (
        value
        .strip()
        .upper()
        .replace(
            " ",
            "",
        )
    )

    if not value:
        return None

    # BTCUSDT -> BTC/USDT
    if (
        "/" not in value
        and value.endswith(
            "USDT"
        )
    ):

        base = value[:-4]

        if base:

            value = (
                f"{base}/USDT"
            )

    # BTC -> BTC/USDT
    elif "/" not in value:

        value = (
            f"{value}/USDT"
        )

    return value


# ============================================================
# VALIDATE BINANCE SPOT
# ============================================================

async def validate_crypto_symbol(
    value,
):

    symbol = normalize_crypto_symbol(
        value
    )

    if not symbol:
        return None

    exchange = ccxt.binance(
        {
            "enableRateLimit":
                True,

            "timeout":
                20000,
        }
    )

    try:

        markets = await exchange.load_markets()

        market = markets.get(
            symbol
        )

        if market is None:
            return None

        if not market.get(
            "spot",
            False,
        ):
            return None

        if not market.get(
            "active",
            True,
        ):
            return None

        return market[
            "symbol"
        ]

    finally:

        await exchange.close()


# ============================================================
# SEARCH BINANCE SPOT
# ============================================================

async def search_crypto_symbols(
    query,
    limit=10,
):

    query = (
        query
        .strip()
        .upper()
    )

    if not query:
        return []

    exchange = ccxt.binance(
        {
            "enableRateLimit":
                True,

            "timeout":
                20000,
        }
    )

    try:

        markets = await exchange.load_markets()

        results = []

        for symbol, market in markets.items():

            if not market.get(
                "spot",
                False,
            ):
                continue

            if not market.get(
                "active",
                True,
            ):
                continue

            if market.get(
                "quote"
            ) != "USDT":

                continue

            base = (
                market.get(
                    "base",
                    "",
                )
                or ""
            )

            if (
                query not in base.upper()
                and
                query not in symbol.upper()
            ):
                continue

            results.append(
                symbol
            )

        results.sort(
            key=lambda item: (
                not item.startswith(
                    query
                ),
                len(item),
                item,
            )
        )

        return results[
            :limit
        ]

    finally:

        await exchange.close()
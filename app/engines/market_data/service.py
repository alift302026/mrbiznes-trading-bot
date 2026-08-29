import asyncio
import os
import time

from dotenv import load_dotenv

from app.engines.market_data.crypto import (
    CoinGeckoProvider,
)

from app.engines.market_data.forex import (
    ForexProvider,
)

from app.engines.market_data.twelve_data import (
    TwelveDataProvider,
)


load_dotenv()


class MarketDataService:

    def __init__(
        self,
    ):

        self.crypto = (
            CoinGeckoProvider()
        )

        self.forex = (
            ForexProvider()
        )

        self.twelve = (
            TwelveDataProvider(
                os.getenv(
                    "TWELVE_DATA_API_KEY",
                    "",
                )
            )
        )

        self.cache = {}

        self.cache_ttl = 60


    async def cached(
        self,
        key,
        loader,
    ):

        now = time.time()

        item = self.cache.get(
            key
        )

        if item:

            created_at, value = (
                item
            )

            if (
                now - created_at
                < self.cache_ttl
            ):

                return value

        value = await loader()

        self.cache[key] = (
            now,
            value,
        )

        return value


    # ========================================================
    # CRYPTO
    # ========================================================

    async def crypto_market(
        self,
    ):

        return await self.cached(
            "crypto_top_10",
            lambda: (
                self.crypto
                .get_markets(10)
            ),
        )


    # ========================================================
    # FOREX
    # ========================================================

    async def forex_market(
        self,
    ):

        return await self.cached(
            "forex_major_pairs",
            (
                self.forex
                .get_major_pairs
            ),
        )


    # ========================================================
    # GOLD
    # ========================================================

    async def gold_market(
        self,
    ):

        return await self.cached(
            "gold",
            self.twelve.gold,
        )


    # ========================================================
    # OIL
    # ========================================================

    async def oil_market(
        self,
    ):

        async def loader():

            results = (
                await asyncio.gather(
                    self.twelve.wti(),
                    self.twelve.brent(),
                    return_exceptions=True,
                )
            )

            output = []

            names = [
                "WTI",
                "BRENT",
            ]

            for name, result in zip(
                names,
                results,
            ):

                if isinstance(
                    result,
                    Exception,
                ):

                    output.append(
                        {
                            "name": name,
                            "error": str(
                                result
                            ),
                        }
                    )

                else:

                    result["name"] = name

                    output.append(
                        result
                    )

            return output

        return await self.cached(
            "oil",
            loader,
        )


market_service = (
    MarketDataService()
)
import aiohttp


class TwelveDataProvider:

    BASE_URL = "https://api.twelvedata.com"

    GOLD_SYMBOLS = [
        "XAU/USD",
    ]

    WTI_SYMBOLS = [
        "WTI/USD",
        "WTI",
        "CL",
    ]

    BRENT_SYMBOLS = [
        "BRENT/USD",
        "BRENT",
    ]

    def __init__(
        self,
        api_key: str,
    ):

        self.api_key = (
            api_key.strip()
        )

    def check_key(
        self,
    ):

        if not self.api_key:

            raise RuntimeError(
                "TWELVE_DATA_API_KEY "
                "is not configured"
            )

    async def quote(
        self,
        symbol: str,
    ) -> dict:

        self.check_key()

        timeout = aiohttp.ClientTimeout(
            total=15
        )

        params = {
            "symbol": symbol,
            "apikey": self.api_key,
        }

        async with aiohttp.ClientSession(
            timeout=timeout
        ) as session:

            async with session.get(
                f"{self.BASE_URL}/quote",
                params=params,
            ) as response:

                response.raise_for_status()

                data = (
                    await response.json()
                )

        if data.get("status") == "error":

            raise RuntimeError(
                data.get(
                    "message",
                    f"{symbol} unavailable",
                )
            )

        close = data.get(
            "close"
        )

        if close is None:

            raise RuntimeError(
                f"No price returned "
                f"for {symbol}"
            )

        try:

            price = float(
                close
            )

        except (
            TypeError,
            ValueError,
        ):

            raise RuntimeError(
                f"Invalid price for "
                f"{symbol}"
            )

        try:

            change = float(
                data.get(
                    "percent_change"
                )
            )

        except (
            TypeError,
            ValueError,
        ):

            change = None

        return {
            "symbol": symbol,
            "price": price,
            "change": change,
            "datetime": data.get(
                "datetime"
            ),
            "source": "Twelve Data",
        }

    async def first_available(
        self,
        symbols: list[str],
    ) -> dict:

        errors = []

        for symbol in symbols:

            try:

                return await self.quote(
                    symbol
                )

            except Exception as exc:

                errors.append(
                    f"{symbol}: {exc}"
                )

        raise RuntimeError(
            " | ".join(errors)
        )

    async def gold(
        self,
    ) -> dict:

        return await self.first_available(
            self.GOLD_SYMBOLS
        )

    async def wti(
        self,
    ) -> dict:

        return await self.first_available(
            self.WTI_SYMBOLS
        )

    async def brent(
        self,
    ) -> dict:

        return await self.first_available(
            self.BRENT_SYMBOLS
        )
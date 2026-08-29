import aiohttp


class CoinGeckoProvider:

    BASE_URL = "https://api.coingecko.com/api/v3"

    async def get_markets(
        self,
        limit: int = 10,
    ) -> list[dict]:

        timeout = aiohttp.ClientTimeout(
            total=15
        )

        params = {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": limit,
            "page": 1,
            "sparkline": "false",
            "price_change_percentage": "24h",
        }

        headers = {
            "Accept": "application/json",
        }

        async with aiohttp.ClientSession(
            timeout=timeout
        ) as session:

            async with session.get(
                f"{self.BASE_URL}/coins/markets",
                params=params,
                headers=headers,
            ) as response:

                response.raise_for_status()

                data = await response.json()

        if not isinstance(data, list):
            raise RuntimeError(
                "Invalid CoinGecko response"
            )

        return data
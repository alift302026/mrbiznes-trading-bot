import asyncio

import aiohttp


class ForexProvider:

    BASE_URL = "https://api.frankfurter.app"

    PAIRS = [
        ("EUR", "USD"),
        ("GBP", "USD"),
        ("USD", "JPY"),
        ("USD", "CHF"),
        ("AUD", "USD"),
        ("USD", "CAD"),
        ("NZD", "USD"),
        ("EUR", "GBP"),
        ("EUR", "JPY"),
        ("GBP", "JPY"),
    ]

    async def get_rate(
        self,
        base: str,
        quote: str,
    ) -> dict:

        timeout = aiohttp.ClientTimeout(
            total=15
        )

        async with aiohttp.ClientSession(
            timeout=timeout
        ) as session:

            async with session.get(
                f"{self.BASE_URL}/latest",
                params={
                    "from": base,
                    "to": quote,
                },
            ) as response:

                response.raise_for_status()

                data = await response.json()

        rate = (
            data
            .get("rates", {})
            .get(quote)
        )

        if rate is None:
            raise RuntimeError(
                f"{base}/{quote} unavailable"
            )

        return {
            "symbol": f"{base}/{quote}",
            "price": float(rate),
            "date": data.get("date"),
            "source": (
                "Frankfurter / ECB"
            ),
        }

    async def get_major_pairs(
        self,
    ) -> list[dict]:

        tasks = [
            self.get_rate(
                base,
                quote,
            )
            for base, quote
            in self.PAIRS
        ]

        results = await asyncio.gather(
            *tasks,
            return_exceptions=True,
        )

        output = []

        for result in results:

            if isinstance(
                result,
                Exception,
            ):
                continue

            output.append(
                result
            )

        if not output:

            raise RuntimeError(
                "Forex data unavailable"
            )

        return output
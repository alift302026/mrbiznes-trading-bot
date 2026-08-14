from app.engines.alerts.symbol_search import (
    search_crypto_symbols,
    validate_crypto_symbol,
)

from app.services.search_limit_service import (
    crypto_search_capacity,
    register_crypto_search,
)


class SearchLimitReached(Exception):

    def __init__(self, capacity):
        self.capacity = capacity

        super().__init__(
            "Monthly crypto search limit reached"
        )


async def search_crypto(
    telegram_id,
    query,
):
    """
    Validate/search a Crypto symbol on XT.

    Rules:
    - Admin: unlimited.
    - VIP: unlimited.
    - Normal: 3 successful searches/month.
    - Invalid searches do NOT consume quota.
    """

    capacity = crypto_search_capacity(
        telegram_id
    )

    if not capacity["allowed"]:
        raise SearchLimitReached(
            capacity
        )

    symbol = await validate_crypto_symbol(
        query
    )

    # Exact successful symbol
    if symbol:

        register_crypto_search(
            telegram_id,
            symbol,
        )

        return {
            "found": True,
            "symbol": symbol,
            "suggestions": [],
            "capacity": crypto_search_capacity(
                telegram_id
            ),
        }

    # Invalid search does NOT consume quota.
    suggestions = await search_crypto_symbols(
        query,
        limit=8,
    )

    return {
        "found": False,
        "symbol": None,
        "suggestions": suggestions,
        "capacity": capacity,
    }
from app.engines.alerts.forex_provider import (
    POPULAR_FOREX,
    normalize_forex_symbol,
    validate_forex_symbol,
)


# ============================================================
# POPULAR PAIRS
# ============================================================

def popular_forex_pairs():

    return list(
        dict.fromkeys(
            POPULAR_FOREX.values()
        )
    )


# ============================================================
# SEARCH / VALIDATE
# ============================================================

async def search_forex(
    query,
):

    symbol = normalize_forex_symbol(
        query
    )

    if not symbol:

        return {
            "found": False,
            "symbol": None,
        }

    valid = await validate_forex_symbol(
        symbol
    )

    if not valid:

        return {
            "found": False,
            "symbol": None,
        }

    return {
        "found": True,
        "symbol": valid,
    }


# ============================================================
# ALERT PARAMETERS
# ============================================================

def forex_parameters(
    parameters=None,
):

    result = dict(
        parameters
        or {}
    )

    result["market"] = "forex"

    return result
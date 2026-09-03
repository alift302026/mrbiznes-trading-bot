import logging
import re
from typing import List, Optional

import ccxt.async_support as ccxt
import requests

from app.core.config import XT_API_KEY, XT_SECRET_KEY

logger = logging.getLogger(__name__)


# List of top standard crypto pairs on XT Spot
POPULAR_XT_SYMBOLS = [
    "BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "XRP/USDT",
    "DOGE/USDT", "TON/USDT", "PEPE/USDT", "SUI/USDT", "AVAX/USDT",
    "ADA/USDT", "NEAR/USDT", "SHIB/USDT", "LINK/USDT", "LTC/USDT",
    "DOT/USDT", "TRX/USDT", "UNI/USDT", "ATOM/USDT", "ICP/USDT",
    "APT/USDT", "ARB/USDT", "OP/USDT", "INJ/USDT", "TIA/USDT",
    "FET/USDT", "RENDER/USDT", "NOT/USDT", "WIF/USDT", "BONK/USDT",
    "FLOKI/USDT", "KAS/USDT", "SEI/USDT", "TAO/USDT", "JUP/USDT",
    "STX/USDT", "FIL/USDT", "XLM/USDT", "BCH/USDT", "ETC/USDT",
]


def normalize_crypto_symbol(value: str) -> Optional[str]:
    if not value:
        return None

    value = str(value).strip().upper().replace(" ", "")

    # Replace separators like _ or - with /
    value = value.replace("-", "/").replace("_", "/")

    # BTCUSDT -> BTC/USDT
    if "/" not in value and value.endswith("USDT") and len(value) > 4:
        base = value[:-4]
        if base:
            return f"{base}/USDT"

    # BTC -> BTC/USDT
    elif "/" not in value:
        return f"{value}/USDT"

    return value


def create_xt_exchange():
    config = {
        "enableRateLimit": True,
        "timeout": 15000,
    }
    if XT_API_KEY:
        config["apiKey"] = XT_API_KEY
    if XT_SECRET_KEY:
        config["secret"] = XT_SECRET_KEY

    return ccxt.xt(config)


async def validate_crypto_symbol(value: str) -> Optional[str]:
    symbol = normalize_crypto_symbol(value)
    if not symbol:
        return None

    # Check popular list first for instant response
    if symbol in POPULAR_XT_SYMBOLS:
        return symbol

    # Try XT CCXT
    exchange = create_xt_exchange()
    try:
        markets = await exchange.load_markets()
        if symbol in markets:
            market = markets[symbol]
            if market.get("active", True):
                return market.get("symbol", symbol)
    except Exception as exc:
        logger.debug("XT ccxt validate error: %s", exc)
    finally:
        try:
            await exchange.close()
        except Exception:
            pass

    # If format is standard Base/USDT with 2-10 char base, treat as valid XT candidate
    parts = symbol.split("/")
    if len(parts) == 2 and parts[1] == "USDT" and 2 <= len(parts[0]) <= 12 and parts[0].isalnum():
        return symbol

    return None


async def search_crypto_symbols(query: str, limit: int = 10) -> List[str]:
    q = query.strip().upper().replace("/", "").replace("_", "")
    if not q:
        return POPULAR_XT_SYMBOLS[:limit]

    # Search in popular XT list first
    matches = []
    for s in POPULAR_XT_SYMBOLS:
        base = s.split("/")[0]
        if q in base or q in s.replace("/", ""):
            matches.append(s)

    # Try XT exchange
    exchange = create_xt_exchange()
    try:
        markets = await exchange.load_markets()
        for s, market in markets.items():
            if market.get("quote") != "USDT":
                continue
            base = market.get("base", "")
            if q in base.upper() or q in s.upper():
                if s not in matches:
                    matches.append(s)
            if len(matches) >= limit * 2:
                break
    except Exception as exc:
        logger.debug("XT search ccxt error: %s", exc)
    finally:
        try:
            await exchange.close()
        except Exception:
            pass

    # Sort so prefix matches come first
    matches.sort(
        key=lambda item: (
            not item.startswith(f"{q}/"),
            not item.replace("/USDT", "").startswith(q),
            len(item),
            item,
        )
    )

    return matches[:limit]

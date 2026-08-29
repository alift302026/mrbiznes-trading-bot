from typing import Any, Dict, List

from app.engines.alerts.market_alert_engine import (
    fetch_market_snapshot,
)
from app.engines.signals.livecoinwatch_provider import (
    LiveCoinWatchError,
    get_coin,
)


DEFAULT_PARAMETERS = {
    "ema_fast": 20,
    "ema_slow": 50,
    "rsi_period": 14,
    "atr_period": 14,
    "volume_period": 20,
}


def _crypto_code(symbol: str) -> str:
    value = str(symbol or "").strip().upper()

    if "/" in value:
        return value.split("/", 1)[0]

    if value.endswith("USDT"):
        return value[:-4]

    return value


def _technical_score(
    snapshot: Dict[str, Any],
) -> Dict[str, Any]:
    score = 0
    reasons: List[str] = []

    ema_fast = float(snapshot["ema_fast"])
    ema_slow = float(snapshot["ema_slow"])
    rsi = float(snapshot["rsi"])
    macd = float(snapshot["macd"])
    macd_signal = float(snapshot["macd_signal"])
    volume = float(snapshot["volume"])
    volume_average = float(snapshot["volume_average"])

    if ema_fast > ema_slow:
        score += 2
        reasons.append("EMA trend bullish")
    elif ema_fast < ema_slow:
        score -= 2
        reasons.append("EMA trend bearish")

    if macd > macd_signal:
        score += 2
        reasons.append("MACD above signal")
    elif macd < macd_signal:
        score -= 2
        reasons.append("MACD below signal")

    if 50 <= rsi < 70:
        score += 1
        reasons.append("RSI positive")
    elif 30 < rsi < 50:
        score -= 1
        reasons.append("RSI weak")
    elif rsi >= 70:
        reasons.append("RSI overbought")
    elif rsi <= 30:
        reasons.append("RSI oversold")

    if volume_average > 0:
        ratio = volume / volume_average

        if ratio >= 1.5:
            reasons.append(
                f"High XT volume ({ratio:.2f}x average)"
            )

    return {
        "score": score,
        "reasons": reasons,
    }


def _context_score(
    context: Dict[str, Any],
) -> Dict[str, Any]:
    score = 0
    reasons: List[str] = []

    change_24h = context.get("change_24h_percent")
    change_7d = context.get("change_7d_percent")
    liquidity = context.get("liquidity_usd")
    volume = context.get("volume_24h_usd")

    if change_24h is not None:
        if change_24h >= 1:
            score += 1
            reasons.append(
                f"24h market momentum +{change_24h:.2f}%"
            )
        elif change_24h <= -1:
            score -= 1
            reasons.append(
                f"24h market momentum {change_24h:.2f}%"
            )

    if change_7d is not None:
        if change_7d >= 3:
            score += 1
            reasons.append(
                f"7d market momentum +{change_7d:.2f}%"
            )
        elif change_7d <= -3:
            score -= 1
            reasons.append(
                f"7d market momentum {change_7d:.2f}%"
            )

    if (
        liquidity is not None
        and volume is not None
        and liquidity > 0
        and volume > 0
    ):
        reasons.append("LiveCoinWatch liquidity available")

    return {
        "score": score,
        "reasons": reasons,
    }


def _classification(score: int) -> str:
    if score >= 4:
        return "BULLISH"

    if score <= -4:
        return "BEARISH"

    return "NEUTRAL"


async def analyze_crypto_signal(
    symbol: str,
    timeframe: str = "1h",
    parameters: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    settings = dict(DEFAULT_PARAMETERS)

    if parameters:
        settings.update(parameters)

    snapshot = await fetch_market_snapshot(
        symbol=symbol,
        timeframe=timeframe,
        parameters=settings,
    )

    technical = _technical_score(snapshot)

    context = None
    context_error = None
    context_result = {
        "score": 0,
        "reasons": [],
    }

    try:
        context = get_coin(_crypto_code(symbol))
        context_result = _context_score(context)
    except LiveCoinWatchError as exc:
        # LiveCoinWatch is confirmation/context.
        # A temporary provider failure must not destroy
        # the technical signal engine.
        context_error = str(exc)

    total_score = (
        technical["score"]
        + context_result["score"]
    )

    return {
        "symbol": snapshot["symbol"],
        "timeframe": timeframe,
        "signal": _classification(total_score),
        "score": total_score,
        "technical_score": technical["score"],
        "context_score": context_result["score"],
        "technical_reasons": technical["reasons"],
        "context_reasons": context_result["reasons"],
        "technical": {
            "provider": snapshot["exchange"],
            "price": snapshot["price"],
            "ema_fast": snapshot["ema_fast"],
            "ema_slow": snapshot["ema_slow"],
            "rsi": snapshot["rsi"],
            "macd": snapshot["macd"],
            "macd_signal": snapshot["macd_signal"],
            "atr": snapshot["atr"],
            "atr_percent": snapshot["atr_percent"],
            "volume": snapshot["volume"],
            "volume_average": snapshot["volume_average"],
        },
        "market_context": context,
        "market_context_error": context_error,
        "settings": snapshot["settings"],
        "interpretation_note": (
            "Signal classification is rule-based analysis, "
            "not a guaranteed market direction."
        ),
    }
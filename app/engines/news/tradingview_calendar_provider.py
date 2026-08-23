from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests

from app.engines.news.economic_calendar_provider import (
    EconomicCalendarProvider,
)


CALENDAR_URL = "https://economic-calendar.tradingview.com/events"

REQUEST_TIMEOUT = 20


class TradingViewCalendarError(RuntimeError):
    pass


def _utc_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        dt = value
    else:
        text = str(value or "").strip()

        if not text:
            raise ValueError("Economic event has no date")

        if text.endswith("Z"):
            text = text[:-1] + "+00:00"

        dt = datetime.fromisoformat(text)

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)

    return dt


def _api_datetime(value: datetime) -> str:
    dt = _utc_datetime(value)

    return (
        dt.isoformat(timespec="milliseconds")
        .replace("+00:00", "Z")
    )


def _text(value: Any) -> Optional[str]:
    if value is None:
        return None

    value = str(value).strip()

    return value or None


def _economic_value(
    item: Dict[str, Any],
    name: str,
) -> Optional[str]:
    """
    Prefer formatted API values, then fall back to raw values.

    Examples:
        previous / previousRaw
        forecast / forecastRaw
        actual / actualRaw
    """
    value = item.get(name)

    if value is not None and str(value).strip():
        return str(value).strip()

    raw_value = item.get(f"{name}Raw")

    if raw_value is not None:
        return str(raw_value)

    return None


def _importance(value: Any) -> str:
    """
    TradingView currently returns numeric importance.

    Normalize provider-specific values into ALIFT's:
        low | medium | high
    """
    try:
        level = int(value)
    except (TypeError, ValueError):
        return "low"

    if level >= 1:
        return "high"

    if level == 0:
        return "medium"

    return "low"


def _normalize_event(
    item: Dict[str, Any],
) -> Dict[str, Any]:
    title = _text(item.get("title"))

    if not title:
        raise ValueError("Economic event has no title")

    event_id = item.get("id")

    provider_source = _text(item.get("source"))
    provider_source_url = _text(item.get("source_url"))

    return {
        "external_id": (
            f"tradingview:{event_id}"
            if event_id is not None
            else None
        ),
        "title": title,
        "title_fa": None,
        "country": _text(item.get("country")),
        "currency": _text(item.get("currency")),
        "category": (
            _text(item.get("indicator"))
            or _text(item.get("category"))
        ),
        "importance": _importance(
            item.get("importance")
        ),
        "previous": _economic_value(
            item,
            "previous",
        ),
        "forecast": _economic_value(
            item,
            "forecast",
        ),
        "actual": _economic_value(
            item,
            "actual",
        ),
        "event_time": _utc_datetime(
            item.get("date")
        ),
        "source": "TradingView Economic Calendar",
        "source_url": (
            provider_source_url
            or "https://www.tradingview.com/economic-calendar/"
        ),
        "provider_source": provider_source,
    }


def _fetch_sync(
    start: datetime,
    end: datetime,
) -> List[Dict[str, Any]]:
    params = {
        "from": _api_datetime(start),
        "to": _api_datetime(end),
    }

    headers = {
        "Origin": "https://www.tradingview.com",
        "User-Agent": "ALIFT-TRADER/1.0",
        "Accept": "application/json",
    }

    try:
        response = requests.get(
            CALENDAR_URL,
            params=params,
            headers=headers,
            timeout=REQUEST_TIMEOUT,
        )
    except requests.RequestException as exc:
        raise TradingViewCalendarError(
            f"Economic calendar request failed: {exc}"
        ) from exc

    if response.status_code != 200:
        raise TradingViewCalendarError(
            "Economic calendar returned "
            f"HTTP {response.status_code}: "
            f"{response.text[:300]}"
        )

    try:
        payload = response.json()
    except ValueError as exc:
        raise TradingViewCalendarError(
            "Economic calendar returned invalid JSON"
        ) from exc

    if payload.get("status") != "ok":
        raise TradingViewCalendarError(
            f"Unexpected calendar response: {payload}"
        )

    result = payload.get("result")

    if not isinstance(result, list):
        raise TradingViewCalendarError(
            "Calendar result is not a list"
        )

    events: List[Dict[str, Any]] = []

    for item in result:
        if not isinstance(item, dict):
            continue

        try:
            events.append(
                _normalize_event(item)
            )
        except (ValueError, TypeError):
            # One malformed upstream event must not break
            # the complete calendar synchronization.
            continue

    return events


class TradingViewEconomicCalendarProvider(
    EconomicCalendarProvider
):

    async def fetch_events(
        self,
        start,
        end,
    ):
        start_utc = _utc_datetime(start)
        end_utc = _utc_datetime(end)

        if end_utc <= start_utc:
            raise ValueError(
                "Calendar end must be after start"
            )

        return await asyncio.to_thread(
            _fetch_sync,
            start_utc,
            end_utc,
        )
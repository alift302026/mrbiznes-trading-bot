from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import select

from app.engines.news.economic_calendar_provider import (
    EconomicCalendarProvider,
)
from app.models.database import SessionLocal
from app.models.economic_event import EconomicEvent


class EconomicCalendarSyncError(RuntimeError):
    pass


def _utc_datetime(value: datetime) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError(
            "event_time must be a datetime"
        )

    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


def _same_datetime(
    current: Optional[datetime],
    new: Optional[datetime],
) -> bool:
    if current is None or new is None:
        return current is new

    current_utc = _utc_datetime(current)
    new_utc = _utc_datetime(new)

    return current_utc == new_utc


def _text(value: Any) -> Optional[str]:
    if value is None:
        return None

    value = str(value).strip()

    return value or None


def _importance(value: Any) -> str:
    value = str(value or "").strip().lower()

    if value in {
        "low",
        "medium",
        "high",
    }:
        return value

    return "low"


def _update_event(
    event: EconomicEvent,
    data: Dict[str, Any],
) -> bool:
    changed = False

    fields = {
        "title": _text(data.get("title")),
        "title_fa": _text(data.get("title_fa")),
        "country": _text(data.get("country")),
        "currency": _text(data.get("currency")),
        "category": _text(data.get("category")),
        "importance": _importance(
            data.get("importance")
        ),
        "previous": _text(data.get("previous")),
        "forecast": _text(data.get("forecast")),
        "actual": _text(data.get("actual")),
        "source": _text(data.get("source")),
        "source_url": _text(data.get("source_url")),
        "external_id": _text(
            data.get("external_id")
        ),
    }

    nullable_fields = {
        "title_fa",
        "country",
        "currency",
        "category",
        "previous",
        "forecast",
        "actual",
        "source_url",
    }

    for name, value in fields.items():
        if value is None and name in nullable_fields:
            # Do not erase previously stored useful values
            # when an upstream refresh temporarily returns null.
            continue

        if getattr(event, name) != value:
            setattr(event, name, value)
            changed = True

    event_time = data.get("event_time")

    if event_time is not None:
        normalized_time = _utc_datetime(
            event_time
        )

        if not _same_datetime(
            event.event_time,
            normalized_time,
        ):
            event.event_time = normalized_time
            changed = True

    return changed


def _create_event(
    data: Dict[str, Any],
) -> EconomicEvent:
    title = _text(data.get("title"))
    source = _text(data.get("source"))
    event_time = data.get("event_time")

    if not title:
        raise ValueError(
            "Economic event title is required"
        )

    if not source:
        raise ValueError(
            "Economic event source is required"
        )

    if event_time is None:
        raise ValueError(
            "Economic event time is required"
        )

    return EconomicEvent(
        title=title,
        title_fa=_text(data.get("title_fa")),
        country=_text(data.get("country")),
        currency=_text(data.get("currency")),
        category=_text(data.get("category")),
        importance=_importance(
            data.get("importance")
        ),
        previous=_text(data.get("previous")),
        forecast=_text(data.get("forecast")),
        actual=_text(data.get("actual")),
        event_time=_utc_datetime(event_time),
        source=source,
        source_url=_text(data.get("source_url")),
        external_id=_text(
            data.get("external_id")
        ),
    )


async def sync_economic_calendar(
    provider: EconomicCalendarProvider,
    start: datetime,
    end: datetime,
) -> Dict[str, int]:
    """
    Fetch normalized events and upsert them by external_id.

    Repeated syncs do not create duplicates. Later provider
    refreshes can update actual, forecast, previous, time,
    importance and other normalized metadata.
    """

    events = await provider.fetch_events(
        start,
        end,
    )

    if not isinstance(events, list):
        raise EconomicCalendarSyncError(
            "Calendar provider did not return a list"
        )

    stats = {
        "fetched": len(events),
        "created": 0,
        "updated": 0,
        "unchanged": 0,
        "skipped": 0,
    }

    session = SessionLocal()

    try:
        for data in events:
            if not isinstance(data, dict):
                stats["skipped"] += 1
                continue

            external_id = _text(
                data.get("external_id")
            )

            if not external_id:
                stats["skipped"] += 1
                continue

            existing = session.execute(
                select(EconomicEvent).where(
                    EconomicEvent.external_id
                    == external_id
                )
            ).scalar_one_or_none()

            if existing is None:
                try:
                    event = _create_event(data)
                except (TypeError, ValueError):
                    stats["skipped"] += 1
                    continue

                session.add(event)
                stats["created"] += 1
                continue

            if _update_event(existing, data):
                stats["updated"] += 1
            else:
                stats["unchanged"] += 1

        session.commit()
        return stats

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()
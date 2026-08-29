from datetime import (
    datetime,
    timedelta,
)

from sqlalchemy import (
    select,
)

from app.models.database import (
    SessionLocal,
)

from app.models.economic_event import (
    EconomicEvent,
)


# ============================================================
# IMPORTANT CATEGORIES
# ============================================================

HIGH_IMPACT_KEYWORDS = {
    "cpi",
    "consumer price",
    "inflation",
    "nfp",
    "nonfarm",
    "non-farm",
    "fomc",
    "federal reserve",
    "interest rate",
    "rate decision",
    "gdp",
    "unemployment",
    "ppi",
    "powell",
    "ecb",
    "boe",
    "boj",
    "retail sales",
    "pce",
}


# ============================================================
# IMPORTANCE
# ============================================================

def detect_importance(
    title,
):

    title = (
        title
        or ""
    ).lower()

    for keyword in (
        HIGH_IMPACT_KEYWORDS
    ):

        if keyword in title:
            return "high"

    return "medium"


# ============================================================
# COUNTDOWN
# ============================================================

def countdown(
    event_time,
    now=None,
):

    if now is None:
        now = datetime.utcnow()

    difference = (
        event_time
        - now
    )

    seconds = int(
        difference.total_seconds()
    )

    if seconds <= 0:

        return {
            "expired": True,
            "days": 0,
            "hours": 0,
            "minutes": 0,
            "seconds": 0,
            "text": "منتشر شده",
        }

    days, remainder = divmod(
        seconds,
        86400,
    )

    hours, remainder = divmod(
        remainder,
        3600,
    )

    minutes, seconds = divmod(
        remainder,
        60,
    )

    if days > 0:

        text = (
            f"{days} روز "
            f"{hours:02d}:"
            f"{minutes:02d}:"
            f"{seconds:02d}"
        )

    else:

        text = (
            f"{hours:02d}:"
            f"{minutes:02d}:"
            f"{seconds:02d}"
        )

    return {
        "expired": False,
        "days": days,
        "hours": hours,
        "minutes": minutes,
        "seconds": seconds,
        "text": text,
    }


# ============================================================
# UPCOMING EVENTS
# ============================================================

def upcoming_events(
    hours=72,
    importance=None,
    limit=30,
):

    now = datetime.utcnow()

    end = (
        now
        + timedelta(
            hours=hours
        )
    )

    with SessionLocal() as db:

        query = (
            select(
                EconomicEvent
            )
            .where(
                EconomicEvent.event_time
                >= now,

                EconomicEvent.event_time
                <= end,

                EconomicEvent.is_published
                .is_(True),

                EconomicEvent.is_cancelled
                .is_(False),
            )
            .order_by(
                EconomicEvent.event_time
                .asc()
            )
            .limit(
                limit
            )
        )

        if importance:

            query = query.where(
                EconomicEvent.importance
                == importance
            )

        return list(
            db.scalars(
                query
            ).all()
        )


# ============================================================
# NEXT IMPORTANT EVENT
# ============================================================

def next_important_event():

    now = datetime.utcnow()

    with SessionLocal() as db:

        return db.scalar(
            select(
                EconomicEvent
            )
            .where(
                EconomicEvent.event_time
                >= now,

                EconomicEvent.importance
                == "high",

                EconomicEvent.is_published
                .is_(True),

                EconomicEvent.is_cancelled
                .is_(False),
            )
            .order_by(
                EconomicEvent.event_time
                .asc()
            )
            .limit(1)
        )


# ============================================================
# RECENT RELEASES
# ============================================================

def recent_events(
    hours=24,
    limit=30,
):

    now = datetime.utcnow()

    start = (
        now
        - timedelta(
            hours=hours
        )
    )

    with SessionLocal() as db:

        return list(
            db.scalars(
                select(
                    EconomicEvent
                )
                .where(
                    EconomicEvent.event_time
                    >= start,

                    EconomicEvent.event_time
                    <= now,

                    EconomicEvent.is_published
                    .is_(True),

                    EconomicEvent.is_cancelled
                    .is_(False),
                )
                .order_by(
                    EconomicEvent.event_time
                    .desc()
                )
                .limit(
                    limit
                )
            ).all()
        )


# ============================================================
# GET EVENT
# ============================================================

def get_event(
    event_id,
):

    with SessionLocal() as db:

        return db.get(
            EconomicEvent,
            int(
                event_id
            ),
        )


# ============================================================
# CREATE EVENT
# Used by automatic provider or Admin.
# ============================================================

def create_event(
    title,
    event_time,
    source,
    title_fa=None,
    country=None,
    currency=None,
    category=None,
    importance=None,
    previous=None,
    forecast=None,
    actual=None,
    source_url=None,
    external_id=None,
):

    if not title:
        raise ValueError(
            "Title is required"
        )

    if not isinstance(
        event_time,
        datetime,
    ):

        raise ValueError(
            "event_time must be datetime"
        )

    if not importance:

        importance = detect_importance(
            title
        )

    importance = (
        importance.lower()
    )

    if importance not in {
        "low",
        "medium",
        "high",
    }:

        importance = "medium"

    with SessionLocal() as db:

        if external_id:

            existing = db.scalar(
                select(
                    EconomicEvent
                )
                .where(
                    EconomicEvent.external_id
                    == external_id
                )
            )

            if existing:
                return existing

        item = EconomicEvent(
            title=title,
            title_fa=title_fa,
            country=country,
            currency=currency,
            category=category,
            importance=importance,
            previous=previous,
            forecast=forecast,
            actual=actual,
            event_time=event_time,
            source=source,
            source_url=source_url,
            external_id=external_id,
            is_published=True,
            is_cancelled=False,
        )

        db.add(
            item
        )

        db.commit()
        db.refresh(
            item
        )

        return item


# ============================================================
# UPDATE ACTUAL
# ============================================================

def update_actual(
    event_id,
    actual,
):

    with SessionLocal() as db:

        item = db.get(
            EconomicEvent,
            int(
                event_id
            ),
        )

        if item is None:
            return False

        item.actual = str(
            actual
        )

        item.updated_at = (
            datetime.utcnow()
        )

        db.commit()

        return True


# ============================================================
# DELETE EVENT
# ============================================================

def delete_event(
    event_id,
):

    with SessionLocal() as db:

        item = db.get(
            EconomicEvent,
            int(
                event_id
            ),
        )

        if item is None:
            return False

        db.delete(
            item
        )

        db.commit()

        return True
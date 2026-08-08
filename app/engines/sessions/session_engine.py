from datetime import (
    datetime,
    time,
    timedelta,
    timezone,
)

from zoneinfo import ZoneInfo


# Session definitions are configurable.
# Times below are conventional FX session windows.
SESSIONS = {

    "tokyo": {
        "name": "Tokyo 🇯🇵",
        "timezone": "Asia/Tokyo",
        "open": time(9, 0),
        "close": time(18, 0),
    },

    "london": {
        "name": "London 🇬🇧",
        "timezone": "Europe/London",
        "open": time(8, 0),
        "close": time(17, 0),
    },

    "new_york": {
        "name": "New York 🇺🇸",
        "timezone": "America/New_York",
        "open": time(8, 0),
        "close": time(17, 0),
    },
}


def format_duration(
    delta: timedelta,
):

    seconds = max(
        0,
        int(delta.total_seconds()),
    )

    hours, remainder = divmod(
        seconds,
        3600,
    )

    minutes = (
        remainder // 60
    )

    return (
        f"{hours:02d}:"
        f"{minutes:02d}"
    )


def session_status(
    key: str,
    now_utc: datetime | None = None,
):

    config = SESSIONS[key]

    zone = ZoneInfo(
        config["timezone"]
    )

    if now_utc is None:

        now_utc = datetime.now(
            timezone.utc
        )

    local_now = (
        now_utc.astimezone(
            zone
        )
    )

    today = (
        local_now.date()
    )

    open_dt = datetime.combine(
        today,
        config["open"],
        tzinfo=zone,
    )

    close_dt = datetime.combine(
        today,
        config["close"],
        tzinfo=zone,
    )

    # FX sessions are treated as Monday-Friday.
    weekday = local_now.weekday()

    if (
        weekday < 5
        and
        open_dt
        <= local_now
        < close_dt
    ):

        return {
            "key": key,
            "name": config["name"],
            "is_open": True,
            "local_time": local_now,
            "event_time": close_dt,
            "remaining": (
                close_dt
                - local_now
            ),
        }

    candidate = open_dt

    if local_now >= open_dt:

        candidate += timedelta(
            days=1
        )

    while (
        candidate.weekday()
        >= 5
    ):

        candidate += timedelta(
            days=1
        )

    return {
        "key": key,
        "name": config["name"],
        "is_open": False,
        "local_time": local_now,
        "event_time": candidate,
        "remaining": (
            candidate
            - local_now
        ),
    }


def all_sessions():

    return [
        session_status(key)
        for key in SESSIONS
    ]
from datetime import (
    datetime,
    time,
    timedelta,
    timezone,
)

from zoneinfo import ZoneInfo

import jdatetime
from hijridate import Gregorian


TEHRAN_ZONE = ZoneInfo(
    "Asia/Tehran"
)

NEW_YORK_ZONE = ZoneInfo(
    "America/New_York"
)


SESSIONS = {
    "sydney": {
        "name": "Sydney",
        "flag": "🇦🇺",
        "timezone": "Australia/Sydney",
        "open": time(8, 0),
        "close": time(17, 0),
    },

    "tokyo": {
        "name": "Tokyo",
        "flag": "🇯🇵",
        "timezone": "Asia/Tokyo",
        "open": time(9, 0),
        "close": time(18, 0),
    },

    "london": {
        "name": "London",
        "flag": "🇬🇧",
        "timezone": "Europe/London",
        "open": time(8, 0),
        "close": time(17, 0),
    },

    "new_york": {
        "name": "New York",
        "flag": "🇺🇸",
        "timezone": "America/New_York",
        "open": time(8, 0),
        "close": time(17, 0),
    },
}


def date_center():

    now_utc = datetime.now(
        timezone.utc
    )

    tehran = now_utc.astimezone(
        TEHRAN_ZONE
    )

    g = tehran.date()

    jalali = (
        jdatetime.date
        .fromgregorian(
            date=g
        )
    )

    hijri = Gregorian(
        g.year,
        g.month,
        g.day,
    ).to_hijri()

    return {
        "gregorian":
            "{:04d}/{:02d}/{:02d}".format(
                g.year,
                g.month,
                g.day,
            ),

        "jalali":
            "{:04d}/{:02d}/{:02d}".format(
                jalali.year,
                jalali.month,
                jalali.day,
            ),

        "hijri":
            "{:04d}/{:02d}/{:02d}".format(
                hijri.year,
                hijri.month,
                hijri.day,
            ),

        "utc_time":
            now_utc.strftime(
                "%H:%M:%S"
            ),

        "tehran_time":
            tehran.strftime(
                "%H:%M:%S"
            ),
    }


def format_countdown(
    delta,
):

    seconds = max(
        0,
        int(
            delta.total_seconds()
        ),
    )

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

    return {
        "days": days,
        "hours": hours,
        "minutes": minutes,
        "seconds": seconds,

        "compact":
            "{}d {:02d}:{:02d}:{:02d}".format(
                days,
                hours,
                minutes,
                seconds,
            ),
    }


def progress_bar(
    percent,
):

    percent = max(
        0,
        min(
            100,
            float(percent),
        ),
    )

    blocks = 10

    filled = round(
        percent / 100 * blocks
    )

    return (
        "█" * filled
        + "░" * (
            blocks - filled
        )
    )


def next_workday_open(
    local_now,
    opening,
):

    candidate = opening

    if local_now >= candidate:

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

    return candidate


def get_session_status(
    key,
    now_utc=None,
):

    config = SESSIONS[key]

    zone = ZoneInfo(
        config["timezone"]
    )

    if now_utc is None:

        now_utc = datetime.now(
            timezone.utc
        )

    local_now = now_utc.astimezone(
        zone
    )

    opening = datetime.combine(
        local_now.date(),
        config["open"],
        tzinfo=zone,
    )

    closing = datetime.combine(
        local_now.date(),
        config["close"],
        tzinfo=zone,
    )

    is_open = (
        local_now.weekday() < 5
        and
        opening
        <= local_now
        < closing
    )

    if is_open:

        next_event = closing

        remaining = (
            closing
            - local_now
        )

        total = (
            closing
            - opening
        ).total_seconds()

        elapsed = (
            local_now
            - opening
        ).total_seconds()

        progress = (
            elapsed / total * 100
            if total > 0
            else 0
        )

    else:

        next_event = (
            next_workday_open(
                local_now,
                opening,
            )
        )

        remaining = (
            next_event
            - local_now
        )

        progress = 0

    open_tehran = (
        opening.astimezone(
            TEHRAN_ZONE
        )
    )

    close_tehran = (
        closing.astimezone(
            TEHRAN_ZONE
        )
    )

    offset = (
        local_now.utcoffset()
    )

    offset_hours = (
        offset.total_seconds()
        / 3600
        if offset
        else 0
    )

    if offset_hours >= 0:

        offset_text = (
            "UTC+{:g}"
        ).format(
            offset_hours
        )

    else:

        offset_text = (
            "UTC{:g}"
        ).format(
            offset_hours
        )

    countdown = (
        format_countdown(
            remaining
        )
    )

    return {
        "key": key,
        "name": config["name"],
        "flag": config["flag"],

        "is_open":
            is_open,

        "local_now":
            local_now,

        "open_time":
            config["open"],

        "close_time":
            config["close"],

        "open_tehran":
            open_tehran,

        "close_tehran":
            close_tehran,

        "next_event":
            next_event,

        "remaining":
            remaining,

        "countdown":
            countdown,

        "progress":
            progress,

        "progress_bar":
            progress_bar(
                progress
            ),

        "utc_offset":
            offset_text,
    }


def all_sessions():

    now = datetime.now(
        timezone.utc
    )

    return [
        get_session_status(
            key,
            now,
        )
        for key
        in SESSIONS
    ]


def active_sessions():

    return [
        item
        for item
        in all_sessions()
        if item["is_open"]
    ]


def next_session():

    closed = [
        item
        for item
        in all_sessions()
        if not item["is_open"]
    ]

    if not closed:
        return None

    return min(
        closed,
        key=lambda item:
            item["remaining"],
    )


def current_overlap():

    active = active_sessions()

    if len(active) < 2:
        return None

    return " + ".join(
        "{} {}".format(
            item["flag"],
            item["name"],
        )
        for item
        in active
    )


# ============================================================
# WEEKLY FOREX MARKET
# ============================================================

def weekly_forex_status(
    now_utc=None,
):

    if now_utc is None:

        now_utc = datetime.now(
            timezone.utc
        )

    ny_now = now_utc.astimezone(
        NEW_YORK_ZONE
    )

    weekday = (
        ny_now.weekday()
    )

    # Friday of the current logical week
    days_until_friday = (
        4 - weekday
    )

    friday_date = (
        ny_now.date()
        + timedelta(
            days=days_until_friday
        )
    )

    friday_close = datetime.combine(
        friday_date,
        time(17, 0),
        tzinfo=NEW_YORK_ZONE,
    )

    # Sunday corresponding to weekend
    sunday_open = (
        friday_close
        + timedelta(
            days=2
        )
    )

    # Friday after 17:00:
    # currently in weekly closure
    if (
        weekday == 4
        and
        ny_now >= friday_close
    ):

        market_open = False

        next_open = (
            friday_close
            + timedelta(
                days=2
            )
        )

        remaining = (
            next_open - ny_now
        )

        event = (
            "weekly_open"
        )

        next_close = None

    # Saturday
    elif weekday == 5:

        market_open = False

        # Find the next Sunday 17:00
        days_to_sunday = 1

        next_open = datetime.combine(
            ny_now.date()
            + timedelta(
                days=days_to_sunday
            ),
            time(17, 0),
            tzinfo=NEW_YORK_ZONE,
        )

        remaining = (
            next_open - ny_now
        )

        event = (
            "weekly_open"
        )

        next_close = None

    # Sunday before 17:00
    elif (
        weekday == 6
        and
        ny_now.time()
        < time(17, 0)
    ):

        market_open = False

        next_open = datetime.combine(
            ny_now.date(),
            time(17, 0),
            tzinfo=NEW_YORK_ZONE,
        )

        remaining = (
            next_open - ny_now
        )

        event = (
            "weekly_open"
        )

        next_close = None

    # Market is open
    else:

        market_open = True

        # Next Friday
        days_to_friday = (
            4 - weekday
        )

        if days_to_friday < 0:

            days_to_friday += 7

        next_close = datetime.combine(
            ny_now.date()
            + timedelta(
                days=days_to_friday
            ),
            time(17, 0),
            tzinfo=NEW_YORK_ZONE,
        )

        if next_close <= ny_now:

            next_close += timedelta(
                days=7
            )

        remaining = (
            next_close - ny_now
        )

        next_open = (
            next_close
            + timedelta(
                days=2
            )
        )

        event = (
            "weekly_close"
        )

    iran_now = (
        now_utc.astimezone(
            TEHRAN_ZONE
        )
    )

    close_tehran = (
        next_close.astimezone(
            TEHRAN_ZONE
        )
        if next_close
        else None
    )

    open_tehran = (
        next_open.astimezone(
            TEHRAN_ZONE
        )
    )

    countdown = (
        format_countdown(
            remaining
        )
    )

    return {
        "market_open":
            market_open,

        "event":
            event,

        "ny_now":
            ny_now,

        "iran_now":
            iran_now,

        "next_close":
            next_close,

        "next_close_tehran":
            close_tehran,

        "next_open":
            next_open,

        "next_open_tehran":
            open_tehran,

        "remaining":
            remaining,

        "countdown":
            countdown,
    }
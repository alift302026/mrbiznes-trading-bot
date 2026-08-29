from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from app.engines.sessions.session_engine import (
    SESSIONS,
    get_session_status,
    weekly_forex_status,
)

from app.services.user_service import (
    get_session_alert_users,
)


# ============================================================
# CONFIG
# ============================================================

TEHRAN_ZONE = ZoneInfo(
    "Asia/Tehran"
)

# چند دقیقه قبل از رویداد هشدار بده
PRE_ALERT_MINUTES = {
    30,
    15,
    5,
}


# ============================================================
# HELPERS
# ============================================================

def seconds_left(delta):

    return max(
        0,
        int(
            delta.total_seconds()
        ),
    )


def minutes_left(delta):

    return (
        seconds_left(delta)
        // 60
    )


def event_marker(
    prefix,
    target,
    stage,
):

    return (
        "{}:{}:{}"
    ).format(
        prefix,
        target.isoformat(
            timespec="minutes"
        ),
        stage,
    )


def iran_datetime(
    value,
):

    return (
        value
        .astimezone(
            TEHRAN_ZONE
        )
        .strftime(
            "%Y/%m/%d %H:%M"
        )
    )


# ============================================================
# SESSION PRE-ALERT TEXT
# ============================================================

def build_session_pre_alert(
    language,
    item,
    event_type,
    minutes,
):

    iran_time = iran_datetime(
        item["next_event"]
    )

    flag = item["flag"]
    name = item["name"]

    # Persian
    if language == "fa":

        if event_type == "open":
            action = "باز شدن"
            icon = "🔔"
        else:
            action = "بسته شدن"
            icon = "🔕"

        return (
            "🌍 ALIFT SESSION ALERT\n"
            "━━━━━━━━━━━━━━━━\n\n"
            "{} {} {}\n\n"
            "⏳ {} دقیقه تا {}\n\n"
            "🇮🇷 زمان رویداد به وقت ایران:\n"
            "{}"
        ).format(
            flag,
            name,
            icon,
            minutes,
            action,
            iran_time,
        )

    # Arabic
    if language == "ar":

        if event_type == "open":
            action = "افتتاح الجلسة"
            icon = "🔔"
        else:
            action = "إغلاق الجلسة"
            icon = "🔕"

        return (
            "🌍 ALIFT SESSION ALERT\n"
            "━━━━━━━━━━━━━━━━\n\n"
            "{} {} {}\n\n"
            "⏳ بقي {} دقيقة حتى {}\n\n"
            "🇮🇷 بتوقيت إيران:\n"
            "{}"
        ).format(
            flag,
            name,
            icon,
            minutes,
            action,
            iran_time,
        )

    # English
    if event_type == "open":
        action = "session open"
        icon = "🔔"
    else:
        action = "session close"
        icon = "🔕"

    return (
        "🌍 ALIFT SESSION ALERT\n"
        "━━━━━━━━━━━━━━━━\n\n"
        "{} {} {}\n\n"
        "⏳ {} minutes until {}\n\n"
        "🇮🇷 Iran Time:\n"
        "{}"
    ).format(
        flag,
        name,
        icon,
        minutes,
        action,
        iran_time,
    )


# ============================================================
# SESSION EVENT TEXT
# ============================================================

def build_session_event_alert(
    language,
    item,
    event_type,
):

    iran_time = iran_datetime(
        item["next_event"]
    )

    flag = item["flag"]
    name = item["name"]

    if language == "fa":

        if event_type == "open":
            title = "🟢 سشن باز شد"
        else:
            title = "🔴 سشن بسته شد"

        return (
            "🌍 ALIFT SESSION ALERT\n"
            "━━━━━━━━━━━━━━━━\n\n"
            "{}\n\n"
            "{} {}\n\n"
            "🇮🇷 زمان ایران:\n"
            "{}"
        ).format(
            title,
            flag,
            name,
            iran_time,
        )

    if language == "ar":

        if event_type == "open":
            title = "🟢 بدأت الجلسة"
        else:
            title = "🔴 أغلقت الجلسة"

        return (
            "🌍 ALIFT SESSION ALERT\n"
            "━━━━━━━━━━━━━━━━\n\n"
            "{}\n\n"
            "{} {}\n\n"
            "🇮🇷 بتوقيت إيران:\n"
            "{}"
        ).format(
            title,
            flag,
            name,
            iran_time,
        )

    if event_type == "open":
        title = "🟢 SESSION OPENED"
    else:
        title = "🔴 SESSION CLOSED"

    return (
        "🌍 ALIFT SESSION ALERT\n"
        "━━━━━━━━━━━━━━━━\n\n"
        "{}\n\n"
        "{} {}\n\n"
        "🇮🇷 Iran Time:\n"
        "{}"
    ).format(
        title,
        flag,
        name,
        iran_time,
    )


# ============================================================
# WEEKLY PRE-ALERT TEXT
# ============================================================

def build_weekly_pre_alert(
    language,
    weekly,
    minutes,
):

    event = weekly["event"]

    if event == "weekly_open":

        event_time = (
            weekly[
                "next_open_tehran"
            ]
        )

    else:

        event_time = (
            weekly[
                "next_close_tehran"
            ]
        )

    iran_time = event_time.strftime(
        "%Y/%m/%d %H:%M"
    )

    if language == "fa":

        if event == "weekly_open":
            title = (
                "🔔 بازگشایی هفتگی بازار"
            )
        else:
            title = (
                "🔕 شروع تعطیلی هفتگی بازار"
            )

        return (
            "📅 ALIFT WEEKLY ALERT\n"
            "━━━━━━━━━━━━━━━━\n\n"
            "{}\n\n"
            "⏳ {} دقیقه باقی مانده\n\n"
            "🇮🇷 زمان ایران:\n"
            "{}"
        ).format(
            title,
            minutes,
            iran_time,
        )

    if language == "ar":

        if event == "weekly_open":
            title = (
                "🔔 إعادة افتتاح السوق الأسبوعي"
            )
        else:
            title = (
                "🔕 بداية عطلة السوق الأسبوعية"
            )

        return (
            "📅 ALIFT WEEKLY ALERT\n"
            "━━━━━━━━━━━━━━━━\n\n"
            "{}\n\n"
            "⏳ بقي {} دقيقة\n\n"
            "🇮🇷 بتوقيت إيران:\n"
            "{}"
        ).format(
            title,
            minutes,
            iran_time,
        )

    if event == "weekly_open":
        title = "🔔 WEEKLY MARKET REOPEN"
    else:
        title = "🔕 WEEKLY MARKET CLOSE"

    return (
        "📅 ALIFT WEEKLY ALERT\n"
        "━━━━━━━━━━━━━━━━\n\n"
        "{}\n\n"
        "⏳ {} minutes remaining\n\n"
        "🇮🇷 Iran Time:\n"
        "{}"
    ).format(
        title,
        minutes,
        iran_time,
    )


# ============================================================
# WEEKLY EVENT TEXT
# ============================================================

def build_weekly_event_alert(
    language,
    weekly,
):

    event = weekly["event"]

    if event == "weekly_open":
        event_time = (
            weekly[
                "next_open_tehran"
            ]
        )
    else:
        event_time = (
            weekly[
                "next_close_tehran"
            ]
        )

    iran_time = event_time.strftime(
        "%Y/%m/%d %H:%M"
    )

    if language == "fa":

        if event == "weekly_open":
            title = (
                "🟢 بازار بعد از تعطیلی "
                "هفتگی باز شد"
            )
        else:
            title = (
                "🔴 تعطیلی هفتگی "
                "بازار شروع شد"
            )

        return (
            "📅 ALIFT WEEKLY ALERT\n"
            "━━━━━━━━━━━━━━━━\n\n"
            "{}\n\n"
            "🇮🇷 زمان ایران:\n"
            "{}"
        ).format(
            title,
            iran_time,
        )

    if language == "ar":

        if event == "weekly_open":
            title = (
                "🟢 أعيد فتح السوق "
                "بعد العطلة الأسبوعية"
            )
        else:
            title = (
                "🔴 بدأت عطلة "
                "السوق الأسبوعية"
            )

        return (
            "📅 ALIFT WEEKLY ALERT\n"
            "━━━━━━━━━━━━━━━━\n\n"
            "{}\n\n"
            "🇮🇷 بتوقيت إيران:\n"
            "{}"
        ).format(
            title,
            iran_time,
        )

    if event == "weekly_open":
        title = (
            "🟢 MARKET REOPENED "
            "AFTER WEEKEND"
        )
    else:
        title = (
            "🔴 WEEKLY MARKET "
            "BREAK STARTED"
        )

    return (
        "📅 ALIFT WEEKLY ALERT\n"
        "━━━━━━━━━━━━━━━━\n\n"
        "{}\n\n"
        "🇮🇷 Iran Time:\n"
        "{}"
    ).format(
        title,
        iran_time,
    )


# ============================================================
# SEND TO SUBSCRIBED USERS
# ============================================================

async def broadcast_session_alert(
    context,
    builder,
):

    users = (
        get_session_alert_users()
    )

    for user in users:

        try:

            text = builder(
                user["language"]
            )

            await context.bot.send_message(
                chat_id=(
                    user[
                        "telegram_id"
                    ]
                ),
                text=text,
            )

        except Exception as exc:

            print(
                "SESSION ALERT ERROR:",
                user["telegram_id"],
                repr(exc),
            )


# ============================================================
# CHECK INDIVIDUAL SESSIONS
# ============================================================

async def check_sessions(
    context,
    now,
):

    memory = (
        context.application
        .bot_data
    )

    for key in SESSIONS:

        item = get_session_status(
            key,
            now,
        )

        total_seconds = seconds_left(
            item["remaining"]
        )

        minutes = (
            total_seconds // 60
        )

        if item["is_open"]:
            event_type = "close"
        else:
            event_type = "open"

        # ----------------------------------------------------
        # 30 / 15 / 5 MINUTES BEFORE
        # ----------------------------------------------------

        if minutes in PRE_ALERT_MINUTES:

            marker = event_marker(
                "session:{}:{}".format(
                    key,
                    event_type,
                ),
                item["next_event"],
                "{}m".format(
                    minutes
                ),
            )

            if not memory.get(marker):

                memory[marker] = True

                def builder(
                    language,
                    item=item,
                    event_type=event_type,
                    minutes=minutes,
                ):

                    return (
                        build_session_pre_alert(
                            language,
                            item,
                            event_type,
                            minutes,
                        )
                    )

                await broadcast_session_alert(
                    context,
                    builder,
                )

        # ----------------------------------------------------
        # EXACT EVENT
        #
        # Job runs frequently, so first 45 seconds counts
        # as event moment.
        # ----------------------------------------------------

        if total_seconds <= 45:

            marker = event_marker(
                "session:{}:{}".format(
                    key,
                    event_type,
                ),
                item["next_event"],
                "event",
            )

            if not memory.get(marker):

                memory[marker] = True

                def event_builder(
                    language,
                    item=item,
                    event_type=event_type,
                ):

                    return (
                        build_session_event_alert(
                            language,
                            item,
                            event_type,
                        )
                    )

                await broadcast_session_alert(
                    context,
                    event_builder,
                )


# ============================================================
# CHECK WEEKLY MARKET
# ============================================================

async def check_weekly_market(
    context,
    now,
):

    weekly = weekly_forex_status(
        now
    )

    total_seconds = seconds_left(
        weekly["remaining"]
    )

    minutes = (
        total_seconds // 60
    )

    event = weekly["event"]

    if event == "weekly_open":

        target = (
            weekly["next_open"]
        )

    else:

        target = (
            weekly["next_close"]
        )

    memory = (
        context.application
        .bot_data
    )

    # --------------------------------------------------------
    # PRE ALERT
    # --------------------------------------------------------

    if minutes in PRE_ALERT_MINUTES:

        marker = event_marker(
            event,
            target,
            "{}m".format(
                minutes
            ),
        )

        if not memory.get(marker):

            memory[marker] = True

            def builder(
                language,
                weekly=weekly,
                minutes=minutes,
            ):

                return (
                    build_weekly_pre_alert(
                        language,
                        weekly,
                        minutes,
                    )
                )

            await broadcast_session_alert(
                context,
                builder,
            )

    # --------------------------------------------------------
    # EXACT EVENT
    # --------------------------------------------------------

    if total_seconds <= 45:

        marker = event_marker(
            event,
            target,
            "event",
        )

        if not memory.get(marker):

            memory[marker] = True

            def event_builder(
                language,
                weekly=weekly,
            ):

                return (
                    build_weekly_event_alert(
                        language,
                        weekly,
                    )
                )

            await broadcast_session_alert(
                context,
                event_builder,
            )


# ============================================================
# CLEAN MEMORY
# ============================================================

def cleanup_memory(
    context,
):

    memory = (
        context.application
        .bot_data
    )

    if len(memory) <= 1000:
        return

    keys = list(
        memory.keys()
    )

    for key in keys[:500]:

        memory.pop(
            key,
            None,
        )


# ============================================================
# MAIN SESSION JOB
# ============================================================

async def session_alert_job(
    context,
):

    now = datetime.now(
        timezone.utc
    )

    await check_sessions(
        context,
        now,
    )

    await check_weekly_market(
        context,
        now,
    )

    cleanup_memory(
        context
    )
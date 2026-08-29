from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)

from telegram.ext import (
    ContextTypes,
)

from app.engines.sessions.session_engine import (
    active_sessions,
    all_sessions,
    current_overlap,
    date_center,
    next_session,
    weekly_forex_status,
)

from app.i18n.translations import t

from app.services.user_service import (
    get_user,
    toggle_session_alerts,
)


def lang_for_user(
    telegram_id,
):

    user = get_user(
        telegram_id
    )

    if (
        user
        and user.language
        in {
            "fa",
            "en",
            "ar",
        }
    ):

        return user.language

    return "en"


def session_keyboard(
    telegram_id,
):

    user = get_user(
        telegram_id
    )

    language = lang_for_user(
        telegram_id
    )

    enabled = (
        user.session_alerts_enabled
        if user
        else False
    )

    alert_label = t(
        language,
        (
            "disable_session_alert"
            if enabled
            else
            "enable_session_alert"
        ),
    )

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    t(
                        language,
                        "refresh",
                    ),
                    callback_data=(
                        "session_refresh"
                    ),
                )
            ],

            [
                InlineKeyboardButton(
                    alert_label,
                    callback_data=(
                        "session_toggle"
                    ),
                )
            ],
        ]
    )


def date_header(
    language,
):

    data = date_center()

    return (
        "{}\n"
        "━━━━━━━━━━━━━━━━\n"
        "{}: {}\n"
        "{}: {}\n"
        "{}: {}\n"
        "{}: {}\n"
        "{}: {}"
    ).format(
        t(
            language,
            "date_center",
        ),

        t(
            language,
            "jalali",
        ),
        data["jalali"],

        t(
            language,
            "gregorian",
        ),
        data["gregorian"],

        t(
            language,
            "hijri",
        ),
        data["hijri"],

        t(
            language,
            "iran_clock",
        ),
        data["tehran_time"],

        t(
            language,
            "utc_clock",
        ),
        data["utc_time"],
    )


def session_card(
    language,
    item,
):

    if item["is_open"]:

        state = t(
            language,
            "session_open",
        )

        timer = t(
            language,
            "time_to_close",
        )

        progress = (
            "\n{}: {:.0f}%\n{}"
        ).format(
            t(
                language,
                "progress",
            ),
            item["progress"],
            item["progress_bar"],
        )

    else:

        state = t(
            language,
            "session_closed",
        )

        timer = t(
            language,
            "time_to_open",
        )

        progress = ""

    count = item[
        "countdown"
    ]

    return (
        "{} {}\n"
        "━━━━━━━━━━━━━━\n"
        "{}\n"
        "{}: {}\n"
        "{}: {}\n\n"

        "{}\n"
        "{}: {}\n"
        "{}: {}\n\n"

        "{}\n"
        "{}: {}\n"
        "{}: {}\n\n"

        "{}: "
        "{}d {:02d}:{:02d}:{:02d}"
        "{}"
    ).format(
        item["flag"],
        item["name"],

        state,

        t(
            language,
            "local_time",
        ),
        item[
            "local_now"
        ].strftime(
            "%H:%M:%S"
        ),

        t(
            language,
            "timezone",
        ),
        item[
            "utc_offset"
        ],

        t(
            language,
            "official_hours",
        ),

        t(
            language,
            "opens",
        ),
        item[
            "open_time"
        ].strftime(
            "%H:%M"
        ),

        t(
            language,
            "closes",
        ),
        item[
            "close_time"
        ].strftime(
            "%H:%M"
        ),

        t(
            language,
            "iran_time",
        ),

        t(
            language,
            "opens",
        ),
        item[
            "open_tehran"
        ].strftime(
            "%H:%M"
        ),

        t(
            language,
            "closes",
        ),
        item[
            "close_tehran"
        ].strftime(
            "%H:%M"
        ),

        timer,

        count["days"],
        count["hours"],
        count["minutes"],
        count["seconds"],

        progress,
    )


def weekly_market_card(
    language,
):

    weekly = (
        weekly_forex_status()
    )

    count = (
        weekly["countdown"]
    )

    if language == "fa":

        if weekly[
            "market_open"
        ]:

            title = (
                "📅 تعطیلی هفتگی بازار"
            )

            status = (
                "🟢 بازار هفتگی باز است"
            )

            timer = (
                "⏳ زمان تا شروع "
                "تعطیلی هفتگی"
            )

        else:

            title = (
                "📅 تعطیلی هفتگی بازار"
            )

            status = (
                "🔴 بازار در تعطیلی "
                "آخر هفته است"
            )

            timer = (
                "⏳ زمان تا بازگشایی "
                "هفتگی"
            )

        open_label = (
            "🔔 بازگشایی بعد از تعطیلی"
        )

        close_label = (
            "🔕 تعطیلی بعدی"
        )

    elif language == "ar":

        if weekly[
            "market_open"
        ]:

            title = (
                "📅 عطلة السوق الأسبوعية"
            )

            status = (
                "🟢 السوق مفتوح"
            )

            timer = (
                "⏳ الوقت حتى "
                "الإغلاق الأسبوعي"
            )

        else:

            title = (
                "📅 عطلة السوق الأسبوعية"
            )

            status = (
                "🔴 السوق في عطلة "
                "نهاية الأسبوع"
            )

            timer = (
                "⏳ الوقت حتى "
                "إعادة الافتتاح"
            )

        open_label = (
            "🔔 إعادة الافتتاح"
        )

        close_label = (
            "🔕 الإغلاق القادم"
        )

    else:

        if weekly[
            "market_open"
        ]:

            title = (
                "📅 WEEKLY MARKET BREAK"
            )

            status = (
                "🟢 Weekly market is open"
            )

            timer = (
                "⏳ Time until weekly close"
            )

        else:

            title = (
                "📅 WEEKLY MARKET BREAK"
            )

            status = (
                "🔴 Weekend market closure"
            )

            timer = (
                "⏳ Time until weekly reopen"
            )

        open_label = (
            "🔔 Weekly reopen"
        )

        close_label = (
            "🔕 Next weekly close"
        )

    lines = [
        title,
        "━━━━━━━━━━━━━━━━",
        status,
        "",
    ]

    if (
        weekly[
            "next_close_tehran"
        ]
        is not None
    ):

        lines.append(
            "{}: {}".format(
                close_label,
                weekly[
                    "next_close_tehran"
                ].strftime(
                    "%Y/%m/%d %H:%M"
                ),
            )
        )

    lines.append(
        "{}: {}".format(
            open_label,
            weekly[
                "next_open_tehran"
            ].strftime(
                "%Y/%m/%d %H:%M"
            ),
        )
    )

    lines.extend(
        [
            "",
            "{}:".format(
                timer
            ),
            (
                "{} روز، "
                "{:02d} ساعت، "
                "{:02d} دقیقه، "
                "{:02d} ثانیه"
            ).format(
                count["days"],
                count["hours"],
                count["minutes"],
                count["seconds"],
            )
            if language == "fa"
            else
            (
                "{}d "
                "{:02d}:"
                "{:02d}:"
                "{:02d}"
            ).format(
                count["days"],
                count["hours"],
                count["minutes"],
                count["seconds"],
            ),
            "",
            (
                "🇮🇷 تمام زمان‌های بالا "
                "به وقت ایران هستند."
                if language == "fa"
                else
                "🇮🇷 Times shown above "
                "are in Iran time."
            ),
        ]
    )

    return "\n".join(
        lines
    )


def build_page(
    telegram_id,
):

    language = lang_for_user(
        telegram_id
    )

    cards = [
        session_card(
            language,
            item,
        )
        for item
        in all_sessions()
    ]

    user = get_user(
        telegram_id
    )

    alerts = (
        user.session_alerts_enabled
        if user
        else False
    )

    alert_text = t(
        language,
        (
            "session_alert_on"
            if alerts
            else
            "session_alert_off"
        ),
    )

    return (
        "{}\n\n"
        "{}\n"
        "━━━━━━━━━━━━━━━━\n\n"
        "{}\n\n"
        "━━━━━━━━━━━━━━━━\n\n"
        "{}\n\n"
        "━━━━━━━━━━━━━━━━\n"
        "{}"
    ).format(
        date_header(
            language
        ),

        t(
            language,
            "session_center",
        ),

        (
            "\n\n"
            "━━━━━━━━━━━━━━━━\n\n"
        ).join(
            cards
        ),

        weekly_market_card(
            language
        ),

        alert_text,
    )


async def sessions_page(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    telegram_id = (
        update.effective_user.id
    )

    await update.message.reply_text(
        build_page(
            telegram_id
        ),
        reply_markup=(
            session_keyboard(
                telegram_id
            )
        ),
    )


async def session_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = (
        update.callback_query
    )

    if query is None:
        return

    await query.answer()

    telegram_id = (
        query.from_user.id
    )

    if (
        query.data
        == "session_toggle"
    ):

        toggle_session_alerts(
            telegram_id
        )

    try:

        await query.edit_message_text(
            build_page(
                telegram_id
            ),
            reply_markup=(
                session_keyboard(
                    telegram_id
                )
            ),
        )

    except Exception as exc:

        if (
            "Message is not modified"
            not in str(exc)
        ):

            raise
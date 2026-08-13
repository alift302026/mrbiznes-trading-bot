from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)

from telegram.ext import (
    ContextTypes,
)

from app.engines.alerts.market_alert_engine import (
    SUPPORTED_SYMBOLS,
    SUPPORTED_TIMEFRAMES,
)

from app.services.alert_service import (
    AlertLimitReached,
    alert_capacity,
    create_alert,
    delete_alert,
    toggle_alert,
    user_alerts,
)

from app.services.user_service import (
    get_user,
)


# ============================================================
# LANGUAGE
# ============================================================

def user_language(
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


# ============================================================
# CAPACITY BAR
# ============================================================

def capacity_bar(
    current,
    limit,
):

    if limit is None:

        return "██████████ ∞"

    if limit <= 0:

        return "░░░░░░░░░░"

    percentage = min(
        1,
        current / limit,
    )

    filled = round(
        percentage * 10
    )

    return (
        "█" * filled
        + "░" * (
            10 - filled
        )
    )


# ============================================================
# HOME TEXT
# ============================================================

def alert_home_text(
    telegram_id,
):

    language = user_language(
        telegram_id
    )

    capacity = alert_capacity(
        telegram_id
    )

    active = capacity[
        "active"
    ]

    limit = capacity[
        "limit"
    ]

    if capacity[
        "is_admin"
    ]:

        plan_text = (
            "🛡 ADMIN"
        )

        usage = (
            "{} / ∞"
        ).format(
            active
        )

    elif capacity[
        "plan"
    ] == "vip":

        plan_text = (
            "💎 VIP"
        )

        usage = (
            "{} / {}"
        ).format(
            active,
            limit,
        )

    else:

        plan_text = (
            "👤 NORMAL"
        )

        usage = (
            "{} / {}"
        ).format(
            active,
            limit,
        )

    bar = capacity_bar(
        active,
        limit,
    )

    if language == "fa":

        return (
            "🔔 ALIFT SMART ALERTS\n"
            "━━━━━━━━━━━━━━━━\n\n"

            "👁 بازار رو لازم نیست ۲۴ ساعته "
            "نگاه کنی؛ ALIFT برات زیر نظرش می‌گیره.\n\n"

            "{}\n"
            "🔔 آلارم فعال: {}\n"
            "{}\n\n"

            "چه چیزی می‌خوای زیر نظر بگیری؟\n\n"

            "💰 Price Alert\n"
            "📈 EMA20/50 Cross\n"
            "📊 RSI\n"
            "〽️ MACD\n"
            "💧 Volume Spike\n"
            "🌍 Session Alerts"
        ).format(
            plan_text,
            usage,
            bar,
        )

    if language == "ar":

        return (
            "🔔 ALIFT SMART ALERTS\n"
            "━━━━━━━━━━━━━━━━\n\n"

            "دع ALIFT يراقب السوق بدلاً منك 👀\n\n"

            "{}\n"
            "🔔 التنبيهات النشطة: {}\n"
            "{}\n\n"

            "💰 تنبيه السعر\n"
            "📈 تقاطع EMA\n"
            "📊 RSI\n"
            "〽️ MACD\n"
            "💧 ارتفاع الحجم\n"
            "🌍 تنبيهات الجلسات"
        ).format(
            plan_text,
            usage,
            bar,
        )

    return (
        "🔔 ALIFT SMART ALERTS\n"
        "━━━━━━━━━━━━━━━━\n\n"

        "You don't need to watch the market "
        "24/7. Let ALIFT watch it for you 👀\n\n"

        "{}\n"
        "🔔 Active Alerts: {}\n"
        "{}\n\n"

        "💰 Price Alert\n"
        "📈 EMA20/50 Cross\n"
        "📊 RSI\n"
        "〽️ MACD\n"
        "💧 Volume Spike\n"
        "🌍 Session Alerts"
    ).format(
        plan_text,
        usage,
        bar,
    )


# ============================================================
# HOME KEYBOARD
# ============================================================

def alert_home_keyboard(
    language,
):

    labels = {
        "fa": {
            "new":
                "➕ ساخت آلارم جدید",

            "mine":
                "📋 آلارم‌های من",

            "guide":
                "📖 راهنمای آلارم‌ها",

            "test":
                "🧪 تست اعلان",

            "vip":
                "💎 ارتقا به VIP",
        },

        "en": {
            "new":
                "➕ Create Alert",

            "mine":
                "📋 My Alerts",

            "guide":
                "📖 Alert Guide",

            "test":
                "🧪 Test Notification",

            "vip":
                "💎 Upgrade to VIP",
        },

        "ar": {
            "new":
                "➕ إنشاء تنبيه",

            "mine":
                "📋 تنبيهاتي",

            "guide":
                "📖 دليل التنبيهات",

            "test":
                "🧪 اختبار الإشعار",

            "vip":
                "💎 الترقية إلى VIP",
        },
    }[language]

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    labels["new"],
                    callback_data="alert_new",
                )
            ],

            [
                InlineKeyboardButton(
                    labels["mine"],
                    callback_data="alert_list",
                )
            ],

            [
                InlineKeyboardButton(
                    labels["guide"],
                    callback_data="alert_guide",
                ),

                InlineKeyboardButton(
                    labels["test"],
                    callback_data="alert_test",
                ),
            ],

            [
                InlineKeyboardButton(
                    labels["vip"],
                    callback_data="alert_vip",
                )
            ],
        ]
    )


# ============================================================
# ALERT HOME
# ============================================================

async def alerts_home(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    telegram_id = (
        update.effective_user.id
    )

    language = user_language(
        telegram_id
    )

    await update.message.reply_text(
        alert_home_text(
            telegram_id
        ),
        reply_markup=(
            alert_home_keyboard(
                language
            )
        ),
    )


# ============================================================
# LIMIT MESSAGE
# ============================================================

def limit_message(
    language,
    current,
    limit,
    plan,
):

    if language == "fa":

        return (
            "🔒 سقف آلارم‌های حسابت تکمیل شده\n"
            "━━━━━━━━━━━━━━━━\n\n"

            "👤 پلن فعلی: {}\n"
            "🔔 آلارم فعال: {} / {}\n\n"

            "برای ساخت آلارم بیشتر:\n"
            "💎 ALIFT VIP → تا 50 آلارم فعال\n\n"

            "می‌تونی یکی از آلارم‌های فعلی رو "
            "خاموش/حذف کنی یا حسابت رو ارتقا بدی."
        ).format(
            plan.upper(),
            current,
            limit,
        )

    if language == "ar":

        return (
            "🔒 وصلت إلى الحد الأقصى للتنبيهات\n"
            "━━━━━━━━━━━━━━━━\n\n"

            "الخطة: {}\n"
            "التنبيهات النشطة: {} / {}\n\n"

            "💎 VIP يسمح بما يصل إلى 50 تنبيهاً."
        ).format(
            plan.upper(),
            current,
            limit,
        )

    return (
        "🔒 ACTIVE ALERT LIMIT REACHED\n"
        "━━━━━━━━━━━━━━━━\n\n"

        "Plan: {}\n"
        "Active Alerts: {} / {}\n\n"

        "💎 ALIFT VIP supports up to "
        "50 active alerts.\n\n"

        "Disable/delete an existing alert "
        "or upgrade your plan."
    ).format(
        plan.upper(),
        current,
        limit,
    )


def limit_keyboard(
    language,
):

    labels = {
        "fa": {
            "vip":
                "💎 مشاهده VIP",

            "alerts":
                "📋 مدیریت آلارم‌ها",
        },

        "en": {
            "vip":
                "💎 View VIP",

            "alerts":
                "📋 Manage Alerts",
        },

        "ar": {
            "vip":
                "💎 عرض VIP",

            "alerts":
                "📋 إدارة التنبيهات",
        },
    }[language]

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    labels["vip"],
                    callback_data="alert_vip",
                )
            ],

            [
                InlineKeyboardButton(
                    labels["alerts"],
                    callback_data="alert_list",
                )
            ],
        ]
    )


# ============================================================
# GUIDE
# ============================================================

def guide_text(
    language,
):

    if language == "fa":

        return (
            "📖 راهنمای ALIFT ALERTS\n"
            "━━━━━━━━━━━━━━━━\n\n"

            "💰 Price Alert\n"
            "وقتی قیمت به عددی که مشخص کردی برسه.\n\n"

            "📈 EMA Cross\n"
            "کراس EMA20 و EMA50 رو زیر نظر می‌گیره.\n\n"

            "📊 RSI\n"
            "اشباع خرید RSI ≥ 70 یا "
            "اشباع فروش RSI ≤ 30.\n\n"

            "〽️ MACD\n"
            "کراس صعودی یا نزولی MACD.\n\n"

            "💧 Volume Spike\n"
            "وقتی حجم حدود 1.8 برابر "
            "میانگین 20 کندل اخیر بشه.\n\n"

            "🌍 Session Alerts\n"
            "هشدار شروع/پایان سشن‌ها و "
            "تعطیلی هفتگی.\n\n"

            "💡 نکته:\n"
            "آلارم فقط اطلاع‌رسانیه و هیچ "
            "معامله‌ای برای تو اجرا نمی‌کنه."
        )

    if language == "ar":

        return (
            "📖 دليل ALIFT ALERTS\n"
            "━━━━━━━━━━━━━━━━\n\n"

            "💰 السعر: عند وصول السعر إلى هدفك.\n\n"
            "📈 EMA: تقاطع EMA20 و EMA50.\n\n"
            "📊 RSI: مناطق التشبع.\n\n"
            "〽️ MACD: التقاطع الصاعد أو الهابط.\n\n"
            "💧 Volume: ارتفاع غير عادي في الحجم.\n\n"
            "🌍 Sessions: افتتاح وإغلاق الجلسات.\n\n"
            "💡 التنبيه للمعلومات فقط ولا ينفذ صفقات."
        )

    return (
        "📖 ALIFT ALERT GUIDE\n"
        "━━━━━━━━━━━━━━━━\n\n"

        "💰 Price Alert\n"
        "Triggered when price reaches your target.\n\n"

        "📈 EMA Cross\n"
        "Monitors EMA20 / EMA50 crosses.\n\n"

        "📊 RSI\n"
        "RSI ≥ 70 or RSI ≤ 30.\n\n"

        "〽️ MACD\n"
        "Bullish or bearish MACD cross.\n\n"

        "💧 Volume Spike\n"
        "Volume reaches about 1.8x "
        "the recent 20-candle average.\n\n"

        "🌍 Session Alerts\n"
        "Session open/close and weekly market alerts.\n\n"

        "💡 Alerts are informational only. "
        "They never execute trades."
    )


# ============================================================
# SYMBOL KEYBOARD
# ============================================================

def symbol_keyboard():

    items = list(
        SUPPORTED_SYMBOLS.items()
    )

    rows = []

    for index in range(
        0,
        len(items),
        2,
    ):

        row = []

        for code, symbol in (
            items[
                index:
                index + 2
            ]
        ):

            row.append(
                InlineKeyboardButton(
                    symbol,
                    callback_data=(
                        "alert_symbol_{}"
                    ).format(
                        code
                    ),
                )
            )

        rows.append(row)

    rows.append(
        [
            InlineKeyboardButton(
                "⬅️ Back",
                callback_data="alert_home",
            )
        ]
    )

    return InlineKeyboardMarkup(
        rows
    )


# ============================================================
# TYPE KEYBOARD
# ============================================================

def type_keyboard(
    code,
):

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "💰 Price Above",
                    callback_data=(
                        "alert_type_{}_price_above"
                    ).format(code),
                ),

                InlineKeyboardButton(
                    "💰 Price Below",
                    callback_data=(
                        "alert_type_{}_price_below"
                    ).format(code),
                ),
            ],

            [
                InlineKeyboardButton(
                    "📈 EMA Bull",
                    callback_data=(
                        "alert_type_{}_ema_bull"
                    ).format(code),
                ),

                InlineKeyboardButton(
                    "📉 EMA Bear",
                    callback_data=(
                        "alert_type_{}_ema_bear"
                    ).format(code),
                ),
            ],

            [
                InlineKeyboardButton(
                    "📊 RSI ≥ 70",
                    callback_data=(
                        "alert_type_{}_rsi_high"
                    ).format(code),
                ),

                InlineKeyboardButton(
                    "📊 RSI ≤ 30",
                    callback_data=(
                        "alert_type_{}_rsi_low"
                    ).format(code),
                ),
            ],

            [
                InlineKeyboardButton(
                    "〽️ MACD Bull",
                    callback_data=(
                        "alert_type_{}_macd_bull"
                    ).format(code),
                ),

                InlineKeyboardButton(
                    "〽️ MACD Bear",
                    callback_data=(
                        "alert_type_{}_macd_bear"
                    ).format(code),
                ),
            ],

            [
                InlineKeyboardButton(
                    "💧 Volume Spike",
                    callback_data=(
                        "alert_type_{}_volume_spike"
                    ).format(code),
                )
            ],

            [
                InlineKeyboardButton(
                    "⬅️ Back",
                    callback_data="alert_new",
                )
            ],
        ]
    )


# ============================================================
# TIMEFRAME KEYBOARD
# ============================================================

def timeframe_keyboard(
    code,
    alert_type,
):

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "15M",
                    callback_data=(
                        "alert_tf_{}_{}_15m"
                    ).format(
                        code,
                        alert_type,
                    ),
                ),

                InlineKeyboardButton(
                    "1H",
                    callback_data=(
                        "alert_tf_{}_{}_1h"
                    ).format(
                        code,
                        alert_type,
                    ),
                ),
            ],

            [
                InlineKeyboardButton(
                    "4H",
                    callback_data=(
                        "alert_tf_{}_{}_4h"
                    ).format(
                        code,
                        alert_type,
                    ),
                ),

                InlineKeyboardButton(
                    "1D",
                    callback_data=(
                        "alert_tf_{}_{}_1d"
                    ).format(
                        code,
                        alert_type,
                    ),
                ),
            ],
        ]
    )


# ============================================================
# ALERT TYPE NAME
# ============================================================

def alert_type_name(
    value,
):

    names = {
        "price_above":
            "Price ≥",

        "price_below":
            "Price ≤",

        "ema_bull":
            "EMA20/50 Bull Cross",

        "ema_bear":
            "EMA20/50 Bear Cross",

        "rsi_high":
            "RSI ≥ 70",

        "rsi_low":
            "RSI ≤ 30",

        "macd_bull":
            "MACD Bull Cross",

        "macd_bear":
            "MACD Bear Cross",

        "volume_spike":
            "Volume Spike",
    }

    return names.get(
        value,
        value,
    )


# ============================================================
# ALERT LIST KEYBOARD
# ============================================================

def list_keyboard(
    items,
):

    rows = []

    for item in items:

        icon = (
            "🟢"
            if item.is_active
            else "⚫"
        )

        rows.append(
            [
                InlineKeyboardButton(
                    (
                        "{} #{} {}"
                    ).format(
                        icon,
                        item.id,
                        item.symbol,
                    ),
                    callback_data=(
                        "alert_view_{}"
                    ).format(
                        item.id
                    ),
                )
            ]
        )

    rows.append(
        [
            InlineKeyboardButton(
                "➕ New Alert",
                callback_data="alert_new",
            )
        ]
    )

    rows.append(
        [
            InlineKeyboardButton(
                "🏠 Alert Home",
                callback_data="alert_home",
            )
        ]
    )

    return InlineKeyboardMarkup(
        rows
    )


# ============================================================
# CREATE WITH LIMIT HANDLING
# ============================================================

def safely_create_alert(
    telegram_id,
    symbol,
    alert_type,
    timeframe,
    target_value=None,
):

    try:

        item = create_alert(
            telegram_id=telegram_id,
            symbol=symbol,
            alert_type=alert_type,
            timeframe=timeframe,
            target_value=target_value,
        )

        return item, None

    except AlertLimitReached as exc:

        return None, exc


# ============================================================
# CALLBACK
# ============================================================

async def alert_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = (
        update.callback_query
    )

    if query is None:

        return

    await query.answer()

    user_id = (
        query.from_user.id
    )

    language = user_language(
        user_id
    )

    data = (
        query.data
    )

    # HOME

    if data == "alert_home":

        await query.edit_message_text(
            alert_home_text(
                user_id
            ),
            reply_markup=(
                alert_home_keyboard(
                    language
                )
            ),
        )

        return

    # GUIDE

    if data == "alert_guide":

        await query.edit_message_text(
            guide_text(
                language
            ),
            reply_markup=(
                alert_home_keyboard(
                    language
                )
            ),
        )

        return

    # TEST

    if data == "alert_test":

        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "🚨 ALIFT TEST ALERT\n"
                "━━━━━━━━━━━━━━━━\n\n"
                "✅ Notifications are working.\n\n"
                "BTC/USDT\n"
                "💵 Test Price: $100,000\n\n"
                "این یک آلارم آزمایشی است."
            ),
        )

        await query.answer(
            "✅ Test alert sent",
            show_alert=True,
        )

        return

    # VIP

    if data == "alert_vip":

        await query.edit_message_text(
            (
                "💎 ALIFT VIP\n"
                "━━━━━━━━━━━━━━━━\n\n"
                "👤 NORMAL\n"
                "🔔 Up to 5 active alerts\n\n"
                "💎 VIP\n"
                "🔔 Up to 50 active alerts\n\n"
                "بخش خرید اشتراک در Payment "
                "Engine فعال می‌شود."
            ),
            reply_markup=(
                alert_home_keyboard(
                    language
                )
            ),
        )

        return

    # NEW

    if data == "alert_new":

        capacity = alert_capacity(
            user_id
        )

        if capacity["full"]:

            await query.edit_message_text(
                limit_message(
                    language,
                    capacity[
                        "active"
                    ],
                    capacity[
                        "limit"
                    ],
                    capacity[
                        "plan"
                    ],
                ),
                reply_markup=(
                    limit_keyboard(
                        language
                    )
                ),
            )

            return

        await query.edit_message_text(
            "🪙 Select Asset",
            reply_markup=(
                symbol_keyboard()
            ),
        )

        return

    # SYMBOL

    if data.startswith(
        "alert_symbol_"
    ):

        code = data.replace(
            "alert_symbol_",
            "",
            1,
        )

        if code not in SUPPORTED_SYMBOLS:
            return

        await query.edit_message_text(
            (
                "🔔 {}\n\n"
                "Select Alert Type:"
            ).format(
                SUPPORTED_SYMBOLS[
                    code
                ]
            ),
            reply_markup=(
                type_keyboard(
                    code
                )
            ),
        )

        return

    # TYPE

    if data.startswith(
        "alert_type_"
    ):

        payload = data.replace(
            "alert_type_",
            "",
            1,
        )

        code = None
        alert_type = None

        for possible_code in SUPPORTED_SYMBOLS:

            prefix = (
                possible_code
                + "_"
            )

            if payload.startswith(
                prefix
            ):

                code = possible_code

                alert_type = (
                    payload[
                        len(prefix):
                    ]
                )

                break

        if (
            code is None
            or alert_type is None
        ):

            return

        await query.edit_message_text(
            (
                "⏱ {}\n\n"
                "Select Timeframe:"
            ).format(
                alert_type_name(
                    alert_type
                )
            ),
            reply_markup=(
                timeframe_keyboard(
                    code,
                    alert_type,
                )
            ),
        )

        return

    # TIMEFRAME

    if data.startswith(
        "alert_tf_"
    ):

        payload = data.replace(
            "alert_tf_",
            "",
            1,
        )

        code = None
        remainder = None

        for possible_code in SUPPORTED_SYMBOLS:

            prefix = (
                possible_code
                + "_"
            )

            if payload.startswith(
                prefix
            ):

                code = possible_code

                remainder = (
                    payload[
                        len(prefix):
                    ]
                )

                break

        if (
            code is None
            or remainder is None
        ):

            return

        timeframe = None
        alert_type = None

        for possible_tf in SUPPORTED_TIMEFRAMES:

            suffix = (
                "_"
                + possible_tf
            )

            if remainder.endswith(
                suffix
            ):

                timeframe = (
                    possible_tf
                )

                alert_type = (
                    remainder[
                        :-len(suffix)
                    ]
                )

                break

        if (
            timeframe is None
            or alert_type is None
        ):

            return

        symbol = (
            SUPPORTED_SYMBOLS[
                code
            ]
        )

        # PRICE INPUT

        if alert_type in {
            "price_above",
            "price_below",
        }:

            context.user_data[
                "awaiting_alert_price"
            ] = {
                "symbol":
                    symbol,

                "alert_type":
                    alert_type,

                "timeframe":
                    timeframe,
            }

            await query.edit_message_text(
                (
                    "💰 PRICE ALERT\n"
                    "━━━━━━━━━━━━━━━━\n\n"
                    "Asset: {}\n"
                    "Type: {}\n"
                    "TF: {}\n\n"
                    "حالا قیمت موردنظر رو "
                    "به صورت عدد بفرست.\n\n"
                    "مثال: 65000"
                ).format(
                    symbol,
                    alert_type_name(
                        alert_type
                    ),
                    timeframe,
                )
            )

            return

        # INDICATOR CREATE

        item, limit_error = (
            safely_create_alert(
                telegram_id=user_id,
                symbol=symbol,
                alert_type=alert_type,
                timeframe=timeframe,
            )
        )

        if limit_error:

            await query.edit_message_text(
                limit_message(
                    language,
                    limit_error.current,
                    limit_error.limit,
                    limit_error.plan,
                ),
                reply_markup=(
                    limit_keyboard(
                        language
                    )
                ),
            )

            return

        await query.edit_message_text(
            (
                "✅ ALERT CREATED\n"
                "━━━━━━━━━━━━━━━━\n\n"
                "#{}\n"
                "{}\n"
                "{}\n"
                "TF: {}\n\n"
                "🟢 ACTIVE"
            ).format(
                item.id,
                item.symbol,
                alert_type_name(
                    item.alert_type
                ),
                item.timeframe,
            ),
            reply_markup=(
                alert_home_keyboard(
                    language
                )
            ),
        )

        return

    # LIST

    if data == "alert_list":

        items = user_alerts(
            user_id
        )

        capacity = alert_capacity(
            user_id
        )

        if not items:

            text = (
                "📋 MY ALERTS\n\n"
                "هنوز آلارمی نساختی."
            )

        else:

            lines = [
                "📋 MY ALERTS",
                "━━━━━━━━━━━━━━━━",
                "",
                "Active: {} / {}".format(
                    capacity["active"],
                    (
                        capacity["limit"]
                        if capacity[
                            "limit"
                        ] is not None
                        else "∞"
                    ),
                ),
                "",
            ]

            for item in items:

                lines.append(
                    "{} #{} | {} | {} | {}".format(
                        (
                            "🟢"
                            if item.is_active
                            else "⚫"
                        ),
                        item.id,
                        item.symbol,
                        alert_type_name(
                            item.alert_type
                        ),
                        item.timeframe,
                    )
                )

            text = "\n".join(
                lines
            )

        await query.edit_message_text(
            text,
            reply_markup=(
                list_keyboard(
                    items
                )
            ),
        )

        return

    # VIEW

    if data.startswith(
        "alert_view_"
    ):

        alert_id = int(
            data.replace(
                "alert_view_",
                "",
                1,
            )
        )

        item = next(
            (
                alert
                for alert
                in user_alerts(
                    user_id
                )
                if alert.id
                == alert_id
            ),
            None,
        )

        if item is None:

            return

        await query.edit_message_text(
            (
                "🔔 ALERT #{}\n"
                "━━━━━━━━━━━━━━━━\n\n"
                "Asset: {}\n"
                "Type: {}\n"
                "TF: {}\n"
                "Target: {}\n"
                "Status: {}\n"
                "Triggers: {}"
            ).format(
                item.id,
                item.symbol,
                alert_type_name(
                    item.alert_type
                ),
                item.timeframe,
                (
                    item.target_value
                    if item.target_value
                    is not None
                    else "-"
                ),
                (
                    "🟢 ACTIVE"
                    if item.is_active
                    else "⚫ OFF"
                ),
                item.trigger_count,
            ),
            reply_markup=(
                InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "⏯ Toggle",
                                callback_data=(
                                    "alert_toggle_{}"
                                ).format(
                                    item.id
                                ),
                            )
                        ],

                        [
                            InlineKeyboardButton(
                                "🗑 Delete",
                                callback_data=(
                                    "alert_delete_{}"
                                ).format(
                                    item.id
                                ),
                            )
                        ],

                        [
                            InlineKeyboardButton(
                                "⬅️ My Alerts",
                                callback_data=(
                                    "alert_list"
                                ),
                            )
                        ],
                    ]
                )
            ),
        )

        return

    # TOGGLE

    if data.startswith(
        "alert_toggle_"
    ):

        alert_id = int(
            data.replace(
                "alert_toggle_",
                "",
                1,
            )
        )

        try:

            toggle_alert(
                alert_id,
                user_id,
            )

        except AlertLimitReached as exc:

            await query.edit_message_text(
                limit_message(
                    language,
                    exc.current,
                    exc.limit,
                    exc.plan,
                ),
                reply_markup=(
                    limit_keyboard(
                        language
                    )
                ),
            )

            return

        await query.edit_message_text(
            "✅ Alert status changed.",
            reply_markup=(
                alert_home_keyboard(
                    language
                )
            ),
        )

        return

    # DELETE

    if data.startswith(
        "alert_delete_"
    ):

        alert_id = int(
            data.replace(
                "alert_delete_",
                "",
                1,
            )
        )

        delete_alert(
            alert_id,
            user_id,
        )

        await query.edit_message_text(
            "🗑 Alert deleted.",
            reply_markup=(
                alert_home_keyboard(
                    language
                )
            ),
        )


# ============================================================
# PRICE MESSAGE
# ============================================================

async def alert_price_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    pending = (
        context.user_data.get(
            "awaiting_alert_price"
        )
    )

    if not pending:

        return False

    text = (
        update.message.text
        .strip()
        .replace(
            ",",
            "",
        )
    )

    try:

        value = float(
            text
        )

        if value <= 0:
            raise ValueError

    except ValueError:

        await update.message.reply_text(
            (
                "❌ قیمت معتبر بفرست.\n"
                "مثال: 65000"
            )
        )

        return True

    language = user_language(
        update.effective_user.id
    )

    item, limit_error = (
        safely_create_alert(
            telegram_id=(
                update.effective_user.id
            ),
            symbol=pending[
                "symbol"
            ],
            alert_type=pending[
                "alert_type"
            ],
            timeframe=pending[
                "timeframe"
            ],
            target_value=value,
        )
    )

    context.user_data.pop(
        "awaiting_alert_price",
        None,
    )

    if limit_error:

        await update.message.reply_text(
            limit_message(
                language,
                limit_error.current,
                limit_error.limit,
                limit_error.plan,
            ),
            reply_markup=(
                limit_keyboard(
                    language
                )
            ),
        )

        return True

    await update.message.reply_text(
        (
            "✅ PRICE ALERT CREATED\n"
            "━━━━━━━━━━━━━━━━\n\n"
            "ID: #{}\n"
            "Asset: {}\n"
            "Type: {}\n"
            "Target: {:,.8f}\n"
            "Status: 🟢 ACTIVE"
        ).format(
            item.id,
            item.symbol,
            alert_type_name(
                item.alert_type
            ),
            item.target_value,
        ),
        reply_markup=(
            alert_home_keyboard(
                language
            )
        ),
    )

    return True
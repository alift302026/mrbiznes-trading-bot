import json

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

from app.engines.alerts.symbol_search import (
    search_crypto_symbols,
    validate_crypto_symbol,
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
# CAPACITY
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
# HOME
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

        plan_text = "🛡 ADMIN"
        usage = f"{active} / ∞"

    elif capacity[
        "plan"
    ] == "vip":

        plan_text = "💎 VIP"
        usage = (
            f"{active} / {limit}"
        )

    else:

        plan_text = "👤 NORMAL"
        usage = (
            f"{active} / {limit}"
        )

    bar = capacity_bar(
        active,
        limit,
    )

    if language == "fa":

        return (
            "🔔 ALIFT SMART ALERTS\n"
            "━━━━━━━━━━━━━━━━\n\n"

            "👁 لازم نیست ۲۴ ساعته بازار رو "
            "نگاه کنی؛ ALIFT برات زیر نظرش می‌گیره.\n\n"

            f"{plan_text}\n"
            f"🔔 آلارم فعال: {usage}\n"
            f"{bar}\n\n"

            "🏦 منبع Crypto Alerts: XT\n\n"

            "💰 Price Above / Below\n"
            "📈 Custom EMA Cross\n"
            "📊 Custom RSI\n"
            "〽️ MACD Cross\n"
            "💧 Custom Volume\n"
            "📏 Custom ATR\n"
            "📐 Custom ATR%"
        )

    if language == "ar":

        return (
            "🔔 ALIFT SMART ALERTS\n"
            "━━━━━━━━━━━━━━━━\n\n"

            f"{plan_text}\n"
            f"Active: {usage}\n"
            f"{bar}\n\n"

            "🏦 Crypto Provider: XT\n\n"
            "💰 Price\n"
            "📈 EMA\n"
            "📊 RSI\n"
            "〽️ MACD\n"
            "💧 Volume\n"
            "📏 ATR\n"
            "📐 ATR%"
        )

    return (
        "🔔 ALIFT SMART ALERTS\n"
        "━━━━━━━━━━━━━━━━\n\n"

        f"{plan_text}\n"
        f"🔔 Active Alerts: {usage}\n"
        f"{bar}\n\n"

        "🏦 Crypto Provider: XT\n\n"

        "💰 Price Above / Below\n"
        "📈 Custom EMA Cross\n"
        "📊 Custom RSI\n"
        "〽️ MACD Cross\n"
        "💧 Custom Volume\n"
        "📏 Custom ATR\n"
        "📐 Custom ATR%"
    )


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
                "💎 VIP",
        },
    }[
        language
    ]

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    labels["new"],
                    callback_data=(
                        "alert_new"
                    ),
                )
            ],

            [
                InlineKeyboardButton(
                    labels["mine"],
                    callback_data=(
                        "alert_list"
                    ),
                )
            ],

            [
                InlineKeyboardButton(
                    labels["guide"],
                    callback_data=(
                        "alert_guide"
                    ),
                ),

                InlineKeyboardButton(
                    labels["test"],
                    callback_data=(
                        "alert_test"
                    ),
                ),
            ],

            [
                InlineKeyboardButton(
                    labels["vip"],
                    callback_data=(
                        "alert_vip"
                    ),
                )
            ],
        ]
    )


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
# LIMIT
# ============================================================

def limit_message(
    language,
    current,
    limit,
    plan,
):

    if language == "fa":

        return (
            "🔒 سقف آلارم‌های حساب تکمیل شده.\n\n"
            f"👤 پلن: {plan.upper()}\n"
            f"🔔 آلارم فعال: {current} / {limit}\n\n"
            "💎 VIP تا 50 آلارم فعال"
        )

    return (
        "🔒 ALERT LIMIT REACHED\n\n"
        f"Plan: {plan.upper()}\n"
        f"Active: {current} / {limit}\n\n"
        "VIP supports up to 50 active alerts."
    )


def limit_keyboard(
    language,
):

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "💎 VIP",
                    callback_data=(
                        "alert_vip"
                    ),
                )
            ],

            [
                InlineKeyboardButton(
                    "📋 Alerts",
                    callback_data=(
                        "alert_list"
                    ),
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
            "📖 ALIFT ALERT GUIDE\n"
            "━━━━━━━━━━━━━━━━\n\n"

            "🔎 جستجوی Crypto\n"
            "نام ارز را وارد کن؛ مثال:\n"
            "PEPE\n"
            "SUI\n"
            "TON\n"
            "BTC\n"
            "یا PEPE/USDT\n\n"

            "نماد قبل از ساخت آلارم روی XT "
            "اعتبارسنجی می‌شود.\n\n"

            "💰 Price\n"
            "قیمت بالا یا پایین عدد دلخواه.\n\n"

            "📈 EMA Cross\n"
            "دو عدد دلخواه بین 2 تا 200.\n"
            "مثال: 7 25\n\n"

            "📊 RSI\n"
            "Period و Level دلخواه.\n"
            "مثال: 14 70\n\n"

            "〽️ MACD\n"
            "Bull / Bear Cross\n\n"

            "💧 Volume\n"
            "ضریب حجم دلخواه.\n\n"

            "📏 ATR / ATR%\n"
            "Period و Threshold دلخواه.\n\n"

            "⚠️ آلارم فقط اطلاع‌رسانی است "
            "و معامله‌ای اجرا نمی‌کند."
        )

    return (
        "📖 ALIFT ALERT GUIDE\n"
        "━━━━━━━━━━━━━━━━\n\n"

        "🔎 Search any supported XT Spot/USDT asset.\n\n"
        "Example: PEPE, SUI, BTC, PEPE/USDT\n\n"

        "Price / EMA / RSI / MACD / "
        "Volume / ATR / ATR% are supported.\n\n"

        "Alerts are informational only."
    )


# ============================================================
# ASSET SELECTION
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
                        f"alert_symbol_{code}"
                    ),
                )
            )

        rows.append(
            row
        )

    rows.append(
        [
            InlineKeyboardButton(
                "🔎 جستجوی رمز ارز",
                callback_data=(
                    "alert_search_crypto"
                ),
            )
        ]
    )

    rows.append(
        [
            InlineKeyboardButton(
                "⬅️ Back",
                callback_data=(
                    "alert_home"
                ),
            )
        ]
    )

    return InlineKeyboardMarkup(
        rows
    )


# ============================================================
# ALERT TYPES
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
                        f"alert_type_{code}_price_above"
                    ),
                ),

                InlineKeyboardButton(
                    "💰 Price Below",
                    callback_data=(
                        f"alert_type_{code}_price_below"
                    ),
                ),
            ],

            [
                InlineKeyboardButton(
                    "📈 EMA Bull Cross",
                    callback_data=(
                        f"alert_type_{code}_ema_bull"
                    ),
                ),

                InlineKeyboardButton(
                    "📉 EMA Bear Cross",
                    callback_data=(
                        f"alert_type_{code}_ema_bear"
                    ),
                ),
            ],

            [
                InlineKeyboardButton(
                    "📊 RSI Above",
                    callback_data=(
                        f"alert_type_{code}_rsi_above"
                    ),
                ),

                InlineKeyboardButton(
                    "📊 RSI Below",
                    callback_data=(
                        f"alert_type_{code}_rsi_below"
                    ),
                ),
            ],

            [
                InlineKeyboardButton(
                    "〽️ MACD Bull",
                    callback_data=(
                        f"alert_type_{code}_macd_bull"
                    ),
                ),

                InlineKeyboardButton(
                    "〽️ MACD Bear",
                    callback_data=(
                        f"alert_type_{code}_macd_bear"
                    ),
                ),
            ],

            [
                InlineKeyboardButton(
                    "💧 Volume Spike",
                    callback_data=(
                        f"alert_type_{code}_volume_spike"
                    ),
                )
            ],

            [
                InlineKeyboardButton(
                    "📏 ATR Above",
                    callback_data=(
                        f"alert_type_{code}_atr_above"
                    ),
                ),

                InlineKeyboardButton(
                    "📏 ATR Below",
                    callback_data=(
                        f"alert_type_{code}_atr_below"
                    ),
                ),
            ],

            [
                InlineKeyboardButton(
                    "📐 ATR% Above",
                    callback_data=(
                        f"alert_type_{code}_atr_percent_above"
                    ),
                ),

                InlineKeyboardButton(
                    "📐 ATR% Below",
                    callback_data=(
                        f"alert_type_{code}_atr_percent_below"
                    ),
                ),
            ],

            [
                InlineKeyboardButton(
                    "⬅️ Asset",
                    callback_data=(
                        "alert_new"
                    ),
                )
            ],
        ]
    )


# ============================================================
# CUSTOM SEARCH SYMBOL TYPES
# ============================================================

def searched_type_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "💰 Price Above",
                    callback_data=(
                        "alert_search_type_price_above"
                    ),
                ),

                InlineKeyboardButton(
                    "💰 Price Below",
                    callback_data=(
                        "alert_search_type_price_below"
                    ),
                ),
            ],

            [
                InlineKeyboardButton(
                    "📈 EMA Bull Cross",
                    callback_data=(
                        "alert_search_type_ema_bull"
                    ),
                ),

                InlineKeyboardButton(
                    "📉 EMA Bear Cross",
                    callback_data=(
                        "alert_search_type_ema_bear"
                    ),
                ),
            ],

            [
                InlineKeyboardButton(
                    "📊 RSI Above",
                    callback_data=(
                        "alert_search_type_rsi_above"
                    ),
                ),

                InlineKeyboardButton(
                    "📊 RSI Below",
                    callback_data=(
                        "alert_search_type_rsi_below"
                    ),
                ),
            ],

            [
                InlineKeyboardButton(
                    "〽️ MACD Bull",
                    callback_data=(
                        "alert_search_type_macd_bull"
                    ),
                ),

                InlineKeyboardButton(
                    "〽️ MACD Bear",
                    callback_data=(
                        "alert_search_type_macd_bear"
                    ),
                ),
            ],

            [
                InlineKeyboardButton(
                    "💧 Volume Spike",
                    callback_data=(
                        "alert_search_type_volume_spike"
                    ),
                )
            ],

            [
                InlineKeyboardButton(
                    "📏 ATR Above",
                    callback_data=(
                        "alert_search_type_atr_above"
                    ),
                ),

                InlineKeyboardButton(
                    "📏 ATR Below",
                    callback_data=(
                        "alert_search_type_atr_below"
                    ),
                ),
            ],

            [
                InlineKeyboardButton(
                    "📐 ATR% Above",
                    callback_data=(
                        "alert_search_type_atr_percent_above"
                    ),
                ),

                InlineKeyboardButton(
                    "📐 ATR% Below",
                    callback_data=(
                        "alert_search_type_atr_percent_below"
                    ),
                ),
            ],

            [
                InlineKeyboardButton(
                    "🔎 جستجوی ارز دیگر",
                    callback_data=(
                        "alert_search_crypto"
                    ),
                )
            ],
        ]
    )


# ============================================================
# TIMEFRAME
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
                        f"alert_tf_{code}_{alert_type}_15m"
                    ),
                ),

                InlineKeyboardButton(
                    "1H",
                    callback_data=(
                        f"alert_tf_{code}_{alert_type}_1h"
                    ),
                ),
            ],

            [
                InlineKeyboardButton(
                    "4H",
                    callback_data=(
                        f"alert_tf_{code}_{alert_type}_4h"
                    ),
                ),

                InlineKeyboardButton(
                    "1D",
                    callback_data=(
                        f"alert_tf_{code}_{alert_type}_1d"
                    ),
                ),
            ],
        ]
    )


def searched_timeframe_keyboard(
    alert_type,
):

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "15M",
                    callback_data=(
                        f"alert_search_tf_{alert_type}_15m"
                    ),
                ),

                InlineKeyboardButton(
                    "1H",
                    callback_data=(
                        f"alert_search_tf_{alert_type}_1h"
                    ),
                ),
            ],

            [
                InlineKeyboardButton(
                    "4H",
                    callback_data=(
                        f"alert_search_tf_{alert_type}_4h"
                    ),
                ),

                InlineKeyboardButton(
                    "1D",
                    callback_data=(
                        f"alert_search_tf_{alert_type}_1d"
                    ),
                ),
            ],
        ]
    )


# ============================================================
# TYPE NAMES
# ============================================================

def item_parameters(
    item,
):

    raw = getattr(
        item,
        "parameters",
        None,
    )

    if not raw:
        return {}

    if isinstance(
        raw,
        dict,
    ):
        return raw

    try:

        value = json.loads(
            raw
        )

        if isinstance(
            value,
            dict,
        ):
            return value

    except Exception:
        pass

    return {}


def alert_type_name(
    value,
    parameters=None,
):

    params = (
        parameters
        or {}
    )

    if value == "price_above":
        return "Price ≥"

    if value == "price_below":
        return "Price ≤"

    if value in {
        "ema_bull",
        "ema_bear",
    }:

        fast = params.get(
            "ema_fast",
            20,
        )

        slow = params.get(
            "ema_slow",
            50,
        )

        direction = (
            "Bull"
            if value
            == "ema_bull"
            else "Bear"
        )

        return (
            f"EMA {fast}/{slow} "
            f"{direction} Cross"
        )

    if value in {
        "rsi_high",
        "rsi_above",
    }:

        period = params.get(
            "rsi_period",
            14,
        )

        level = params.get(
            "value",
            70,
        )

        return (
            f"RSI({period}) ≥ {level}"
        )

    if value in {
        "rsi_low",
        "rsi_below",
    }:

        period = params.get(
            "rsi_period",
            14,
        )

        level = params.get(
            "value",
            30,
        )

        return (
            f"RSI({period}) ≤ {level}"
        )

    if value == "macd_bull":
        return "MACD Bull Cross"

    if value == "macd_bear":
        return "MACD Bear Cross"

    if value == "volume_spike":

        multiplier = params.get(
            "multiplier",
            1.8,
        )

        return (
            f"Volume ≥ {multiplier}x"
        )

    if value == "atr_above":

        period = params.get(
            "atr_period",
            14,
        )

        return (
            f"ATR({period}) Above"
        )

    if value == "atr_below":

        period = params.get(
            "atr_period",
            14,
        )

        return (
            f"ATR({period}) Below"
        )

    if value == "atr_percent_above":

        period = params.get(
            "atr_period",
            14,
        )

        return (
            f"ATR%({period}) Above"
        )

    if value == "atr_percent_below":

        period = params.get(
            "atr_period",
            14,
        )

        return (
            f"ATR%({period}) Below"
        )

    return value


# ============================================================
# CREATE
# ============================================================

def safely_create_alert(
    telegram_id,
    symbol,
    alert_type,
    timeframe,
    target_value=None,
    parameters=None,
):

    try:

        item = create_alert(
            telegram_id=telegram_id,
            symbol=symbol,
            alert_type=alert_type,
            timeframe=timeframe,
            target_value=target_value,
            parameters=parameters,
        )

        return item, None

    except AlertLimitReached as exc:

        return None, exc


# ============================================================
# LIST
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
                        f"{icon} #{item.id} "
                        f"{item.symbol}"
                    ),
                    callback_data=(
                        f"alert_view_{item.id}"
                    ),
                )
            ]
        )

    rows.append(
        [
            InlineKeyboardButton(
                "➕ New Alert",
                callback_data=(
                    "alert_new"
                ),
            )
        ]
    )

    rows.append(
        [
            InlineKeyboardButton(
                "🏠 Alert Home",
                callback_data=(
                    "alert_home"
                ),
            )
        ]
    )

    return InlineKeyboardMarkup(
        rows
    )


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
        or ""
    )

    # --------------------------------------------------------
    # HOME
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # GUIDE
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # TEST
    # --------------------------------------------------------

    if data == "alert_test":

        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "🚨 ALIFT TEST ALERT\n"
                "━━━━━━━━━━━━━━━━\n\n"
                "✅ Notifications are working."
            ),
        )

        return

    # --------------------------------------------------------
    # VIP
    # --------------------------------------------------------

    if data == "alert_vip":

        await query.edit_message_text(
            (
                "💎 ALIFT VIP\n"
                "━━━━━━━━━━━━━━━━\n\n"
                "NORMAL: 5 Active Alerts\n"
                "VIP: 50 Active Alerts\n"
                "ADMIN: Unlimited"
            ),
            reply_markup=(
                alert_home_keyboard(
                    language
                )
            ),
        )

        return

    # --------------------------------------------------------
    # NEW
    # --------------------------------------------------------

    if data == "alert_new":

        capacity = alert_capacity(
            user_id
        )

        if capacity[
            "full"
        ]:

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

        context.user_data.pop(
            "alert_search",
            None,
        )

        context.user_data.pop(
            "awaiting_alert_search",
            None,
        )

        await query.edit_message_text(
            (
                "🪙 SELECT CRYPTO\n"
                "━━━━━━━━━━━━━━━━\n\n"
                "ارزهای سریع یا جستجوی هر ارز "
                "Spot/USDT موجود در XT:"
            ),
            reply_markup=(
                symbol_keyboard()
            ),
        )

        return

    # --------------------------------------------------------
    # SEARCH CRYPTO
    # --------------------------------------------------------

    if data == "alert_search_crypto":

        context.user_data[
            "awaiting_alert_search"
        ] = True

        context.user_data.pop(
            "alert_search",
            None,
        )

        await query.edit_message_text(
            (
                "🔎 SEARCH CRYPTO ON XT\n"
                "━━━━━━━━━━━━━━━━\n\n"

                "نام رمز ارز را بفرست.\n\n"

                "مثال:\n"
                "PEPE\n"
                "SUI\n"
                "TON\n"
                "BTC\n"
                "PEPE/USDT\n\n"

                "🔍 نماد روی XT بررسی می‌شود."
            )
        )

        return

    # --------------------------------------------------------
    # QUICK SYMBOL
    # --------------------------------------------------------

    if data.startswith(
        "alert_symbol_"
    ):

        code = data.replace(
            "alert_symbol_",
            "",
            1,
        )

        if (
            code
            not in SUPPORTED_SYMBOLS
        ):
            return

        await query.edit_message_text(
            (
                f"🔔 {SUPPORTED_SYMBOLS[code]}\n\n"
                "Select Alert Type:"
            ),
            reply_markup=(
                type_keyboard(
                    code
                )
            ),
        )

        return

    # --------------------------------------------------------
    # QUICK TYPE
    # --------------------------------------------------------

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

        for possible_code in (
            SUPPORTED_SYMBOLS
        ):

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

        symbol = (
            SUPPORTED_SYMBOLS[
                code
            ]
        )

        # Custom parameters
        if alert_type in {
            "ema_bull",
            "ema_bear",
            "rsi_above",
            "rsi_below",
            "volume_spike",
            "atr_above",
            "atr_below",
            "atr_percent_above",
            "atr_percent_below",
        }:

            await begin_custom_input(
                query=query,
                context=context,
                symbol=symbol,
                alert_type=alert_type,
                code=code,
                searched=False,
            )

            return

        await query.edit_message_text(
            "⏱ Select Timeframe:",
            reply_markup=(
                timeframe_keyboard(
                    code,
                    alert_type,
                )
            ),
        )

        return

    # --------------------------------------------------------
    # SEARCHED SYMBOL TYPE
    # --------------------------------------------------------

    if data.startswith(
        "alert_search_type_"
    ):

        alert_type = data.replace(
            "alert_search_type_",
            "",
            1,
        )

        search = (
            context.user_data.get(
                "alert_search"
            )
        )

        if not search:
            return

        symbol = search[
            "symbol"
        ]

        if alert_type in {
            "ema_bull",
            "ema_bear",
            "rsi_above",
            "rsi_below",
            "volume_spike",
            "atr_above",
            "atr_below",
            "atr_percent_above",
            "atr_percent_below",
        }:

            await begin_custom_input(
                query=query,
                context=context,
                symbol=symbol,
                alert_type=alert_type,
                searched=True,
            )

            return

        await query.edit_message_text(
            (
                f"🔔 {symbol}\n\n"
                "⏱ Select Timeframe:"
            ),
            reply_markup=(
                searched_timeframe_keyboard(
                    alert_type
                )
            ),
        )

        return

    # --------------------------------------------------------
    # QUICK TIMEFRAME
    # --------------------------------------------------------

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

        for possible_code in (
            SUPPORTED_SYMBOLS
        ):

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

        for possible_tf in (
            SUPPORTED_TIMEFRAMES
        ):

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

        await finish_timeframe(
            query=query,
            context=context,
            user_id=user_id,
            language=language,
            symbol=symbol,
            alert_type=alert_type,
            timeframe=timeframe,
        )

        return

    # --------------------------------------------------------
    # SEARCH TIMEFRAME
    # --------------------------------------------------------

    if data.startswith(
        "alert_search_tf_"
    ):

        payload = data.replace(
            "alert_search_tf_",
            "",
            1,
        )

        timeframe = None
        alert_type = None

        for possible_tf in (
            SUPPORTED_TIMEFRAMES
        ):

            suffix = (
                "_"
                + possible_tf
            )

            if payload.endswith(
                suffix
            ):

                timeframe = (
                    possible_tf
                )

                alert_type = (
                    payload[
                        :-len(suffix)
                    ]
                )

                break

        search = (
            context.user_data.get(
                "alert_search"
            )
        )

        if (
            timeframe is None
            or alert_type is None
            or not search
        ):
            return

        await finish_timeframe(
            query=query,
            context=context,
            user_id=user_id,
            language=language,
            symbol=search[
                "symbol"
            ],
            alert_type=alert_type,
            timeframe=timeframe,
        )

        return

    # --------------------------------------------------------
    # LIST
    # --------------------------------------------------------

    if data == "alert_list":

        items = user_alerts(
            user_id
        )

        capacity = alert_capacity(
            user_id
        )

        lines = [
            "📋 MY ALERTS",
            "━━━━━━━━━━━━━━━━",
            "",
            (
                "Active: {} / {}"
            ).format(
                capacity[
                    "active"
                ],
                capacity[
                    "limit"
                ]
                if capacity[
                    "limit"
                ] is not None
                else "∞",
            ),
            "",
        ]

        if not items:

            lines.append(
                "هنوز آلارمی نساختی."
            )

        for item in items:

            params = (
                item_parameters(
                    item
                )
            )

            lines.append(
                (
                    "{} #{} | {} | {} | {}"
                ).format(
                    "🟢"
                    if item.is_active
                    else "⚫",

                    item.id,
                    item.symbol,

                    alert_type_name(
                        item.alert_type,
                        params,
                    ),

                    item.timeframe,
                )
            )

        await query.edit_message_text(
            "\n".join(
                lines
            ),
            reply_markup=(
                list_keyboard(
                    items
                )
            ),
        )

        return

    # --------------------------------------------------------
    # VIEW
    # --------------------------------------------------------

    if data.startswith(
        "alert_view_"
    ):

        try:

            alert_id = int(
                data.replace(
                    "alert_view_",
                    "",
                    1,
                )
            )

        except ValueError:
            return

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

        params = (
            item_parameters(
                item
            )
        )

        await query.edit_message_text(
            (
                f"🔔 ALERT #{item.id}\n"
                "━━━━━━━━━━━━━━━━\n\n"

                f"Asset: {item.symbol}\n"

                "Type: "
                f"{alert_type_name(item.alert_type, params)}\n"

                f"TF: {item.timeframe}\n"

                "Target: "
                f"{item.target_value if item.target_value is not None else '-'}\n"

                "Status: "
                f"{'🟢 ACTIVE' if item.is_active else '⚫ OFF'}\n"

                f"Triggers: {item.trigger_count}\n\n"

                "🏦 Provider: XT"
            ),
            reply_markup=(
                InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "⏯ Toggle",
                                callback_data=(
                                    f"alert_toggle_{item.id}"
                                ),
                            )
                        ],

                        [
                            InlineKeyboardButton(
                                "🗑 Delete",
                                callback_data=(
                                    f"alert_delete_{item.id}"
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

    # --------------------------------------------------------
    # TOGGLE
    # --------------------------------------------------------

    if data.startswith(
        "alert_toggle_"
    ):

        try:

            alert_id = int(
                data.replace(
                    "alert_toggle_",
                    "",
                    1,
                )
            )

        except ValueError:
            return

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

    # --------------------------------------------------------
    # DELETE
    # --------------------------------------------------------

    if data.startswith(
        "alert_delete_"
    ):

        try:

            alert_id = int(
                data.replace(
                    "alert_delete_",
                    "",
                    1,
                )
            )

        except ValueError:
            return

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
# CUSTOM INPUT START
# ============================================================

async def begin_custom_input(
    query,
    context,
    symbol,
    alert_type,
    code=None,
    searched=False,
):

    if alert_type in {
        "ema_bull",
        "ema_bear",
    }:

        stage = "ema"

        message = (
            "📈 CUSTOM EMA\n"
            "━━━━━━━━━━━━━━━━\n\n"
            f"Asset: {symbol}\n\n"

            "دو عدد EMA را بفرست.\n"
            "مثال:\n7 25\n\n"

            "محدوده هر عدد: 2 تا 200"
        )

    elif alert_type in {
        "rsi_above",
        "rsi_below",
    }:

        stage = "rsi"

        message = (
            "📊 CUSTOM RSI\n"
            "━━━━━━━━━━━━━━━━\n\n"
            f"Asset: {symbol}\n\n"

            "Period و Level را بفرست.\n"
            "مثال:\n14 70"
        )

    elif alert_type in {
        "atr_above",
        "atr_below",
        "atr_percent_above",
        "atr_percent_below",
    }:

        stage = "atr"

        example = (
            "14 2.5"
            if "percent"
            in alert_type
            else "14 500"
        )

        message = (
            "📏 CUSTOM ATR\n"
            "━━━━━━━━━━━━━━━━\n\n"
            f"Asset: {symbol}\n\n"

            "Period و Threshold را بفرست.\n"
            f"مثال:\n{example}"
        )

    elif (
        alert_type
        == "volume_spike"
    ):

        stage = "volume"

        message = (
            "💧 CUSTOM VOLUME\n"
            "━━━━━━━━━━━━━━━━\n\n"
            f"Asset: {symbol}\n\n"

            "ضریب حجم را بفرست.\n"
            "مثال:\n2.5"
        )

    else:
        return

    context.user_data[
        "awaiting_alert_custom"
    ] = {
        "stage":
            stage,

        "symbol":
            symbol,

        "alert_type":
            alert_type,

        "code":
            code,

        "searched":
            searched,
    }

    await query.edit_message_text(
        message
    )


# ============================================================
# FINISH TIMEFRAME
# ============================================================

async def finish_timeframe(
    query,
    context,
    user_id,
    language,
    symbol,
    alert_type,
    timeframe,
):

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

                f"Asset: {symbol}\n"
                f"TF: {timeframe}\n\n"

                "قیمت هدف را بفرست."
            )
        )

        return

    prepared = (
        context.user_data.get(
            "prepared_alert"
        )
    )

    parameters = None

    if (
        prepared
        and prepared.get(
            "symbol"
        ) == symbol
        and prepared.get(
            "alert_type"
        ) == alert_type
    ):

        parameters = (
            prepared.get(
                "parameters"
            )
        )

    item, error = (
        safely_create_alert(
            telegram_id=user_id,
            symbol=symbol,
            alert_type=alert_type,
            timeframe=timeframe,
            parameters=parameters,
        )
    )

    context.user_data.pop(
        "prepared_alert",
        None,
    )

    if error:

        await query.edit_message_text(
            limit_message(
                language,
                error.current,
                error.limit,
                error.plan,
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

            f"ID: #{item.id}\n"
            f"Asset: {item.symbol}\n"

            "Type: "
            f"{alert_type_name(item.alert_type, item_parameters(item))}\n"

            f"TF: {item.timeframe}\n"
            "🏦 Provider: XT\n"
            "Status: 🟢 ACTIVE"
        ),
        reply_markup=(
            alert_home_keyboard(
                language
            )
        ),
    )


# ============================================================
# TEXT INPUT
# ============================================================

async def alert_price_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if (
        update.message is None
        or update.effective_user
        is None
    ):
        return False

    user_id = (
        update.effective_user.id
    )

    text = (
        update.message.text
        or ""
    ).strip()

    # --------------------------------------------------------
    # SEARCH CRYPTO
    # --------------------------------------------------------

    if context.user_data.get(
        "awaiting_alert_search"
    ):

        if len(text) > 30:

            await update.message.reply_text(
                "❌ نام رمز ارز معتبر نیست."
            )

            return True

        await update.message.reply_text(
            "🔍 در حال بررسی نماد روی XT..."
        )

        try:

            symbol = (
                await validate_crypto_symbol(
                    text
                )
            )

        except Exception:

            await update.message.reply_text(
                (
                    "❌ ارتباط با XT یا بررسی نماد "
                    "با خطا مواجه شد.\n"
                    "چند لحظه بعد دوباره تلاش کن."
                )
            )

            return True

        if not symbol:

            try:

                results = (
                    await search_crypto_symbols(
                        text,
                        limit=8,
                    )
                )

            except Exception:

                results = []

            if results:

                suggestions = (
                    "\n".join(
                        f"• {item}"
                        for item
                        in results
                    )
                )

                await update.message.reply_text(
                    (
                        "❌ نماد دقیق پیدا نشد.\n\n"
                        "نتایج نزدیک روی XT:\n"
                        f"{suggestions}\n\n"
                        "یکی از نمادها را دوباره ارسال کن."
                    )
                )

            else:

                await update.message.reply_text(
                    (
                        "❌ این نماد در بازار Spot/USDT "
                        "صرافی XT پیدا نشد.\n\n"
                        "مثال: BTC یا PEPE/USDT"
                    )
                )

            return True

        context.user_data.pop(
            "awaiting_alert_search",
            None,
        )

        context.user_data[
            "alert_search"
        ] = {
            "symbol":
                symbol
        }

        await update.message.reply_text(
            (
                "✅ رمز ارز پیدا شد\n"
                "━━━━━━━━━━━━━━━━\n\n"

                f"🪙 {symbol}\n"
                "🏦 XT Spot\n\n"

                "نوع آلارم را انتخاب کن:"
            ),
            reply_markup=(
                searched_type_keyboard()
            ),
        )

        return True

    # --------------------------------------------------------
    # CUSTOM INDICATOR
    # --------------------------------------------------------

    custom = (
        context.user_data.get(
            "awaiting_alert_custom"
        )
    )

    if custom:

        value_text = (
            text.replace(
                ",",
                ".",
            )
        )

        stage = (
            custom[
                "stage"
            ]
        )

        try:

            if stage == "ema":

                parts = (
                    value_text.split()
                )

                if len(parts) != 2:
                    raise ValueError

                first = int(
                    parts[0]
                )

                second = int(
                    parts[1]
                )

                if not (
                    2 <= first <= 200
                    and
                    2 <= second <= 200
                ):
                    raise ValueError

                if first == second:
                    raise ValueError

                fast = min(
                    first,
                    second,
                )

                slow = max(
                    first,
                    second,
                )

                parameters = {
                    "ema_fast":
                        fast,

                    "ema_slow":
                        slow,
                }

                confirmation = (
                    f"EMA {fast}/{slow}"
                )

            elif stage == "rsi":

                parts = (
                    value_text.split()
                )

                if len(parts) != 2:
                    raise ValueError

                period = int(
                    parts[0]
                )

                level = float(
                    parts[1]
                )

                if not (
                    2 <= period <= 200
                ):
                    raise ValueError

                if not (
                    0 < level < 100
                ):
                    raise ValueError

                parameters = {
                    "rsi_period":
                        period,

                    "value":
                        level,
                }

                confirmation = (
                    f"RSI({period}) {level:g}"
                )

            elif stage == "atr":

                parts = (
                    value_text.split()
                )

                if len(parts) != 2:
                    raise ValueError

                period = int(
                    parts[0]
                )

                threshold = float(
                    parts[1]
                )

                if not (
                    2 <= period <= 200
                ):
                    raise ValueError

                if threshold <= 0:
                    raise ValueError

                parameters = {
                    "atr_period":
                        period,

                    "value":
                        threshold,
                }

                confirmation = (
                    f"ATR({period}) "
                    f"{threshold:g}"
                )

            elif stage == "volume":

                multiplier = float(
                    value_text
                )

                if not (
                    1 < multiplier <= 100
                ):
                    raise ValueError

                parameters = {
                    "volume_period":
                        20,

                    "multiplier":
                        multiplier,
                }

                confirmation = (
                    f"Volume {multiplier:g}x"
                )

            else:
                return False

        except ValueError:

            await update.message.reply_text(
                (
                    "❌ مقدار معتبر نیست.\n\n"

                    "EMA: 7 25\n"
                    "RSI: 14 70\n"
                    "ATR: 14 2.5\n"
                    "Volume: 2.5"
                )
            )

            return True

        context.user_data[
            "prepared_alert"
        ] = {
            "symbol":
                custom[
                    "symbol"
                ],

            "alert_type":
                custom[
                    "alert_type"
                ],

            "parameters":
                parameters,
        }

        context.user_data.pop(
            "awaiting_alert_custom",
            None,
        )

        if custom.get(
            "searched"
        ):

            keyboard = (
                searched_timeframe_keyboard(
                    custom[
                        "alert_type"
                    ]
                )
            )

        else:

            keyboard = (
                timeframe_keyboard(
                    custom[
                        "code"
                    ],
                    custom[
                        "alert_type"
                    ],
                )
            )

        await update.message.reply_text(
            (
                "✅ تنظیمات ثبت شد\n\n"
                f"{confirmation}\n\n"
                "⏱ Timeframe را انتخاب کن:"
            ),
            reply_markup=keyboard,
        )

        return True

    # --------------------------------------------------------
    # PRICE
    # --------------------------------------------------------

    pending = (
        context.user_data.get(
            "awaiting_alert_price"
        )
    )

    if not pending:
        return False

    value_text = (
        text
        .replace(
            ",",
            "",
        )
    )

    try:

        value = float(
            value_text
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
        user_id
    )

    item, error = (
        safely_create_alert(
            telegram_id=user_id,
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

    if error:

        await update.message.reply_text(
            limit_message(
                language,
                error.current,
                error.limit,
                error.plan,
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

            f"ID: #{item.id}\n"
            f"Asset: {item.symbol}\n"
            f"Target: {item.target_value:,.8f}\n"
            f"TF: {item.timeframe}\n"
            "🏦 Provider: XT\n"
            "Status: 🟢 ACTIVE"
        ),
        reply_markup=(
            alert_home_keyboard(
                language
            )
        ),
    )

    return True
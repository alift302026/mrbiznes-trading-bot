import json

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)

from telegram.ext import ContextTypes

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

from app.services.user_service import get_user


# ============================================================
# LANGUAGE
# ============================================================

def user_language(telegram_id):
    user = get_user(telegram_id)

    if user and user.language in {"fa", "en", "ar"}:
        return user.language

    return "en"


# ============================================================
# CAPACITY
# ============================================================

def capacity_bar(current, limit):
    if limit is None:
        return "██████████ ∞"

    if limit <= 0:
        return "░░░░░░░░░░"

    percentage = min(1, current / limit)
    filled = round(percentage * 10)

    return (
        "█" * filled
        + "░" * (10 - filled)
    )


def alert_home_text(telegram_id):
    language = user_language(telegram_id)
    capacity = alert_capacity(telegram_id)

    active = capacity["active"]
    limit = capacity["limit"]

    if capacity["is_admin"]:
        plan_text = "🛡 ADMIN"
        usage = f"{active} / ∞"

    elif capacity["plan"] == "vip":
        plan_text = "💎 VIP"
        usage = f"{active} / {limit}"

    else:
        plan_text = "👤 NORMAL"
        usage = f"{active} / {limit}"

    bar = capacity_bar(active, limit)

    if language == "fa":
        return (
            "🔔 ALIFT SMART ALERTS\n"
            "━━━━━━━━━━━━━━━━\n\n"
            "👁 لازم نیست ۲۴ ساعته بازار رو نگاه کنی؛ "
            "ALIFT برات زیر نظرش می‌گیره.\n\n"
            f"{plan_text}\n"
            f"🔔 آلارم فعال: {usage}\n"
            f"{bar}\n\n"
            "💰 Price Above / Below\n"
            "📈 EMA Custom Cross (2 - 200)\n"
            "📊 Custom RSI\n"
            "〽️ MACD Cross\n"
            "💧 Custom Volume Spike\n"
            "📏 Custom ATR\n"
            "📐 Custom ATR%\n"
            "🌍 Session Alerts"
        )

    if language == "ar":
        return (
            "🔔 ALIFT SMART ALERTS\n"
            "━━━━━━━━━━━━━━━━\n\n"
            f"{plan_text}\n"
            f"Active: {usage}\n"
            f"{bar}\n\n"
            "💰 Price\n"
            "📈 Custom EMA Cross\n"
            "📊 Custom RSI\n"
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
        "💰 Price Above / Below\n"
        "📈 Custom EMA Cross (2 - 200)\n"
        "📊 Custom RSI\n"
        "〽️ MACD Cross\n"
        "💧 Custom Volume Spike\n"
        "📏 Custom ATR\n"
        "📐 Custom ATR%\n"
        "🌍 Session Alerts"
    )


def alert_home_keyboard(language):
    labels = {
        "fa": {
            "new": "➕ ساخت آلارم جدید",
            "mine": "📋 آلارم‌های من",
            "guide": "📖 راهنمای آلارم‌ها",
            "test": "🧪 تست اعلان",
            "vip": "💎 ارتقا به VIP",
        },
        "en": {
            "new": "➕ Create Alert",
            "mine": "📋 My Alerts",
            "guide": "📖 Alert Guide",
            "test": "🧪 Test Notification",
            "vip": "💎 Upgrade to VIP",
        },
        "ar": {
            "new": "➕ إنشاء تنبيه",
            "mine": "📋 تنبيهاتي",
            "guide": "📖 دليل التنبيهات",
            "test": "🧪 اختبار الإشعار",
            "vip": "💎 VIP",
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


async def alerts_home(update, context):
    telegram_id = update.effective_user.id
    language = user_language(telegram_id)

    await update.message.reply_text(
        alert_home_text(telegram_id),
        reply_markup=alert_home_keyboard(language),
    )


# ============================================================
# LIMIT
# ============================================================

def limit_message(language, current, limit, plan):
    if language == "fa":
        return (
            "🔒 سقف آلارم‌های حساب تکمیل شده.\n\n"
            f"پلن: {plan.upper()}\n"
            f"آلارم فعال: {current} / {limit}\n\n"
            "💎 VIP تا 50 آلارم فعال"
        )

    return (
        "🔒 ALERT LIMIT REACHED\n\n"
        f"Plan: {plan.upper()}\n"
        f"Active: {current} / {limit}\n\n"
        "VIP supports up to 50 active alerts."
    )


def limit_keyboard(language):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "💎 VIP",
                    callback_data="alert_vip",
                )
            ],
            [
                InlineKeyboardButton(
                    "📋 Alerts",
                    callback_data="alert_list",
                )
            ],
        ]
    )


# ============================================================
# GUIDE
# ============================================================

def guide_text(language):
    if language == "fa":
        return (
            "📖 ALIFT ALERT GUIDE\n"
            "━━━━━━━━━━━━━━━━\n\n"
            "💰 Price\n"
            "قیمت بالاتر یا پایین‌تر از عدد دلخواه.\n\n"
            "📈 EMA CROSS\n"
            "دو EMA دلخواه از 2 تا 200.\n"
            "مثال: 7 25 یا 50 200\n\n"
            "📊 RSI\n"
            "Period و سطح دلخواه.\n"
            "مثال: 14 70\n\n"
            "〽️ MACD\n"
            "کراس صعودی یا نزولی.\n\n"
            "💧 Volume\n"
            "ضریب حجم نسبت به میانگین.\n\n"
            "📏 ATR\n"
            "Period و مقدار ATR دلخواه.\n\n"
            "📐 ATR%\n"
            "ATR به درصد قیمت.\n\n"
            "⚠️ آلارم صرفاً اطلاع‌رسانی است "
            "و معامله‌ای اجرا نمی‌کند."
        )

    return (
        "📖 ALIFT ALERT GUIDE\n"
        "━━━━━━━━━━━━━━━━\n\n"
        "Price: custom above/below target.\n"
        "EMA: custom periods from 2 to 200.\n"
        "RSI: custom period and threshold.\n"
        "MACD: bullish/bearish cross.\n"
        "Volume: custom volume multiplier.\n"
        "ATR: custom period and value.\n"
        "ATR%: ATR as percentage of price.\n\n"
        "Alerts are informational only."
    )


# ============================================================
# SYMBOLS
# ============================================================

def symbol_keyboard():
    items = list(SUPPORTED_SYMBOLS.items())
    rows = []

    for index in range(0, len(items), 2):
        row = []

        for code, symbol in items[index:index + 2]:
            row.append(
                InlineKeyboardButton(
                    symbol,
                    callback_data=f"alert_symbol_{code}",
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

    return InlineKeyboardMarkup(rows)


# ============================================================
# TYPES
# ============================================================

def type_keyboard(code):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "💰 Price Above",
                    callback_data=f"alert_type_{code}_price_above",
                ),
                InlineKeyboardButton(
                    "💰 Price Below",
                    callback_data=f"alert_type_{code}_price_below",
                ),
            ],
            [
                InlineKeyboardButton(
                    "📈 EMA Bull Cross",
                    callback_data=f"alert_type_{code}_ema_bull",
                ),
                InlineKeyboardButton(
                    "📉 EMA Bear Cross",
                    callback_data=f"alert_type_{code}_ema_bear",
                ),
            ],
            [
                InlineKeyboardButton(
                    "📊 RSI Above",
                    callback_data=f"alert_type_{code}_rsi_above",
                ),
                InlineKeyboardButton(
                    "📊 RSI Below",
                    callback_data=f"alert_type_{code}_rsi_below",
                ),
            ],
            [
                InlineKeyboardButton(
                    "〽️ MACD Bull",
                    callback_data=f"alert_type_{code}_macd_bull",
                ),
                InlineKeyboardButton(
                    "〽️ MACD Bear",
                    callback_data=f"alert_type_{code}_macd_bear",
                ),
            ],
            [
                InlineKeyboardButton(
                    "💧 Volume Spike",
                    callback_data=f"alert_type_{code}_volume_spike",
                )
            ],
            [
                InlineKeyboardButton(
                    "📏 ATR Above",
                    callback_data=f"alert_type_{code}_atr_above",
                ),
                InlineKeyboardButton(
                    "📏 ATR Below",
                    callback_data=f"alert_type_{code}_atr_below",
                ),
            ],
            [
                InlineKeyboardButton(
                    "📐 ATR% Above",
                    callback_data=f"alert_type_{code}_atr_percent_above",
                ),
                InlineKeyboardButton(
                    "📐 ATR% Below",
                    callback_data=f"alert_type_{code}_atr_percent_below",
                ),
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
# TIMEFRAME
# ============================================================

def timeframe_keyboard(code, alert_type):
    rows = []

    for left, right in [
        ("15m", "1h"),
        ("4h", "1d"),
    ]:
        rows.append(
            [
                InlineKeyboardButton(
                    left.upper(),
                    callback_data=f"alert_tf_{code}_{alert_type}_{left}",
                ),
                InlineKeyboardButton(
                    right.upper(),
                    callback_data=f"alert_tf_{code}_{alert_type}_{right}",
                ),
            ]
        )

    return InlineKeyboardMarkup(rows)


# ============================================================
# NAMES
# ============================================================

def alert_type_name(value, parameters=None):
    params = parameters or {}

    if value == "price_above":
        return "Price ≥"

    if value == "price_below":
        return "Price ≤"

    if value in {"ema_bull", "ema_bear"}:
        fast = params.get("ema_fast", params.get("fast", 20))
        slow = params.get("ema_slow", params.get("slow", 50))
        direction = "Bull" if value == "ema_bull" else "Bear"
        return f"EMA {fast}/{slow} {direction} Cross"

    if value in {"rsi_high", "rsi_above"}:
        period = params.get("rsi_period", params.get("period", 14))
        level = params.get("value", 70)
        return f"RSI({period}) ≥ {level}"

    if value in {"rsi_low", "rsi_below"}:
        period = params.get("rsi_period", params.get("period", 14))
        level = params.get("value", 30)
        return f"RSI({period}) ≤ {level}"

    if value == "macd_bull":
        return "MACD Bull Cross"

    if value == "macd_bear":
        return "MACD Bear Cross"

    if value == "volume_spike":
        multiplier = params.get("multiplier", 1.8)
        return f"Volume ≥ {multiplier}x"

    if value == "atr_above":
        period = params.get("atr_period", params.get("period", 14))
        return f"ATR({period}) Above"

    if value == "atr_below":
        period = params.get("atr_period", params.get("period", 14))
        return f"ATR({period}) Below"

    if value == "atr_percent_above":
        period = params.get("atr_period", params.get("period", 14))
        return f"ATR%({period}) Above"

    if value == "atr_percent_below":
        period = params.get("atr_period", params.get("period", 14))
        return f"ATR%({period}) Below"

    return value


def item_parameters(item):
    raw = getattr(item, "parameters", None)

    if not raw:
        return {}

    if isinstance(raw, dict):
        return raw

    try:
        result = json.loads(raw)

        if isinstance(result, dict):
            return result
    except Exception:
        pass

    return {}


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


async def created_message(
    query,
    item,
    language,
):
    params = item_parameters(item)

    await query.edit_message_text(
        (
            "✅ ALERT CREATED\n"
            "━━━━━━━━━━━━━━━━\n\n"
            f"ID: #{item.id}\n"
            f"Asset: {item.symbol}\n"
            f"Type: {alert_type_name(item.alert_type, params)}\n"
            f"TF: {item.timeframe}\n"
            "Status: 🟢 ACTIVE"
        ),
        reply_markup=alert_home_keyboard(language),
    )


# ============================================================
# LIST
# ============================================================

def list_keyboard(items):
    rows = []

    for item in items:
        icon = "🟢" if item.is_active else "⚫"

        rows.append(
            [
                InlineKeyboardButton(
                    f"{icon} #{item.id} {item.symbol}",
                    callback_data=f"alert_view_{item.id}",
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

    return InlineKeyboardMarkup(rows)


# ============================================================
# CALLBACK
# ============================================================

async def alert_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    if query is None:
        return

    await query.answer()

    user_id = query.from_user.id
    language = user_language(user_id)
    data = query.data or ""

    if data == "alert_home":
        await query.edit_message_text(
            alert_home_text(user_id),
            reply_markup=alert_home_keyboard(language),
        )
        return

    if data == "alert_guide":
        await query.edit_message_text(
            guide_text(language),
            reply_markup=alert_home_keyboard(language),
        )
        return

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

    if data == "alert_vip":
        await query.edit_message_text(
            (
                "💎 ALIFT VIP\n"
                "━━━━━━━━━━━━━━━━\n\n"
                "NORMAL: 5 Active Alerts\n"
                "VIP: 50 Active Alerts\n"
                "ADMIN: Unlimited"
            ),
            reply_markup=alert_home_keyboard(language),
        )
        return

    if data == "alert_new":
        capacity = alert_capacity(user_id)

        if capacity["full"]:
            await query.edit_message_text(
                limit_message(
                    language,
                    capacity["active"],
                    capacity["limit"],
                    capacity["plan"],
                ),
                reply_markup=limit_keyboard(language),
            )
            return

        await query.edit_message_text(
            "🪙 Select Asset",
            reply_markup=symbol_keyboard(),
        )
        return

    if data.startswith("alert_symbol_"):
        code = data.replace("alert_symbol_", "", 1)

        if code not in SUPPORTED_SYMBOLS:
            return

        await query.edit_message_text(
            f"🔔 {SUPPORTED_SYMBOLS[code]}\n\nSelect Alert Type:",
            reply_markup=type_keyboard(code),
        )
        return

    if data.startswith("alert_type_"):
        payload = data.replace("alert_type_", "", 1)

        code = None
        alert_type = None

        for possible_code in SUPPORTED_SYMBOLS:
            prefix = possible_code + "_"

            if payload.startswith(prefix):
                code = possible_code
                alert_type = payload[len(prefix):]
                break

        if code is None or alert_type is None:
            return

        symbol = SUPPORTED_SYMBOLS[code]

        # EMA custom input BEFORE timeframe
        if alert_type in {"ema_bull", "ema_bear"}:
            context.user_data["awaiting_alert_custom"] = {
                "stage": "ema",
                "code": code,
                "symbol": symbol,
                "alert_type": alert_type,
            }

            await query.edit_message_text(
                (
                    "📈 CUSTOM EMA CROSS\n"
                    "━━━━━━━━━━━━━━━━\n\n"
                    "دو عدد EMA را بفرست.\n\n"
                    "مثال:\n"
                    "7 25\n\n"
                    "✅ هر عدد بین 2 تا 200 مجاز است.\n"
                    "عدد کوچک‌تر Fast و عدد بزرگ‌تر Slow می‌شود."
                )
            )
            return

        # RSI custom input
        if alert_type in {"rsi_above", "rsi_below"}:
            context.user_data["awaiting_alert_custom"] = {
                "stage": "rsi",
                "code": code,
                "symbol": symbol,
                "alert_type": alert_type,
            }

            await query.edit_message_text(
                (
                    "📊 CUSTOM RSI\n"
                    "━━━━━━━━━━━━━━━━\n\n"
                    "Period و Level را بفرست.\n\n"
                    "مثال:\n"
                    "14 70\n\n"
                    "Period: 2 تا 200\n"
                    "Level: بیشتر از 0 و کمتر از 100"
                )
            )
            return

        # ATR
        if alert_type in {
            "atr_above",
            "atr_below",
            "atr_percent_above",
            "atr_percent_below",
        }:
            context.user_data["awaiting_alert_custom"] = {
                "stage": "atr",
                "code": code,
                "symbol": symbol,
                "alert_type": alert_type,
            }

            example = (
                "14 2.5"
                if "percent" in alert_type
                else "14 500"
            )

            await query.edit_message_text(
                (
                    "📏 CUSTOM ATR\n"
                    "━━━━━━━━━━━━━━━━\n\n"
                    "Period و مقدار را بفرست.\n\n"
                    f"مثال:\n{example}\n\n"
                    "Period: 2 تا 200"
                )
            )
            return

        # Volume
        if alert_type == "volume_spike":
            context.user_data["awaiting_alert_custom"] = {
                "stage": "volume",
                "code": code,
                "symbol": symbol,
                "alert_type": alert_type,
            }

            await query.edit_message_text(
                (
                    "💧 VOLUME SPIKE\n"
                    "━━━━━━━━━━━━━━━━\n\n"
                    "ضریب حجم را بفرست.\n\n"
                    "مثال:\n"
                    "2.5\n\n"
                    "یعنی حجم فعلی حداقل 2.5 برابر "
                    "میانگین 20 کندل باشد."
                )
            )
            return

        # Price and MACD go to timeframe
        await query.edit_message_text(
            "⏱ Select Timeframe:",
            reply_markup=timeframe_keyboard(
                code,
                alert_type,
            ),
        )
        return

    if data.startswith("alert_tf_"):
        payload = data.replace("alert_tf_", "", 1)

        code = None
        remainder = None

        for possible_code in SUPPORTED_SYMBOLS:
            prefix = possible_code + "_"

            if payload.startswith(prefix):
                code = possible_code
                remainder = payload[len(prefix):]
                break

        if code is None or remainder is None:
            return

        timeframe = None
        alert_type = None

        for possible_tf in SUPPORTED_TIMEFRAMES:
            suffix = "_" + possible_tf

            if remainder.endswith(suffix):
                timeframe = possible_tf
                alert_type = remainder[:-len(suffix)]
                break

        if timeframe is None or alert_type is None:
            return

        symbol = SUPPORTED_SYMBOLS[code]

        # Price requires value
        if alert_type in {"price_above", "price_below"}:
            context.user_data["awaiting_alert_price"] = {
                "symbol": symbol,
                "alert_type": alert_type,
                "timeframe": timeframe,
            }

            await query.edit_message_text(
                (
                    "💰 PRICE ALERT\n"
                    "━━━━━━━━━━━━━━━━\n\n"
                    f"Asset: {symbol}\n"
                    f"TF: {timeframe}\n\n"
                    "قیمت هدف را بفرست.\n"
                    "مثال: 65000"
                )
            )
            return

        # Custom indicator already has params
        pending = context.user_data.get("prepared_alert")

        if (
            pending
            and pending.get("symbol") == symbol
            and pending.get("alert_type") == alert_type
        ):
            item, error = safely_create_alert(
                telegram_id=user_id,
                symbol=symbol,
                alert_type=alert_type,
                timeframe=timeframe,
                target_value=pending.get("target_value"),
                parameters=pending.get("parameters"),
            )

            context.user_data.pop("prepared_alert", None)

        else:
            item, error = safely_create_alert(
                telegram_id=user_id,
                symbol=symbol,
                alert_type=alert_type,
                timeframe=timeframe,
            )

        if error:
            await query.edit_message_text(
                limit_message(
                    language,
                    error.current,
                    error.limit,
                    error.plan,
                ),
                reply_markup=limit_keyboard(language),
            )
            return

        await created_message(
            query,
            item,
            language,
        )
        return

    if data == "alert_list":
        items = user_alerts(user_id)
        capacity = alert_capacity(user_id)

        lines = [
            "📋 MY ALERTS",
            "━━━━━━━━━━━━━━━━",
            "",
            "Active: {} / {}".format(
                capacity["active"],
                capacity["limit"]
                if capacity["limit"] is not None
                else "∞",
            ),
            "",
        ]

        if not items:
            lines.append("هنوز آلارمی نساختی.")

        for item in items:
            params = item_parameters(item)

            lines.append(
                "{} #{} | {} | {} | {}".format(
                    "🟢" if item.is_active else "⚫",
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
            "\n".join(lines),
            reply_markup=list_keyboard(items),
        )
        return

    if data.startswith("alert_view_"):
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
                for alert in user_alerts(user_id)
                if alert.id == alert_id
            ),
            None,
        )

        if item is None:
            return

        params = item_parameters(item)

        await query.edit_message_text(
            (
                f"🔔 ALERT #{item.id}\n"
                "━━━━━━━━━━━━━━━━\n\n"
                f"Asset: {item.symbol}\n"
                f"Type: {alert_type_name(item.alert_type, params)}\n"
                f"TF: {item.timeframe}\n"
                f"Target: {item.target_value if item.target_value is not None else '-'}\n"
                f"Status: {'🟢 ACTIVE' if item.is_active else '⚫ OFF'}\n"
                f"Triggers: {item.trigger_count}"
            ),
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "⏯ Toggle",
                            callback_data=f"alert_toggle_{item.id}",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "🗑 Delete",
                            callback_data=f"alert_delete_{item.id}",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "⬅️ My Alerts",
                            callback_data="alert_list",
                        )
                    ],
                ]
            ),
        )
        return

    if data.startswith("alert_toggle_"):
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
                reply_markup=limit_keyboard(language),
            )
            return

        await query.edit_message_text(
            "✅ Alert status changed.",
            reply_markup=alert_home_keyboard(language),
        )
        return

    if data.startswith("alert_delete_"):
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
            reply_markup=alert_home_keyboard(language),
        )


# ============================================================
# TEXT INPUT
# ============================================================

async def alert_price_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if update.message is None:
        return False

    user_id = update.effective_user.id

    # --------------------------------------------------------
    # CUSTOM INDICATOR INPUT
    # --------------------------------------------------------

    custom = context.user_data.get(
        "awaiting_alert_custom"
    )

    if custom:
        text = (
            update.message.text
            or ""
        ).strip().replace(",", ".")

        stage = custom["stage"]

        try:
            if stage == "ema":
                parts = text.split()

                if len(parts) != 2:
                    raise ValueError

                first = int(parts[0])
                second = int(parts[1])

                if not (
                    2 <= first <= 200
                    and 2 <= second <= 200
                ):
                    raise ValueError

                if first == second:
                    raise ValueError

                fast = min(first, second)
                slow = max(first, second)

                parameters = {
                    "ema_fast": fast,
                    "ema_slow": slow,
                }

                confirmation = (
                    f"EMA {fast} / {slow}"
                )

            elif stage == "rsi":
                parts = text.split()

                if len(parts) != 2:
                    raise ValueError

                period = int(parts[0])
                value = float(parts[1])

                if not 2 <= period <= 200:
                    raise ValueError

                if not 0 < value < 100:
                    raise ValueError

                parameters = {
                    "rsi_period": period,
                    "value": value,
                }

                confirmation = (
                    f"RSI({period}) / {value:g}"
                )

            elif stage == "atr":
                parts = text.split()

                if len(parts) != 2:
                    raise ValueError

                period = int(parts[0])
                value = float(parts[1])

                if not 2 <= period <= 200:
                    raise ValueError

                if value <= 0:
                    raise ValueError

                parameters = {
                    "atr_period": period,
                    "value": value,
                }

                confirmation = (
                    f"ATR({period}) / {value:g}"
                )

            elif stage == "volume":
                multiplier = float(text)

                if not 1 < multiplier <= 100:
                    raise ValueError

                parameters = {
                    "volume_period": 20,
                    "multiplier": multiplier,
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
                    "EMA مثال: 7 25 (هر عدد 2 تا 200)\n"
                    "RSI مثال: 14 70\n"
                    "ATR مثال: 14 2.5\n"
                    "Volume مثال: 2.5"
                )
            )
            return True

        context.user_data[
            "prepared_alert"
        ] = {
            "symbol": custom["symbol"],
            "alert_type": custom["alert_type"],
            "parameters": parameters,
        }

        context.user_data.pop(
            "awaiting_alert_custom",
            None,
        )

        await update.message.reply_text(
            (
                "✅ تنظیمات ثبت شد\n\n"
                f"{confirmation}\n\n"
                "⏱ حالا Timeframe را انتخاب کن:"
            ),
            reply_markup=timeframe_keyboard(
                custom["code"],
                custom["alert_type"],
            ),
        )

        return True

    # --------------------------------------------------------
    # PRICE INPUT
    # --------------------------------------------------------

    pending = context.user_data.get(
        "awaiting_alert_price"
    )

    if not pending:
        return False

    text = (
        update.message.text
        or ""
    ).strip().replace(
        ",",
        "",
    )

    try:
        value = float(text)

        if value <= 0:
            raise ValueError

    except ValueError:
        await update.message.reply_text(
            "❌ قیمت معتبر بفرست. مثال: 65000"
        )
        return True

    language = user_language(user_id)

    item, error = safely_create_alert(
        telegram_id=user_id,
        symbol=pending["symbol"],
        alert_type=pending["alert_type"],
        timeframe=pending["timeframe"],
        target_value=value,
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
            reply_markup=limit_keyboard(language),
        )
        return True

    await update.message.reply_text(
        (
            "✅ PRICE ALERT CREATED\n"
            "━━━━━━━━━━━━━━━━\n\n"
            f"ID: #{item.id}\n"
            f"Asset: {item.symbol}\n"
            f"Type: {alert_type_name(item.alert_type)}\n"
            f"Target: {item.target_value:,.8f}\n"
            f"TF: {item.timeframe}\n"
            "Status: 🟢 ACTIVE"
        ),
        reply_markup=alert_home_keyboard(
            language
        ),
    )

    return True
import json

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)

from telegram.ext import (
    ContextTypes,
)

from app.bot.alert_asset_handlers import (
    market_keyboard,
    market_text,
)

from app.engines.alerts.market_alert_engine import (
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
        and user.language in {
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
        + "░" * (10 - filled)
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

        plan = "🛡 ADMIN"
        usage = f"{active} / ∞"

    elif capacity[
        "plan"
    ] == "vip":

        plan = "💎 VIP"
        usage = (
            f"{active} / {limit}"
        )

    else:

        plan = "👤 NORMAL"
        usage = (
            f"{active} / {limit}"
        )

    bar = capacity_bar(
        active,
        limit,
    )

    if language == "fa":

        return (
            "🔔 MrBiznes SMART ALERTS\n"
            "━━━━━━━━━━━━━━━━\n\n"

            f"{plan}\n"
            f"🔔 آلارم فعال: {usage}\n"
            f"{bar}\n\n"

            "🪙 Crypto → XT\n"
            "💱 Forex → Twelve Data\n\n"

            "💰 Price\n"
            "📈 EMA Custom\n"
            "📊 RSI Custom\n"
            "〽️ MACD\n"
            "💧 Volume (Crypto)\n"
            "📏 ATR\n"
            "📐 ATR%"
        )

    return (
        "🔔 MrBiznes SMART ALERTS\n"
        "━━━━━━━━━━━━━━━━\n\n"

        f"{plan}\n"
        f"Active Alerts: {usage}\n"
        f"{bar}\n\n"

        "🪙 Crypto → XT\n"
        "💱 Forex → Twelve Data\n\n"

        "Price / EMA / RSI / MACD / ATR / ATR%"
    )


def alert_home_keyboard(
    language,
):

    if language == "fa":

        new = "➕ ساخت آلارم جدید"
        mine = "📋 آلارم‌های من"
        guide = "📖 راهنما"
        test = "🧪 تست اعلان"
        vip = "💎 ارتقا VIP"

    else:

        new = "➕ Create Alert"
        mine = "📋 My Alerts"
        guide = "📖 Guide"
        test = "🧪 Test"
        vip = "💎 VIP"

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    new,
                    callback_data="alert_new",
                )
            ],
            [
                InlineKeyboardButton(
                    mine,
                    callback_data="alert_list",
                )
            ],
            [
                InlineKeyboardButton(
                    guide,
                    callback_data="alert_guide",
                ),
                InlineKeyboardButton(
                    test,
                    callback_data="alert_test",
                ),
            ],
            [
                InlineKeyboardButton(
                    vip,
                    callback_data="alert_vip",
                )
            ],
        ]
    )


async def alerts_home(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user_id = (
        update.effective_user.id
    )

    language = user_language(
        user_id
    )

    clear_alert_flow(
        context
    )

    await update.message.reply_text(
        alert_home_text(
            user_id
        ),
        reply_markup=(
            alert_home_keyboard(
                language
            )
        ),
    )


# ============================================================
# GUIDE
# ============================================================

def guide_text():

    return (
        "📖 MrBiznes ALERT GUIDE\n"
        "━━━━━━━━━━━━━━━━\n\n"

        "🪙 Crypto\n"
        "داده از XT دریافت می‌شود.\n"
        "کاربر Normal ماهانه ۳ جستجوی موفق دارد.\n"
        "VIP و Admin نامحدود هستند.\n\n"

        "💱 Forex\n"
        "داده از Twelve Data دریافت می‌شود.\n\n"

        "📈 EMA\n"
        "دو عدد دلخواه از 2 تا 200.\n"
        "مثال: 7 25 یا 50 200\n\n"

        "📊 RSI\n"
        "Period و Level دلخواه.\n"
        "مثال: 14 70\n\n"

        "📏 ATR / ATR%\n"
        "Period و Threshold دلخواه.\n\n"

        "💧 Volume\n"
        "فقط برای Crypto فعال است.\n\n"

        "⚠️ آلارم‌ها صرفاً اطلاع‌رسانی هستند "
        "و معامله‌ای اجرا نمی‌کنند."
    )


# ============================================================
# PARAMETERS
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
    alert_type,
    parameters=None,
):

    params = parameters or {}

    if alert_type == "price_above":
        return "Price ≥"

    if alert_type == "price_below":
        return "Price ≤"

    if alert_type in {
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
            if alert_type
            == "ema_bull"
            else "Bear"
        )

        return (
            f"EMA {fast}/{slow} "
            f"{direction} Cross"
        )

    if alert_type == "rsi_above":

        return (
            "RSI({}) ≥ {}".format(
                params.get(
                    "rsi_period",
                    14,
                ),
                params.get(
                    "value",
                    70,
                ),
            )
        )

    if alert_type == "rsi_below":

        return (
            "RSI({}) ≤ {}".format(
                params.get(
                    "rsi_period",
                    14,
                ),
                params.get(
                    "value",
                    30,
                ),
            )
        )

    if alert_type == "macd_bull":
        return "MACD Bull Cross"

    if alert_type == "macd_bear":
        return "MACD Bear Cross"

    if alert_type == "volume_spike":

        return (
            "Volume ≥ {}x".format(
                params.get(
                    "multiplier",
                    1.8,
                )
            )
        )

    if alert_type == "atr_above":

        return (
            "ATR({}) Above".format(
                params.get(
                    "atr_period",
                    14,
                )
            )
        )

    if alert_type == "atr_below":

        return (
            "ATR({}) Below".format(
                params.get(
                    "atr_period",
                    14,
                )
            )
        )

    if (
        alert_type
        == "atr_percent_above"
    ):

        return (
            "ATR%({}) Above".format(
                params.get(
                    "atr_period",
                    14,
                )
            )
        )

    if (
        alert_type
        == "atr_percent_below"
    ):

        return (
            "ATR%({}) Below".format(
                params.get(
                    "atr_period",
                    14,
                )
            )
        )

    return alert_type


# ============================================================
# TIMEFRAME
# ============================================================

def external_timeframe_keyboard(
    alert_type,
):

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "15M",
                    callback_data=(
                        f"alert_exttf_{alert_type}_15m"
                    ),
                ),
                InlineKeyboardButton(
                    "1H",
                    callback_data=(
                        f"alert_exttf_{alert_type}_1h"
                    ),
                ),
            ],
            [
                InlineKeyboardButton(
                    "4H",
                    callback_data=(
                        f"alert_exttf_{alert_type}_4h"
                    ),
                ),
                InlineKeyboardButton(
                    "1D",
                    callback_data=(
                        f"alert_exttf_{alert_type}_1d"
                    ),
                ),
            ],
        ]
    )


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


def limit_text(
    error,
):

    return (
        "🔒 ALERT LIMIT REACHED\n"
        "━━━━━━━━━━━━━━━━\n\n"

        f"Plan: {error.plan.upper()}\n"
        f"Active: {error.current} / {error.limit}\n\n"

        "💎 برای آلارم بیشتر حساب VIP لازم است."
    )


# ============================================================
# MY ALERTS
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

        clear_alert_flow(
            context
        )

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
    # NEW ALERT -> MARKET SEARCH
    # --------------------------------------------------------

    if data == "alert_new":

        capacity = alert_capacity(
            user_id
        )

        if capacity[
            "full"
        ]:

            await query.edit_message_text(
                (
                    "🔒 سقف آلارم فعال تکمیل شده.\n\n"
                    "برای ایجاد آلارم جدید، یکی از "
                    "آلارم‌ها را خاموش/حذف کن یا VIP بگیر."
                ),
                reply_markup=(
                    alert_home_keyboard(
                        language
                    )
                ),
            )

            return

        clear_alert_flow(
            context
        )

        await query.edit_message_text(
            market_text(),
            reply_markup=(
                market_keyboard()
            ),
        )

        return

    # --------------------------------------------------------
    # GUIDE
    # --------------------------------------------------------

    if data == "alert_guide":

        await query.edit_message_text(
            guide_text(),
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
                "🚨 MrBiznes TEST ALERT\n"
                "━━━━━━━━━━━━━━━━\n\n"
                "✅ سیستم اعلان فعال است."
            ),
        )

        await query.answer(
            "✅ Test alert sent",
            show_alert=True,
        )

        return

    # --------------------------------------------------------
    # VIP
    # --------------------------------------------------------

    if data == "alert_vip":

        await query.edit_message_text(
            (
                "💎 MrBiznes VIP\n"
                "━━━━━━━━━━━━━━━━\n\n"

                "👤 NORMAL\n"
                "🔔 5 Active Alerts\n"
                "🔎 3 Crypto Searches / Month\n\n"

                "💎 VIP\n"
                "🔔 50 Active Alerts\n"
                "🔎 Unlimited Search\n\n"

                "🛡 ADMIN\n"
                "Unlimited"
            ),
            reply_markup=(
                alert_home_keyboard(
                    language
                )
            ),
        )

        return

    # --------------------------------------------------------
    # EXTERNAL ASSET ALERT TYPE
    # --------------------------------------------------------

    if data.startswith(
        "alert_ext_"
    ):

        alert_type = data.replace(
            "alert_ext_",
            "",
            1,
        )

        selected = (
            context.user_data.get(
                "external_alert_asset"
            )
        )

        if not selected:

            await query.edit_message_text(
                (
                    "❌ Asset selection expired.\n"
                    "دوباره ارز را انتخاب کن."
                ),
                reply_markup=(
                    market_keyboard()
                ),
            )

            return

        market = selected[
            "market"
        ]

        symbol = selected[
            "symbol"
        ]

        valid_types = {
            "price_above",
            "price_below",
            "ema_bull",
            "ema_bear",
            "rsi_above",
            "rsi_below",
            "macd_bull",
            "macd_bear",
            "volume_spike",
            "atr_above",
            "atr_below",
            "atr_percent_above",
            "atr_percent_below",
        }

        if alert_type not in valid_types:
            return

        # Forex has no centralized spot volume.
        if (
            market == "forex"
            and alert_type
            == "volume_spike"
        ):

            await query.answer(
                "Volume Alert برای Spot Forex فعال نیست.",
                show_alert=True,
            )

            return

        # Custom indicators require input first.
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
                market=market,
                alert_type=alert_type,
            )

            return

        # Price/MACD -> timeframe immediately.
        await query.edit_message_text(
            (
                "⏱ SELECT TIMEFRAME\n"
                "━━━━━━━━━━━━━━━━\n\n"
                f"{symbol}\n"
                f"{alert_type_name(alert_type)}"
            ),
            reply_markup=(
                external_timeframe_keyboard(
                    alert_type
                )
            ),
        )

        return

    # --------------------------------------------------------
    # EXTERNAL TIMEFRAME
    # --------------------------------------------------------

    if data.startswith(
        "alert_exttf_"
    ):

        payload = data.replace(
            "alert_exttf_",
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

        if (
            timeframe is None
            or alert_type is None
        ):
            return

        selected = (
            context.user_data.get(
                "external_alert_asset"
            )
        )

        if not selected:

            await query.edit_message_text(
                "❌ Asset selection expired."
            )

            return

        symbol = selected[
            "symbol"
        ]

        market = selected[
            "market"
        ]

        # PRICE requires target.
        if alert_type in {
            "price_above",
            "price_below",
        }:

            context.user_data[
                "awaiting_alert_price"
            ] = {
                "symbol":
                    symbol,

                "market":
                    market,

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
                    f"Market: {market.upper()}\n"
                    f"TF: {timeframe}\n\n"

                    "قیمت هدف را ارسال کن."
                )
            )

            return

        prepared = (
            context.user_data.get(
                "prepared_alert"
            )
        )

        parameters = {}

        if (
            prepared
            and prepared.get(
                "symbol"
            ) == symbol
            and prepared.get(
                "alert_type"
            ) == alert_type
        ):

            parameters.update(
                prepared.get(
                    "parameters"
                )
                or {}
            )

        if market == "forex":

            parameters[
                "market"
            ] = "forex"

        else:

            parameters[
                "market"
            ] = "crypto"

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
                limit_text(
                    error
                ),
                reply_markup=(
                    alert_home_keyboard(
                        language
                    )
                ),
            )

            return

        provider = (
            "Twelve Data"
            if market == "forex"
            else "XT"
        )

        await query.edit_message_text(
            (
                "✅ ALERT CREATED\n"
                "━━━━━━━━━━━━━━━━\n\n"

                f"ID: #{item.id}\n"
                f"Asset: {item.symbol}\n"
                f"Market: {market.upper()}\n"
                f"Provider: {provider}\n"
                "Type: "
                f"{alert_type_name(item.alert_type, item_parameters(item))}\n"
                f"TF: {item.timeframe}\n\n"

                "🟢 ACTIVE"
            ),
            reply_markup=(
                alert_home_keyboard(
                    language
                )
            ),
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

        limit = (
            capacity[
                "limit"
            ]
            if capacity[
                "limit"
            ] is not None
            else "∞"
        )

        lines = [
            "📋 MY ALERTS",
            "━━━━━━━━━━━━━━━━",
            "",
            (
                f"Active: "
                f"{capacity['active']} / "
                f"{limit}"
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

            market = params.get(
                "market",
                "crypto",
            )

            market_icon = (
                "💱"
                if market == "forex"
                else "🪙"
            )

            status = (
                "🟢"
                if item.is_active
                else "⚫"
            )

            lines.append(
                (
                    f"{status} "
                    f"{market_icon} "
                    f"#{item.id} | "
                    f"{item.symbol} | "
                    f"{alert_type_name(item.alert_type, params)} | "
                    f"{item.timeframe}"
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

        market = params.get(
            "market",
            "crypto",
        )

        provider = (
            "Twelve Data"
            if market == "forex"
            else "XT"
        )

        await query.edit_message_text(
            (
                f"🔔 ALERT #{item.id}\n"
                "━━━━━━━━━━━━━━━━\n\n"

                f"Asset: {item.symbol}\n"
                f"Market: {market.upper()}\n"
                f"Provider: {provider}\n"
                "Type: "
                f"{alert_type_name(item.alert_type, params)}\n"
                f"TF: {item.timeframe}\n"
                "Target: "
                f"{item.target_value if item.target_value is not None else '-'}\n"
                "Status: "
                f"{'🟢 ACTIVE' if item.is_active else '⚫ OFF'}\n"
                f"Triggers: {item.trigger_count}"
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
                                callback_data="alert_list",
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
                limit_text(
                    exc
                ),
                reply_markup=(
                    alert_home_keyboard(
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
# CUSTOM INDICATOR INPUT
# ============================================================

async def begin_custom_input(
    query,
    context,
    symbol,
    market,
    alert_type,
):

    if alert_type in {
        "ema_bull",
        "ema_bear",
    }:

        stage = "ema"

        text = (
            "📈 CUSTOM EMA\n"
            "━━━━━━━━━━━━━━━━\n\n"
            f"Asset: {symbol}\n\n"

            "دو عدد EMA را ارسال کن.\n"
            "مثال: 7 25\n\n"

            "حداقل: 2\n"
            "حداکثر: 200\n"
            "دو عدد نباید برابر باشند."
        )

    elif alert_type in {
        "rsi_above",
        "rsi_below",
    }:

        stage = "rsi"

        text = (
            "📊 CUSTOM RSI\n"
            "━━━━━━━━━━━━━━━━\n\n"
            f"Asset: {symbol}\n\n"

            "Period و Level را ارسال کن.\n"
            "مثال: 14 70\n\n"

            "Period: 2 تا 200\n"
            "Level: بین 0 و 100"
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
            else "14 0.005"
        )

        text = (
            "📏 CUSTOM ATR\n"
            "━━━━━━━━━━━━━━━━\n\n"
            f"Asset: {symbol}\n\n"

            "Period و Threshold را ارسال کن.\n"
            f"مثال: {example}\n\n"

            "Period: 2 تا 200"
        )

    elif alert_type == "volume_spike":

        stage = "volume"

        text = (
            "💧 VOLUME SPIKE\n"
            "━━━━━━━━━━━━━━━━\n\n"
            f"Asset: {symbol}\n\n"

            "ضریب حجم را ارسال کن.\n"
            "مثال: 2.5"
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

        "market":
            market,

        "alert_type":
            alert_type,
    }

    await query.edit_message_text(
        text
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
        or update.effective_user is None
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
    # CUSTOM INDICATOR
    # --------------------------------------------------------

    custom = (
        context.user_data.get(
            "awaiting_alert_custom"
        )
    )

    if custom:

        normalized = (
            text.replace(
                ",",
                ".",
            )
        )

        stage = custom[
            "stage"
        ]

        try:

            # EMA
            if stage == "ema":

                parts = (
                    normalized.split()
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

            # RSI
            elif stage == "rsi":

                parts = (
                    normalized.split()
                )

                if len(parts) != 2:
                    raise ValueError

                period = int(
                    parts[0]
                )

                value = float(
                    parts[1]
                )

                if not (
                    2 <= period <= 200
                ):
                    raise ValueError

                if not (
                    0 < value < 100
                ):
                    raise ValueError

                parameters = {
                    "rsi_period":
                        period,

                    "value":
                        value,
                }

                confirmation = (
                    f"RSI({period}) "
                    f"{value:g}"
                )

            # ATR
            elif stage == "atr":

                parts = (
                    normalized.split()
                )

                if len(parts) != 2:
                    raise ValueError

                period = int(
                    parts[0]
                )

                value = float(
                    parts[1]
                )

                if not (
                    2 <= period <= 200
                ):
                    raise ValueError

                if value <= 0:
                    raise ValueError

                parameters = {
                    "atr_period":
                        period,

                    "value":
                        value,
                }

                confirmation = (
                    f"ATR({period}) "
                    f"{value:g}"
                )

            # VOLUME
            elif stage == "volume":

                multiplier = float(
                    normalized
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
                    f"Volume "
                    f"{multiplier:g}x"
                )

            else:
                return False

        except ValueError:

            await update.message.reply_text(
                (
                    "❌ مقدار معتبر نیست.\n\n"

                    "EMA → 7 25\n"
                    "RSI → 14 70\n"
                    "ATR → 14 2.5\n"
                    "Volume → 2.5"
                )
            )

            return True

        market = custom[
            "market"
        ]

        parameters[
            "market"
        ] = market

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

        await update.message.reply_text(
            (
                "✅ تنظیمات ثبت شد\n"
                "━━━━━━━━━━━━━━━━\n\n"

                f"{confirmation}\n\n"
                "⏱ Timeframe را انتخاب کن:"
            ),
            reply_markup=(
                external_timeframe_keyboard(
                    custom[
                        "alert_type"
                    ]
                )
            ),
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

    normalized = (
        text.replace(
            ",",
            "",
        )
    )

    try:

        value = float(
            normalized
        )

        if value <= 0:
            raise ValueError

    except ValueError:

        await update.message.reply_text(
            (
                "❌ قیمت معتبر ارسال کن.\n"
                "مثال: 65000 یا 1.15"
            )
        )

        return True

    market = pending[
        "market"
    ]

    parameters = {
        "market":
            market,
    }

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
            parameters=parameters,
        )
    )

    context.user_data.pop(
        "awaiting_alert_price",
        None,
    )

    language = user_language(
        user_id
    )

    if error:

        await update.message.reply_text(
            limit_text(
                error
            ),
            reply_markup=(
                alert_home_keyboard(
                    language
                )
            ),
        )

        return True

    provider = (
        "Twelve Data"
        if market == "forex"
        else "XT"
    )

    await update.message.reply_text(
        (
            "✅ PRICE ALERT CREATED\n"
            "━━━━━━━━━━━━━━━━\n\n"

            f"ID: #{item.id}\n"
            f"Asset: {item.symbol}\n"
            f"Market: {market.upper()}\n"
            f"Provider: {provider}\n"
            f"Target: {item.target_value}\n"
            f"TF: {item.timeframe}\n\n"

            "🟢 ACTIVE"
        ),
        reply_markup=(
            alert_home_keyboard(
                language
            )
        ),
    )

    return True


# ============================================================
# CLEAR FLOW
# ============================================================

def clear_alert_flow(
    context,
):

    for key in [
        "awaiting_alert_price",
        "awaiting_alert_custom",
        "prepared_alert",
        "external_alert_asset",
        "selected_asset",
        "asset_input",
    ]:

        context.user_data.pop(
            key,
            None,
        )
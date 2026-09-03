from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)

from telegram.ext import (
    ContextTypes,
)

from app.services.asset_search_service import (
    SearchLimitReached,
    search_crypto,
)

from app.services.forex_search_service import (
    popular_forex_pairs,
    search_forex,
)

from app.services.search_limit_service import (
    crypto_search_capacity,
)


# ============================================================
# MARKET SELECT
# ============================================================

def market_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🪙 Crypto",
                    callback_data="asset_crypto",
                ),

                InlineKeyboardButton(
                    "💱 Forex",
                    callback_data="asset_forex",
                ),
            ],

            [
                InlineKeyboardButton(
                    "⬅️ Alerts",
                    callback_data="alert_home",
                )
            ],
        ]
    )


def market_text():

    return (
        "🔎 MrBiznes ASSET SEARCH\n"
        "━━━━━━━━━━━━━━━━\n\n"

        "بازار موردنظر را انتخاب کن.\n\n"

        "🪙 Crypto\n"
        "Provider: XT\n\n"

        "💱 Forex\n"
        "Provider: Twelve Data"
    )


# ============================================================
# CRYPTO
# ============================================================

def crypto_text(
    telegram_id,
):

    capacity = crypto_search_capacity(
        telegram_id
    )

    if capacity[
        "unlimited"
    ]:

        quota = (
            "∞ Unlimited"
        )

    else:

        quota = (
            f"{capacity['used']} / "
            f"{capacity['limit']}\n"
            f"باقی‌مانده: {capacity['remaining']}"
        )

    return (
        "🪙 CRYPTO SEARCH\n"
        "━━━━━━━━━━━━━━━━\n\n"

        "🏦 Provider: XT\n\n"

        f"🔎 سهمیه جستجو:\n{quota}\n\n"

        "نام رمز ارز را ارسال کن.\n\n"

        "مثال:\n"
        "BTC\n"
        "PEPE\n"
        "SUI\n"
        "TON\n"
        "PEPE/USDT"
    )


# ============================================================
# FOREX
# ============================================================

def forex_keyboard():

    pairs = (
        popular_forex_pairs()
    )

    rows = []

    for index in range(
        0,
        min(
            len(pairs),
            10,
        ),
        2,
    ):

        row = []

        for pair in (
            pairs[
                index:
                index + 2
            ]
        ):

            callback_symbol = (
                pair.replace(
                    "/",
                    "",
                )
            )

            row.append(
                InlineKeyboardButton(
                    pair,
                    callback_data=(
                        f"asset_fxpair_{callback_symbol}"
                    ),
                )
            )

        rows.append(
            row
        )

    rows.append(
        [
            InlineKeyboardButton(
                "🔎 جستجوی جفت ارز",
                callback_data="asset_forex_search",
            )
        ]
    )

    rows.append(
        [
            InlineKeyboardButton(
                "⬅️ انتخاب بازار",
                callback_data="asset_home",
            )
        ]
    )

    return InlineKeyboardMarkup(
        rows
    )


# ============================================================
# CALLBACK
# ============================================================

async def asset_callback(
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

    data = (
        query.data
        or ""
    )

    # HOME

    if data == "asset_home":

        clear_asset_input(
            context
        )

        await query.edit_message_text(
            market_text(),
            reply_markup=(
                market_keyboard()
            ),
        )

        return

    # CRYPTO

    if data == "asset_crypto":

        capacity = (
            crypto_search_capacity(
                user_id
            )
        )

        if not capacity[
            "allowed"
        ]:

            await query.edit_message_text(
                (
                    "🔒 سهمیه جستجوی ماهانه تکمیل شده\n"
                    "━━━━━━━━━━━━━━━━\n\n"

                    f"🔎 استفاده: {capacity['used']} / "
                    f"{capacity['limit']}\n\n"

                    "💎 برای جستجوی نامحدود "
                    "اشتراک VIP فعال کن."
                ),
                reply_markup=(
                    InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    "💎 VIP",
                                    callback_data="alert_vip",
                                )
                            ],

                            [
                                InlineKeyboardButton(
                                    "⬅️ بازگشت",
                                    callback_data="asset_home",
                                )
                            ],
                        ]
                    )
                ),
            )

            return

        clear_asset_input(
            context
        )

        context.user_data[
            "asset_input"
        ] = {
            "mode":
                "crypto",
        }

        await query.edit_message_text(
            crypto_text(
                user_id
            )
        )

        return

    # FOREX

    if data == "asset_forex":

        clear_asset_input(
            context
        )

        await query.edit_message_text(
            (
                "💱 FOREX ALERTS\n"
                "━━━━━━━━━━━━━━━━\n\n"

                "📡 Provider: Twelve Data\n\n"

                "یک جفت ارز انتخاب کن یا "
                "نماد دلخواه را جستجو کن."
            ),
            reply_markup=(
                forex_keyboard()
            ),
        )

        return

    # POPULAR FOREX

    if data.startswith(
        "asset_fxpair_"
    ):

        symbol_raw = (
            data.replace(
                "asset_fxpair_",
                "",
                1,
            )
        )

        result = await search_forex(
            symbol_raw
        )

        if not result[
            "found"
        ]:

            await query.answer(
                "نماد فارکس در دسترس نیست.",
                show_alert=True,
            )

            return

        await store_selected_asset(
            context,
            market="forex",
            symbol=result[
                "symbol"
            ],
        )

        await show_selected_asset(
            query,
            context,
        )

        return

    # FOREX SEARCH

    if data == "asset_forex_search":

        clear_asset_input(
            context
        )

        context.user_data[
            "asset_input"
        ] = {
            "mode":
                "forex",
        }

        await query.edit_message_text(
            (
                "🔎 FOREX SEARCH\n"
                "━━━━━━━━━━━━━━━━\n\n"

                "نماد جفت ارز را ارسال کن.\n\n"

                "مثال:\n"
                "EURUSD\n"
                "GBPJPY\n"
                "AUD/USD\n"
                "USD/CHF"
            )
        )

        return

    # SELECTED ASSET -> ALERT SYSTEM

    if data == "asset_use":

        selected = (
            context.user_data.get(
                "selected_asset"
            )
        )

        if not selected:
            return

        market = selected[
            "market"
        ]

        symbol = selected[
            "symbol"
        ]

        context.user_data[
            "external_alert_asset"
        ] = {
            "market":
                market,

            "symbol":
                symbol,
        }

        # alert_handlers.py will consume this.
        if market == "forex":

            keyboard = (
                forex_alert_types_keyboard()
            )

        else:

            keyboard = (
                crypto_alert_types_keyboard()
            )

        await query.edit_message_text(
            (
                "🔔 CREATE ALERT\n"
                "━━━━━━━━━━━━━━━━\n\n"

                f"Asset: {symbol}\n"
                f"Market: {market.upper()}\n\n"

                "نوع آلارم را انتخاب کن:"
            ),
            reply_markup=keyboard,
        )

        return


# ============================================================
# TEXT SEARCH
# ============================================================

MENU_BUTTON_TEXTS = {
    "📊 بازارها",
    "📡 سیگنال‌ها",
    "🔔 آلارم‌ها",
    "🧠 PLT تحلیل چارت",
    "🌍 سشن‌های بازار",
    "📓 ژورنال معاملاتی",
    "🧠 روانشناسی ترید",
    "💎 VIP و پرداخت",
    "🎁 رفرال و امتیاز",
    "📈 عملکرد ماهانه",
    "🏦 صرافی‌های ما",
    "🎧 پشتیبانی",
    "🤝 درباره ما",
    "👤 حساب من",
    "🛡 مدیریت",
}


async def asset_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    if (
        update.message is None
        or update.effective_user is None
    ):
        return False

    pending = (
        context.user_data.get(
            "asset_input"
        )
    )

    if not pending:
        return False

    text = (
        update.message.text
        or ""
    ).strip()

    if not text:
        return True

    if text in MENU_BUTTON_TEXTS or text.startswith("/") or text in {"انصراف", "لغو", "بازگشت"}:
        clear_asset_input(context)
        if text in {"انصراف", "لغو", "بازگشت"}:
            await update.message.reply_text("جستجو لغو شد.")
            return True
        return False

    user_id = (
        update.effective_user.id
    )

    # CRYPTO SEARCH

    if pending[
        "mode"
    ] == "crypto":

        try:

            result = await search_crypto(
                user_id,
                text,
            )

        except SearchLimitReached:

            clear_asset_input(
                context
            )

            await update.message.reply_text(
                (
                    "🔒 سهمیه ۳ جستجوی ماهانه "
                    "شما تکمیل شده است.\n\n"

                    "💎 VIP = جستجوی نامحدود"
                )
            )

            return True

        if not result[
            "found"
        ]:

            suggestions = (
                result.get(
                    "suggestions"
                )
                or []
            )

            if suggestions:

                lines = [
                    "❌ نماد دقیق پیدا نشد.",
                    "",
                    "نتایج نزدیک:",
                ]

                for item in suggestions:

                    lines.append(
                        f"• {item}"
                    )

                lines.append(
                    "\nیکی را دوباره ارسال کن."
                )

                await update.message.reply_text(
                    "\n".join(
                        lines
                    )
                )

            else:

                await update.message.reply_text(
                    (
                        "❌ رمز ارز در XT Spot/USDT "
                        "پیدا نشد."
                    )
                )

            # Failed search does NOT consume quota.
            return True

        clear_asset_input(
            context
        )

        await store_selected_asset(
            context,
            market="crypto",
            symbol=result[
                "symbol"
            ],
        )

        capacity = result[
            "capacity"
        ]

        if capacity[
            "unlimited"
        ]:

            usage = "∞"

        else:

            usage = (
                f"{capacity['used']} / "
                f"{capacity['limit']}"
            )

        await update.message.reply_text(
            (
                "✅ CRYPTO FOUND\n"
                "━━━━━━━━━━━━━━━━\n\n"

                f"🪙 {result['symbol']}\n"
                "🏦 XT Spot\n\n"

                f"🔎 Monthly Search: {usage}"
            ),
            reply_markup=(
                selected_asset_keyboard()
            ),
        )

        return True

    # FOREX SEARCH

    if pending[
        "mode"
    ] == "forex":

        result = await search_forex(
            text
        )

        if not result[
            "found"
        ]:

            await update.message.reply_text(
                (
                    "❌ جفت ارز معتبر پیدا نشد.\n\n"
                    "مثال: EUR/USD یا GBPJPY"
                )
            )

            return True

        clear_asset_input(
            context
        )

        await store_selected_asset(
            context,
            market="forex",
            symbol=result[
                "symbol"
            ],
        )

        await update.message.reply_text(
            (
                "✅ FOREX FOUND\n"
                "━━━━━━━━━━━━━━━━\n\n"

                f"💱 {result['symbol']}\n"
                "📡 Twelve Data"
            ),
            reply_markup=(
                selected_asset_keyboard()
            ),
        )

        return True

    return False


# ============================================================
# SELECTED ASSET
# ============================================================

async def store_selected_asset(
    context,
    market,
    symbol,
):

    context.user_data[
        "selected_asset"
    ] = {
        "market":
            market,

        "symbol":
            symbol,
    }


def selected_asset_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🔔 ساخت آلارم",
                    callback_data="asset_use",
                )
            ],

            [
                InlineKeyboardButton(
                    "🔎 انتخاب ارز دیگر",
                    callback_data="asset_home",
                )
            ],
        ]
    )


async def show_selected_asset(
    query,
    context,
):

    selected = (
        context.user_data.get(
            "selected_asset"
        )
    )

    if not selected:
        return

    await query.edit_message_text(
        (
            "✅ ASSET SELECTED\n"
            "━━━━━━━━━━━━━━━━\n\n"

            f"Symbol: {selected['symbol']}\n"
            f"Market: {selected['market'].upper()}"
        ),
        reply_markup=(
            selected_asset_keyboard()
        ),
    )


# ============================================================
# ALERT TYPE KEYBOARDS
# ============================================================

def crypto_alert_types_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "💰 Price Above",
                    callback_data="alert_ext_price_above",
                ),
                InlineKeyboardButton(
                    "💰 Price Below",
                    callback_data="alert_ext_price_below",
                ),
            ],

            [
                InlineKeyboardButton(
                    "📈 EMA Bull",
                    callback_data="alert_ext_ema_bull",
                ),
                InlineKeyboardButton(
                    "📉 EMA Bear",
                    callback_data="alert_ext_ema_bear",
                ),
            ],

            [
                InlineKeyboardButton(
                    "📊 RSI Above",
                    callback_data="alert_ext_rsi_above",
                ),
                InlineKeyboardButton(
                    "📊 RSI Below",
                    callback_data="alert_ext_rsi_below",
                ),
            ],

            [
                InlineKeyboardButton(
                    "〽️ MACD Bull",
                    callback_data="alert_ext_macd_bull",
                ),
                InlineKeyboardButton(
                    "〽️ MACD Bear",
                    callback_data="alert_ext_macd_bear",
                ),
            ],

            [
                InlineKeyboardButton(
                    "💧 Volume",
                    callback_data="alert_ext_volume_spike",
                )
            ],

            [
                InlineKeyboardButton(
                    "📏 ATR Above",
                    callback_data="alert_ext_atr_above",
                ),
                InlineKeyboardButton(
                    "📏 ATR Below",
                    callback_data="alert_ext_atr_below",
                ),
            ],

            [
                InlineKeyboardButton(
                    "📐 ATR% Above",
                    callback_data="alert_ext_atr_percent_above",
                ),
                InlineKeyboardButton(
                    "📐 ATR% Below",
                    callback_data="alert_ext_atr_percent_below",
                ),
            ],
        ]
    )


def forex_alert_types_keyboard():

    # No Volume Spike for spot Forex.
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "💰 Price Above",
                    callback_data="alert_ext_price_above",
                ),
                InlineKeyboardButton(
                    "💰 Price Below",
                    callback_data="alert_ext_price_below",
                ),
            ],

            [
                InlineKeyboardButton(
                    "📈 EMA Bull",
                    callback_data="alert_ext_ema_bull",
                ),
                InlineKeyboardButton(
                    "📉 EMA Bear",
                    callback_data="alert_ext_ema_bear",
                ),
            ],

            [
                InlineKeyboardButton(
                    "📊 RSI Above",
                    callback_data="alert_ext_rsi_above",
                ),
                InlineKeyboardButton(
                    "📊 RSI Below",
                    callback_data="alert_ext_rsi_below",
                ),
            ],

            [
                InlineKeyboardButton(
                    "〽️ MACD Bull",
                    callback_data="alert_ext_macd_bull",
                ),
                InlineKeyboardButton(
                    "〽️ MACD Bear",
                    callback_data="alert_ext_macd_bear",
                ),
            ],

            [
                InlineKeyboardButton(
                    "📏 ATR Above",
                    callback_data="alert_ext_atr_above",
                ),
                InlineKeyboardButton(
                    "📏 ATR Below",
                    callback_data="alert_ext_atr_below",
                ),
            ],

            [
                InlineKeyboardButton(
                    "📐 ATR% Above",
                    callback_data="alert_ext_atr_percent_above",
                ),
                InlineKeyboardButton(
                    "📐 ATR% Below",
                    callback_data="alert_ext_atr_percent_below",
                ),
            ],
        ]
    )


# ============================================================
# CLEAR
# ============================================================

def clear_asset_input(
    context,
):

    context.user_data.pop(
        "asset_input",
        None,
    )
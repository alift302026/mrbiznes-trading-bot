from pathlib import Path

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)

from telegram.ext import (
    ContextTypes,
)


# ============================================================
# PATHS
# ============================================================

ROOT_DIR = (
    Path(__file__)
    .resolve()
    .parents[2]
)

ASSETS_DIR = (
    ROOT_DIR
    / "assets"
)


# ============================================================
# EXCHANGES
# ============================================================

EXCHANGES = {
    "xt": {
        "name":
            "XT",

        "icon":
            "🟢",

        "code":
            "LYR54K",

        "url":
            "https://www.xt.com/ref/LYR54K",

        "image":
            ASSETS_DIR
            / "xt_referral.png",

        "description":
            (
                "دسترسی به بازارهای متنوع "
                "رمزارزی و ابزارهای معاملاتی."
            ),
    },

    "bitunix": {
        "name":
            "Bitunix",

        "icon":
            "🔵",

        "code":
            "EIrZDA",

        "url":
            (
                "https://www.bitunix.com/register"
                "?inviteCode=EIrZDA&t_act=-1"
            ),

        "image":
            ASSETS_DIR
            / "bitunix_referral.png",

        "description":
            (
                "پلتفرم معاملات رمزارزی با "
                "امکانات Spot و Derivatives."
            ),
    },

    "lbank": {
        "name":
            "LBank",

        "icon":
            "🟣",

        "code":
            "61GTN",

        "url":
            "https://www.lbank.com/ref/61GTN",

        "image":
            ASSETS_DIR
            / "lbank_referral.png",

        "description":
            (
                "بازار رمزارزی با مجموعه‌ای "
                "از دارایی‌ها و جفت‌های معاملاتی."
            ),
    },
}


# ============================================================
# HOME TEXT
# ============================================================

def exchanges_home_text():

    return (
        "🏦 ALIFT EXCHANGE HUB\n"
        "━━━━━━━━━━━━━━━━\n\n"

        "به مرکز صرافی‌های ALIFT خوش آمدی 🚀\n\n"

        "از این بخش می‌توانی لینک‌های معرفی "
        "و کدهای Referral مجموعه ALIFT را "
        "مشاهده کنی.\n\n"

        "━━━━━━━━━━━━━━━━\n"
        "🏦 صرافی‌های فعلی\n\n"

        "🟢 XT\n"
        "🔵 Bitunix\n"
        "🟣 LBank\n\n"

        "🎁 برای مشاهده کد معرفی و لینک ثبت‌نام، "
        "صرافی موردنظر را انتخاب کن.\n\n"

        "━━━━━━━━━━━━━━━━\n"
        "⚠️ نکته مهم\n\n"

        "ALIFT در این بخش فقط لینک معرفی ارائه "
        "می‌کند و به حساب، رمز عبور، API Key، "
        "کیف پول یا دارایی شما دسترسی ندارد.\n\n"

        "قبل از ثبت‌نام، قوانین، احراز هویت، "
        "محدودیت‌های منطقه‌ای، کارمزدها و شرایط "
        "استفاده هر صرافی را شخصاً بررسی کن."
    )


# ============================================================
# HOME KEYBOARD
# ============================================================

def exchanges_keyboard():

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🟢 XT",
                    callback_data=(
                        "exchange_view_xt"
                    ),
                ),

                InlineKeyboardButton(
                    "🔵 Bitunix",
                    callback_data=(
                        "exchange_view_bitunix"
                    ),
                ),
            ],

            [
                InlineKeyboardButton(
                    "🟣 LBank",
                    callback_data=(
                        "exchange_view_lbank"
                    ),
                )
            ],

            [
                InlineKeyboardButton(
                    "🛡 راهنمای امنیت",
                    callback_data=(
                        "exchange_security"
                    ),
                )
            ],
        ]
    )


# ============================================================
# HOME
# ============================================================

async def exchanges_home(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    await update.message.reply_text(
        exchanges_home_text(),
        reply_markup=(
            exchanges_keyboard()
        ),
        disable_web_page_preview=True,
    )


# ============================================================
# EXCHANGE CARD
# ============================================================

def exchange_caption(
    exchange,
):

    return (
        f"{exchange['icon']} "
        f"{exchange['name']}\n"
        "━━━━━━━━━━━━━━━━\n\n"

        f"{exchange['description']}\n\n"

        "🎁 Referral Code:\n"
        f"{exchange['code']}\n\n"

        "🔗 Registration Link:\n"
        f"{exchange['url']}\n\n"

        "📌 می‌توانی از دکمه ثبت‌نام "
        "برای بازکردن لینک رسمی معرفی استفاده کنی.\n\n"

        "⚠️ ثبت‌نام یا استفاده از صرافی "
        "به انتخاب و مسئولیت خود کاربر است."
    )


def exchange_card_keyboard(
    key,
):

    exchange = EXCHANGES[
        key
    ]

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    (
                        f"🚀 ثبت‌نام در "
                        f"{exchange['name']}"
                    ),
                    url=(
                        exchange["url"]
                    ),
                )
            ],

            [
                InlineKeyboardButton(
                    "📋 نمایش کد Referral",
                    callback_data=(
                        f"exchange_code_{key}"
                    ),
                )
            ],

            [
                InlineKeyboardButton(
                    "⬅️ همه صرافی‌ها",
                    callback_data=(
                        "exchange_home"
                    ),
                )
            ],
        ]
    )


# ============================================================
# SEND CARD
# ============================================================

async def send_exchange_card(
    context,
    chat_id,
    key,
):

    exchange = (
        EXCHANGES.get(
            key
        )
    )

    if exchange is None:
        return

    image = exchange[
        "image"
    ]

    caption = exchange_caption(
        exchange
    )

    keyboard = (
        exchange_card_keyboard(
            key
        )
    )

    if image.exists():

        with image.open(
            "rb"
        ) as photo:

            await context.bot.send_photo(
                chat_id=chat_id,
                photo=photo,
                caption=caption,
                reply_markup=keyboard,
            )

    else:

        await context.bot.send_message(
            chat_id=chat_id,
            text=caption,
            reply_markup=keyboard,
            disable_web_page_preview=True,
        )


# ============================================================
# SECURITY
# ============================================================

def security_text():

    return (
        "🛡 ALIFT EXCHANGE SECURITY\n"
        "━━━━━━━━━━━━━━━━\n\n"

        "قبل از استفاده از هر صرافی:\n\n"

        "✅ لینک دامنه را بررسی کن.\n"
        "✅ 2FA را فعال کن.\n"
        "✅ رمز عبور اختصاصی استفاده کن.\n"
        "✅ کدهای Backup را امن نگه دار.\n"
        "✅ قوانین محل اقامتت را بررسی کن.\n"
        "✅ قبل از انتقال مبلغ زیاد، "
        "یک تراکنش کوچک آزمایشی انجام بده.\n\n"

        "❌ Seed Phrase را به کسی نده.\n"
        "❌ Private Key را داخل ربات وارد نکن.\n"
        "❌ API Secret را برای پشتیبانی ارسال نکن.\n\n"

        "ALIFT برای Referral به اطلاعات ورود "
        "حساب صرافی شما نیاز ندارد."
    )


# ============================================================
# CALLBACK
# ============================================================

async def exchange_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = (
        update.callback_query
    )

    if query is None:
        return

    await query.answer()

    data = (
        query.data
        or ""
    )

    # --------------------------------------------------------
    # HOME
    # --------------------------------------------------------

    if data == "exchange_home":

        await query.edit_message_text(
            exchanges_home_text(),
            reply_markup=(
                exchanges_keyboard()
            ),
            disable_web_page_preview=True,
        )

        return

    # --------------------------------------------------------
    # SECURITY
    # --------------------------------------------------------

    if data == "exchange_security":

        await query.edit_message_text(
            security_text(),
            reply_markup=(
                InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "⬅️ صرافی‌ها",
                                callback_data=(
                                    "exchange_home"
                                ),
                            )
                        ]
                    ]
                )
            ),
        )

        return

    # --------------------------------------------------------
    # VIEW EXCHANGE
    # --------------------------------------------------------

    if data.startswith(
        "exchange_view_"
    ):

        key = data.replace(
            "exchange_view_",
            "",
            1,
        )

        if key not in EXCHANGES:

            await query.answer(
                "Exchange not found",
                show_alert=True,
            )

            return

        await send_exchange_card(
            context,
            query.from_user.id,
            key,
        )

        return

    # --------------------------------------------------------
    # REFERRAL CODE
    # --------------------------------------------------------

    if data.startswith(
        "exchange_code_"
    ):

        key = data.replace(
            "exchange_code_",
            "",
            1,
        )

        exchange = (
            EXCHANGES.get(
                key
            )
        )

        if exchange is None:
            return

        await query.answer(
            (
                "Referral Code: "
                f"{exchange['code']}"
            ),
            show_alert=True,
        )

        return
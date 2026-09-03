import logging
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import (
    ContextTypes,
)

from app.services.journal_service import (
    add_trade,
    clear_user_trades,
    delete_trade,
    get_journal_stats,
    get_user_trades,
)

logger = logging.getLogger(__name__)


def journal_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "➕ ثبت معامله جدید",
                    callback_data="journal_add",
                ),
                InlineKeyboardButton(
                    "📊 آمار و کارنامه ژورنال",
                    callback_data="journal_stats",
                ),
            ],
            [
                InlineKeyboardButton(
                    "📜 تاریخچه معاملات من",
                    callback_data="journal_history",
                ),
            ],
            [
                InlineKeyboardButton(
                    "🔄 بروزرسانی",
                    callback_data="journal_home",
                ),
            ],
        ]
    )


def journal_home_text(telegram_id: int) -> str:
    stats = get_journal_stats(telegram_id)
    pnl_sign = "+" if stats["total_pnl_percent"] > 0 else ""
    pnl_color = "🟢" if stats["total_pnl_percent"] > 0 else ("🔴" if stats["total_pnl_percent"] < 0 else "⚪")

    return (
        "📓 ژورنال هوشمند معامله‌گری (MrBiznes Journal)\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "ثبت دقیق معاملات و بررسی نتایج، کلید اصلی تبدیل شدن به یک تریدر سودده و منظم است.\n\n"
        "📊 خلاصه عملکرد ژورنال شما:\n"
        f"• 🎯 مجموع معاملات: {stats['total_trades']}\n"
        f"• ✅ سودده: {stats['wins']}  |  ❌ زیان‌ده: {stats['losses']}\n"
        f"• 📈 وین ریت (Win Rate): {stats['win_rate']}%\n"
        f"• {pnl_color} بازدهی کل ثبت‌شده: {pnl_sign}{stats['total_pnl_percent']}%\n\n"
        "برای ثبت سیگنال یا معامله جدید روی «➕ ثبت معامله جدید» بزنید."
    )


def stats_text(telegram_id: int) -> str:
    stats = get_journal_stats(telegram_id)
    pnl_sign = "+" if stats["total_pnl_percent"] > 0 else ""
    pnl_color = "🟢" if stats["total_pnl_percent"] > 0 else ("🔴" if stats["total_pnl_percent"] < 0 else "⚪")

    return (
        "📊 کارنامه و آمار تفصیلی ژورنال معاملاتی\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🎯 تعداد کل معاملات: {stats['total_trades']}\n"
        f"✅ معاملات موفق (Win): {stats['wins']}\n"
        f"❌ معاملات ناموفق (Loss): {stats['losses']}\n"
        f"➖ معاملات سر به سر (BE): {stats['breakeven']}\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🏆 نرخ موفقیت (Win Rate): {stats['win_rate']}%\n"
        f"{pnl_color} بازده کل: {pnl_sign}{stats['total_pnl_percent']}%\n"
        f"💵 سود دلاری کل: {stats['total_pnl_amount']:+,.2f} $\n"
        f"🚀 بهترین معامله: +{stats['best_trade']}%\n"
        f"⚠️ بدترین معامله: {stats['worst_trade']}%\n"
        f"⚖️ ضریب سودآوری (Profit Factor): {stats['profit_factor']}\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 معامله‌گر حرفه‌ای کسی است که اشتباهات گذشته‌اش را تکرار نمی‌کند."
    )


def history_keyboard(trades):
    rows = []
    for t in trades[:10]:
        pnl_sign = "+" if t.pnl_percent > 0 else ""
        icon = "🟢" if t.pnl_percent > 0 else ("🔴" if t.pnl_percent < 0 else "⚪")
        rows.append(
            [
                InlineKeyboardButton(
                    f"{icon} {t.symbol} ({t.direction}) | {pnl_sign}{t.pnl_percent}%",
                    callback_data=f"journal_view_{t.id}",
                )
            ]
        )
    rows.append(
        [
            InlineKeyboardButton("➕ ثبت معامله جدید", callback_data="journal_add"),
            InlineKeyboardButton("⬅️ بازگشت", callback_data="journal_home"),
        ]
    )
    return InlineKeyboardMarkup(rows)


async def journal_home(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user_id = update.effective_user.id
    text = journal_home_text(user_id)
    if update.message:
        await update.message.reply_text(text, reply_markup=journal_keyboard())


async def journal_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    if query is None:
        return
    await query.answer()

    user_id = query.from_user.id
    data = query.data or ""

    if data == "journal_home":
        context.user_data.pop("journal_input", None)
        await query.edit_message_text(
            journal_home_text(user_id),
            reply_markup=journal_keyboard(),
        )
        return

    if data == "journal_stats":
        await query.edit_message_text(
            stats_text(user_id),
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("⬅️ بازگشت به ژورنال", callback_data="journal_home")]]
            ),
        )
        return

    if data == "journal_history":
        trades = get_user_trades(user_id, limit=10)
        if not trades:
            await query.edit_message_text(
                "📜 هنوز هیچ معامله‌ای در ژورنال ثبت نکرده‌اید.\n\n"
                "با کلیک روی دکمه زیر، اولین معامله خود را ثبت کنید:",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [InlineKeyboardButton("➕ ثبت اولین معامله", callback_data="journal_add")],
                        [InlineKeyboardButton("⬅️ بازگشت", callback_data="journal_home")],
                    ]
                ),
            )
            return

        await query.edit_message_text(
            "📜 آخرین معاملات ثبت‌شده شما در ژورنال:\n"
            "برای مشاهده جزئیات هر معامله روی آن کلیک کنید:",
            reply_markup=history_keyboard(trades),
        )
        return

    if data == "journal_add":
        context.user_data["journal_input"] = {"step": "symbol"}
        await query.edit_message_text(
            "➕ مرحله ۱ از ۳: ثبت نماد معامله\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "نام نماد معاملاتی را بفرستید.\n\n"
            "مثال:\n"
            "BTC/USDT\n"
            "ETH\n"
            "EURUSD\n"
            "GOLD (XAUUSD)",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("❌ انصراف", callback_data="journal_home")]]
            ),
        )
        return

    if data.startswith("journal_dir_"):
        direction = data.replace("journal_dir_", "").upper()
        pending = context.user_data.get("journal_input")
        if not pending:
            return

        pending["direction"] = direction
        pending["step"] = "pnl"

        await query.edit_message_text(
            f"➕ مرحله ۳ از ۳: ثبت سود یا زیان معامله ({pending.get('symbol', '')} - {direction})\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "درصد سود یا زیان معامله را ارسال کنید.\n\n"
            "مثال‌ها:\n"
            "• `+15.5` (برای ۱۵.۵٪ سود)\n"
            "• `-3` (برای ۳٪ ضرر)\n"
            "• `0` (برای سر به سر)",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("❌ انصراف", callback_data="journal_home")]]
            ),
        )
        return

    if data.startswith("journal_view_"):
        try:
            trade_id = int(data.replace("journal_view_", ""))
        except ValueError:
            return

        trades = get_user_trades(user_id, limit=50)
        trade = next((t for t in trades if t.id == trade_id), None)
        if not trade:
            await query.answer("معامله یافت نشد.", show_alert=True)
            return

        icon = "🟢" if trade.pnl_percent > 0 else ("🔴" if trade.pnl_percent < 0 else "⚪")
        pnl_sign = "+" if trade.pnl_percent > 0 else ""

        entry_text = f"{trade.entry_price:,.4f}" if trade.entry_price else "ثبت‌نشده"
        exit_text = f"{trade.exit_price:,.4f}" if trade.exit_price else "ثبت‌نشده"
        created_str = trade.created_at.strftime("%Y/%m/%d %H:%M")

        text = (
            f"📄 جزئیات معامله #{trade.id}\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🪙 نماد: {trade.symbol}\n"
            f"🧭 جهت: {trade.direction}\n"
            f"{icon} درصد سود/زیان: {pnl_sign}{trade.pnl_percent}%\n"
            f"🎯 وضعیت: {trade.status}\n"
            f"📌 منبع سیگنال: {trade.strategy_source or 'شخصی'}\n"
            f"📥 نقطه ورود: {entry_text}\n"
            f"📤 نقطه خروج: {exit_text}\n"
            f"🕒 تاریخ ثبت: {created_str}\n"
        )
        if trade.notes:
            text += f"\n📝 یادداشت: {trade.notes}"

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("🗑 حذف این معامله", callback_data=f"journal_del_{trade.id}")],
                    [InlineKeyboardButton("⬅️ بازگشت به تاریخچه", callback_data="journal_history")],
                ]
            ),
        )
        return

    if data.startswith("journal_del_"):
        try:
            trade_id = int(data.replace("journal_del_", ""))
            deleted = delete_trade(trade_id, user_id)
            if deleted:
                await query.answer("✅ معامله با موفقیت حذف شد.", show_alert=True)
            else:
                await query.answer("خطا در حذف معامله.", show_alert=True)
        except Exception:
            pass

        trades = get_user_trades(user_id, limit=10)
        await query.edit_message_text(
            "📜 تاریخچه معاملات به‌روزرسانی شد:",
            reply_markup=history_keyboard(trades),
        )
        return


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


def to_english_digits(text: str) -> str:
    if not text:
        return ""
    trans = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
    return str(text).translate(trans)


async def journal_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> bool:
    if update.message is None or update.effective_user is None:
        return False

    pending = context.user_data.get("journal_input")
    if not pending:
        return False

    user_id = update.effective_user.id
    text = (update.message.text or "").strip()
    if not text:
        return True

    # Allow cancelling or navigating to another menu
    if text in MENU_BUTTON_TEXTS or text.startswith("/") or text in {"انصراف", "لغو", "بازگشت", "cancel"}:
        context.user_data.pop("journal_input", None)
        if text in {"انصراف", "لغو", "بازگشت", "cancel"}:
            await update.message.reply_text("ثبت معامله لغو شد.", reply_markup=journal_keyboard())
            return True
        return False

    step = pending.get("step")

    # STEP 1: SYMBOL
    if step == "symbol":
        pending["symbol"] = to_english_digits(text).upper()
        pending["step"] = "direction"

        await update.message.reply_text(
            f"➕ مرحله ۲ از ۳: جهت معامله برای نماد {pending['symbol']}\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "جهت معامله را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("🟢 لانگ (LONG / BUY)", callback_data="journal_dir_long"),
                        InlineKeyboardButton("🔴 شورت (SHORT / SELL)", callback_data="journal_dir_short"),
                    ],
                    [InlineKeyboardButton("❌ انصراف", callback_data="journal_home")],
                ]
            ),
        )
        return True

    # STEP 2: PNL
    if step == "pnl":
        try:
            cleaned = to_english_digits(text).replace("%", "").replace("+", "").replace("٪", "").strip()
            pnl_val = float(cleaned)
            if "+" in text:
                pnl_val = abs(pnl_val)
            elif "-" in text:
                pnl_val = -abs(pnl_val)
        except ValueError:
            await update.message.reply_text(
                "❌ لطفاً یک مقدار عددی معتبر ارسال کنید (مثلاً `+12` یا `-3.5`):\n"
                "برای لغو کلمه «لغو» را ارسال کنید.",
                parse_mode="Markdown",
            )
            return True

        symbol = pending.get("symbol", "BTC")
        direction = pending.get("direction", "LONG")

        trade = add_trade(
            telegram_id=user_id,
            symbol=symbol,
            direction=direction,
            pnl_percent=pnl_val,
            strategy_source="سیگنال مستر بیزنس",
        )

        context.user_data.pop("journal_input", None)

        pnl_sign = "+" if pnl_val > 0 else ""
        icon = "🎉 🟢" if pnl_val > 0 else ("🔴" if pnl_val < 0 else "⚪")

        await update.message.reply_text(
            f"{icon} معامله با موفقیت در ژورنال ثبت شد!\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🪙 نماد: {trade.symbol}\n"
            f"🧭 جهت: {trade.direction}\n"
            f"📊 نتیجه: {pnl_sign}{trade.pnl_percent}%\n"
            f"🎯 وضعیت: {trade.status}\n\n"
            "کارنامه معاملاتی شما به‌روزرسانی شد. 🚀",
            reply_markup=journal_keyboard(),
        )
        return True

    return False

"""PLT chart-analysis bot handlers."""
from __future__ import annotations

import asyncio
import logging
import time

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from app.engines.vision_plt import analyze_chart

logger = logging.getLogger(__name__)

PLT_STATE_KEY = "plt_waiting_photo"
PLT_COOLDOWN_KEY = "plt_last_use"
COOLDOWN_SECONDS = 15

WELCOME = (
    "🧠 دستیار هوش مصنوعی تحلیل چارت (PLT)\n"
    "━━━━━━━━━━━━━━━━━━━━━━\n\n"
    "📸 کافیست اسکرین‌شات چارت معاملاتی خود را ارسال کنید!\n\n"
    "✨ ویژگی‌های تحلیل هوشمند PLT:\n"
    "۱) نقد خطوط حمایت، مقاومت و رسم سطوح شما\n"
    "۲) خوانش وضعیت RSI، واگرایی‌ها و حجم معاملات\n"
    "۳) تعیین ساختار بازار (روند صعودی، نزولی یا رنج)\n"
    "۴) ارائه سناریوی اصلی و جایگزین معامله (ورود / حد ضرر / تارگت‌ها)\n"
    "۵) امتیازدهی کیفیت ستاپ از ۰ تا ۱۰۰ و اعلام بزرگترین ریسک\n\n"
    "💡 نکته: می‌توانید نماد و تایم‌فریم (مثلاً «BTC 15m») را در کپشن عکس بنویسید.\n\n"
    "👇 همین الان یک تصویر از چارت ارسال کن:"
)

BUSY_TEXT = "⏳ دستیار PLT در حال پردازش چارت قبلی است… چند لحظه شکیبا باشید."

COOLDOWN_TEXT = (
    "⏲ برای مدیریت ترافیک سرور، لطفاً هر {sec} ثانیه یک تحلیل دریافت کنید. "
    "کمی صبر و دوباره تصویر بفرستید. 🙏"
)


async def plt_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data[PLT_STATE_KEY] = True
    if update.message:
        await update.message.reply_text(
            WELCOME,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "💡 راهنمای ارسال چارت بهینه",
                            callback_data="plt_guide",
                        )
                    ]
                ]
            ),
        )


async def plt_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if query is None:
        return
    await query.answer()

    if query.data == "plt_guide":
        await query.message.reply_text(
            "📋 راهنمای بهترین نتیجه از PLT:\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "• از کندل‌های واضح و تایم‌فریم مشخص اسکرین‌شات بگیرید.\n"
            "• اندیکاتورهای مدنظرتان (مثل RSI یا حجم) داخل تصویر مشخص باشند.\n"
            "• اگر خطوط روند یا سطوح کشیده‌اید، PLT نحوه ترسیم شما را ارزیابی و اصلاح می‌کند."
        )


async def plt_photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    if message is None or not message.photo:
        return

    now = time.time()
    last = context.user_data.get(PLT_COOLDOWN_KEY, 0)
    if now - last < COOLDOWN_SECONDS:
        await message.reply_text(COOLDOWN_TEXT.format(sec=COOLDOWN_SECONDS))
        return

    if context.user_data.get("plt_busy"):
        await message.reply_text(BUSY_TEXT)
        return
    context.user_data["plt_busy"] = True

    try:
        photo = message.photo[-1]
        caption_hint = (message.caption or "").strip()

        waiting = await message.reply_text("🧠 در حال پردازش و تحلیل تخصصی چارت توسط PLT… ⏳")

        tg_file = await photo.get_file()
        image_bytes = bytes(await tg_file.download_as_bytearray())

        hint = caption_hint
        if "4h" in caption_hint.lower() or "۴ساعته" in caption_hint or "4ساعته" in caption_hint:
            hint = (
                "این چارت تایم‌فریم ۴ ساعته است. اولویت: تشخیص جهت روند کلی "
                "(صعودی/نزولی/رنج) و سطوح کلیدی برای هم‌جهت شدن تریدهای کوتاه‌مدت. "
            ) + caption_hint

        result = await asyncio.to_thread(analyze_chart, image_bytes, hint)

        for i in range(0, len(result), 4000):
            chunk = result[i : i + 4000]
            if i == 0:
                await waiting.edit_text(chunk)
            else:
                await message.reply_text(chunk)

        context.user_data[PLT_COOLDOWN_KEY] = time.time()
        context.user_data[PLT_STATE_KEY] = True
    except Exception as exc:
        logger.warning("PLT photo handling failed: %s", exc)
        await message.reply_text(
            "🧠 PLT: دریافت و تحلیل چارت با خطا مواجه شد. لطفاً تصویر واضح‌تری بفرستید. 🙏"
        )
    finally:
        context.user_data["plt_busy"] = False

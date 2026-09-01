"""PLT chart-analysis bot handlers."""
from __future__ import annotations

import asyncio
import logging
import time

from telegram import Update
from telegram.ext import ContextTypes

from app.engines.vision_plt import analyze_chart

logger = logging.getLogger(__name__)

PLT_STATE_KEY = "plt_waiting_photo"
PLT_COOLDOWN_KEY = "plt_last_use"
COOLDOWN_SECONDS = 60

WELCOME = (
    "🧠 PLT | تحلیل چارت هوشمند\n\n"
    "📸 اسکرین‌شات چارت را بفرست (می‌تونی خطوط S/R، RSI و اوسیلاتور حجم را هم کشیده باشی).\n"
    "✍️ توی کپشن عکس بنویس: نماد و تایم‌فریم - مثلا «ETH 15m»\n"
    "📊 برای بررسی روند کلی، عکس بعدی را با کپشن «4H» بفرست تا جهت روند هم جدا بررسی شود.\n\n"
    "PLT چارتت را می‌خواند: نقد رسم ✔️ سطوح ✔️ حجم ✔️ ورود/استاپ/تارگت ✔️ امتیاز ستاپ ✔️\n\n"
    "⚠️ تحلیل آموزشی است؛ تصمیم نهایی همیشه با تو."
)

BUSY_TEXT = (
    "⏳ PLT دارد چارت قبلی‌ات را تحلیل می‌کند… چند لحظه صبر کن."
)

COOLDOWN_TEXT = (
    "⏲ برای صرفه‌جویی، هر {sec} ثانیه یک تحلیل می‌توانی بگیری. "
    "کمی صبر و دوباره بفرست. 🙏"
)


async def plt_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data[PLT_STATE_KEY] = True
    if update.message:
        await update.message.reply_text(WELCOME)


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

        waiting = await message.reply_text("🧠 PLT: در حال دریافت و خواندن چارت…")

        tg_file = await photo.get_file()
        image_bytes = bytes(await tg_file.download_as_bytearray())

        hint = caption_hint
        if "4h" in caption_hint.lower() or "۴ساعته" in caption_hint:
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
            "🧠 PLT: دریافت/تحلیل عکس ناموفق بود. دوباره اسکرین‌شات واضح‌تر بفرست. 🙏"
        )
    finally:
        context.user_data["plt_busy"] = False

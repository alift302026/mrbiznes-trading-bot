"""Admin preview for the final S4 signal engine.

`/signalpreview` — scans the watchlist right now and sends the freshest,
highest-confidence signal card (graphic + Persian caption) to the admin.
This is exactly the card that goes into the bot's signal section.
"""
from __future__ import annotations

import asyncio
import logging

from telegram import Update
from telegram.ext import ContextTypes

from app.core.config import ADMIN_IDS
from app.services import final_signal_service as svc

logger = logging.getLogger(__name__)


def _is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


async def signal_preview_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    user = update.effective_user
    if not user or not _is_admin(user.id):
        if update.message:
            await update.message.reply_text("این بخش فعلاً فقط برای مدیریت فعال است. 👑")
        return

    if update.message:
        await update.message.reply_text("⏳ در حال اسکن بازار با موتور نهایی S4…")

    signals = await asyncio.to_thread(svc.scan_all)
    if not signals:
        stored = svc.load_latest(1)
    else:
        stored = []
        svc.save_signals(signals)

    pool = signals or stored
    if not pool:
        if update.message:
            await update.message.reply_text(
                "🔎 الان ستاپ تازه و باکیفیت پیدا نشد.\n"
                "سیگنال اجباری تولید نمی‌کنیم — صبر، بخشی از استراتژی است. ✅"
            )
        return

    best = max(pool, key=lambda s: (s.get("confidence", 0), str(s.get("decision_time", ""))))
    try:
        card = await asyncio.to_thread(svc.render_card, best)
    except Exception as exc:  # noqa: BLE001
        logger.warning("final signal card render failed: %s", exc)
        card = None

    caption = svc.build_caption_fa(best)
    if update.message:
        if card is not None:
            await update.message.reply_photo(photo=card, caption=caption[:1024])
        else:
            await update.message.reply_text(caption)

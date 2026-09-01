"""Hourly final-signal worker."""
from __future__ import annotations

import asyncio
import logging

from telegram.ext import ContextTypes

from app.core.config import ADMIN_IDS
from app.services import final_signal_service as svc

logger = logging.getLogger(__name__)


async def final_signal_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        signals = await asyncio.to_thread(svc.scan_all)
    except Exception as exc:
        logger.warning("final-signal worker scan error: %s", exc)
        return

    fresh = await asyncio.to_thread(svc.save_signals, signals)
    if not fresh:
        return

    logger.info("final-signal worker: %d fresh signal(s) stored", len(fresh))
    if not svc.push_enabled():
        logger.info("final-signal worker: push disabled - paper mode")
        return

    for sig in fresh:
        try:
            card = await asyncio.to_thread(svc.render_card, sig)
            caption = svc.build_caption_fa(sig)
            for admin_id in ADMIN_IDS:
                try:
                    await context.bot.send_photo(
                        chat_id=admin_id,
                        photo=card,
                        caption=caption[:1024],
                    )
                except Exception as send_exc:
                    logger.warning("final-signal push to %s failed: %s", admin_id, send_exc)
        except Exception as exc:
            logger.warning("final-signal render/push error: %s", exc)

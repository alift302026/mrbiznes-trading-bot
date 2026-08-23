from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

from app.engines.news.tradingview_calendar_provider import (
    TradingViewEconomicCalendarProvider,
)
from app.services.economic_calendar_sync_service import (
    sync_economic_calendar,
)


logger = logging.getLogger(__name__)

SYNC_PAST_HOURS = 24
SYNC_FUTURE_DAYS = 14


async def sync_calendar_now() -> Dict[str, int]:
    """
    Synchronize recent and upcoming economic events.

    Including the previous 24 hours allows newly released
    Actual values to be picked up after publication.
    """
    now = datetime.now(timezone.utc)

    start = now - timedelta(
        hours=SYNC_PAST_HOURS
    )
    end = now + timedelta(
        days=SYNC_FUTURE_DAYS
    )

    provider = (
        TradingViewEconomicCalendarProvider()
    )

    return await sync_economic_calendar(
        provider=provider,
        start=start,
        end=end,
    )


async def economic_calendar_sync_job(
    context: Any,
) -> None:
    """
    python-telegram-bot JobQueue adapter.

    The synchronization logic itself is Telegram-independent.
    """
    try:
        stats = await sync_calendar_now()

        logger.info(
            "Economic Calendar Sync: "
            "fetched=%s created=%s updated=%s "
            "unchanged=%s skipped=%s",
            stats["fetched"],
            stats["created"],
            stats["updated"],
            stats["unchanged"],
            stats["skipped"],
        )

    except Exception:
        # A provider/network failure must not stop the bot
        # or other scheduled workers.
        logger.exception(
            "Economic Calendar Sync failed"
        )
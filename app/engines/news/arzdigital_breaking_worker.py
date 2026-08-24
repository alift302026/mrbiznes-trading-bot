from __future__ import annotations

import logging
import os
import xml.etree.ElementTree as ET

from datetime import (
    datetime,
)
from email.utils import (
    parsedate_to_datetime,
)
from typing import (
    Any,
    Dict,
    List,
    Optional,
)

import requests

from telegram.ext import (
    ContextTypes,
)


logger = logging.getLogger(
    __name__
)


RSS_URL = (
    "https://arzdigital.com/breaking/feed/"
)

REQUEST_TIMEOUT = 20

CHANNEL_USERNAME = (
    "@METATRAID"
)


_last_seen_link: Optional[
    str
] = None

_initialized = False


def _channel_id() -> Optional[int]:
    """
    Read Telegram News Channel ID
    from environment.

    Example:
        NEWS_CHANNEL_ID=-100...
    """
    value = os.getenv(
        "NEWS_CHANNEL_ID",
        "",
    ).strip()

    if not value:
        return None

    try:
        return int(value)

    except ValueError:
        return None


def _fetch_feed() -> List[
    Dict[str, Any]
]:
    """
    Fetch the official ArzDigital
    Breaking News RSS feed.

    No AI is involved here.
    """

    response = requests.get(
        RSS_URL,
        timeout=REQUEST_TIMEOUT,
        headers={
            "User-Agent": (
                "MRBIZNES/1.0"
            ),
            "Accept": (
                "application/rss+xml,"
                "application/xml,"
                "text/xml"
            ),
        },
    )

    response.raise_for_status()

    try:
        root = (
            ET.fromstring(
                response.content
            )
        )

    except ET.ParseError as exc:
        raise RuntimeError(
            "Invalid RSS XML"
        ) from exc

    result: List[
        Dict[str, Any]
    ] = []

    for item in root.findall(
        ".//item"
    ):
        title = (
            item.findtext(
                "title"
            )
            or ""
        ).strip()

        link = (
            item.findtext(
                "link"
            )
            or ""
        ).strip()

        published_text = (
            item.findtext(
                "pubDate"
            )
            or ""
        ).strip()

        if not title:
            continue

        if not link:
            continue

        published_at = None

        if published_text:
            try:
                published_at = (
                    parsedate_to_datetime(
                        published_text
                    )
                )

            except (
                TypeError,
                ValueError,
            ):
                published_at = None

        result.append(
            {
                "title": title,
                "link": link,
                "published_at": (
                    published_at
                ),
            }
        )

    return result


def _format_time(
    published_at: Any,
) -> str:
    if not isinstance(
        published_at,
        datetime,
    ):
        return "—"

    return published_at.strftime(
        "%Y-%m-%d %H:%M UTC"
    )


def _format_message(
    item: Dict[str, Any],
) -> str:
    """
    Telegram news format.

    The publisher's name is intentionally
    not printed as a separate line.

    The original article URL is preserved
    for provenance and verification.
    """

    time_text = _format_time(
        item.get(
            "published_at"
        )
    )

    title = str(
        item.get(
            "title"
        )
        or ""
    ).strip()

    link = str(
        item.get(
            "link"
        )
        or ""
    ).strip()

    return (
        "🚨 خبر فوری ارز دیجیتال\n\n"
        f"📰 {title}\n\n"
        f"🕐 {time_text}\n\n"
        f"{CHANNEL_USERNAME}"
    )


async def arzdigital_breaking_job(
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Poll ArzDigital's official
    Breaking News RSS feed.

    Behaviour:

    - First successful run creates a
      baseline and sends nothing.

    - Later runs send only newly
      discovered feed entries.

    - Existing older articles are not
      intentionally flooded.

    - At most 5 new entries are sent
      during a single run.

    Important:

    This worker does not use AI.

    It does not fabricate, summarize,
    translate or reinterpret news.
    """

    global _initialized
    global _last_seen_link

    channel_id = (
        _channel_id()
    )

    if channel_id is None:
        logger.warning(
            "NEWS_CHANNEL_ID is "
            "missing or invalid"
        )

        return

    try:
        items = _fetch_feed()

    except Exception:
        logger.exception(
            "ArzDigital RSS "
            "fetch failed"
        )

        return

    if not items:
        logger.info(
            "ArzDigital RSS "
            "returned no items"
        )

        return

    newest_link = (
        items[0]["link"]
    )

    # On startup establish a baseline.
    # Do not flood the channel with
    # existing historical articles.
    if not _initialized:
        _last_seen_link = (
            newest_link
        )

        _initialized = True

        logger.info(
            "ArzDigital Breaking "
            "baseline initialized: %s",
            newest_link,
        )

        return

    # Nothing new.
    if (
        newest_link
        == _last_seen_link
    ):
        return

    new_items: List[
        Dict[str, Any]
    ] = []

    for item in items:
        if (
            item["link"]
            == _last_seen_link
        ):
            break

        new_items.append(
            item
        )

    if not new_items:
        # Feed changed in a way where the
        # previous baseline disappeared.
        # Avoid sending the entire feed.
        _last_seen_link = (
            newest_link
        )

        logger.warning(
            "Previous ArzDigital "
            "baseline was not found. "
            "Baseline refreshed."
        )

        return

    # Maximum five items per run.
    new_items = new_items[:5]

    # Feed is newest-first.
    # Send oldest-first so Telegram
    # shows new entries chronologically.
    for item in reversed(
        new_items
    ):
        try:
            await (
                context.bot.send_message(
                    chat_id=(
                        channel_id
                    ),
                    text=(
                        _format_message(
                            item
                        )
                    ),
                    disable_web_page_preview=(
                        False
                    ),
                )
            )

        except Exception:
            logger.exception(
                "Failed to send "
                "ArzDigital Breaking "
                "News to Telegram"
            )

            # Do not advance the baseline
            # after a failed delivery.
            return

    _last_seen_link = (
        newest_link
    )

    logger.info(
        "ArzDigital Breaking: "
        "%s new item(s) sent",
        len(new_items),
    )
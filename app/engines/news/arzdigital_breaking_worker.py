from __future__ import annotations

import html
import logging
import os
import re
import xml.etree.ElementTree as ET

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

CHANNEL_USERNAME = (
    "@MrBiznesMarket"
)

REQUEST_TIMEOUT = 20

MAX_ITEMS_PER_RUN = 5


_last_seen_link: Optional[str] = None
_initialized = False


_SESSION = requests.Session()

_SESSION.headers.update(
    {
        "User-Agent": (
            "Mozilla/5.0 "
            "(Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/139.0 Safari/537.36"
        ),
        "Accept-Language": (
            "fa,en;q=0.8"
        ),
    }
)


def _channel_id() -> Optional[int]:
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


def _clean_text(
    value: Optional[str],
) -> str:
    if not value:
        return ""

    text = html.unescape(
        str(value)
    )

    text = re.sub(
        r"<[^>]+>",
        " ",
        text,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    ).strip()

    return text


def _meta_content(
    page_html: str,
    property_name: str,
) -> Optional[str]:
    escaped = re.escape(
        property_name
    )

    patterns = [
        (
            r'<meta[^>]+'
            r'(?:property|name)'
            r'=["\']'
            + escaped
            + r'["\'][^>]+'
            r'content=["\']'
            r'([^"\']*)'
            r'["\'][^>]*>'
        ),
        (
            r'<meta[^>]+'
            r'content=["\']'
            r'([^"\']*)'
            r'["\'][^>]+'
            r'(?:property|name)'
            r'=["\']'
            + escaped
            + r'["\'][^>]*>'
        ),
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            page_html,
            re.I,
        )

        if not match:
            continue

        value = html.unescape(
            match.group(1)
        ).strip()

        if value:
            return value

    return None


def _fetch_article_image(
    link: str,
) -> Optional[str]:
    """
    Read only the OpenGraph image from
    the original article page.

    The article text is not republished.
    """

    try:
        response = _SESSION.get(
            link,
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

    except requests.RequestException:
        logger.exception(
            "Article image fetch "
            "failed: %s",
            link,
        )

        return None

    return _meta_content(
        response.text,
        "og:image",
    )


def _hashtags(
    title: str,
) -> List[str]:
    text = title.lower()

    rules = [
        (
            (
                "بیت کوین",
                "بیت‌کوین",
                "bitcoin",
                "btc",
            ),
            "#بیت_کوین",
        ),
        (
            (
                "اتریوم",
                "ethereum",
                "eth",
            ),
            "#اتریوم",
        ),
        (
            (
                "ریپل",
                "xrp",
            ),
            "#ریپل",
        ),
        (
            (
                "سولانا",
                "solana",
            ),
            "#سولانا",
        ),
        (
            (
                "تتر",
                "usdt",
            ),
            "#تتر",
        ),
        (
            (
                "دوج کوین",
                "دوج‌کوین",
                "dogecoin",
            ),
            "#دوج_کوین",
        ),
        (
            (
                "طلا",
                "gold",
            ),
            "#طلا",
        ),
        (
            (
                "نفت",
                "oil",
                "brent",
                "wti",
            ),
            "#نفت",
        ),
        (
            (
                "فدرال رزرو",
                "پاول",
                "powell",
            ),
            "#فدرال_رزرو",
        ),
        (
            (
                "تورم",
                "cpi",
                "ppi",
            ),
            "#تورم",
        ),
        (
            (
                "نرخ بهره",
                "interest rate",
            ),
            "#نرخ_بهره",
        ),
        (
            (
                "ترامپ",
                "trump",
            ),
            "#ترامپ",
        ),
        (
            (
                "تحریم",
                "sanction",
            ),
            "#تحریم",
        ),
        (
            (
                "صرافی",
                "exchange",
            ),
            "#صرافی",
        ),
        (
            (
                "هک",
                "hack",
                "exploit",
            ),
            "#امنیت",
        ),
        (
            (
                "دیفای",
                "defi",
            ),
            "#دیفای",
        ),
        (
            (
                "etf",
                "صندوق قابل معامله",
            ),
            "#ETF",
        ),
        (
            (
                "فارکس",
                "forex",
            ),
            "#فارکس",
        ),
        (
            (
                "اقتصاد",
                "تعرفه",
                "gdp",
                "اشتغال",
                "بیکاری",
            ),
            "#اقتصاد",
        ),
    ]

    tags: List[str] = []

    for keywords, tag in rules:
        if any(
            keyword in text
            for keyword in keywords
        ):
            if tag not in tags:
                tags.append(
                    tag
                )

        if len(tags) >= 2:
            break

    for fallback in (
        "#کریپتو",
        "#اقتصاد",
    ):
        if len(tags) >= 2:
            break

        if fallback not in tags:
            tags.append(
                fallback
            )

    return tags[:2]


def _fetch_feed() -> List[
    Dict[str, Any]
]:
    """
    Discover Breaking News from the
    site's official RSS feed.

    Original URLs are retained internally
    for deduplication and provenance.
    """

    response = _SESSION.get(
        RSS_URL,
        timeout=REQUEST_TIMEOUT,
        headers={
            "Accept": (
                "application/rss+xml,"
                "application/xml,"
                "text/xml"
            )
        },
    )

    response.raise_for_status()

    try:
        root = ET.fromstring(
            response.content
        )

    except ET.ParseError as exc:
        raise RuntimeError(
            "Invalid Breaking RSS XML"
        ) from exc

    result: List[
        Dict[str, Any]
    ] = []

    for item in root.findall(
        ".//item"
    ):
        title = _clean_text(
            item.findtext(
                "title"
            )
        )

        link = (
            item.findtext(
                "link"
            )
            or ""
        ).strip()

        if not title:
            continue

        if not link:
            continue

        result.append(
            {
                "title": title,

                # Internal only.
                "link": link,
                "source_url": link,
            }
        )

    return result


def _enrich_item(
    item: Dict[str, Any],
) -> Dict[str, Any]:
    result = dict(
        item
    )

    result[
        "image_url"
    ] = _fetch_article_image(
        item["link"]
    )

    return result


def _format_message(
    item: Dict[str, Any],
) -> str:
    """
    Public Telegram format:

    - Breaking label
    - Headline
    - Two relevant hashtags
    - Channel username

    No date.
    No source-name line.
    No source URL.
    No article paragraph.
    """

    title = _clean_text(
        item.get(
            "title"
        )
    )

    tags = _hashtags(
        title
    )

    return (
        "🚨 فوری | نبض بازار\n\n"
        f"📰 {title}\n\n"
        f"{' '.join(tags)}\n\n"
        f"☕️ {CHANNEL_USERNAME}"
    )


async def _send_item(
    context: ContextTypes.DEFAULT_TYPE,
    channel_id: int,
    item: Dict[str, Any],
) -> None:
    """
    Prefer photo + caption.

    If the article has no usable image,
    fall back to a normal text message.
    """

    enriched = await __import__(
        "asyncio"
    ).to_thread(
        _enrich_item,
        item,
    )

    text = _format_message(
        enriched
    )

    image_url = enriched.get(
        "image_url"
    )

    if image_url:
        try:
            await context.bot.send_photo(
                chat_id=channel_id,
                photo=image_url,
                caption=text,
            )

            return

        except Exception:
            logger.exception(
                "Breaking News image "
                "send failed; "
                "falling back to text"
            )

    await context.bot.send_message(
        chat_id=channel_id,
        text=text,
        disable_web_page_preview=True,
    )


async def arzdigital_breaking_job(
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Breaking News worker.

    Scheduling is configured in main.py.
    Current intended interval:
        every 3600 seconds

    Behaviour:

    1. Read official RSS.
    2. First successful run establishes
       a baseline and sends nothing.
    3. Subsequent runs identify only
       genuinely new feed entries.
    4. Fetch article image.
    5. Send image + headline to Telegram.
    6. Maximum 5 new entries per run.

    Original article links are retained
    internally for provenance/dedup but
    are not displayed publicly.
    """

    global _initialized
    global _last_seen_link

    channel_id = (
        _channel_id()
    )

    if channel_id is None:
        logger.warning(
            "NEWS_CHANNEL_ID "
            "is missing or invalid"
        )

        return

    try:
        items = await __import__(
            "asyncio"
        ).to_thread(
            _fetch_feed
        )

    except Exception:
        logger.exception(
            "Breaking RSS fetch failed"
        )

        return

    if not items:
        return

    newest_link = (
        items[0]["link"]
    )

    # Startup baseline.
    if not _initialized:
        _last_seen_link = (
            newest_link
        )

        _initialized = True

        logger.info(
            "Breaking News baseline "
            "initialized: %s",
            newest_link,
        )

        return

    # No new item.
    if (
        newest_link
        == _last_seen_link
    ):
        return

    new_items: List[
        Dict[str, Any]
    ] = []

    baseline_found = False

    for item in items:
        if (
            item["link"]
            == _last_seen_link
        ):
            baseline_found = True
            break

        new_items.append(
            item
        )

    # Previous baseline disappeared from
    # the current feed. Refresh safely
    # instead of flooding historical news.
    if not baseline_found:
        _last_seen_link = (
            newest_link
        )

        logger.warning(
            "Previous Breaking RSS "
            "baseline not found; "
            "baseline refreshed"
        )

        return

    new_items = new_items[
        :MAX_ITEMS_PER_RUN
    ]

    # RSS is newest-first.
    # Send old -> new to preserve order.
    for item in reversed(
        new_items
    ):
        try:
            await _send_item(
                context,
                channel_id,
                item,
            )

        except Exception:
            logger.exception(
                "Failed to send "
                "Breaking News"
            )

            # Do not advance baseline if
            # Telegram delivery failed.
            return

    _last_seen_link = (
        newest_link
    )

    logger.info(
        "Breaking News: %s "
        "new item(s) sent",
        len(new_items),
    )
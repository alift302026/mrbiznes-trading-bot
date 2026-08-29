from __future__ import annotations

import html
import logging
import os
import re
import xml.etree.ElementTree as ET

from datetime import datetime
from email.utils import parsedate_to_datetime
from typing import Any, Dict, List, Optional

import requests

from telegram.ext import ContextTypes


logger = logging.getLogger(__name__)


RSS_URL = (
    "https://arzdigital.com/breaking/feed/"
)

REQUEST_TIMEOUT = 20

CHANNEL_USERNAME = (
    "@MrBiznesMarket"
)

BRAND_NAME = (
    "مستر بیزنس"
)

MAX_ITEMS_PER_RUN = 5
MAX_SUMMARY_LENGTH = 650


_last_seen_link: Optional[str] = None
_initialized = False


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


def _short_summary(
    value: Optional[str],
) -> str:
    text = _clean_text(
        value
    )

    if not text:
        return ""

    if len(text) <= MAX_SUMMARY_LENGTH:
        return text

    shortened = text[
        :MAX_SUMMARY_LENGTH
    ]

    # Prefer ending on a complete word.
    if " " in shortened:
        shortened = shortened.rsplit(
            " ",
            1,
        )[0]

    return shortened.rstrip(
        "،,؛;:- "
    ) + "…"


def _find_text(
    element: ET.Element,
    names: List[str],
) -> str:
    for child in element:
        tag = child.tag.lower()

        if any(
            name.lower()
            in tag
            for name in names
        ):
            text = (
                child.text
                or ""
            ).strip()

            if text:
                return text

    return ""


def _extract_image(
    item: ET.Element,
    description: str,
) -> Optional[str]:
    # RSS enclosure
    for enclosure in item.findall(
        "enclosure"
    ):
        url = (
            enclosure.attrib.get(
                "url"
            )
            or ""
        ).strip()

        media_type = (
            enclosure.attrib.get(
                "type"
            )
            or ""
        ).lower()

        if (
            url
            and (
                media_type.startswith(
                    "image/"
                )
                or re.search(
                    r"\.(jpg|jpeg|png|webp)"
                    r"($|\?)",
                    url,
                    re.I,
                )
            )
        ):
            return url

    # Namespaced media:content / media:thumbnail
    for child in item:
        tag = child.tag.lower()

        if (
            "thumbnail" in tag
            or "content" in tag
        ):
            url = (
                child.attrib.get(
                    "url"
                )
                or ""
            ).strip()

            media_type = (
                child.attrib.get(
                    "type"
                )
                or ""
            ).lower()

            medium = (
                child.attrib.get(
                    "medium"
                )
                or ""
            ).lower()

            if (
                url
                and (
                    "image" in media_type
                    or medium == "image"
                    or "thumbnail" in tag
                    or re.search(
                        r"\.(jpg|jpeg|png|webp)"
                        r"($|\?)",
                        url,
                        re.I,
                    )
                )
            ):
                return url

    # Image embedded in RSS description HTML
    if description:
        match = re.search(
            r"""<img[^>]+src=["']([^"']+)["']""",
            description,
            re.I,
        )

        if match:
            return html.unescape(
                match.group(1)
            ).strip()

    return None


def _hashtags(
    title: str,
    summary: str,
) -> List[str]:
    text = (
        f"{title} {summary}"
    ).lower()

    rules = [
        (
            (
                "بیت کوین",
                "بیت‌کوین",
                "bitcoin",
                " btc",
            ),
            "#بیت_کوین",
        ),
        (
            (
                "اتریوم",
                "ethereum",
                " eth",
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
                "فدرال رزرو",
                "fed ",
                "powell",
                "پاول",
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
                "بیکاری",
                "اشتغال",
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
                tags.append(tag)

        if len(tags) == 2:
            break

    fallbacks = [
        "#کریپتو",
        "#اقتصاد",
    ]

    for tag in fallbacks:
        if len(tags) >= 2:
            break

        if tag not in tags:
            tags.append(tag)

    return tags[:2]


def _fetch_feed() -> List[
    Dict[str, Any]
]:
    response = requests.get(
        RSS_URL,
        timeout=REQUEST_TIMEOUT,
        headers={
            "User-Agent": (
                "MrBiznes/1.0"
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
        root = ET.fromstring(
            response.content
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

        description_raw = (
            item.findtext(
                "description"
            )
            or ""
        )

        # Some feeds put fuller text in
        # namespaced content:encoded.
        content_raw = _find_text(
            item,
            [
                "encoded",
            ],
        )

        summary_source = (
            description_raw
            or content_raw
        )

        summary = _short_summary(
            summary_source
        )

        published_text = (
            item.findtext(
                "pubDate"
            )
            or ""
        ).strip()

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

        if not title or not link:
            continue

        image_url = _extract_image(
            item,
            description_raw
            or content_raw,
        )

        result.append(
            {
                "title": (
                    _clean_text(
                        title
                    )
                ),
                "summary": summary,
                "link": link,

                # Retained internally for
                # provenance/deduplication.
                # Not displayed in channel post.
                "source_url": link,

                "published_at": (
                    published_at
                ),

                "image_url": (
                    image_url
                ),
            }
        )

    return result


def _format_message(
    item: Dict[str, Any],
) -> str:
    title = _clean_text(
        item.get(
            "title"
        )
    )

    summary = _short_summary(
        item.get(
            "summary"
        )
    )

    tags = _hashtags(
        title,
        summary,
    )

    parts = [
        "🚨 فوری | نبض بازار",
        "",
        f"📰 {title}",
    ]

    if summary:
        parts.extend(
            [
                "",
                f"📌 {summary}",
            ]
        )

    parts.extend(
        [
            "",
            (
                "⚡ جدیدترین تحولات "
                "کریپتو و اقتصاد، "
                "کوتاه و سریع"
            ),
            "",
            " ".join(tags),
            "",
            (
                f"☕️ {CHANNEL_USERNAME} "
                f"| {BRAND_NAME}"
            ),
        ]
    )

    return "\n".join(
        parts
    )


async def _send_item(
    context: ContextTypes.DEFAULT_TYPE,
    channel_id: int,
    item: Dict[str, Any],
) -> None:
    text = _format_message(
        item
    )

    image_url = (
        item.get(
            "image_url"
        )
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
                "News image send failed; "
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
    Poll the official Breaking News RSS.

    First successful execution establishes
    a baseline without flooding old news.

    Later runs send only genuinely new feed
    entries, at most MAX_ITEMS_PER_RUN.

    Original source URL remains in memory
    for deduplication/provenance but is not
    displayed in the Telegram post.
    """
    global _initialized
    global _last_seen_link

    channel_id = _channel_id()

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
            "Breaking RSS fetch failed"
        )
        return

    if not items:
        return

    newest_link = (
        items[0]["link"]
    )

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

    if not baseline_found:
        # Do not flood the channel when the
        # old baseline falls out of the feed.
        _last_seen_link = (
            newest_link
        )

        logger.warning(
            "Previous RSS baseline "
            "not found; baseline refreshed"
        )
        return

    new_items = new_items[
        :MAX_ITEMS_PER_RUN
    ]

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

            # Do not advance baseline after
            # failed Telegram delivery.
            return

    _last_seen_link = (
        newest_link
    )

    logger.info(
        "Breaking News: %s "
        "new item(s) sent",
        len(new_items),
    )
import html
import json
import logging
import os
import re
import xml.etree.ElementTree as ET

from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
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

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
SEEN_FILE = BASE_DIR / "data" / "seen_news.json"


def _load_seen_links() -> set[str]:
    try:
        if SEEN_FILE.exists():
            with open(SEEN_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return set(data)
    except Exception as exc:
        logger.warning("Failed to load seen news links: %s", exc)
    return set()


def _save_seen_links(seen: set[str]) -> None:
    try:
        SEEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        # Keep only last 100 links to save space
        recent = list(seen)[-100:]
        with open(SEEN_FILE, "w", encoding="utf-8") as f:
            json.dump(recent, f, ensure_ascii=False, indent=2)
    except Exception as exc:
        logger.warning("Failed to save seen news links: %s", exc)


def _channel_id() -> Optional[int]:
    value = os.getenv(
        "NEWS_CHANNEL_ID",
        "-1004401069634",
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

    text = html.unescape(value)
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
    cleaned = _clean_text(
        value
    )

    if not cleaned:
        return ""

    if (
        len(cleaned)
        <= MAX_SUMMARY_LENGTH
    ):
        return cleaned

    cut = cleaned[
        :MAX_SUMMARY_LENGTH
    ]

    last_space = (
        cut.rfind(" ")
    )

    if last_space > 0:
        cut = cut[:last_space]

    return f"{cut}..."


def _find_text(
    element: ET.Element,
    tag_name: str,
) -> str:
    for child in element:
        if (
            child.tag.split("}")[-1]
            == tag_name
        ):
            return (
                child.text or ""
            )

    return ""


def _extract_image(
    item_element: ET.Element,
) -> str:
    for child in item_element:
        tag = (
            child.tag.split("}")[-1]
        )

        if (
            tag == "enclosure"
            and child.attrib.get(
                "type", ""
            ).startswith("image/")
        ):
            url = child.attrib.get(
                "url", ""
            ).strip()

            if url:
                return url

        if tag in {
            "content",
            "thumbnail",
        }:
            url = child.attrib.get(
                "url", ""
            ).strip()

            if url:
                return url

    description_raw = _find_text(
        item_element,
        "description",
    )

    if description_raw:
        match = re.search(
            r'<img[^>]+src=["\']([^"\']+)["\']',
            description_raw,
            re.IGNORECASE,
        )

        if match:
            url = (
                match.group(1).strip()
            )

            if url:
                return url

    return ""


def _hashtags(
    title: str,
    summary: str,
) -> List[str]:
    combined = (
        f"{title} {summary}".lower()
    )

    tags = []

    keyword_map = [
        ("بیت کوین", "#بیت_کوین"),
        ("اتریوم", "#اتریوم"),
        ("ریپل", "#ریپل"),
        ("سولانا", "#سولانا"),
        ("طلا", "#طلا"),
        ("فدرال رزرو", "#فدرال_رزرو"),
        ("پاول", "#فدرال_رزرو"),
        ("تورم", "#تورم"),
        ("نرخ بهره", "#نرخ_بهره"),
        ("ترامپ", "#ترامپ"),
        ("تحریم", "#تحریم"),
        ("صرافی", "#صرافی"),
        ("هک", "#امنیت"),
        ("دیفای", "#دیفای"),
        ("etf", "#ETF"),
        ("فارکس", "#فارکس"),
        ("اقتصاد", "#اقتصاد"),
    ]

    for (
        kw,
        tag,
    ) in keyword_map:
        if (
            kw in combined
            and tag not in tags
        ):
            tags.append(tag)

        if len(tags) >= 2:
            break

    if not tags:
        tags = [
            "#کریپتو",
            "#اقتصاد",
        ]

    elif len(tags) == 1:
        fallback = (
            "#اقتصاد"
            if tags[0] != "#اقتصاد"
            else "#کریپتو"
        )
        tags.append(fallback)

    return tags[:2]


def _fetch_feed() -> List[
    Dict[str, Any]
]:
    response = requests.get(
        RSS_URL,
        timeout=REQUEST_TIMEOUT,
        headers={
            "User-Agent": (
                "Mozilla/5.0 "
                "(Windows NT 10.0; "
                "Win64; x64) "
                "AppleWebKit/537.36"
            )
        },
    )

    response.raise_for_status()

    root = ET.fromstring(
        response.content
    )

    items: List[
        Dict[str, Any]
    ] = []

    for item in root.findall(
        ".//item"
    ):
        title = _clean_text(
            _find_text(
                item, "title"
            )
        )

        link = _clean_text(
            _find_text(
                item, "link"
            )
        )

        description = (
            _find_text(
                item,
                "description",
            )
        )

        summary = _clean_text(
            description
        )

        pub_date_raw = _clean_text(
            _find_text(
                item, "pubDate"
            )
        )

        pub_date = None

        if pub_date_raw:
            try:
                pub_date = parsedate_to_datetime(
                    pub_date_raw
                )

            except Exception:
                pub_date = None

        image_url = _extract_image(
            item
        )

        if title and link:
            items.append(
                {
                    "title": title,
                    "link": link,
                    "summary": summary,
                    "pub_date": pub_date,
                    "image_url": image_url,
                }
            )

    return items


def _format_message(
    item: Dict[str, Any],
) -> str:
    title = _clean_text(
        item.get("title")
    )

    summary = _short_summary(
        item.get("summary")
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
            "⚡ جدیدترین تحولات کریپتو و اقتصاد، کوتاه و سریع",
            "",
            " ".join(tags),
            "",
            f"☕️ {CHANNEL_USERNAME}",
        ]
    )

    return "\n".join(parts)


async def _send_item(
    context: ContextTypes.DEFAULT_TYPE,
    channel_id: int,
    item: Dict[str, Any],
) -> None:
    text = _format_message(item)

    image_url = item.get("image_url")

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
                "News image send failed; falling back to text"
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
    Poll the official Breaking News RSS hourly with disk-persisted deduplication.
    """
    channel_id = _channel_id()

    if channel_id is None:
        logger.warning("NEWS_CHANNEL_ID is missing or invalid")
        return

    try:
        items = _fetch_feed()

    except Exception:
        logger.exception("Breaking RSS fetch failed")
        return

    if not items:
        return

    seen_links = _load_seen_links()

    # If first run ever (no seen links saved at all):
    if not seen_links:
        for it in items:
            seen_links.add(it["link"])
        _save_seen_links(seen_links)
        logger.info("Initialized news seen links baseline (%d items)", len(items))
        return

    # Find new items not in seen_links
    new_items = [it for it in items if it["link"] not in seen_links]

    if not new_items:
        return

    # Send from oldest to newest among new items
    new_items.reverse()
    new_items = new_items[:MAX_ITEMS_PER_RUN]

    for item in new_items:
        try:
            await _send_item(context, channel_id, item)
            seen_links.add(item["link"])
        except Exception:
            logger.exception("Failed sending news item: %s", item.get("link"))

    _save_seen_links(seen_links)
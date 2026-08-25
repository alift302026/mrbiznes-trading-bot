import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")


BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

REQUIRED_CHANNEL = os.getenv(
    "REQUIRED_CHANNEL",
    "@MrBiznesMarket",
).strip()

REQUIRED_CHANNEL_URL = os.getenv(
    "REQUIRED_CHANNEL_URL",
    "https://t.me/MrBiznesMarket",
).strip()


def parse_admin_ids() -> set[int]:
    output = set()

    raw = os.getenv(
        "ADMIN_IDS",
        "",
    )

    for item in raw.split(","):
        item = item.strip()

        if item.isdigit():
            output.add(int(item))

    return output


ADMIN_IDS = parse_admin_ids()


WELCOME_IMAGE = (
    BASE_DIR
    / "assets"
    / "welcome.jpg"
)


if not BOT_TOKEN:
    raise RuntimeError(
        "BOT_TOKEN is missing from .env"
    )
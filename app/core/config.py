import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")


BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

# Force override if old brand metatraid is present in env variables
raw_channel = os.getenv("REQUIRED_CHANNEL", "@MrBiznesMarket").strip()
if not raw_channel or "metatraid" in raw_channel.lower():
    REQUIRED_CHANNEL = "@MrBiznesMarket"
else:
    REQUIRED_CHANNEL = raw_channel

raw_url = os.getenv("REQUIRED_CHANNEL_URL", "https://t.me/MrBiznesMarket").strip()
if not raw_url or "metatraid" in raw_url.lower():
    REQUIRED_CHANNEL_URL = "https://t.me/MrBiznesMarket"
else:
    REQUIRED_CHANNEL_URL = raw_url


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

# XT Exchange Credentials
XT_API_KEY = os.getenv("XT_API_KEY", "").strip()
XT_SECRET_KEY = os.getenv("XT_SECRET_KEY", "").strip()
XT_ACCESS_KEY = os.getenv("XT_ACCESS_KEY", XT_API_KEY).strip()

# Other API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
TWELVE_DATA_API_KEY = os.getenv("TWELVE_DATA_API_KEY", "").strip()

WELCOME_IMAGE = (
    BASE_DIR
    / "assets"
    / "welcome.jpg"
)

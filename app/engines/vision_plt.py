"""PLT - vision chart-analysis engine for MrBiznes."""
from __future__ import annotations

import base64
import json
import logging
import os
import time
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

OPENAI_URL = "https://api.openai.com/v1/chat/completions"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
TIMEOUT = 60

DEFAULT_OPENAI_MODEL = "gpt-4o"
DEFAULT_FALLBACK_MODEL = "nousresearch/hermes-4-70b"

SYSTEM_PROMPT_FA = """تو «PLT» هستی، دستیار تحلیل تکنیکال چارت برای برند مستر بیزنس.

قوانین سخت:
- فقط بر اساس چیزی که روی تصویر می‌بینی تحلیل کن؛ داده‌ی زنده نداری، پس قیمت‌ها را تقریبی و روی همان چارت بخوان و بگو «تقریبی».
- هیچ‌وقت قطعیت نفروش؛ همیشه سناریو با شرط بده (اگر/آنگاه).
- خروجی دقیقاً با همین ساختار فارسی باشد:

🧠 PLT | تحلیل چارت

۱) نقد رسم و سطوح: درستی خطوط حمایت/مقاومت کشیده‌شده را ارزیابی کن؛ اگر خط اشتباه است بگو چرا و نسخه‌ی درست را پیشنهاد بده.
۲) اندیکاتورها: RSI (وضعیت و واگرایی احتمالی)، اوسیلاتور حجم.
۳) ساختار بازار: HH/HL یا LH/LL؛ اگر کاربر چارت ۴ ساعته فرستاده، جهت روند کلی را جدا بگو.
۴) سناریوها: سناریوی اصلی (ورود | استاپ | TP1/TP2 | R:R | شرط فعال شدن) + سناریوی جایگزین.
۵) حجم و نقدینگی اگر دیده می‌شود.
۶) امتیاز کیفیت ستاپ (۰-۱۰۰) + یک خط مهم‌ترین ریسک.

⚠️ پایان‌بندی ثابت: «این تحلیل آموزشی است؛ تصمیم نهایی و مسئولیت معامله با تویی.»

اگر تصویر چارت نیست یا واضح نیست، مؤدبانه بگو چه بفرستد."""


def _b64_image(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode("ascii")


def _messages(image_bytes: bytes, hint: str) -> List[Dict[str, Any]]:
    user_text = hint.strip() or "این چارت را تحلیل کن."
    return [
        {"role": "system", "content": SYSTEM_PROMPT_FA},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": user_text},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{_b64_image(image_bytes)}",
                        "detail": "high",
                    },
                },
            ],
        },
    ]


def _call_openai(image_bytes: bytes, hint: str) -> str:
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        raise RuntimeError("OPENAI_API_KEY missing")
    model = os.getenv("PLT_OPENAI_MODEL", DEFAULT_OPENAI_MODEL)
    resp = requests.post(
        OPENAI_URL,
        headers={"Authorization": f"Bearer {key}"},
        json={
            "model": model,
            "messages": _messages(image_bytes, hint),
            "max_tokens": 1400,
            "temperature": 0.2,
        },
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]


def _call_openrouter(image_bytes: bytes, hint: str) -> str:
    key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY missing")
    model = os.getenv("PLT_FALLBACK_MODEL", DEFAULT_FALLBACK_MODEL)
    resp = requests.post(
        OPENROUTER_URL,
        headers={
            "Authorization": f"Bearer {key}",
            "HTTP-Referer": "https://t.me/MrBiznesMarket",
            "X-Title": "MrBiznes PLT",
        },
        json={
            "model": model,
            "messages": _messages(image_bytes, hint),
            "max_tokens": 1400,
            "temperature": 0.2,
        },
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]


def analyze_chart(image_bytes: bytes, hint: str = "") -> str:
    started = time.time()
    try:
        out = _call_openai(image_bytes, hint)
        logger.info("PLT: OpenAI vision OK in %.1fs", time.time() - started)
        return out
    except Exception as exc:
        logger.warning("PLT OpenAI failed (%s) - trying fallback", exc)

    try:
        out = _call_openrouter(image_bytes, hint)
        logger.info("PLT: fallback OK in %.1fs", time.time() - started)
        return out
    except Exception as exc:
        logger.warning("PLT fallback failed: %s", exc)

    return (
        "🧠 PLT\n\n"
        "الان موتور تحلیل در دسترس نیست (خطای سرویس هوش مصنوعی).\n"
        "چند دقیقه‌ی دیگر دوباره عکس را بفرست. 🙏"
    )

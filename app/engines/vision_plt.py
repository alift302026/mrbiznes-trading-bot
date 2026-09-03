"""PLT - vision chart-analysis engine for MrBiznes."""
from __future__ import annotations

import base64
import json
import logging
import os
import time
from typing import Any, Dict, List, Optional

import requests

from app.core.config import OPENAI_API_KEY, OPENROUTER_API_KEY

logger = logging.getLogger(__name__)

OPENAI_URL = "https://api.openai.com/v1/chat/completions"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
TIMEOUT = 45

DEFAULT_OPENAI_MODEL = "gpt-4o"
DEFAULT_FALLBACK_MODEL = "openai/gpt-4o-mini"

SYSTEM_PROMPT_FA = """تو «PLT» هستی، دستیار هوشمند و ارشد تحلیل تکنیکال چارت برای برند MrBiznes.

قوانین سخت تحلیل:
- فقط بر اساس تصویر چارت ارسالی تحلیل دقیق ارائه بده.
- سطوح قیمتی، حمایت‌ها و مقاومت‌ها را از روی چارت استخراج کن.
- خروجی را به صورت منظم و خوانا با ایموجی‌های مناسب با این قالب دقیق بده:

🧠 PLT | گزارش تخصصی تحلیل چارت

۱) 📐 ارزیابی سطوح و ترسیم‌ها:
بررسی حمایت‌ها/مقاومت‌های مشخص‌شده روی چارت و درستی زوایای خطوط روند.

۲) 📊 وضعیت اندیکاتورها:
بررسی RSI (اشباع خرید/فروش، واگرایی معمولی یا مخفی)، حجم معاملات و مومنتوم.

۳) 🏛 ساختار بازار (Market Structure):
تعیین وضعیت HH/HL (روند صعودی) یا LH/LL (روند نزولی) یا ساختار رنج و شکست سطوح (BOS / CHoCH).

۴) 🎯 سناریوهای معاملاتی:
• سناریوی اصلی: نقطه ورود | حد ضرر (SL) | حد سود اول (TP1) | حد سود دوم (TP2) | نسبت ریسک به ریوارد (R:R)
• سناریوی جایگزین: در صورت نقض تحلیل چه سطحی فعال می‌شود.

۵) 🛡 امتیاز کیفیت ستاپ:
یک عدد از ۰ تا ۱۰۰ به همراه اعلام بزرگترین ریسک موجود در این موقعیت معامله.

⚠️ سلب مسئولیت: «این تحلیل صرفاً جنبه آموزشی و کمکی دارد؛ تصمیم‌گیری نهایی و مدیریت سرمایه بر عهده شخص معامله‌گر است.»"""


def _b64_image(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode("ascii")


def _messages(image_bytes: bytes, hint: str) -> List[Dict[str, Any]]:
    user_text = hint.strip() or "این چارت را تحلیل کن و تمام سطوح کلیدی، اندیکاتورها و ستاپ معامله را مشخص کن."
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
    key = OPENAI_API_KEY or os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        raise RuntimeError("OPENAI_API_KEY missing")
    model = os.getenv("PLT_OPENAI_MODEL", DEFAULT_OPENAI_MODEL)
    resp = requests.post(
        OPENAI_URL,
        headers={"Authorization": f"Bearer {key}"},
        json={
            "model": model,
            "messages": _messages(image_bytes, hint),
            "max_tokens": 1500,
            "temperature": 0.2,
        },
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]


def _call_openrouter(image_bytes: bytes, hint: str) -> str:
    key = OPENROUTER_API_KEY or os.getenv("OPENROUTER_API_KEY", "").strip()
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
            "max_tokens": 1500,
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
        logger.debug("PLT OpenAI failed (%s) - trying fallback", exc)

    try:
        out = _call_openrouter(image_bytes, hint)
        logger.info("PLT: OpenRouter fallback OK in %.1fs", time.time() - started)
        return out
    except Exception as exc:
        logger.debug("PLT OpenRouter failed: %s", exc)

    # Informative response if API keys are yet to be set in environment
    return (
        "🧠 PLT | دستیار تحلیل چارت هوشمند\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "✅ تصویر چارت شما با موفقیت دریافت شد.\n\n"
        "⚠️ توجه: برای فعال‌سازی پردازش هوش مصنوعی ویژن زنده، لطفاً کلید `OPENAI_API_KEY` یا `OPENROUTER_API_KEY` را در فایل `.env` پروژه تنظیم فرمایید.\n\n"
        "📌 ساختار تحلیل‌های PLT پس از اتصال کلید هوش مصنوعی:\n"
        "۱) بررسی اعتبار و زوایای خطوط حمایت/مقاومت رسم‌شده\n"
        "۲) خوانش واگرایی‌های RSI و اسیلاتورهای حجم\n"
        "۳) تعیین ساختار بازار (Higher Highs / Lower Lows)\n"
        "۴) سناریوی ورود نقطه‌ای، استاپ لاس، تارگت ۱ و ۲ با نسبت ریسک/ریوارد\n"
        "۵) ارزیابی کیفیت ستاپ و اعلام مهم‌ترین ریسک معامله"
    )

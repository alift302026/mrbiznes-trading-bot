"""Regression: welcome text must be Persian-only (no Latin sentences)."""

import re

from app.bot.welcome_handlers import WELCOME_TEXT


def _latin_words(text):
    return re.findall(r"[A-Za-z]{2,}", text)


def test_no_english_quote():
    assert "Goodness" not in WELCOME_TEXT
    assert "investment" not in WELCOME_TEXT
    assert "never fails" not in WELCOME_TEXT


def test_no_english_feature_lines():
    for word in ("Markets", "Signals", "Alerts", "News", "Watchlists", "Trading"):
        assert word not in WELCOME_TEXT


def test_only_allowed_latin_word_is_brand():
    # only the brand name and the universal "VIP" term may stay in Latin
    latin = set(_latin_words(WELCOME_TEXT))
    assert latin <= {"MrBiznes", "VIP"}, f"unexpected Latin words: {latin}"


def test_persian_quote_present():
    assert "سرمایه‌گذاری" in WELCOME_TEXT
    assert "شکست نمی‌خورد" in WELCOME_TEXT


def test_disclaimer_present():
    assert "آموزشی" in WELCOME_TEXT

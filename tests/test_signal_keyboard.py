"""Regression: removed signal-center buttons must stay gone.

User request: the main signal keyboard must NOT contain
- "⚡ سیگنال‌های نهایی S4 (خودکار ساعتی)"  (signal_final_home)
- "🎯 برترین ستاپ‌ها"                      (signal_top_setups)
- "⚡ فعالیت غیرعادی"                      (signal_activity)
"""

from app.bot.signal_handlers import _main_keyboard

REMOVED_CALLBACKS = {
    "signal_final_home",
    "signal_top_setups",
    "signal_activity",
}


def _all_callback_data(markup):
    for row in markup.inline_keyboard:
        for button in row:
            yield button.callback_data


def test_removed_buttons_are_gone():
    markup = _main_keyboard()
    callbacks = set(_all_callback_data(markup))

    assert not (callbacks & REMOVED_CALLBACKS), (
        f"removed buttons re-appeared: {callbacks & REMOVED_CALLBACKS}"
    )


def test_core_buttons_still_present():
    markup = _main_keyboard()
    callbacks = set(_all_callback_data(markup))

    for expected in (
        "signal_winners",
        "signal_losers",
        "signal_volume",
        "signal_momentum",
        "signal_home",
    ):
        assert expected in callbacks, f"missing button: {expected}"


def test_welcome_caption_has_no_final_s4_ads():
    from app.bot.welcome_handlers import WELCOME_TEXT

    assert "S4" not in WELCOME_TEXT

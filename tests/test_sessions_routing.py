"""Regression: the "سشن‌های بازار" menu button must open SESSIONS, not MARKETS.

The sessions button text contains the word "بازار", so a market-first
keyword router made sessions unreachable (looked like sessions were
merged into / deleted by markets). The router must check sessions
before markets.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

import main


class FakeMessage:
    def __init__(self, text):
        self.text = text
        self.reply_text = AsyncMock()
        self.reply_photo = AsyncMock()


def _make_update(text):
    update = MagicMock()
    update.message = FakeMessage(text)
    update.effective_user.id = 424242
    update.effective_user.username = "tester"
    return update


def _make_context():
    context = MagicMock()
    context.user_data = {}
    return context


@pytest.fixture
def wired_router(monkeypatch):
    """Patch main.menu_router's collaborators; return dict of recorded calls."""
    calls = {"market": 0, "sessions": 0}

    async def fake_require_channel(update, context):
        return True

    fake_user = MagicMock()
    fake_user.is_banned = False

    async def fake_sessions_page(update, context):
        calls["sessions"] += 1

    async def fake_market_home(update, context):
        calls["market"] += 1

    async def fake_signal_center(update, context):
        pass

    async def fake_plt_entry(update, context):
        pass

    async def fake_journal_home(update, context):
        pass

    async def fake_alerts_home(update, context):
        pass

    monkeypatch.setattr(main, "require_channel", fake_require_channel)
    monkeypatch.setattr(main, "get_user", lambda tid: fake_user)
    monkeypatch.setattr(main, "sessions_page", fake_sessions_page)
    monkeypatch.setattr(main, "market_home", fake_market_home)
    monkeypatch.setattr(main, "signal_center", fake_signal_center)
    monkeypatch.setattr(main, "plt_entry", fake_plt_entry)
    monkeypatch.setattr(main, "journal_home", fake_journal_home)
    monkeypatch.setattr(main, "alerts_home", fake_alerts_home)
    return calls


@pytest.mark.asyncio
async def test_sessions_button_opens_sessions_not_markets(wired_router):
    update = _make_update("🌍 سشن‌های بازار")
    context = _make_context()

    await main.menu_router(update, context)

    assert wired_router["sessions"] == 1, (
        "sessions button must open the sessions page"
    )
    assert wired_router["market"] == 0, (
        "sessions button must NOT be swallowed by the markets handler"
    )


@pytest.mark.asyncio
async def test_markets_button_still_opens_markets(wired_router):
    update = _make_update("📊 بازارها")
    context = _make_context()

    await main.menu_router(update, context)

    assert wired_router["market"] == 1
    assert wired_router["sessions"] == 0


@pytest.mark.asyncio
async def test_english_sessions_word_routes_to_sessions(wired_router):
    update = _make_update("trading sessions")
    context = _make_context()

    await main.menu_router(update, context)

    assert wired_router["sessions"] == 1
    assert wired_router["market"] == 0


# ============================================================
# menu layout / markets page button
# ============================================================

def test_main_menu_has_sessions_button():
    markup = main.main_menu("fa", admin=False)
    rows = markup.keyboard
    texts = [btn for row in rows for btn in row]
    assert any("سشن" in btn.text for btn in texts), (
        "main menu must contain the sessions button"
    )


def test_sessions_button_is_above_middle():
    """User asked for the sessions button to be raised in the menu."""
    markup = main.main_menu("fa", admin=False)
    rows = markup.keyboard
    session_row_index = next(
        i for i, row in enumerate(rows)
        if any("سشن" in btn.text for btn in row)
    )
    assert session_row_index <= 1, (
        f"sessions button is on row {session_row_index}; expected in the top half"
    )


def test_markets_page_keyboard_has_sessions_button_on_top():
    from app.bot.market_handlers import market_keyboard

    markup = market_keyboard()
    first_button = markup.inline_keyboard[0][0]
    assert "سشن" in first_button.text
    assert first_button.callback_data == "session_home"


def test_router_source_checks_sessions_before_market():
    import inspect
    source = inspect.getsource(main.menu_router)
    sessions_pos = source.find('if "سشن" in text')
    market_pos = source.find('if "بازار" in text')
    assert sessions_pos != -1 and market_pos != -1
    assert sessions_pos < market_pos, (
        "router must check سشن before بازار"
    )

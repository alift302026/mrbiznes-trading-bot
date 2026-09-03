"""Regression test for the `clear_payment_input` NameError.

Before the fix, typing a main-menu button text (or a cancel word)
during an active payment flow crashed with NameError.
"""

import asyncio

from app.bot.payment_handlers import payment_message


class FakeMessage:

    def __init__(self, text):
        self.text = text
        self.replies = []

    async def reply_text(self, text, **kwargs):
        self.replies.append(text)


class FakeUser:

    id = 424242


class FakeUpdate:

    def __init__(self, message):
        self.message = message
        self.effective_user = FakeUser()


class FakeContext:

    def __init__(self):
        self.user_data = {}


def _run(text, with_pending_flow=True):
    context = FakeContext()
    if with_pending_flow:
        context.user_data["payment_flow"] = {"bank_key": "melal"}
        context.user_data["payment_input"] = {"mode": "bank_amount"}

    message = FakeMessage(text)
    result = asyncio.run(payment_message(FakeUpdate(message), context))
    return result, context, message


def test_cancel_word_no_name_error():
    result, context, message = _run("انصراف")

    assert result is True
    assert "payment_input" not in context.user_data
    assert "payment_flow" not in context.user_data
    assert message.replies  # user got a cancellation confirmation


def test_menu_button_text_no_name_error():
    result, context, _ = _run("📊 بازارها")

    assert result is False
    assert "payment_input" not in context.user_data
    assert "payment_flow" not in context.user_data


def test_slash_command_no_name_error():
    result, context, _ = _run("/start")

    assert result is False
    assert "payment_input" not in context.user_data


def test_normal_payment_text_still_routed():
    # amount input inside an active flow must NOT be swallowed
    result, context, message = _run("8500000")

    assert result is True
    assert context.user_data["payment_input"]["mode"] == "bank_tracking"
    assert message.replies


def test_no_pending_flow_returns_false():
    result, context, _ = _run("hello", with_pending_flow=False)
    assert result is False

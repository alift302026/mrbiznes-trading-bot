"""Regression: the old welcome card must stay removed.

User request: on /start, the quote/feature/disclaimer card
(photo caption from app.bot.welcome_handlers, English quote
"Goodness is the only investment...", Markets/News/... lines)
must NEVER be sent again. Only the main-menu greeting remains.
"""

import inspect
import pathlib

import main

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent


def test_start_does_not_call_send_welcome():
    source = inspect.getsource(main.start)
    assert "send_welcome" not in source
    assert "welcome_handlers" not in source


def test_main_does_not_import_welcome_handlers():
    source = pathlib.Path(main.__file__).read_text(encoding="utf-8")
    assert "welcome_handlers" not in source


def test_welcome_handlers_module_is_gone():
    module_path = REPO_ROOT / "app" / "bot" / "welcome_handlers.py"
    assert not module_path.exists(), "welcome card module was re-added"

"""Integration test: build_application() must wire every worker & handler.

Regression coverage:
- final-signal worker must be registered (was silently dead before)
- /signalpreview command must be registered
- news workers are registered only when NEWS_CHANNEL_ID is configured
- signal_ callback pattern must be anchored (^) so it cannot
  swallow unrelated callback_data like "market_signal_home"
"""

import os

from telegram.ext import CallbackQueryHandler, CommandHandler

import main


def _build(monkeypatch=None, news_channel=None):
    if monkeypatch is not None:
        if news_channel is None:
            monkeypatch.delenv("NEWS_CHANNEL_ID", raising=False)
        else:
            monkeypatch.setenv("NEWS_CHANNEL_ID", news_channel)
    return main.build_application()


def _commands(app):
    names = set()
    for handlers in app.handlers.values():
        for h in handlers:
            if isinstance(h, CommandHandler):
                names |= set(h.commands)
    return names


def _callback_handler(app, callback_name):
    for handlers in app.handlers.values():
        for h in handlers:
            if isinstance(h, CallbackQueryHandler):
                cb = h.callback
                if getattr(cb, "__name__", "") == callback_name:
                    return h
    return None


# ============================================================
# HANDLERS
# ============================================================

def test_core_commands_registered():
    app = _build()
    commands = _commands(app)
    assert "start" in commands
    assert "payments" in commands
    assert "givevip" in commands
    assert "removevip" in commands


def test_signalpreview_command_registered():
    app = _build()
    assert "signalpreview" in _commands(app)


def test_error_handler_registered():
    app = _build()
    assert app.error_handlers


# ============================================================
# SIGNAL CALLBACK PATTERN
# ============================================================

def test_signal_pattern_is_anchored():
    app = _build()
    handler = _callback_handler(app, "signal_callback")
    assert handler is not None, "signal_callback is not registered"

    pattern = handler.pattern
    assert pattern.pattern.startswith("^"), "signal pattern must be anchored with ^"

    assert pattern.match("signal_home")
    assert pattern.match("signal_final_list")
    # must NOT swallow foreign callback data containing "signal_"
    assert not pattern.match("market_signal_home")
    assert not pattern.match("alert_signal_toggle")


# ============================================================
# JOB QUEUE WORKERS
# ============================================================

def test_all_background_workers_registered():
    app = _build()
    job_names = {job.name for job in app.job_queue.jobs()}

    assert "session-alert-engine" in job_names
    assert "market-alert-worker" in job_names
    assert "economic-calendar-sync-worker" in job_names
    assert "final-signal-worker" in job_names


def test_news_workers_off_without_channel(monkeypatch):
    app = _build(monkeypatch, news_channel=None)
    job_names = {job.name for job in app.job_queue.jobs()}

    assert "arzdigital-breaking-worker" not in job_names
    assert "wallex-news-worker" not in job_names


def test_news_workers_on_with_channel(monkeypatch):
    app = _build(monkeypatch, news_channel="-1001234567890")
    job_names = {job.name for job in app.job_queue.jobs()}

    assert "arzdigital-breaking-worker" in job_names
    assert "wallex-news-worker" in job_names


def test_final_signal_worker_is_hourly():
    app = _build()
    for job in app.job_queue.jobs():
        if job.name == "final-signal-worker":
            trigger = getattr(job, "trigger", None)
            interval = getattr(trigger, "interval", None)
            assert interval is not None, "final-signal-worker has no interval trigger"
            assert interval.total_seconds() == 3600
            return
    raise AssertionError("final-signal-worker not found")

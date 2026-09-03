"""Shared pytest configuration.

Environment variables must be set BEFORE any `app.*` import,
because `app.core.config` reads them at import time.
"""

import os

os.environ.setdefault("BOT_TOKEN", "123456789:PYTEST_FAKE_TOKEN")
os.environ.setdefault("NEWS_CHANNEL_ID", "")

import pytest

from app.models.database import Base, engine


@pytest.fixture(autouse=True)
def clean_db():
    """Fresh empty database for every test."""

    Base.metadata.create_all(bind=engine)

    yield

    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())

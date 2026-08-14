from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    Integer,
    String,
    Text,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from .database import Base


class EconomicEvent(Base):

    __tablename__ = "economic_events"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    # Example: US CPI / FOMC / NFP
    title: Mapped[str] = mapped_column(
        String(300),
        nullable=False,
        index=True,
    )

    title_fa: Mapped[str | None] = mapped_column(
        String(300),
        nullable=True,
    )

    country: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        index=True,
    )

    currency: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
        index=True,
    )

    category: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
    )

    # low / medium / high
    importance: Mapped[str] = mapped_column(
        String(20),
        default="medium",
        nullable=False,
        index=True,
    )

    previous: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    forecast: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    actual: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # Always store event time in UTC.
    event_time: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        index=True,
    )

    source: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    source_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Prevent duplicate provider events when possible.
    external_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
        index=True,
    )

    is_published: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    is_cancelled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
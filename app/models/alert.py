from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    Integer,
    String,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from .database import Base


class MarketAlert(Base):
    __tablename__ = "market_alerts"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        index=True,
    )

    symbol: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )

    alert_type: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
    )

    timeframe: Mapped[str] = mapped_column(
        String(10),
        default="1h",
        nullable=False,
    )

    target_value: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    last_state: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    last_triggered_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    trigger_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
from datetime import datetime

from sqlalchemy import (
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


class MonthlyPerformance(Base):
    __tablename__ = "monthly_performance"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    year: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    month: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    signal_type: Mapped[str] = mapped_column(
        String(30),
        default="all",
    )

    total_signals: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    wins: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    losses: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    breakeven: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    return_percent: Mapped[float] = mapped_column(
        Float,
        default=0.0,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )
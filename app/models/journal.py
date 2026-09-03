from datetime import datetime

from sqlalchemy import (
    BigInteger,
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


class TradeJournal(Base):
    __tablename__ = "trade_journal"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        index=True,
        nullable=False,
    )

    symbol: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    direction: Mapped[str] = mapped_column(
        String(20),
        default="LONG",
        nullable=False,
    )

    entry_price: Mapped[float] = mapped_column(
        Float,
        nullable=True,
    )

    exit_price: Mapped[float] = mapped_column(
        Float,
        nullable=True,
    )

    pnl_percent: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )

    pnl_amount: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="WIN",
        nullable=False,
    )

    strategy_source: Mapped[str] = mapped_column(
        String(100),
        default="سیگنال مستر بیزنس",
        nullable=True,
    )

    notes: Mapped[str] = mapped_column(
        Text,
        default="",
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )

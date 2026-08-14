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


class Payment(Base):
    __tablename__ = "payments"

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

    # crypto / bank
    payment_method: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        index=True,
    )

    # VIP duration
    plan_days: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    # Expected price in USDT
    plan_price: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    # BTC / USDT / BNB / SOL / TRX / IRR
    asset: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    # Bitcoin / TRC20 / BEP20 / Solana / BANK
    network: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    # Amount user reports/sends
    amount: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    # Crypto TXID or bank tracking/reference code
    txid: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
        index=True,
    )

    # Optional bank/card identifier used for payment
    destination: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # pending / confirmed / rejected
    status: Mapped[str] = mapped_column(
        String(30),
        default="pending",
        nullable=False,
        index=True,
    )

    # Optional user note / receipt file_id / admin note
    details: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    reviewed_by: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )
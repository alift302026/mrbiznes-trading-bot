from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Integer,
    String,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from .database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        nullable=False,
        index=True,
    )

    username: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    first_name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # ورود عادی نیازی به شماره ندارد
    phone_number: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    # None یعنی هنوز زبان انتخاب نشده
    language: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    membership_type: Mapped[str] = mapped_column(
        String(20),
        default="normal",
        nullable=False,
    )

    vip_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    referral_code: Mapped[str | None] = mapped_column(
        String(32),
        unique=True,
        nullable=True,
        index=True,
    )

    referred_by: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
    )

    points: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    session_alerts_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    is_registered: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    is_banned: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
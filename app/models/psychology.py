from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Integer,
    String,
    Text,
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from .database import Base


class PsychologyAssessment(Base):
    __tablename__ = "psychology_assessments"

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

    mental_score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    cognitive_score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    discipline_score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    emotion_score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    overall_score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    level: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    critical_flag: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    critical_reasons: Mapped[str] = mapped_column(
        Text,
        default="[]",
        nullable=False,
    )

    question_set: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    answers: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )


class EndOfDayCheck(Base):
    __tablename__ = "psychology_eod_checks"

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

    followed_plan: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )

    respected_stop: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )

    emotional_trade: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )
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


# ============================================================
# ASSET MARKET SNAPSHOT
# ============================================================

class AssetMarketSnapshot(Base):

    __tablename__ = (
        "asset_market_snapshots"
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    symbol: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )

    market: Mapped[str] = mapped_column(
        String(20),
        default="crypto",
        nullable=False,
        index=True,
    )

    price: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    change_24h: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    volume_24h: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    quote_volume_24h: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    captured_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )


# ============================================================
# EXCHANGE FLOW
# ============================================================

class ExchangeFlowSnapshot(Base):

    __tablename__ = (
        "exchange_flow_snapshots"
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    asset: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )

    exchange: Mapped[str] = mapped_column(
        String(50),
        default="all",
        nullable=False,
        index=True,
    )

    timeframe: Mapped[str] = mapped_column(
        String(20),
        default="24h",
        nullable=False,
        index=True,
    )

    inflow: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    outflow: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    netflow: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    reserve: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    source: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    captured_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )


# ============================================================
# WHALE TRANSFER
# ============================================================

class WhaleTransfer(Base):

    __tablename__ = (
        "whale_transfers"
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    asset: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )

    amount: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    usd_value: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    direction: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )

    exchange: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    tx_hash: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
    )

    source: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    occurred_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
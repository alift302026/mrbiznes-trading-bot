from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import delete, desc, func, select

from app.models.database import SessionLocal
from app.models.journal import TradeJournal


def add_trade(
    telegram_id: int,
    symbol: str,
    direction: str = "LONG",
    pnl_percent: float = 0.0,
    pnl_amount: float = 0.0,
    entry_price: Optional[float] = None,
    exit_price: Optional[float] = None,
    status: Optional[str] = None,
    strategy_source: str = "سیگنال ربات",
    notes: str = "",
) -> TradeJournal:
    symbol = symbol.strip().upper()
    direction = direction.strip().upper()

    if status is None:
        if pnl_percent > 0 or pnl_amount > 0:
            status = "WIN"
        elif pnl_percent < 0 or pnl_amount < 0:
            status = "LOSS"
        else:
            status = "BREAKEVEN"

    with SessionLocal() as db:
        item = TradeJournal(
            telegram_id=telegram_id,
            symbol=symbol,
            direction=direction,
            entry_price=entry_price,
            exit_price=exit_price,
            pnl_percent=pnl_percent,
            pnl_amount=pnl_amount,
            status=status,
            strategy_source=strategy_source,
            notes=notes,
            created_at=datetime.utcnow(),
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return item


def get_user_trades(telegram_id: int, limit: int = 20, offset: int = 0) -> List[TradeJournal]:
    with SessionLocal() as db:
        return list(
            db.scalars(
                select(TradeJournal)
                .where(TradeJournal.telegram_id == telegram_id)
                .order_by(desc(TradeJournal.created_at))
                .offset(offset)
                .limit(limit)
            ).all()
        )


def get_trade_by_id(trade_id: int, telegram_id: int) -> Optional[TradeJournal]:
    with SessionLocal() as db:
        return db.scalar(
            select(TradeJournal).where(
                TradeJournal.id == trade_id,
                TradeJournal.telegram_id == telegram_id,
            )
        )


def delete_trade(trade_id: int, telegram_id: int) -> bool:
    with SessionLocal() as db:
        result = db.execute(
            delete(TradeJournal).where(
                TradeJournal.id == trade_id,
                TradeJournal.telegram_id == telegram_id,
            )
        )
        db.commit()
        return result.rowcount > 0


def clear_user_trades(telegram_id: int) -> int:
    with SessionLocal() as db:
        result = db.execute(
            delete(TradeJournal).where(TradeJournal.telegram_id == telegram_id)
        )
        db.commit()
        return result.rowcount


def get_journal_stats(telegram_id: int) -> Dict[str, Any]:
    with SessionLocal() as db:
        trades = list(
            db.scalars(
                select(TradeJournal).where(TradeJournal.telegram_id == telegram_id)
            ).all()
        )

    if not trades:
        return {
            "total_trades": 0,
            "wins": 0,
            "losses": 0,
            "breakeven": 0,
            "win_rate": 0.0,
            "total_pnl_percent": 0.0,
            "total_pnl_amount": 0.0,
            "best_trade": 0.0,
            "worst_trade": 0.0,
            "profit_factor": 0.0,
        }

    total = len(trades)
    wins = sum(1 for t in trades if t.pnl_percent > 0 or t.status == "WIN")
    losses = sum(1 for t in trades if t.pnl_percent < 0 or t.status == "LOSS")
    breakeven = total - (wins + losses)

    decided = wins + losses
    win_rate = round((wins / decided * 100), 1) if decided > 0 else 0.0

    total_pnl_percent = sum(t.pnl_percent or 0.0 for t in trades)
    total_pnl_amount = sum(t.pnl_amount or 0.0 for t in trades)

    best_trade = max((t.pnl_percent or 0.0 for t in trades), default=0.0)
    worst_trade = min((t.pnl_percent or 0.0 for t in trades), default=0.0)

    total_win_amount = sum(t.pnl_percent for t in trades if t.pnl_percent > 0)
    total_loss_amount = abs(sum(t.pnl_percent for t in trades if t.pnl_percent < 0))

    profit_factor = (
        round(total_win_amount / total_loss_amount, 2)
        if total_loss_amount > 0
        else (total_win_amount if total_win_amount > 0 else 1.0)
    )

    return {
        "total_trades": total,
        "wins": wins,
        "losses": losses,
        "breakeven": breakeven,
        "win_rate": win_rate,
        "total_pnl_percent": round(total_pnl_percent, 2),
        "total_pnl_amount": round(total_pnl_amount, 2),
        "best_trade": round(best_trade, 2),
        "worst_trade": round(worst_trade, 2),
        "profit_factor": profit_factor,
    }

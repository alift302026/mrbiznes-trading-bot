from datetime import (
    datetime,
)

from sqlalchemy import (
    desc,
    func,
    select,
)

from app.models.database import (
    SessionLocal,
)

from app.models.performance import (
    MonthlyPerformance,
)


# ============================================================
# MONTH NAME
# ============================================================

MONTH_NAMES = {
    1: "January",
    2: "February",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December",
}


# ============================================================
# WIN RATE
# ============================================================

def calculate_win_rate(
    wins,
    losses,
    breakeven=0,
):

    decided = (
        (wins or 0)
        + (losses or 0)
    )

    if decided <= 0:
        return 0.0

    return round(
        (
            (wins or 0)
            / decided
        )
        * 100,
        2,
    )


# ============================================================
# CURRENT MONTH
# ============================================================

def current_period():

    now = datetime.utcnow()

    return (
        now.year,
        now.month,
    )


# ============================================================
# MONTH PERFORMANCE
# ============================================================

def month_performance(
    year,
    month,
):

    with SessionLocal() as db:

        return list(
            db.scalars(
                select(
                    MonthlyPerformance
                )
                .where(
                    MonthlyPerformance.year
                    == int(year),

                    MonthlyPerformance.month
                    == int(month),
                )
                .order_by(
                    MonthlyPerformance.signal_type
                    .asc()
                )
            ).all()
        )


# ============================================================
# CURRENT MONTH PERFORMANCE
# ============================================================

def current_month_performance():

    year, month = (
        current_period()
    )

    return month_performance(
        year,
        month,
    )


# ============================================================
# AVAILABLE MONTHS
# ============================================================

def available_months(
    limit=12,
):

    with SessionLocal() as db:

        rows = db.execute(
            select(
                MonthlyPerformance.year,
                MonthlyPerformance.month,
            )
            .distinct()
            .order_by(
                MonthlyPerformance.year.desc(),
                MonthlyPerformance.month.desc(),
            )
            .limit(limit)
        ).all()

        return [
            (
                int(year),
                int(month),
            )
            for year, month
            in rows
        ]


# ============================================================
# MONTH SUMMARY
# ============================================================

def month_summary(
    year,
    month,
):

    items = month_performance(
        year,
        month,
    )

    total = sum(
        item.total_signals or 0
        for item in items
    )

    wins = sum(
        item.wins or 0
        for item in items
    )

    losses = sum(
        item.losses or 0
        for item in items
    )

    breakeven = sum(
        item.breakeven or 0
        for item in items
    )

    total_return = sum(
        item.return_percent or 0.0
        for item in items
    )

    return {
        "year":
            int(year),

        "month":
            int(month),

        "items":
            items,

        "total":
            total,

        "wins":
            wins,

        "losses":
            losses,

        "breakeven":
            breakeven,

        "win_rate":
            calculate_win_rate(
                wins,
                losses,
                breakeven,
            ),

        "return_percent":
            round(
                total_return,
                2,
            ),
    }


# ============================================================
# ALL TIME
# ============================================================

def all_time_summary():

    with SessionLocal() as db:

        total = (
            db.scalar(
                select(
                    func.sum(
                        MonthlyPerformance.total_signals
                    )
                )
            )
            or 0
        )

        wins = (
            db.scalar(
                select(
                    func.sum(
                        MonthlyPerformance.wins
                    )
                )
            )
            or 0
        )

        losses = (
            db.scalar(
                select(
                    func.sum(
                        MonthlyPerformance.losses
                    )
                )
            )
            or 0
        )

        breakeven = (
            db.scalar(
                select(
                    func.sum(
                        MonthlyPerformance.breakeven
                    )
                )
            )
            or 0
        )

        total_return = (
            db.scalar(
                select(
                    func.sum(
                        MonthlyPerformance.return_percent
                    )
                )
            )
            or 0.0
        )

    return {
        "total":
            int(total),

        "wins":
            int(wins),

        "losses":
            int(losses),

        "breakeven":
            int(breakeven),

        "win_rate":
            calculate_win_rate(
                wins,
                losses,
                breakeven,
            ),

        "return_percent":
            round(
                float(
                    total_return
                ),
                2,
            ),
    }


# ============================================================
# UPSERT PERFORMANCE
# Used later by Signal Engine/Admin.
# ============================================================

def upsert_performance(
    year,
    month,
    signal_type,
    total_signals,
    wins,
    losses,
    breakeven,
    return_percent,
):

    year = int(year)
    month = int(month)

    if not (
        1 <= month <= 12
    ):
        raise ValueError(
            "Invalid month"
        )

    signal_type = (
        str(signal_type)
        .strip()
        .lower()
    )

    if not signal_type:
        raise ValueError(
            "Invalid signal type"
        )

    total_signals = max(
        0,
        int(total_signals),
    )

    wins = max(
        0,
        int(wins),
    )

    losses = max(
        0,
        int(losses),
    )

    breakeven = max(
        0,
        int(breakeven),
    )

    return_percent = float(
        return_percent
    )

    with SessionLocal() as db:

        item = db.scalar(
            select(
                MonthlyPerformance
            ).where(
                MonthlyPerformance.year
                == year,

                MonthlyPerformance.month
                == month,

                MonthlyPerformance.signal_type
                == signal_type,
            )
        )

        if item is None:

            item = MonthlyPerformance(
                year=year,
                month=month,
                signal_type=signal_type,
                total_signals=total_signals,
                wins=wins,
                losses=losses,
                breakeven=breakeven,
                return_percent=return_percent,
            )

            db.add(
                item
            )

        else:

            item.total_signals = (
                total_signals
            )

            item.wins = wins
            item.losses = losses

            item.breakeven = (
                breakeven
            )

            item.return_percent = (
                return_percent
            )

            item.updated_at = (
                datetime.utcnow()
            )

        db.commit()
        db.refresh(item)

        return item
from datetime import (
    datetime,
)

from sqlalchemy import (
    func,
    select,
)

from app.core.config import (
    ADMIN_IDS,
)

from app.models.database import (
    SessionLocal,
)

from app.models.search_usage import (
    SearchUsage,
)

from app.models.user import (
    User,
)


NORMAL_CRYPTO_SEARCH_LIMIT = 3


# ============================================================
# MONTH RANGE
# ============================================================

def current_month_range():

    now = datetime.utcnow()

    start = datetime(
        now.year,
        now.month,
        1,
    )

    if now.month == 12:

        end = datetime(
            now.year + 1,
            1,
            1,
        )

    else:

        end = datetime(
            now.year,
            now.month + 1,
            1,
        )

    return (
        start,
        end,
    )


# ============================================================
# PLAN
# ============================================================

def get_plan(
    telegram_id,
):

    if telegram_id in ADMIN_IDS:

        return {
            "plan": "admin",
            "unlimited": True,
        }

    with SessionLocal() as db:

        user = db.scalar(
            select(
                User
            ).where(
                User.telegram_id
                == telegram_id
            )
        )

        if user is None:

            return {
                "plan": "normal",
                "unlimited": False,
            }

        membership = (
            user.membership_type
            or "normal"
        ).lower()

        if membership == "vip":

            return {
                "plan": "vip",
                "unlimited": True,
            }

        return {
            "plan": "normal",
            "unlimited": False,
        }


# ============================================================
# MONTHLY USAGE
# ============================================================

def monthly_search_count(
    telegram_id,
    search_type="crypto",
):

    start, end = (
        current_month_range()
    )

    with SessionLocal() as db:

        count = db.scalar(
            select(
                func.count(
                    SearchUsage.id
                )
            ).where(
                SearchUsage.telegram_id
                == telegram_id,

                SearchUsage.search_type
                == search_type,

                SearchUsage.created_at
                >= start,

                SearchUsage.created_at
                < end,
            )
        )

        return count or 0


# ============================================================
# SEARCH CAPACITY
# ============================================================

def crypto_search_capacity(
    telegram_id,
):

    plan = get_plan(
        telegram_id
    )

    used = monthly_search_count(
        telegram_id,
        "crypto",
    )

    if plan["unlimited"]:

        return {
            "plan":
                plan["plan"],

            "used":
                used,

            "limit":
                None,

            "remaining":
                None,

            "allowed":
                True,

            "unlimited":
                True,
        }

    remaining = max(
        0,
        NORMAL_CRYPTO_SEARCH_LIMIT
        - used,
    )

    return {
        "plan":
            "normal",

        "used":
            used,

        "limit":
            NORMAL_CRYPTO_SEARCH_LIMIT,

        "remaining":
            remaining,

        "allowed":
            used
            < NORMAL_CRYPTO_SEARCH_LIMIT,

        "unlimited":
            False,
    }


# ============================================================
# CAN SEARCH
# ============================================================

def can_search_crypto(
    telegram_id,
):

    return crypto_search_capacity(
        telegram_id
    )["allowed"]


# ============================================================
# REGISTER SUCCESSFUL SEARCH
# ============================================================

def register_crypto_search(
    telegram_id,
    symbol,
):

    capacity = (
        crypto_search_capacity(
            telegram_id
        )
    )

    # VIP and Admin do not consume quota.
    if capacity[
        "unlimited"
    ]:

        return {
            "registered":
                False,

            "capacity":
                capacity,
        }

    if not capacity[
        "allowed"
    ]:

        return {
            "registered":
                False,

            "capacity":
                capacity,
        }

    with SessionLocal() as db:

        usage = SearchUsage(
            telegram_id=telegram_id,
            search_type="crypto",
            symbol=symbol,
        )

        db.add(
            usage
        )

        db.commit()

    new_capacity = (
        crypto_search_capacity(
            telegram_id
        )
    )

    return {
        "registered":
            True,

        "capacity":
            new_capacity,
    }


# ============================================================
# DISPLAY
# ============================================================

def crypto_search_usage_text(
    telegram_id,
):

    capacity = (
        crypto_search_capacity(
            telegram_id
        )
    )

    if capacity[
        "unlimited"
    ]:

        if capacity[
            "plan"
        ] == "admin":

            return (
                "🛡 Search: Unlimited"
            )

        return (
            "💎 Search: Unlimited"
        )

    return (
        "🔎 جستجوی ماهانه: "
        f"{capacity['used']} / "
        f"{capacity['limit']}\n"
        "باقی‌مانده: "
        f"{capacity['remaining']}"
    )
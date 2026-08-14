from datetime import (
    datetime,
    timedelta,
)

from sqlalchemy import (
    func,
    or_,
    select,
)

from app.models.admin_audit import (
    AdminAuditLog,
)

from app.models.alert import (
    MarketAlert,
)

from app.models.database import (
    SessionLocal,
)

from app.models.referral import (
    PointTransaction,
    ReferralReward,
)

from app.models.search_usage import (
    SearchUsage,
)

from app.models.support import (
    SupportTicket,
)

from app.models.user import (
    User,
)


# ============================================================
# AUDIT
# ============================================================

def audit(
    admin_id,
    action,
    target_type=None,
    target_id=None,
    details=None,
):

    with SessionLocal() as db:

        item = AdminAuditLog(
            admin_id=admin_id,
            action=action,
            target_type=target_type,
            target_id=(
                str(target_id)
                if target_id
                is not None
                else None
            ),
            details=details,
        )

        db.add(item)
        db.commit()


# ============================================================
# DASHBOARD
# ============================================================

def dashboard_stats():

    with SessionLocal() as db:

        total_users = (
            db.scalar(
                select(
                    func.count(
                        User.id
                    )
                )
            )
            or 0
        )

        active_users = (
            db.scalar(
                select(
                    func.count(
                        User.id
                    )
                ).where(
                    User.is_active
                    .is_(True)
                )
            )
            or 0
        )

        banned_users = (
            db.scalar(
                select(
                    func.count(
                        User.id
                    )
                ).where(
                    User.is_banned
                    .is_(True)
                )
            )
            or 0
        )

        vip_users = (
            db.scalar(
                select(
                    func.count(
                        User.id
                    )
                ).where(
                    User.membership_type
                    == "vip"
                )
            )
            or 0
        )

        active_alerts = (
            db.scalar(
                select(
                    func.count(
                        MarketAlert.id
                    )
                ).where(
                    MarketAlert.is_active
                    .is_(True)
                )
            )
            or 0
        )

        total_alerts = (
            db.scalar(
                select(
                    func.count(
                        MarketAlert.id
                    )
                )
            )
            or 0
        )

        referrals = (
            db.scalar(
                select(
                    func.count(
                        ReferralReward.id
                    )
                )
            )
            or 0
        )

        searches = (
            db.scalar(
                select(
                    func.count(
                        SearchUsage.id
                    )
                )
            )
            or 0
        )

        open_tickets = (
            db.scalar(
                select(
                    func.count(
                        SupportTicket.id
                    )
                ).where(
                    SupportTicket.status
                    != "closed"
                )
            )
            or 0
        )

        return {
            "users":
                total_users,

            "active_users":
                active_users,

            "banned":
                banned_users,

            "vip":
                vip_users,

            "active_alerts":
                active_alerts,

            "alerts":
                total_alerts,

            "referrals":
                referrals,

            "searches":
                searches,

            "open_tickets":
                open_tickets,
        }


# ============================================================
# USERS
# ============================================================

def recent_users(
    limit=20,
):

    with SessionLocal() as db:

        return list(
            db.scalars(
                select(
                    User
                )
                .order_by(
                    User.id.desc()
                )
                .limit(limit)
            ).all()
        )


# ============================================================
# FIND USER
# ============================================================

def find_user(
    query,
):

    value = (
        str(query)
        .strip()
    )

    if not value:
        return None

    if value.startswith("@"):
        value = value[1:]

    with SessionLocal() as db:

        if value.isdigit():

            telegram_id = int(
                value
            )

            user = db.scalar(
                select(
                    User
                ).where(
                    User.telegram_id
                    == telegram_id
                )
            )

            if user:
                return user

        return db.scalar(
            select(
                User
            ).where(
                func.lower(
                    User.username
                )
                == value.lower()
            )
        )


# ============================================================
# GET USER
# ============================================================

def get_admin_user(
    telegram_id,
):

    with SessionLocal() as db:

        return db.scalar(
            select(
                User
            ).where(
                User.telegram_id
                == telegram_id
            )
        )


# ============================================================
# USER STATS
# ============================================================

def user_stats(
    telegram_id,
):

    with SessionLocal() as db:

        alerts = (
            db.scalar(
                select(
                    func.count(
                        MarketAlert.id
                    )
                ).where(
                    MarketAlert.telegram_id
                    == telegram_id
                )
            )
            or 0
        )

        active_alerts = (
            db.scalar(
                select(
                    func.count(
                        MarketAlert.id
                    )
                ).where(
                    MarketAlert.telegram_id
                    == telegram_id,

                    MarketAlert.is_active
                    .is_(True),
                )
            )
            or 0
        )

        referrals = (
            db.scalar(
                select(
                    func.count(
                        ReferralReward.id
                    )
                ).where(
                    ReferralReward.referrer_id
                    == telegram_id
                )
            )
            or 0
        )

        searches = (
            db.scalar(
                select(
                    func.count(
                        SearchUsage.id
                    )
                ).where(
                    SearchUsage.telegram_id
                    == telegram_id
                )
            )
            or 0
        )

        tickets = (
            db.scalar(
                select(
                    func.count(
                        SupportTicket.id
                    )
                ).where(
                    SupportTicket.telegram_id
                    == telegram_id
                )
            )
            or 0
        )

        return {
            "alerts":
                alerts,

            "active_alerts":
                active_alerts,

            "referrals":
                referrals,

            "searches":
                searches,

            "tickets":
                tickets,
        }


# ============================================================
# BAN
# ============================================================

def set_ban(
    admin_id,
    telegram_id,
    banned,
):

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
            return False

        user.is_banned = bool(
            banned
        )

        db.commit()

    audit(
        admin_id=admin_id,
        action=(
            "ban_user"
            if banned
            else "unban_user"
        ),
        target_type="user",
        target_id=telegram_id,
    )

    return True


# ============================================================
# VIP
# ============================================================

def give_vip(
    admin_id,
    telegram_id,
    days,
):

    days = int(
        days
    )

    if (
        days < 1
        or days > 3650
    ):
        return False

    now = datetime.utcnow()

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
            return False

        if (
            user.membership_type
            == "vip"
            and user.vip_expires_at
            and user.vip_expires_at
            > now
        ):

            start = (
                user.vip_expires_at
            )

        else:

            start = now

        user.membership_type = "vip"

        user.vip_expires_at = (
            start
            + timedelta(
                days=days
            )
        )

        db.commit()

    audit(
        admin_id=admin_id,
        action="give_vip",
        target_type="user",
        target_id=telegram_id,
        details=(
            f"{days} days"
        ),
    )

    return True


def remove_vip(
    admin_id,
    telegram_id,
):

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
            return False

        user.membership_type = (
            "normal"
        )

        user.vip_expires_at = None

        db.commit()

    audit(
        admin_id=admin_id,
        action="remove_vip",
        target_type="user",
        target_id=telegram_id,
    )

    return True


# ============================================================
# POINTS
# ============================================================

def change_points(
    admin_id,
    telegram_id,
    amount,
):

    amount = int(
        amount
    )

    if amount == 0:
        return False

    if abs(amount) > 1_000_000:
        return False

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
            return False

        current = (
            user.points
            or 0
        )

        new_balance = (
            current
            + amount
        )

        if new_balance < 0:
            return False

        user.points = (
            new_balance
        )

        transaction = (
            PointTransaction(
                telegram_id=telegram_id,
                amount=amount,
                reason="admin_adjustment",
                reference=str(
                    admin_id
                ),
            )
        )

        db.add(
            transaction
        )

        db.commit()

    audit(
        admin_id=admin_id,
        action="change_points",
        target_type="user",
        target_id=telegram_id,
        details=(
            f"amount={amount}"
        ),
    )

    return True


# ============================================================
# AUDIT HISTORY
# ============================================================

def audit_history(
    limit=30,
):

    with SessionLocal() as db:

        return list(
            db.scalars(
                select(
                    AdminAuditLog
                )
                .order_by(
                    AdminAuditLog.id
                    .desc()
                )
                .limit(limit)
            ).all()
        )


# ============================================================
# BROADCAST TARGETS
# ============================================================

def broadcast_targets():

    with SessionLocal() as db:

        return list(
            db.scalars(
                select(
                    User.telegram_id
                ).where(
                    User.is_active
                    .is_(True),

                    User.is_banned
                    .is_(False),
                )
            ).all()
        )
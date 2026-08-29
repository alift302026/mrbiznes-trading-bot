from sqlalchemy import (
    func,
    select,
)

from app.models.database import (
    SessionLocal,
)

from app.models.referral import (
    PointTransaction,
    ReferralReward,
)

from app.models.user import (
    User,
)


REFERRAL_REWARD_POINTS = 10


# ============================================================
# REFERRAL LINK
# ============================================================

def referral_link(
    telegram_id,
    bot_username="@Mrbiznesssbot",
):

    with SessionLocal() as db:

        user = db.scalar(
            select(User).where(
                User.telegram_id
                == telegram_id
            )
        )

        if (
            user is None
            or not user.referral_code
        ):
            return None

        username = (
            bot_username
            .lstrip("@")
        )

        return (
            f"https://t.me/{username}"
            f"?start={user.referral_code}"
        )


# ============================================================
# REFERRAL COUNT
# ============================================================

def referral_count(
    telegram_id,
):

    with SessionLocal() as db:

        count = db.scalar(
            select(
                func.count(
                    ReferralReward.id
                )
            ).where(
                ReferralReward.referrer_id
                == telegram_id
            )
        )

        return count or 0


# ============================================================
# POINT BALANCE
# ============================================================

def point_balance(
    telegram_id,
):

    with SessionLocal() as db:

        user = db.scalar(
            select(User).where(
                User.telegram_id
                == telegram_id
            )
        )

        if user is None:
            return 0

        return user.points or 0


# ============================================================
# POINT HISTORY
# ============================================================

def point_history(
    telegram_id,
    limit=20,
):

    with SessionLocal() as db:

        return list(
            db.scalars(
                select(
                    PointTransaction
                )
                .where(
                    PointTransaction.telegram_id
                    == telegram_id
                )
                .order_by(
                    PointTransaction.id.desc()
                )
                .limit(limit)
            ).all()
        )


# ============================================================
# ADD POINTS
# ============================================================

def add_points(
    telegram_id,
    amount,
    reason,
    reference=None,
):

    amount = int(amount)

    if amount == 0:
        return False

    with SessionLocal() as db:

        user = db.scalar(
            select(User).where(
                User.telegram_id
                == telegram_id
            )
        )

        if user is None:
            return False

        new_balance = (
            (user.points or 0)
            + amount
        )

        if new_balance < 0:
            return False

        user.points = new_balance

        transaction = PointTransaction(
            telegram_id=telegram_id,
            amount=amount,
            reason=reason,
            reference=reference,
        )

        db.add(transaction)
        db.commit()

        return True


# ============================================================
# PROCESS REFERRAL REWARD
# ============================================================

def process_referral_reward(
    referred_user_id,
):

    with SessionLocal() as db:

        referred_user = db.scalar(
            select(User).where(
                User.telegram_id
                == referred_user_id
            )
        )

        if referred_user is None:
            return False

        if not referred_user.referred_by:
            return False

        referrer = db.scalar(
            select(User).where(
                User.referral_code
                == referred_user.referred_by
            )
        )

        if referrer is None:
            return False

        # Self-referral protection
        if (
            referrer.telegram_id
            == referred_user.telegram_id
        ):
            return False

        # Reward can only be issued once
        existing = db.scalar(
            select(
                ReferralReward
            ).where(
                ReferralReward.referred_user_id
                == referred_user.telegram_id
            )
        )

        if existing:
            return False

        reward = ReferralReward(
            referrer_id=referrer.telegram_id,
            referred_user_id=(
                referred_user.telegram_id
            ),
            points=REFERRAL_REWARD_POINTS,
        )

        transaction = PointTransaction(
            telegram_id=referrer.telegram_id,
            amount=REFERRAL_REWARD_POINTS,
            reason="referral_reward",
            reference=str(
                referred_user.telegram_id
            ),
        )

        referrer.points = (
            (referrer.points or 0)
            + REFERRAL_REWARD_POINTS
        )

        db.add(reward)
        db.add(transaction)

        db.commit()

        return True


# ============================================================
# REFERRAL SUMMARY
# ============================================================

def referral_summary(
    telegram_id,
):

    return {
        "invites":
            referral_count(
                telegram_id
            ),

        "points":
            point_balance(
                telegram_id
            ),

        "link":
            referral_link(
                telegram_id
            ),

        "reward_per_invite":
            REFERRAL_REWARD_POINTS,
    }
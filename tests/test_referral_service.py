from app.services.referral_service import (
    REFERRAL_REWARD_POINTS,
    add_points,
    point_balance,
    process_referral_reward,
    referral_count,
    referral_link,
)
from app.services.user_service import get_or_create_user


def _make_user(telegram_id, referred_by=None):
    user, _ = get_or_create_user(
        telegram_id=telegram_id,
        username=f"u{telegram_id}",
        first_name=f"U{telegram_id}",
        referred_by=referred_by,
    )
    return user


# ============================================================
# LINK
# ============================================================

def test_referral_link_contains_code():
    user = _make_user(5001)

    link = referral_link(5001, bot_username="@MrBiznesBot")
    assert link == f"https://t.me/MrBiznesBot?start={user.referral_code}"


def test_referral_link_unknown_user_returns_none():
    assert referral_link(999999999) is None


# ============================================================
# REWARD
# ============================================================

def test_referral_reward_granted_once():
    referrer = _make_user(5002)
    referred = _make_user(5003, referred_by=referrer.referral_code)

    assert point_balance(referrer.telegram_id) == 0

    assert process_referral_reward(referred.telegram_id) is True
    assert point_balance(referrer.telegram_id) == REFERRAL_REWARD_POINTS
    assert referral_count(referrer.telegram_id) == 1

    # second call must be a no-op (anti double-reward)
    assert process_referral_reward(referred.telegram_id) is False
    assert point_balance(referrer.telegram_id) == REFERRAL_REWARD_POINTS
    assert referral_count(referrer.telegram_id) == 1


def test_self_referral_rejected():
    from sqlalchemy import update

    from app.models.database import SessionLocal
    from app.models.user import User

    user = _make_user(5004)

    # simulate a user whose referred_by points to their own code
    with SessionLocal() as db:
        db.execute(
            update(User)
            .where(User.telegram_id == user.telegram_id)
            .values(referred_by=user.referral_code)
        )
        db.commit()

    assert process_referral_reward(user.telegram_id) is False


def test_reward_without_referrer_rejected():
    _make_user(5006)
    assert process_referral_reward(5006) is False


def test_reward_unknown_user_rejected():
    assert process_referral_reward(987654321) is False


# ============================================================
# POINTS
# ============================================================

def test_add_points_updates_balance():
    _make_user(5007)

    assert add_points(5007, 25, reason="test") is True
    assert point_balance(5007) == 25


def test_add_points_unknown_user_fails():
    assert add_points(111222333, 10, reason="test") is False


def test_add_points_invalid_amount_fails():
    _make_user(5008)
    assert add_points(5008, 0, reason="test") is False
    assert add_points(5008, -5, reason="test") is False
    assert point_balance(5008) == 0

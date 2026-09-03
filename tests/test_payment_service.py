from datetime import datetime, timedelta

import pytest

from app.models.payment import Payment
from app.services.payment_service import (
    BANK_CARDS,
    CRYPTO_DESTINATIONS,
    VIP_PLANS,
    approve_payment,
    create_bank_payment,
    create_crypto_payment,
    get_payment,
    get_plan,
    pending_payments,
    reject_payment,
    txid_exists,
    user_payments,
)
from app.services.user_service import get_user, get_or_create_user


# ============================================================
# PLANS
# ============================================================

def test_get_plan_valid():
    plan = get_plan(30)
    assert plan["days"] == 30
    assert plan["price"] == 10.0


def test_get_plan_invalid_raises():
    with pytest.raises(ValueError):
        get_plan(7)


def test_all_plan_prices_positive():
    for days, price in VIP_PLANS.items():
        assert days > 0
        assert price > 0


# ============================================================
# BANK PAYMENT
# ============================================================

def test_create_bank_payment_ok():
    payment = create_bank_payment(
        telegram_id=1001,
        plan_days=30,
        bank_key="melal",
        tracking_code="123456789",
        amount=6500000,
    )

    assert payment.status == "pending"
    assert payment.plan_days == 30
    assert payment.amount == 6500000
    assert payment.txid == "BANK-123456789"
    assert txid_exists("BANK-123456789")


def test_duplicate_tracking_code_rejected():
    create_bank_payment(1001, 30, "melal", "TRK-111", 6500000)

    with pytest.raises(ValueError, match="already exists"):
        create_bank_payment(1002, 30, "mehr", "TRK-111", 6500000)


def test_invalid_bank_card_rejected():
    with pytest.raises(ValueError, match="Invalid bank card"):
        create_bank_payment(1001, 30, "fake_bank", "TRK-222", 100)


def test_short_tracking_code_rejected():
    with pytest.raises(ValueError, match="Invalid tracking code"):
        create_bank_payment(1001, 30, "melal", "12", 100)


# ============================================================
# CRYPTO PAYMENT
# ============================================================

def test_create_crypto_payment_ok():
    payment = create_crypto_payment(
        telegram_id=2002,
        plan_days=90,
        crypto_key="usdt_trc20",
        txid="0xABCDEF1234567890",
        amount=27.0,
    )

    assert payment.status == "pending"
    assert payment.plan_days == 90


def test_duplicate_txid_rejected():
    create_crypto_payment(2002, 90, "btc", "0xDUP000111222", 27.0)

    with pytest.raises(ValueError, match="already exists"):
        create_crypto_payment(2003, 30, "btc", "0xDUP000111222", 10.0)


def test_invalid_crypto_destination_rejected():
    with pytest.raises(ValueError, match="Invalid crypto destination"):
        create_crypto_payment(2002, 30, "doge", "0xABCDEF1234567890", 10.0)


def test_short_txid_rejected():
    with pytest.raises(ValueError, match="Invalid TXID"):
        create_crypto_payment(2002, 30, "btc", "abc", 10.0)


def test_bad_amount_rejected():
    with pytest.raises(ValueError, match="Invalid amount"):
        create_crypto_payment(2002, 30, "btc", "0xABCDEF1234567890", 0)


# ============================================================
# APPROVE / REJECT
# ============================================================

def test_approve_activates_vip_once():
    get_or_create_user(3001, "ali", "Ali")
    payment = create_bank_payment(3001, 30, "melal", "APPROVE-1", 6500000)

    result = approve_payment(payment.id, admin_id=777)
    assert result is not None

    user = get_user(3001)
    assert user.membership_type == "vip"
    assert user.vip_expires_at is not None

    expected = datetime.utcnow() + timedelta(days=30)
    assert (user.vip_expires_at - expected).total_seconds() < 60


def test_double_approve_does_not_extend_vip():
    get_or_create_user(3002, "sara", "Sara")
    payment = create_bank_payment(3002, 30, "mehr", "APPROVE-2", 6500000)

    first = approve_payment(payment.id, admin_id=777)
    expiry_1 = first["vip_expires_at"]

    # approving twice must be a no-op (returns payment, does not extend)
    second = approve_payment(payment.id, admin_id=777)
    assert second is not None
    assert second.status == "confirmed"

    user = get_user(3002)
    assert user.vip_expires_at == expiry_1


def test_reject_then_approve_is_refused():
    get_or_create_user(3003, "reza", "Reza")
    payment = create_bank_payment(3003, 30, "tejarat", "REJECT-1", 6500000)

    assert reject_payment(payment.id, admin_id=777) is True
    assert approve_payment(payment.id, admin_id=777) is None


def test_approve_missing_payment_returns_none():
    assert approve_payment(999999, admin_id=777) is None


def test_pending_and_user_payments_lists():
    get_or_create_user(4001, "mina", "Mina")
    p1 = create_bank_payment(4001, 30, "melal", "LIST-1", 100)
    create_bank_payment(4001, 90, "mehr", "LIST-2", 200)

    pend = pending_payments()
    assert {p.id for p in pend} >= {p1.id}

    mine = user_payments(4001)
    assert len(mine) == 2

    assert get_payment(p1.id).telegram_id == 4001


# ============================================================
# CONFIG SANITY
# ============================================================

def test_bank_cards_have_owner_and_valid_card_number():
    for key, card in BANK_CARDS.items():
        assert card["bank"]
        assert card["owner"]
        assert len(card["card"]) == 16, f"{key}: card number must be 16 digits"


def test_crypto_destinations_have_address():
    for key, dest in CRYPTO_DESTINATIONS.items():
        assert dest["asset"]
        assert dest["network"]
        assert len(dest["address"]) >= 20, f"{key}: address looks too short"

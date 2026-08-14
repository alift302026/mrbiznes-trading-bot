from datetime import (
    datetime,
    timedelta,
)

from sqlalchemy import (
    select,
)

from app.models.database import (
    SessionLocal,
)

from app.models.payment import (
    Payment,
)

from app.models.user import (
    User,
)


# ============================================================
# VIP PLANS
# ============================================================

VIP_PLANS = {
    30: 10.0,
    90: 27.0,
    180: 50.0,
    365: 80.0,
}


# ============================================================
# CRYPTO DESTINATIONS
# ============================================================

CRYPTO_DESTINATIONS = {
    "btc": {
        "asset": "BTC",
        "network": "Bitcoin",
        "address": (
            "bc1qqdumgvslv9kxak8mdxrjvmen3gq9q00ch8egt7"
        ),
    },

    "bnb": {
        "asset": "BNB",
        "network": "BEP20",
        "address": (
            "0xB7b1d0243ad2c11CA7a680E33be8BD1F92233fEA"
        ),
    },

    "sol": {
        "asset": "SOL",
        "network": "Solana",
        "address": (
            "A8YPCXEEQvZQHxTXroG8kHb4odP4BrAFGSkmbbFhQspa"
        ),
    },

    "trx": {
        "asset": "TRX",
        "network": "TRON",
        "address": (
            "TJpmauXS4E9iF1mfUtSUQewLEREeFXxMxp"
        ),
    },

    "usdt_trc20": {
        "asset": "USDT",
        "network": "TRC20",
        "address": (
            "TJpmauXS4E9iF1mfUtSUQewLEREeFXxMxp"
        ),
    },
}


# ============================================================
# BANK CARDS
# ============================================================

BANK_CARDS = {
    "melal": {
        "bank": "ملل",
        "card": "6062561023546123",
        "owner": "علیرضا افتخاری",
    },

    "mehr": {
        "bank": "مهر",
        "card": "6063731079881364",
        "owner": "علیرضا افتخاری",
    },

    "tejarat": {
        "bank": "تجارت",
        "card": "5859831836736420",
        "owner": "علیرضا افتخاری",
    },

    "refah": {
        "bank": "رفاه",
        "card": "5894631194233193",
        "owner": "علیرضا افتخاری",
    },

    "sina": {
        "bank": "سینا",
        "card": "6393461067343968",
        "owner": "علیرضا افتخاری",
    },

    "blu_backup": {
        "bank": "بلو بانک - پشتیبان",
        "card": "6219861926000646",
        "owner": "فاطمه نصراللهی",
    },
}


# ============================================================
# PLAN
# ============================================================

def get_plan(
    days,
):

    days = int(
        days
    )

    price = (
        VIP_PLANS.get(
            days
        )
    )

    if price is None:

        raise ValueError(
            "Invalid VIP plan"
        )

    return {
        "days": days,
        "price": price,
    }


# ============================================================
# CHECK TXID
# ============================================================

def txid_exists(
    txid,
):

    txid = (
        str(txid)
        .strip()
    )

    if not txid:
        return False

    with SessionLocal() as db:

        item = db.scalar(
            select(
                Payment
            ).where(
                Payment.txid
                == txid
            )
        )

        return item is not None


# ============================================================
# CREATE CRYPTO PAYMENT
# ============================================================

def create_crypto_payment(
    telegram_id,
    plan_days,
    crypto_key,
    txid,
    amount,
):

    plan = get_plan(
        plan_days
    )

    destination = (
        CRYPTO_DESTINATIONS.get(
            crypto_key
        )
    )

    if destination is None:

        raise ValueError(
            "Invalid crypto destination"
        )

    txid = (
        str(txid)
        .strip()
    )

    if len(txid) < 6:

        raise ValueError(
            "Invalid TXID"
        )

    if txid_exists(
        txid
    ):

        raise ValueError(
            "TXID already exists"
        )

    amount = float(
        amount
    )

    if amount <= 0:

        raise ValueError(
            "Invalid amount"
        )

    with SessionLocal() as db:

        item = Payment(
            telegram_id=telegram_id,

            payment_method="crypto",

            plan_days=(
                plan["days"]
            ),

            plan_price=(
                plan["price"]
            ),

            asset=(
                destination["asset"]
            ),

            network=(
                destination["network"]
            ),

            amount=amount,

            txid=txid,

            destination=(
                destination["address"]
            ),

            status="pending",

            details=None,
        )

        db.add(
            item
        )

        db.commit()
        db.refresh(
            item
        )

        return item


# ============================================================
# CREATE BANK PAYMENT
# ============================================================

def create_bank_payment(
    telegram_id,
    plan_days,
    bank_key,
    tracking_code,
    amount,
    details=None,
):

    plan = get_plan(
        plan_days
    )

    bank = (
        BANK_CARDS.get(
            bank_key
        )
    )

    if bank is None:

        raise ValueError(
            "Invalid bank card"
        )

    tracking_code = (
        str(tracking_code)
        .strip()
    )

    if len(
        tracking_code
    ) < 3:

        raise ValueError(
            "Invalid tracking code"
        )

    reference = (
        f"BANK-{tracking_code}"
    )

    if txid_exists(
        reference
    ):

        raise ValueError(
            "Tracking code already exists"
        )

    amount = float(
        amount
    )

    if amount <= 0:

        raise ValueError(
            "Invalid amount"
        )

    with SessionLocal() as db:

        item = Payment(
            telegram_id=telegram_id,

            payment_method="bank",

            plan_days=(
                plan["days"]
            ),

            plan_price=(
                plan["price"]
            ),

            asset="IRR",

            network="BANK",

            amount=amount,

            txid=reference,

            destination=(
                bank["card"]
            ),

            status="pending",

            details=details,
        )

        db.add(
            item
        )

        db.commit()
        db.refresh(
            item
        )

        return item


# ============================================================
# USER PAYMENT HISTORY
# ============================================================

def user_payments(
    telegram_id,
    limit=20,
):

    with SessionLocal() as db:

        return list(
            db.scalars(
                select(
                    Payment
                )
                .where(
                    Payment.telegram_id
                    == telegram_id
                )
                .order_by(
                    Payment.id.desc()
                )
                .limit(
                    limit
                )
            ).all()
        )


# ============================================================
# PENDING PAYMENTS
# ============================================================

def pending_payments(
    limit=100,
):

    with SessionLocal() as db:

        return list(
            db.scalars(
                select(
                    Payment
                )
                .where(
                    Payment.status
                    == "pending"
                )
                .order_by(
                    Payment.id.asc()
                )
                .limit(
                    limit
                )
            ).all()
        )


# ============================================================
# GET PAYMENT
# ============================================================

def get_payment(
    payment_id,
):

    with SessionLocal() as db:

        return db.get(
            Payment,
            int(
                payment_id
            ),
        )


# ============================================================
# ACTIVATE VIP
# ============================================================

def _activate_vip(
    db,
    telegram_id,
    days,
):

    user = db.scalar(
        select(
            User
        ).where(
            User.telegram_id
            == telegram_id
        )
    )

    if user is None:

        raise ValueError(
            "User not found"
        )

    now = (
        datetime.utcnow()
    )

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

    user.membership_type = (
        "vip"
    )

    user.vip_expires_at = (
        start
        + timedelta(
            days=int(days)
        )
    )

    return user


# ============================================================
# APPROVE PAYMENT
# ============================================================

def approve_payment(
    payment_id,
    admin_id,
):

    with SessionLocal() as db:

        payment = db.get(
            Payment,
            int(
                payment_id
            ),
        )

        if payment is None:
            return None

        # Critical:
        # never activate VIP twice.
        if (
            payment.status
            == "confirmed"
        ):

            return payment

        if (
            payment.status
            == "rejected"
        ):

            return None

        if not payment.plan_days:

            return None

        user = _activate_vip(
            db,
            payment.telegram_id,
            payment.plan_days,
        )

        payment.status = (
            "confirmed"
        )

        payment.reviewed_by = (
            admin_id
        )

        payment.reviewed_at = (
            datetime.utcnow()
        )

        db.commit()
        db.refresh(
            payment
        )

        return {
            "payment":
                payment,

            "telegram_id":
                user.telegram_id,

            "vip_expires_at":
                user.vip_expires_at,
        }


# ============================================================
# REJECT PAYMENT
# ============================================================

def reject_payment(
    payment_id,
    admin_id,
    reason=None,
):

    with SessionLocal() as db:

        payment = db.get(
            Payment,
            int(
                payment_id
            ),
        )

        if payment is None:
            return False

        if payment.status != "pending":
            return False

        payment.status = (
            "rejected"
        )

        payment.reviewed_by = (
            admin_id
        )

        payment.reviewed_at = (
            datetime.utcnow()
        )

        if reason:

            old_details = (
                payment.details
                or ""
            )

            payment.details = (
                old_details
                + "\nAdmin: "
                + str(
                    reason
                )
            ).strip()

        db.commit()

        return True

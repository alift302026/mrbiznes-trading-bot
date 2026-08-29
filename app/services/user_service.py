import secrets
import string

from sqlalchemy import select

from app.models.database import SessionLocal
from app.models.user import User


SUPPORTED_LANGUAGES = {
    "fa",
    "en",
    "ar",
}


def generate_referral_code():
    alphabet = (
        string.ascii_uppercase
        + string.digits
    )

    suffix = "".join(
        secrets.choice(alphabet)
        for _ in range(8)
    )

    return f"MrBiznes-{suffix}"


def get_or_create_user(
    telegram_id,
    username,
    first_name,
    referred_by=None,
):

    with SessionLocal() as db:
        user = db.scalar(
            select(User).where(
                User.telegram_id
                == telegram_id
            )
        )

        if user:
            user.username = username
            user.first_name = first_name
            user.is_registered = True

            # زبان‌های قدیمی حذف شوند
            if (
                user.language
                not in SUPPORTED_LANGUAGES
            ):
                user.language = None

            db.commit()
            db.refresh(user)

            return user, False

        referral_code = (
            generate_referral_code()
        )

        while db.scalar(
            select(User).where(
                User.referral_code
                == referral_code
            )
        ):
            referral_code = (
                generate_referral_code()
            )

        valid_referrer = None

        if referred_by:
            owner = db.scalar(
                select(User).where(
                    User.referral_code
                    == referred_by
                )
            )

            if owner:
                valid_referrer = (
                    referred_by
                )

        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            phone_number=None,
            language=None,
            membership_type="normal",
            referral_code=referral_code,
            referred_by=valid_referrer,
            points=0,
            session_alerts_enabled=True,
            is_registered=True,
            is_active=True,
            is_banned=False,
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return user, True


def get_user(
    telegram_id,
):

    with SessionLocal() as db:
        return db.scalar(
            select(User).where(
                User.telegram_id
                == telegram_id
            )
        )


def set_language(
    telegram_id,
    language,
):

    if language not in SUPPORTED_LANGUAGES:
        return False

    with SessionLocal() as db:
        user = db.scalar(
            select(User).where(
                User.telegram_id
                == telegram_id
            )
        )

        if not user:
            return False

        user.language = language

        db.commit()

        return True


def save_phone_number(
    telegram_id,
    phone_number,
):

    # اختیاری؛ برای ورود استفاده نمی‌شود
    with SessionLocal() as db:
        user = db.scalar(
            select(User).where(
                User.telegram_id
                == telegram_id
            )
        )

        if not user:
            return False

        user.phone_number = (
            phone_number
        )

        db.commit()

        return True


def toggle_session_alerts(
    telegram_id,
):

    with SessionLocal() as db:
        user = db.scalar(
            select(User).where(
                User.telegram_id
                == telegram_id
            )
        )

        if not user:
            return None

        user.session_alerts_enabled = (
            not user.session_alerts_enabled
        )

        enabled = (
            user.session_alerts_enabled
        )

        db.commit()

        return enabled


def get_session_alert_users():

    with SessionLocal() as db:
        users = db.scalars(
            select(User).where(
                User.is_active.is_(True),
                User.is_banned.is_(False),
                User.session_alerts_enabled.is_(True),
            )
        ).all()

        result = []

        for user in users:
            language = (
                user.language
                if user.language
                in SUPPORTED_LANGUAGES
                else "en"
            )

            result.append(
                {
                    "telegram_id":
                        user.telegram_id,

                    "language":
                        language,
                }
            )

        return result
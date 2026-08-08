import secrets
import string

from sqlalchemy import (
    func,
    select,
)

from app.models.database import (
    SessionLocal,
)

from app.models.user import (
    User,
)


SUPPORTED_LANGUAGES = {
    "fa",
    "en",
    "ar",
    "tr",
    "hi",
    "zh",
    "ja",
    "ms",
    "id",
    "ng",
}


def generate_referral_code():

    chars = (
        string.ascii_uppercase
        + string.digits
    )

    return "ALIFT-" + "".join(
        secrets.choice(chars)
        for _ in range(8)
    )


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

            referrer = db.scalar(
                select(User).where(
                    User.referral_code
                    == referred_by
                )
            )

            if referrer:

                valid_referrer = (
                    referred_by
                )

        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            referral_code=referral_code,
            referred_by=valid_referrer,
            language="fa",
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


def save_phone_number(
    telegram_id,
    phone_number,
):

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

        user.is_registered = True

        db.commit()

        return True


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


def referral_stats(
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

        count = db.scalar(
            select(
                func.count(User.id)
            ).where(
                User.referred_by
                == user.referral_code
            )
        )

        return {
            "code":
                user.referral_code,

            "invites":
                count or 0,

            "points":
                user.points,
        }


def all_users_count():

    with SessionLocal() as db:

        return (
            db.scalar(
                select(
                    func.count(User.id)
                )
            )
            or 0
        )


def registered_users_count():

    with SessionLocal() as db:

        return (
            db.scalar(
                select(
                    func.count(User.id)
                ).where(
                    User.is_registered
                    .is_(True)
                )
            )
            or 0
        )


def vip_users_count():

    with SessionLocal() as db:

        return (
            db.scalar(
                select(
                    func.count(User.id)
                ).where(
                    User.membership_type
                    == "vip"
                )
            )
            or 0
        )
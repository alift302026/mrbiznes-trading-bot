from sqlalchemy import select

from app.models.database import SessionLocal
from app.models.user import User


def get_or_create_user(
    telegram_id: int,
    username: str | None,
    first_name: str | None,
) -> tuple[User, bool]:

    with SessionLocal() as db:

        user = db.scalar(
            select(User).where(
                User.telegram_id == telegram_id
            )
        )

        if user:
            user.username = username
            user.first_name = first_name

            db.commit()
            db.refresh(user)

            return user, False

        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            membership_type="normal",
            is_registered=False,
            is_active=True,
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return user, True


def get_user(
    telegram_id: int,
) -> User | None:

    with SessionLocal() as db:

        user = db.scalar(
            select(User).where(
                User.telegram_id == telegram_id
            )
        )

        return user


def save_phone_number(
    telegram_id: int,
    phone_number: str,
) -> bool:

    with SessionLocal() as db:

        user = db.scalar(
            select(User).where(
                User.telegram_id == telegram_id
            )
        )

        if not user:
            return False

        user.phone_number = phone_number
        user.is_registered = True

        db.commit()

        return True
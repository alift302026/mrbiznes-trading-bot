from datetime import datetime
import json

from sqlalchemy import (
    func,
    select,
)

from app.core.config import (
    ADMIN_IDS,
)

from app.core.plan_limits import (
    get_alert_limit,
)

from app.models.alert import (
    MarketAlert,
)

from app.models.database import (
    SessionLocal,
)

from app.models.user import (
    User,
)


# ============================================================
# EXCEPTION
# ============================================================

class AlertLimitReached(Exception):

    def __init__(
        self,
        current,
        limit,
        plan,
    ):

        self.current = current
        self.limit = limit
        self.plan = plan

        super().__init__(
            "Alert limit reached"
        )


# ============================================================
# USER PLAN
# ============================================================

def get_user_plan(
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
            return "normal"

        return (
            user.membership_type
            or "normal"
        ).lower()


# ============================================================
# ACTIVE ALERT COUNT
# ============================================================

def active_alert_count(
    telegram_id,
):

    with SessionLocal() as db:

        count = db.scalar(
            select(
                func.count(
                    MarketAlert.id
                )
            )
            .where(
                MarketAlert.telegram_id
                == telegram_id,

                MarketAlert.is_active
                .is_(True),
            )
        )

        return count or 0


# ============================================================
# CAPACITY
# ============================================================

def alert_capacity(
    telegram_id,
):

    plan = get_user_plan(
        telegram_id
    )

    admin = (
        telegram_id
        in ADMIN_IDS
    )

    limit = get_alert_limit(
        plan,
        is_admin=admin,
    )

    active = active_alert_count(
        telegram_id
    )

    if limit is None:

        remaining = None
        full = False

    else:

        remaining = max(
            0,
            limit - active,
        )

        full = (
            active >= limit
        )

    return {
        "plan": plan,
        "active": active,
        "limit": limit,
        "remaining": remaining,
        "full": full,
        "is_admin": admin,
    }


# ============================================================
# ASSERT CAPACITY
# ============================================================

def ensure_alert_capacity(
    telegram_id,
):

    capacity = alert_capacity(
        telegram_id
    )

    if capacity["full"]:

        raise AlertLimitReached(
            current=capacity["active"],
            limit=capacity["limit"],
            plan=capacity["plan"],
        )

    return capacity


# ============================================================
# PARAMETERS
# ============================================================

def encode_parameters(
    parameters,
):

    if parameters is None:
        return None

    if isinstance(
        parameters,
        str,
    ):
        return parameters

    return json.dumps(
        parameters,
        ensure_ascii=False,
        separators=(
            ",",
            ":",
        ),
    )


def decode_parameters(
    parameters,
):

    if not parameters:
        return {}

    if isinstance(
        parameters,
        dict,
    ):
        return parameters

    try:

        result = json.loads(
            parameters
        )

        if isinstance(
            result,
            dict,
        ):
            return result

    except (
        TypeError,
        ValueError,
        json.JSONDecodeError,
    ):
        pass

    return {}


# ============================================================
# CREATE ALERT
# ============================================================

def create_alert(
    telegram_id,
    symbol,
    alert_type,
    timeframe="1h",
    target_value=None,
    parameters=None,
):

    ensure_alert_capacity(
        telegram_id
    )

    encoded_parameters = (
        encode_parameters(
            parameters
        )
    )

    with SessionLocal() as db:

        item = MarketAlert(
            telegram_id=telegram_id,
            symbol=symbol,
            alert_type=alert_type,
            timeframe=timeframe,
            target_value=target_value,
            parameters=encoded_parameters,
            is_active=True,
        )

        db.add(item)
        db.commit()
        db.refresh(item)

        return item


# ============================================================
# USER ALERTS
# ============================================================

def user_alerts(
    telegram_id,
):

    with SessionLocal() as db:

        return list(
            db.scalars(
                select(
                    MarketAlert
                )
                .where(
                    MarketAlert.telegram_id
                    == telegram_id
                )
                .order_by(
                    MarketAlert.id
                    .desc()
                )
            ).all()
        )


# ============================================================
# ACTIVE ALERTS
# ============================================================

def active_alerts():

    with SessionLocal() as db:

        return list(
            db.scalars(
                select(
                    MarketAlert
                )
                .where(
                    MarketAlert.is_active
                    .is_(True)
                )
            ).all()
        )


# ============================================================
# TOGGLE
# ============================================================

def toggle_alert(
    alert_id,
    telegram_id,
):

    with SessionLocal() as db:

        item = db.scalar(
            select(
                MarketAlert
            )
            .where(
                MarketAlert.id
                == alert_id,

                MarketAlert.telegram_id
                == telegram_id,
            )
        )

        if item is None:
            return None

        if not item.is_active:

            ensure_alert_capacity(
                telegram_id
            )

            item.is_active = True

        else:

            item.is_active = False

        result = (
            item.is_active
        )

        db.commit()

        return result


# ============================================================
# DELETE
# ============================================================

def delete_alert(
    alert_id,
    telegram_id,
):

    with SessionLocal() as db:

        item = db.scalar(
            select(
                MarketAlert
            )
            .where(
                MarketAlert.id
                == alert_id,

                MarketAlert.telegram_id
                == telegram_id,
            )
        )

        if item is None:
            return False

        db.delete(item)
        db.commit()

        return True


# ============================================================
# UPDATE STATE
# ============================================================

def update_alert_state(
    alert_id,
    state,
):

    with SessionLocal() as db:

        item = db.get(
            MarketAlert,
            alert_id,
        )

        if item is None:
            return

        item.last_state = state

        db.commit()


# ============================================================
# MARK TRIGGERED
# ============================================================

def mark_triggered(
    alert_id,
    state,
    disable=False,
):

    with SessionLocal() as db:

        item = db.get(
            MarketAlert,
            alert_id,
        )

        if item is None:
            return

        item.last_state = state

        item.last_triggered_at = (
            datetime.utcnow()
        )

        item.trigger_count += 1

        if disable:
            item.is_active = False

        db.commit()
# ============================================================
# ALIFT PLAN LIMITS
# ============================================================

PLAN_LIMITS = {
    "normal": {
        "active_alerts": 5,
    },

    "vip": {
        "active_alerts": 50,
    },
}


def get_alert_limit(
    membership_type,
    is_admin=False,
):

    if is_admin:
        return None

    plan = (
        membership_type
        or "normal"
    ).lower()

    if plan not in PLAN_LIMITS:
        plan = "normal"

    return (
        PLAN_LIMITS[plan][
            "active_alerts"
        ]
    )
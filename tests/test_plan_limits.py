from app.core.plan_limits import PLAN_LIMITS, get_alert_limit


def test_normal_plan_limit():
    assert get_alert_limit("normal") == 5


def test_vip_plan_limit():
    assert get_alert_limit("vip") == 50


def test_none_defaults_to_normal():
    assert get_alert_limit(None) == 5


def test_unknown_plan_falls_back_to_normal():
    assert get_alert_limit("gold") == 5
    assert get_alert_limit("") == 5


def test_admin_is_unlimited():
    assert get_alert_limit("normal", is_admin=True) is None
    assert get_alert_limit("vip", is_admin=True) is None


def test_plan_limits_structure():
    assert PLAN_LIMITS["normal"]["active_alerts"] > 0
    assert PLAN_LIMITS["vip"]["active_alerts"] > PLAN_LIMITS["normal"]["active_alerts"]

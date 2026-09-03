from app.services.user_service import generate_referral_code, get_or_create_user, get_user


def test_generate_referral_code_format():
    code = generate_referral_code()
    assert code.startswith("MrBiznes-")
    assert len(code) > len("MrBiznes-")


def test_create_and_update_user():
    user, created = get_or_create_user(6001, "ali", "Ali")
    assert created is True
    assert user.telegram_id == 6001
    assert user.referral_code.startswith("MrBiznes-")

    # second call updates, does not duplicate
    same, created_again = get_or_create_user(6001, "ali_new", "Ali2")
    assert created_again is False
    assert same.id == user.id
    assert same.username == "ali_new"


def test_referral_codes_are_unique():
    seen = set()
    for i in range(50):
        code = generate_referral_code()
        assert code not in seen
        seen.add(code)


def test_get_user_unknown_returns_none():
    assert get_user(1234567890) is None


def test_invalid_referral_code_is_ignored():
    user, created = get_or_create_user(
        6002,
        "nima",
        "Nima",
        referred_by="MrBiznes-DOESNOTEXIST",
    )
    assert created is True
    assert user.referred_by is None


def test_valid_referral_code_is_stored():
    referrer, _ = get_or_create_user(6003, "ref", "Ref")
    referred, _ = get_or_create_user(
        6004,
        "new",
        "New",
        referred_by=referrer.referral_code,
    )
    assert referred.referred_by == referrer.referral_code

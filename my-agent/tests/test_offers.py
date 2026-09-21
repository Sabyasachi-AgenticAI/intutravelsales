from integrations import offers


def test_category_for_maps_services() -> None:
    assert offers.category_for("front brake pads") == "brakes"
    assert offers.category_for("4 new tires and an alignment") == "tires"
    assert offers.category_for("dead battery, needs a jump") == "batteries"
    assert offers.category_for("a/c blows warm") == "ac"
    assert offers.category_for("oil change") == "oil"


def test_category_for_unknown_service_is_none() -> None:
    assert offers.category_for("windshield chip") is None
    assert offers.category_for("") is None
    assert offers.category_for(None) is None


# --- coupon eligibility: full-set tire deals only for a 4-tire purchase -------

_FULL_SET_COUPON = {
    "headline": "Free 4th Tire",
    "title": "Save up to $300 when you buy and install 4 Cooper tires",
    "terms": "Terms apply.",
}
_PLAIN_COUPON = {
    "headline": "$100 Savings",
    "title": "Save up to $100 on select Brake Service Packages",
    "terms": "Terms apply.",
}


def test_requires_full_set_detects_buy_four_deals() -> None:
    assert offers.requires_full_set(_FULL_SET_COUPON) is True
    assert offers.requires_full_set(_PLAIN_COUPON) is False


def test_service_is_full_set() -> None:
    assert offers.service_is_full_set("4 new tires") is True
    assert offers.service_is_full_set("four tires") is True
    assert offers.service_is_full_set("full set of tires") is True
    assert offers.service_is_full_set("tire rotation") is False
    assert offers.service_is_full_set("one tire") is False
    assert offers.service_is_full_set("flat tire repair") is False


def test_is_eligible_withholds_full_set_deal_unless_buying_four() -> None:
    # The 4th-tire deal only for a full set; a rotation must not surface it.
    assert offers.is_eligible(_FULL_SET_COUPON, "4 new tires") is True
    assert offers.is_eligible(_FULL_SET_COUPON, "tire rotation") is False
    assert offers.is_eligible(_FULL_SET_COUPON, "one tire") is False
    # Unconditional coupons always pass.
    assert offers.is_eligible(_PLAIN_COUPON, "brake service") is True

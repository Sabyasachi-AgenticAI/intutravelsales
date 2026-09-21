"""Guards for the reason-first upsell strategy.

The add-on and its reason are now deterministic (`integrations/upsell.py`); the
agent only decides *whether* to pitch (the stress/time gate). These pin the
mapping, the tool seam, and that the instructions lead with the reason and keep
the coupon as a closer.
"""

import inspect

from agent import _ADVISOR_INSTRUCTIONS, ServiceAdvisorAgent
from integrations import scheduling, upsell


def test_recommend_maps_service_to_relevant_add_on() -> None:
    # The strongest cases: the add-on follows the visit, deterministically.
    assert "alignment" in upsell.recommend("brake pads and rotors").add_on
    assert "alignment" in upsell.recommend("4 new tires").add_on
    assert "alignment" in upsell.recommend("strut replacement").add_on
    assert "rotation" in upsell.recommend("oil change").add_on
    assert "cabin air filter" in upsell.recommend("air conditioning not cold").add_on
    assert "charging" in upsell.recommend("battery replacement").add_on
    assert "oil change" in upsell.recommend("state inspection").add_on


def test_recommend_falls_back_to_oil_for_unknown() -> None:
    rec = upsell.recommend("something completely unrelated")
    assert "oil change" in rec.add_on
    assert rec.offer_category == "oil"


def test_recommend_never_pitches_battery_for_a_brake_job() -> None:
    # The old non-sequitur we explicitly guard against.
    assert "battery" not in upsell.recommend("front brake service").add_on.lower()
    assert "charging" not in upsell.recommend("front brake service").add_on.lower()


def test_coupon_closer_only_when_it_actually_applies() -> None:
    # A rotation add-on must NOT carry a tire-purchase coupon (wrong-coupon
    # mismatch breaks trust); an oil-change add-on legitimately can.
    assert upsell.recommend("oil change").offer_category is None  # → tire rotation
    assert upsell.recommend("4 new tires").offer_category is None  # → alignment
    assert upsell.recommend("battery replacement").offer_category is None  # → charging
    assert upsell.recommend("state inspection").offer_category == "oil"  # → oil change


def test_every_rule_has_a_nonempty_reason() -> None:
    # Reason-first only works if every recommendation carries a real reason.
    for _keywords, rec in upsell._RULES:
        assert rec.reason.strip()
    assert upsell._DEFAULT.reason.strip()


def test_recommend_upsell_tool_exists() -> None:
    params = inspect.signature(ServiceAdvisorAgent.recommend_upsell).parameters
    assert "main_service" in params


def test_book_service_captures_add_ons_and_offers() -> None:
    params = inspect.signature(ServiceAdvisorAgent.book_service).parameters
    assert "add_ons" in params
    assert "offer" in params
    assert params["add_ons"].default is None


def test_add_ons_lengthen_the_appointment() -> None:
    primary = scheduling.duration_for("brake check")
    add_on = scheduling.duration_for("oil change")
    assert primary + add_on == 150


def test_instructions_are_reason_first_and_gated() -> None:
    text = _ADVISOR_INSTRUCTIONS.lower()
    # The value reason leads; the coupon is only a closer.
    assert "reason-first" in text
    assert "recommend_upsell" in text
    assert "closer" in text
    # Upsell is the default on a routine booking; only a real reason skips it.
    assert "default" in text
    # The stress/time gate is still present.
    assert "rush" in text or "hurry" in text

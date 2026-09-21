"""Deterministic guardrails on the booking/VIN tools.

These pin the code-level protections (not prompt-level): a VIN must be a real
17-character VIN before we hit NHTSA, a phone number must have enough digits,
the two write tools reject accidental duplicate fires, and a second booking on
the same call is refused rather than silently creating a duplicate ticket.
"""

import inspect

from agent import (
    ServiceAdvisorAgent,
    ServiceAdvisorData,
    _clean_vin,
    _is_duplicate_ticket,
    _phone_digits,
)

# --- input normalization helpers -------------------------------------------


def test_clean_vin_accepts_a_valid_vin() -> None:
    # 17 alphanumerics, mixed case and stray spaces/dashes the caller might add.
    assert _clean_vin(" 1hg-cm82 633a00 0352 ") == "1HGCM82633A000352"


def test_clean_vin_rejects_wrong_length() -> None:
    assert _clean_vin("1HGCM82633") is None  # too short
    assert _clean_vin("1HGCM82633A000352EXTRA") is None  # too long


def test_phone_digits_strips_formatting() -> None:
    assert _phone_digits("+1 (512) 555-0100") == "15125550100"
    assert len(_phone_digits("555-0100")) == 7  # too short to be a real number


# --- duplicate-ticket guard -------------------------------------------------


def test_no_duplicate_on_a_fresh_call() -> None:
    assert _is_duplicate_ticket(ServiceAdvisorData()) is False


def test_duplicate_detected_once_a_ticket_exists() -> None:
    ud = ServiceAdvisorData(booking_id="bk_123")
    assert _is_duplicate_ticket(ud) is True


# --- write tools refuse accidental double-fire ------------------------------


def test_write_tools_reject_duplicate_calls() -> None:
    # A caller talking over the agent can make the model re-issue a write; the
    # framework must refuse the second concurrent call, not book twice.
    assert ServiceAdvisorAgent.book_service.info.on_duplicate == "reject"
    assert ServiceAdvisorAgent.arrange_tow.info.on_duplicate == "reject"


def test_read_tools_stay_allow() -> None:
    # Reads are idempotent; no reason to reject duplicates.
    assert ServiceAdvisorAgent.check_service_availability.info.on_duplicate == "allow"
    assert ServiceAdvisorAgent.check_offers.info.on_duplicate == "allow"


# --- signature stability (the guards read these) ----------------------------


def test_book_service_still_takes_phone_and_vehicle() -> None:
    params = inspect.signature(ServiceAdvisorAgent.book_service).parameters
    assert "customer_phone" in params
    assert "vehicle" in params

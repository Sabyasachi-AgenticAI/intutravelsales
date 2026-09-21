"""Contract tests for multi-day booking.

The date math lives in test_scheduling.py; these pin that the agent tools and the
board write actually expose the day/booking_date seam multi-day depends on.
"""

import inspect

from agent import ServiceAdvisorAgent
from integrations import dashboard, scheduling


def test_availability_and_booking_take_a_day() -> None:
    avail = inspect.signature(ServiceAdvisorAgent.check_service_availability).parameters
    book = inspect.signature(ServiceAdvisorAgent.book_service).parameters
    assert "day" in avail
    assert avail["day"].default == "today"
    assert "day" in book
    assert book["day"].default == "today"


def test_record_booking_accepts_booking_date() -> None:
    params = inspect.signature(dashboard.record_booking).parameters
    assert "booking_date" in params
    assert params["booking_date"].default is None  # optional → same-day when omitted


def test_record_callback_tool_exists_and_needs_contact() -> None:
    params = inspect.signature(ServiceAdvisorAgent.record_callback).parameters
    assert "customer_name" in params
    assert "customer_phone" in params
    assert "service" in params


def test_instructions_are_grounded_on_todays_date() -> None:
    # The current date is injected into the prompt so the agent doesn't guess
    # the month/day from training memory (which caused a "June, then July" flip)
    # or compute past dates.
    text = ServiceAdvisorAgent().instructions
    assert scheduling.today_label() in text


def test_get_scheduled_is_date_aware() -> None:
    # Defaulting to today keeps existing callers working; a date narrows the read.
    params = inspect.signature(scheduling.get_scheduled).parameters
    assert "for_date" in params
    assert params["for_date"].default is None

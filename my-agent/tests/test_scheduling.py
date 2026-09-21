from datetime import date

from integrations import scheduling


def test_resolve_day_keywords_and_iso() -> None:
    today = date(2026, 7, 18)  # a Saturday
    assert scheduling.resolve_day("today", today=today) == today
    assert scheduling.resolve_day("", today=today) == today
    assert scheduling.resolve_day(None, today=today) == today
    assert scheduling.resolve_day("tomorrow", today=today) == date(2026, 7, 19)
    assert scheduling.resolve_day("2026-07-25", today=today) == date(2026, 7, 25)
    # Unparseable phrases return None (the LLM resolves them to ISO upstream).
    assert scheduling.resolve_day("sometime next week", today=today) is None


def test_within_booking_window_rejects_past_and_far_future() -> None:
    today = date(2026, 7, 18)
    assert scheduling.within_booking_window(today, today=today) is True
    assert scheduling.within_booking_window(date(2026, 7, 19), today=today) is True
    assert scheduling.within_booking_window(date(2026, 7, 17), today=today) is False
    too_far = date(2026, 7, 18) + __import__("datetime").timedelta(
        days=scheduling.MAX_ADVANCE_DAYS + 1
    )
    assert scheduling.within_booking_window(too_far, today=today) is False


def test_date_label_speaks_today_tomorrow_or_weekday() -> None:
    today = date(2026, 7, 18)
    assert scheduling.date_label(today, today=today) == "today"
    assert scheduling.date_label(date(2026, 7, 19), today=today) == "tomorrow"
    # A further-out date reads as a full weekday + date.
    assert scheduling.date_label(date(2026, 7, 21), today=today) == "Tuesday, July 21"


def test_is_today() -> None:
    today = date(2026, 7, 18)
    assert scheduling.is_today(today, today=today) is True
    assert scheduling.is_today(date(2026, 7, 19), today=today) is False


def test_duration_for_matches_service_keywords() -> None:
    assert scheduling.duration_for("oil change and rotation") == 60
    assert scheduling.duration_for("front brake pads") == 90
    assert scheduling.duration_for("misfire diagnostic") == 120
    assert scheduling.duration_for("car won't start, needs a tow") == 180
    assert scheduling.duration_for("state inspection") == 30
    assert scheduling.duration_for("something unusual") == scheduling.DEFAULT_DURATION


def test_parse_and_fmt_time_roundtrip() -> None:
    assert scheduling.parse_time("9:30 AM") == 9 * 60 + 30
    assert scheduling.parse_time("2:00 PM") == 14 * 60
    assert scheduling.parse_time("12:00 PM") == 12 * 60
    assert scheduling.parse_time("12:00 AM") == 0
    assert scheduling.parse_time("4 PM") == 16 * 60
    assert scheduling.parse_time("not a time") is None

    assert scheduling.fmt_time(9 * 60 + 30) == "9:30 AM"
    assert scheduling.fmt_time(14 * 60) == "2:00 PM"
    assert scheduling.fmt_time(12 * 60) == "12:00 PM"


def test_within_business_hours_enforces_8_to_6() -> None:
    # 5:00 PM oil change (60 min) finishes at 6 PM — allowed.
    assert scheduling.within_business_hours(17 * 60, 60) is True
    # 5:30 PM oil change (60 min) would run to 6:30 PM — rejected.
    assert scheduling.within_business_hours(17 * 60 + 30, 60) is False
    # 7:00 PM anything — after hours, rejected.
    assert scheduling.within_business_hours(19 * 60, 30) is False
    # 7:30 AM — before open, rejected.
    assert scheduling.within_business_hours(7 * 60 + 30, 30) is False
    # 8:00 AM open, 90-min job — allowed.
    assert scheduling.within_business_hours(scheduling.BUSINESS_START, 90) is True
    # A job that ends exactly at close (6 PM) — allowed.
    assert scheduling.within_business_hours(scheduling.BUSINESS_END - 60, 60) is True


def test_find_open_slots_on_empty_board() -> None:
    slots = scheduling.find_open_slots([], 60, limit=3)
    # First offerings start at the top of the business day, bay 0.
    assert slots[0] == (scheduling.BUSINESS_START, 0)
    assert len(slots) == 3
    # Distinct, ascending, half-hour-aligned times.
    times = [s for s, _ in slots]
    assert times == sorted(times)
    assert all(t % scheduling.SLOT_STEP == 0 for t in times)


def test_find_open_slots_skips_occupied_bays() -> None:
    # Fill all 4 bays 8:00-9:00, leaving 9:00 as the first fully-open time.
    nine = 9 * 60
    scheduled = [
        {"bay": b, "start_min": scheduling.BUSINESS_START, "duration_min": 60}
        for b in range(scheduling.NUM_BAYS)
    ]
    slots = scheduling.find_open_slots(scheduled, 60, limit=1)
    assert slots[0][0] >= nine


def test_assign_bay_returns_free_bay_then_none_when_full() -> None:
    start = 10 * 60
    # Bays 0 and 1 busy at 10:00, so bay 2 should be offered.
    scheduled = [
        {"bay": 0, "start_min": start, "duration_min": 60},
        {"bay": 1, "start_min": start, "duration_min": 60},
    ]
    assert scheduling.assign_bay(scheduled, start, 60) == 2

    full = [
        {"bay": b, "start_min": start, "duration_min": 60}
        for b in range(scheduling.NUM_BAYS)
    ]
    assert scheduling.assign_bay(full, start, 60) is None


def test_find_open_slots_spreads_across_the_day_not_just_the_morning() -> None:
    # Mirrors the real bug: bay 0 busy 8-11:30, others clear by 11am. Without
    # spreading, the first 5 chronological openings all land by ~10am even
    # though bay 0 alone is free from 11:30 straight through to close.
    scheduled = [
        {"bay": 0, "start_min": scheduling.BUSINESS_START, "duration_min": 210},
        {"bay": 1, "start_min": scheduling.BUSINESS_START, "duration_min": 60},
        {"bay": 2, "start_min": 9 * 60, "duration_min": 60},
    ]
    slots = scheduling.find_open_slots(scheduled, 60, limit=5)
    times = [s for s, _ in slots]
    # The offered times should span well into the afternoon, not cluster
    # entirely in the morning.
    assert max(times) >= 14 * 60
    assert times == sorted(times)


def test_find_open_slots_includes_soonest_and_latest_when_spreading() -> None:
    slots = scheduling.find_open_slots([], 30, limit=3)
    times = [s for s, _ in slots]
    assert times[0] == scheduling.BUSINESS_START
    # Last candidate of the day for a 30-min job is 5:30 PM (BUSINESS_END - 30).
    assert times[-1] == scheduling.BUSINESS_END - 30


def test_now_min_and_today_label_are_sane() -> None:
    assert 0 <= scheduling.now_min() < 24 * 60
    assert len(scheduling.today_label()) > 0


def test_assign_bay_allows_non_overlapping_same_bay() -> None:
    # A job 8:00-9:00 in every bay shouldn't block a 9:00 booking.
    scheduled = [
        {"bay": b, "start_min": 8 * 60, "duration_min": 60}
        for b in range(scheduling.NUM_BAYS)
    ]
    assert scheduling.assign_bay(scheduled, 9 * 60, 60) == 0

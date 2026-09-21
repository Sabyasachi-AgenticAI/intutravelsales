from unittest.mock import AsyncMock, patch

import pytest

from integrations import dashboard

# --------------------------- pure helpers ---------------------------


def test_format_vehicle_full() -> None:
    assert (
        dashboard.format_vehicle(
            {"ModelYear": "2019", "Make": "Toyota", "Model": "Camry"}
        )
        == "2019 Toyota Camry"
    )


def test_format_vehicle_missing() -> None:
    assert dashboard.format_vehicle(None) == "Vehicle"
    assert dashboard.format_vehicle({}) == "Vehicle"


def test_derive_severity_bands() -> None:
    assert (
        dashboard.derive_severity(
            emergency_active=True, vehicle_drivable=None, has_diagnosis=False
        )
        == "urgent"
    )
    assert (
        dashboard.derive_severity(
            emergency_active=False, vehicle_drivable=False, has_diagnosis=True
        )
        == "urgent"
    )
    assert (
        dashboard.derive_severity(
            emergency_active=False, vehicle_drivable=True, has_diagnosis=True
        )
        == "diag"
    )
    assert (
        dashboard.derive_severity(
            emergency_active=False, vehicle_drivable=True, has_diagnosis=False
        )
        == "routine"
    )


def test_derive_badges() -> None:
    assert dashboard.derive_badges(has_photo=False, undrivable=False) == ["AI"]
    assert dashboard.derive_badges(has_photo=True, undrivable=True) == [
        "AI",
        "PHOTO",
        "TOW",
    ]


def test_friendly_time_utc() -> None:
    # No tz_name -> render in the timestamp's own (UTC) offset, deterministically.
    assert dashboard.friendly_time("2026-07-15T14:05:00Z") == "2:05 PM"
    assert dashboard.friendly_time("2026-07-15T00:00:00Z") == "12:00 AM"


def test_friendly_time_bad_input_passthrough() -> None:
    assert dashboard.friendly_time("not-a-time") == "not-a-time"


# --------------------------- record wrappers ---------------------------


@pytest.mark.asyncio
async def test_record_call_builds_demo_calls_row() -> None:
    with patch.object(
        dashboard, "_insert", new_callable=AsyncMock, return_value=True
    ) as mock_insert:
        ok = await dashboard.record_call(
            store="Aramingo",
            intent="Safety",
            summary="Smoke from the hood",
            outcome="Human handoff",
            outcome_type="critical",
            extra="warm transfer",
        )

    assert ok is True
    table, row = mock_insert.await_args.args
    assert table == "demo_calls"
    assert row["intent"] == "Safety"
    assert row["outcome"] == "Human handoff"
    assert row["outcome_type"] == "critical"
    assert row["extra"] == "warm transfer"


@pytest.mark.asyncio
async def test_record_booking_defaults_badges_and_parts() -> None:
    with patch.object(
        dashboard, "_insert", new_callable=AsyncMock, return_value=True
    ) as mock_insert:
        await dashboard.record_booking(
            title="Front brake pads",
            customer="Dana K.",
            vehicle="2018 Chevy Equinox",
            phone="+15125550100",
            store="Aramingo",
            complaint="Grinding when braking",
            bay=2,
            start_min=600,
            duration_min=90,
            offer="$100 off Brake Service",
            photo_urls=[
                "https://example.supabase.co/storage/v1/object/public/vehicle-photos/a.jpg"
            ],
        )

    table, row = mock_insert.await_args.args
    assert table == "demo_bookings"
    assert row["store"] == "Aramingo"
    assert row["phone"] == "+15125550100"
    assert row["complaint"] == "Grinding when braking"
    assert row["bay"] == 2
    assert row["start_min"] == 600
    assert row["duration_min"] == 90
    assert row["offer"] == "$100 off Brake Service"
    assert row["severity"] == "routine"
    assert row["badges"] == ["AI"]
    assert row["parts"] == []
    assert row["photo_urls"] == [
        "https://example.supabase.co/storage/v1/object/public/vehicle-photos/a.jpg"
    ]


@pytest.mark.asyncio
async def test_record_booking_photo_urls_defaults_to_empty_list() -> None:
    with patch.object(
        dashboard, "_insert", new_callable=AsyncMock, return_value=True
    ) as mock_insert:
        await dashboard.record_booking(
            title="Oil change", customer="Sam T.", vehicle="2017 Chevy Malibu"
        )

    _table, row = mock_insert.await_args.args
    assert row["photo_urls"] == []


# --------------------------- _insert HTTP behavior ---------------------------


class _FakeResp:
    def __init__(self, status: int) -> None:
        self.status = status

    async def __aenter__(self) -> "_FakeResp":
        return self

    async def __aexit__(self, *_a: object) -> bool:
        return False

    async def text(self) -> str:
        return "error body"


class _FakeSession:
    def __init__(self, capture: dict, status: int) -> None:
        self._capture = capture
        self._status = status

    async def __aenter__(self) -> "_FakeSession":
        return self

    async def __aexit__(self, *_a: object) -> bool:
        return False

    def post(self, url: str, json: dict, headers: dict) -> _FakeResp:
        self._capture["url"] = url
        self._capture["json"] = json
        self._capture["headers"] = headers
        return _FakeResp(self._status)


@pytest.mark.asyncio
async def test_insert_posts_to_rest_endpoint_and_drops_none(monkeypatch) -> None:
    monkeypatch.setenv("DASHBOARD_SUPABASE_URL", "https://demo.supabase.co")
    monkeypatch.setenv("DASHBOARD_SUPABASE_KEY", "sb_publishable_test")
    capture: dict = {}

    monkeypatch.setattr(
        dashboard.aiohttp,
        "ClientSession",
        lambda: _FakeSession(capture, 201),
    )

    ok = await dashboard._insert(
        "demo_calls", {"store": "Aramingo", "value": None, "intent": "Booking"}
    )

    assert ok is True
    assert capture["url"] == "https://demo.supabase.co/rest/v1/demo_calls"
    # None-valued keys dropped so DB defaults apply.
    assert capture["json"] == {"store": "Aramingo", "intent": "Booking"}
    assert capture["headers"]["apikey"] == "sb_publishable_test"
    assert capture["headers"]["Authorization"] == "Bearer sb_publishable_test"


@pytest.mark.asyncio
async def test_insert_non_fatal_on_http_error(monkeypatch) -> None:
    monkeypatch.setenv("DASHBOARD_SUPABASE_URL", "https://demo.supabase.co")
    monkeypatch.setenv("DASHBOARD_SUPABASE_KEY", "sb_publishable_test")
    monkeypatch.setattr(
        dashboard.aiohttp, "ClientSession", lambda: _FakeSession({}, 500)
    )

    assert await dashboard._insert("demo_calls", {"store": "X"}) is False


@pytest.mark.asyncio
async def test_insert_skips_without_config(monkeypatch) -> None:
    monkeypatch.setenv("DASHBOARD_SUPABASE_URL", "")
    monkeypatch.setenv("DASHBOARD_SUPABASE_KEY", "")

    called = False

    def _boom() -> None:
        nonlocal called
        called = True
        raise AssertionError("HTTP should not be attempted without config")

    monkeypatch.setattr(dashboard.aiohttp, "ClientSession", _boom)

    assert await dashboard._insert("demo_calls", {"store": "X"}) is False
    assert called is False


@pytest.mark.asyncio
async def test_emit_schedules_and_runs_coroutine() -> None:
    ran = {"v": False}

    async def _work() -> None:
        ran["v"] = True

    dashboard.emit(_work())
    # Yield control so the scheduled task runs.
    import asyncio

    await asyncio.sleep(0)
    assert ran["v"] is True

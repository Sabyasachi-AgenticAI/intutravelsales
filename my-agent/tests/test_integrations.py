import base64
from unittest.mock import AsyncMock, patch

import pytest

from integrations import pcodes, photo_storage, vlm_photo
from integrations.parts import find_parts, suggest_related_parts
from integrations.photo_storage import store_photo
from integrations.whatsapp import send_whatsapp


def test_find_parts_matches_by_name() -> None:
    results = find_parts("brake pads")
    assert {p.part_number for p in results} == {"BP-1001", "BP-1002"}


def test_find_parts_filters_by_make() -> None:
    results = find_parts("brake pads", make="Honda")
    assert len(results) == 2

    results = find_parts("brake pads", make="Ford")
    assert results == []


def test_find_parts_no_match() -> None:
    assert find_parts("flux capacitor") == []


def test_suggest_related_parts_for_symptom() -> None:
    suggestions = suggest_related_parts("There's a squealing noise when I brake")
    part_numbers = {p.part_number for p in suggestions}
    assert "BP-1001" in part_numbers
    assert "BLT-7001" in part_numbers


def test_suggest_related_parts_no_match() -> None:
    assert suggest_related_parts("the radio doesn't turn on") == []


def test_lookup_pcode_found() -> None:
    entry = pcodes.lookup_pcode("p0300")
    assert entry is not None
    assert entry.code == "P0300"
    assert entry.severity == "high"


def test_lookup_pcode_not_found() -> None:
    assert pcodes.lookup_pcode("P9999") is None


def test_find_codes_by_symptom() -> None:
    results = pcodes.find_codes_by_symptom("rough idle")
    codes = {entry.code for entry in results}
    assert "P0300" in codes
    assert "P0301" in codes


@pytest.mark.asyncio
async def test_send_whatsapp_adds_prefix_and_uses_whatsapp_from(monkeypatch) -> None:
    monkeypatch.setenv("TWILIO_ACCOUNT_SID", "AC_test")
    monkeypatch.setenv("TWILIO_AUTH_TOKEN", "test_token")
    monkeypatch.setenv("TWILIO_WHATSAPP_FROM", "+15550001111")

    with patch(
        "integrations.whatsapp._post_twilio_message", new_callable=AsyncMock
    ) as mock_post:
        await send_whatsapp(to="+15125550100", body="Your appointment is confirmed.")

    mock_post.assert_awaited_once_with(
        to="whatsapp:+15125550100",
        from_number="whatsapp:+15550001111",
        body="Your appointment is confirmed.",
    )


@pytest.mark.asyncio
async def test_analyze_vehicle_photo_sends_automotive_prompt_and_base64_image() -> None:
    fake_response = {"choices": [{"message": {"content": "That's a worn brake pad."}}]}

    with patch(
        "integrations.vlm_photo._post_chat_completion",
        new_callable=AsyncMock,
        return_value=fake_response,
    ) as mock_post:
        result = await vlm_photo.analyze_vehicle_photo(
            image_bytes=b"fake-jpeg-bytes",
            mime_type="image/jpeg",
            question="What's wrong with this part?",
        )

    assert result == "That's a worn brake pad."

    payload = mock_post.await_args.args[0]
    system_message = next(m for m in payload["messages"] if m["role"] == "system")
    assert "automotive" in system_message["content"].lower()

    user_content = payload["messages"][-1]["content"]
    image_part = next(p for p in user_content if p["type"] == "image_url")
    expected_data_url = "data:image/jpeg;base64," + base64.b64encode(
        b"fake-jpeg-bytes"
    ).decode("ascii")
    assert image_part["image_url"]["url"] == expected_data_url

    text_part = next(p for p in user_content if p["type"] == "text")
    assert text_part["text"] == "What's wrong with this part?"


@pytest.mark.asyncio
async def test_analyze_vehicle_photo_handles_missing_response_content() -> None:
    with patch(
        "integrations.vlm_photo._post_chat_completion",
        new_callable=AsyncMock,
        return_value={"choices": []},
    ):
        result = await vlm_photo.analyze_vehicle_photo(image_bytes=b"fake-jpeg-bytes")

    assert "didn't return" in result.lower()


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

    def post(self, url: str, data: bytes, headers: dict) -> _FakeResp:
        self._capture["url"] = url
        self._capture["data"] = data
        self._capture["headers"] = headers
        return _FakeResp(self._status)


@pytest.mark.asyncio
async def test_store_photo_uploads_and_returns_public_url(monkeypatch) -> None:
    capture: dict = {}
    monkeypatch.setattr(
        photo_storage.dashboard,
        "_config",
        lambda: ("https://demo.supabase.co", "sb_publishable_test"),
    )
    monkeypatch.setattr(
        photo_storage.aiohttp, "ClientSession", lambda: _FakeSession(capture, 200)
    )

    url = await store_photo(
        image_bytes=b"fake-jpeg-bytes",
        mime_type="image/jpeg",
        participant_identity="caller-123",
        analysis="That's a worn brake pad.",
    )

    assert url is not None
    assert url.startswith(
        "https://demo.supabase.co/storage/v1/object/public/vehicle-photos/caller-123/"
    )
    assert capture["url"].startswith(
        "https://demo.supabase.co/storage/v1/object/vehicle-photos/caller-123/"
    )
    assert capture["data"] == b"fake-jpeg-bytes"
    assert capture["headers"]["apikey"] == "sb_publishable_test"


@pytest.mark.asyncio
async def test_store_photo_returns_none_on_http_error(monkeypatch) -> None:
    monkeypatch.setattr(
        photo_storage.dashboard,
        "_config",
        lambda: ("https://demo.supabase.co", "sb_publishable_test"),
    )
    monkeypatch.setattr(
        photo_storage.aiohttp, "ClientSession", lambda: _FakeSession({}, 500)
    )

    url = await store_photo(
        image_bytes=b"fake-jpeg-bytes",
        mime_type="image/jpeg",
        participant_identity="caller-123",
        analysis="analysis",
    )
    assert url is None


@pytest.mark.asyncio
async def test_store_photo_returns_none_without_config(monkeypatch) -> None:
    monkeypatch.setattr(photo_storage.dashboard, "_config", lambda: None)

    def _boom() -> None:
        raise AssertionError("HTTP should not be attempted without config")

    monkeypatch.setattr(photo_storage.aiohttp, "ClientSession", _boom)

    url = await store_photo(
        image_bytes=b"fake-jpeg-bytes",
        mime_type="image/jpeg",
        participant_identity="caller-123",
        analysis="analysis",
    )
    assert url is None

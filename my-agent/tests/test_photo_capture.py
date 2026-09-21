from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from agent import ServiceAdvisorData, _handle_uploaded_photo


class _FakeByteStreamReader:
    def __init__(self, chunks: list[bytes], mime_type: str = "image/jpeg") -> None:
        self._chunks = chunks
        self.info = SimpleNamespace(mime_type=mime_type, name="photo.jpg")

    def __aiter__(self):
        return self._iter()

    async def _iter(self):
        for chunk in self._chunks:
            yield chunk


def _fake_session() -> SimpleNamespace:
    return SimpleNamespace(userdata=ServiceAdvisorData(), generate_reply=AsyncMock())


@pytest.mark.asyncio
async def test_handle_uploaded_photo_records_analysis_and_speaks_reply() -> None:
    session = _fake_session()
    reader = _FakeByteStreamReader([b"chunk1", b"chunk2"])

    with (
        patch(
            "agent.analyze_vehicle_photo",
            new_callable=AsyncMock,
            return_value="Looks like a cracked serpentine belt.",
        ) as mock_analyze,
        patch("agent.store_photo", new_callable=AsyncMock) as mock_store,
    ):
        await _handle_uploaded_photo(reader, "participant-123", session)

    mock_analyze.assert_awaited_once()
    assert mock_analyze.await_args.kwargs["image_bytes"] == b"chunk1chunk2"
    assert mock_analyze.await_args.kwargs["mime_type"] == "image/jpeg"

    mock_store.assert_awaited_once()
    assert mock_store.await_args.kwargs["participant_identity"] == "participant-123"

    assert session.userdata.photo_analyses == ["Looks like a cracked serpentine belt."]
    session.generate_reply.assert_awaited_once()
    assert (
        "cracked serpentine belt"
        in session.generate_reply.await_args.kwargs["instructions"]
    )


@pytest.mark.asyncio
async def test_handle_uploaded_photo_reports_technical_failure_gracefully() -> None:
    session = _fake_session()
    reader = _FakeByteStreamReader([b"chunk"])

    with patch(
        "agent.analyze_vehicle_photo",
        new_callable=AsyncMock,
        side_effect=Exception("boom"),
    ):
        await _handle_uploaded_photo(reader, "participant-123", session)

    assert session.userdata.photo_analyses == []
    session.generate_reply.assert_awaited_once()
    fallback_instructions = session.generate_reply.await_args.kwargs["instructions"]
    assert "technical issue" in fallback_instructions.lower()

"""Shared pytest fixtures.

The agent now runs an STT-LLM-TTS pipeline (Deepgram/OpenAI/Cartesia). Those
plugins fetch a shared aiohttp session from LiveKit's job-scoped http context,
which only exists inside the agent worker. Behavior tests that start an
`AgentSession` therefore need that context opened around them; this autouse
fixture provides it so tests can run outside the worker.
"""

import pytest_asyncio
from livekit.agents.utils import http_context


@pytest_asyncio.fixture(autouse=True)
async def _open_http_context():
    async with http_context.open():
        yield

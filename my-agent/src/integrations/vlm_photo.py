import base64
import os
from typing import Any

import aiohttp

API_BASE = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "qwen/qwen2.5-vl-72b-instruct"

_AUTOMOTIVE_SYSTEM_PROMPT = (
    "You are an automotive assistant analyzing a photo submitted by a customer "
    "during a call with a vehicle service center. Only answer questions about "
    "the vehicle, its parts, damage, warning lights, fluids, or condition shown "
    "in the photo. If a license plate is visible and legible, read it out. If "
    "the photo or question is not automotive-related, say so briefly and "
    "decline to answer anything else."
)

_DEFAULT_QUESTION = (
    "What do you see in this photo of the customer's vehicle, and is anything "
    "noteworthy about its condition?"
)


async def _post_chat_completion(payload: dict[str, Any]) -> dict[str, Any]:
    """POST to OpenRouter's OpenAI-compatible /chat/completions endpoint.

    Requires OPENROUTER_API_KEY in the environment.
    """
    api_key = os.environ["OPENROUTER_API_KEY"]
    headers = {"Authorization": f"Bearer {api_key}"}

    async with (
        aiohttp.ClientSession() as session,
        session.post(
            f"{API_BASE}/chat/completions", json=payload, headers=headers
        ) as resp,
    ):
        resp.raise_for_status()
        return await resp.json()


async def analyze_vehicle_photo(
    *,
    image_bytes: bytes,
    mime_type: str = "image/jpeg",
    question: str | None = None,
    model: str = DEFAULT_MODEL,
) -> str:
    """Ask Qwen (via OpenRouter) an automotive-only question about a photo.

    Restricted to vehicle-related content by system prompt: the model
    declines to answer if the photo or question isn't automotive-related.
    """
    data_url = (
        f"data:{mime_type};base64,{base64.b64encode(image_bytes).decode('ascii')}"
    )

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": _AUTOMOTIVE_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": question or _DEFAULT_QUESTION},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            },
        ],
    }

    data = await _post_chat_completion(payload)
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        return "Qwen didn't return a usable analysis."

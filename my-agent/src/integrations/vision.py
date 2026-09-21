import base64
import os

import aiohttp

API_BASE = "https://generativelanguage.googleapis.com/v1beta"
DEFAULT_MODEL = "gemini-2.5-flash"


async def describe_image(
    *, image_bytes: bytes, prompt: str, model: str = DEFAULT_MODEL
) -> str:
    """Ask Gemini to describe or answer a question about a JPEG image."""
    api_key = os.environ["GOOGLE_API_KEY"]
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": base64.b64encode(image_bytes).decode("ascii"),
                        }
                    },
                ]
            }
        ]
    }

    async with (
        aiohttp.ClientSession() as session,
        session.post(
            f"{API_BASE}/models/{model}:generateContent",
            params={"key": api_key},
            json=payload,
        ) as resp,
    ):
        resp.raise_for_status()
        data = await resp.json()

    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        return "Gemini didn't return a usable description."

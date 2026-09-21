"""Persist caller-uploaded vehicle photos to Supabase Storage.

Photos sent via the in-call photo button (see `_handle_uploaded_photo` in
agent.py) are uploaded here so a public URL can travel with the booking and
render on the Shop board. Best-effort: a storage failure never blocks sharing
the Qwen analysis with the caller — the call already has the answer, uploading
is just how we make it visible to the shop.
"""

import logging
import time
import uuid

import aiohttp

from integrations import dashboard

logger = logging.getLogger("agent.integrations.photo_storage")

BUCKET = "vehicle-photos"


async def store_photo(
    *,
    image_bytes: bytes,
    mime_type: str,
    participant_identity: str,
    analysis: str,
) -> str | None:
    """Upload a photo to Supabase Storage and return its public URL.

    Returns None (and logs) on any failure — storage is a nice-to-have for
    the shop board, not something a photo-analysis reply should ever wait on
    or fail because of.
    """
    cfg = dashboard._config()
    if cfg is None:
        logger.debug("photo_storage: no Supabase config; skipping upload")
        return None
    base_url, key = cfg

    ext = (mime_type.rsplit("/", 1)[-1] or "jpg").split("+")[0]
    path = f"{participant_identity}/{int(time.time())}-{uuid.uuid4().hex[:8]}.{ext}"

    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": mime_type,
    }
    try:
        async with (
            aiohttp.ClientSession() as session,
            session.post(
                f"{base_url}/storage/v1/object/{BUCKET}/{path}",
                data=image_bytes,
                headers=headers,
            ) as resp,
        ):
            if resp.status >= 400:
                body = await resp.text()
                logger.warning("photo upload failed (%s): %s", resp.status, body)
                return None
    except Exception:
        logger.exception("photo upload errored")
        return None

    logger.info(
        "stored photo (%d bytes, %s) for %s at %s",
        len(image_bytes),
        mime_type,
        participant_identity,
        path,
    )
    return f"{base_url}/storage/v1/object/public/{BUCKET}/{path}"

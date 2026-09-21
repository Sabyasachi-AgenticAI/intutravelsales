"""Emit live call/booking events to the ops & shop dashboards.

The dashboards in `frontend/public/ops.html` and `frontend/public/shop.html`
subscribe to two Supabase tables via realtime:

- `demo_calls`   — the ops live feed (every call outcome).
- `demo_bookings`— the shop "arriving next" queue and bay board, and shows up
  on the ops feed too.

This module inserts rows into those tables over Supabase's REST (PostgREST)
endpoint using the publishable key. Every write is best-effort and non-fatal:
a dashboard insert must never add latency to, or fail, a live voice call. Use
`emit()` to fire a write off the voice turn's critical path.
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Any

import aiohttp

logger = logging.getLogger("agent.integrations.dashboard")

# Demo Supabase project — the same world-insert tables the ops/shop dashboards
# read from. The publishable key is safe to embed: the demo_calls/demo_bookings
# tables are world-read/insert and truncated between demos (see the matching
# note in ops.html/shop.html). Override both via env for a real deployment.
_DEFAULT_URL = "https://cpoxlwfvgtifgybjyvnm.supabase.co"
_DEFAULT_KEY = "sb_publishable_BmJ4oJYthFcQhqW5B8d5eA_nDGUa738"

# Track fire-and-forget writes so they aren't garbage-collected mid-flight.
_pending: set[asyncio.Task] = set()


def _config() -> tuple[str, str] | None:
    """Return (base_url, key), or None if either is unset (disables writes)."""
    url = os.environ.get("DASHBOARD_SUPABASE_URL", _DEFAULT_URL)
    key = os.environ.get("DASHBOARD_SUPABASE_KEY", _DEFAULT_KEY)
    if not url or not key:
        return None
    return url.rstrip("/"), key


async def _insert(
    table: str, row: dict[str, Any], *, returning: bool = False
) -> bool | str | None:
    """POST a single row into a public demo table. Never raises.

    Keys whose value is None are dropped so the column's database default (e.g.
    `severity`, `outcome_type`, `badges`, `parts`) applies. By default returns
    True only on a 2xx response. If `returning=True`, asks PostgREST for the
    inserted row and returns its `id` (str) on success, or None on any failure.
    """
    cfg = _config()
    if cfg is None:
        logger.debug("dashboard: no Supabase config; skipping %s insert", table)
        return None if returning else False
    base_url, key = cfg

    payload = {k: v for k, v in row.items() if v is not None}
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation" if returning else "return=minimal",
    }
    try:
        async with (
            aiohttp.ClientSession() as session,
            session.post(
                f"{base_url}/rest/v1/{table}", json=payload, headers=headers
            ) as resp,
        ):
            if resp.status >= 400:
                body = await resp.text()
                logger.warning(
                    "dashboard %s insert failed (%s): %s", table, resp.status, body
                )
                return None if returning else False
            if returning:
                try:
                    data = await resp.json()
                    row_id = data[0]["id"] if isinstance(data, list) and data else None
                except (ValueError, KeyError, IndexError, TypeError):
                    logger.exception("dashboard %s insert: could not read id", table)
                    return None
                return str(row_id) if row_id is not None else None
    except Exception:
        logger.exception("dashboard %s insert errored", table)
        return None if returning else False
    return True


async def update_booking(booking_id: str, fields: dict[str, Any]) -> bool:
    """PATCH an existing `demo_bookings` row — e.g. to attach a photo that
    arrived after the ticket was created. Best-effort; never raises.
    """
    cfg = _config()
    if cfg is None:
        return False
    base_url, key = cfg
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }
    url = f"{base_url}/rest/v1/demo_bookings?id=eq.{booking_id}"
    try:
        async with (
            aiohttp.ClientSession() as session,
            session.patch(url, json=fields, headers=headers) as resp,
        ):
            if resp.status >= 400:
                body = await resp.text()
                logger.warning(
                    "dashboard booking update failed (%s): %s", resp.status, body
                )
                return False
    except Exception:
        logger.exception("dashboard booking update errored")
        return False
    return True


async def record_call(
    *,
    store: str,
    intent: str,
    summary: str,
    outcome: str,
    outcome_type: str = "good",
    value: str | None = None,
    duration: str | None = None,
    upsell: str | None = None,
    extra: str | None = None,
) -> bool:
    """Record a call outcome on the ops live feed (`demo_calls`).

    `outcome_type` drives the feed chip colour: "good", "info", "neutral",
    "critical", or "upsell".
    """
    return await _insert(
        "demo_calls",
        {
            "store": store,
            "intent": intent,
            "summary": summary,
            "outcome": outcome,
            "outcome_type": outcome_type,
            "value": value,
            "duration": duration,
            "upsell": upsell,
            "extra": extra,
        },
    )


async def record_booking(
    *,
    title: str,
    customer: str,
    vehicle: str,
    store: str = "Aramingo",
    phone: str | None = None,
    arrive_at: str | None = None,
    bay: int | None = None,
    start_min: int | None = None,
    duration_min: int | None = None,
    booking_date: str | None = None,
    offer: str | None = None,
    severity: str = "routine",
    badges: list[str] | None = None,
    note: str | None = None,
    complaint: str | None = None,
    triage: str | None = None,
    dtc: str | None = None,
    parts: list[list[str]] | None = None,
    promised: str | None = None,
    booked_via: str | None = None,
    photo_urls: list[str] | None = None,
) -> str | None:
    """Record a booking on the shop board + ops feed (`demo_bookings`).

    Returns the new row's `id` (str) on success, or None on failure — the id
    lets the caller update the ticket later (e.g. attach a late photo).

    `severity` is "routine" | "diag" | "urgent"; `parts` is a list of
    [name, "in" | "ord"] pairs staged for the job. `phone` is the customer's
    contact number, `store` the service center the car is going to, and
    `complaint` the problem the caller reported. `bay`/`start_min`/`duration_min`
    place the appointment on the live bay schedule (start_min is minutes from
    midnight; bay is 0-3). `booking_date` is the appointment's calendar date as
    an ISO string ("YYYY-MM-DD"); omit it for a same-day booking (the board dates
    undated rows to their creation day). `photo_urls` are public Supabase Storage
    URLs for any photos the caller sent during the call, shown on the shop ticket.
    """
    return await _insert(
        "demo_bookings",
        {
            "store": store,
            "phone": phone,
            "arrive_at": arrive_at,
            "bay": bay,
            "start_min": start_min,
            "duration_min": duration_min,
            "booking_date": booking_date,
            "offer": offer,
            "title": title,
            "customer": customer,
            "vehicle": vehicle,
            "severity": severity,
            "badges": badges if badges is not None else ["AI"],
            "note": note,
            "complaint": complaint,
            "triage": triage,
            "dtc": dtc,
            "parts": parts if parts is not None else [],
            "photo_urls": photo_urls if photo_urls is not None else [],
            "promised": promised,
            "booked_via": booked_via,
        },
        returning=True,
    )


def emit(coro: "asyncio.Future | Any") -> None:
    """Schedule a dashboard write without blocking the current voice turn.

    Fire-and-forget: exceptions inside the write are already swallowed by the
    record_* helpers, and if there's no running event loop the coroutine is
    simply discarded.
    """
    try:
        task = asyncio.create_task(coro)
    except RuntimeError:
        # No running loop (e.g. called from a sync context); nothing to do.
        if hasattr(coro, "close"):
            coro.close()
        return
    _pending.add(task)
    task.add_done_callback(_pending.discard)


# --------------------------- pure field helpers ---------------------------
# Kept side-effect-free so the agent's state -> row mapping is unit-testable.


def format_vehicle(vehicle: dict[str, Any] | None) -> str:
    """Render a decoded-VIN dict as "2019 Toyota Camry"-style text."""
    if not vehicle:
        return "Vehicle"
    ordered = [
        str(vehicle[k]) for k in ("ModelYear", "Make", "Model") if vehicle.get(k)
    ]
    return " ".join(ordered) or "Vehicle"


def derive_severity(
    *, emergency_active: bool, vehicle_drivable: bool | None, has_diagnosis: bool
) -> str:
    """Map call state to a shop-board severity band."""
    if emergency_active or vehicle_drivable is False:
        return "urgent"
    if has_diagnosis:
        return "diag"
    return "routine"


def derive_badges(*, has_photo: bool, undrivable: bool) -> list[str]:
    """Every AI-booked job carries the AI badge, plus PHOTO/TOW when they apply."""
    badges = ["AI"]
    if has_photo:
        badges.append("PHOTO")
    if undrivable:
        badges.append("TOW")
    return badges


def friendly_time(iso: str, tz_name: str | None = None) -> str:
    """Turn an ISO-8601 timestamp into a "2:00 PM"-style label.

    Converts to `tz_name` when the zone is available (falls back to the
    timestamp's own offset otherwise), and returns the input unchanged if it
    can't be parsed.
    """
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return iso
    if tz_name:
        try:
            from zoneinfo import ZoneInfo

            dt = dt.astimezone(ZoneInfo(tz_name))
        except Exception:
            pass
    hour = dt.hour % 12 or 12
    return f"{hour}:{dt.minute:02d} {'AM' if dt.hour < 12 else 'PM'}"

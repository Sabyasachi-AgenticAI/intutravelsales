"""Bay-native scheduling over the live shop board (`demo_bookings`).

The shop's bay schedule IS the calendar: availability is computed from open
[time x bay] slots, and booking writes straight to `demo_bookings` (via
`dashboard.record_booking`), which reflects on the board in real time. This
replaces the earlier Calendly integration, so availability the agent offers is
always a genuinely-free bay.
"""

import logging
import re
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import aiohttp

from integrations import dashboard

logger = logging.getLogger("agent.integrations.scheduling")

# Shop day + bays (mirror frontend/public/shop.html).
BUSINESS_START = 8 * 60  # 08:00
BUSINESS_END = 18 * 60  # 18:00
NUM_BAYS = 4
SLOT_STEP = 30  # offer/align slots on the half hour
DEFAULT_DURATION = 90

# How far ahead a caller can book. Same-day plus a rolling window of future days.
MAX_ADVANCE_DAYS = 30

# Alpine View, Comstock Park, MI is in US Eastern time.
SHOP_TIMEZONE = "America/Detroit"


def now_local() -> datetime:
    """Current wall-clock time at the shop (US Eastern)."""
    return datetime.now(ZoneInfo(SHOP_TIMEZONE))


def now_min() -> int:
    """Current time today, in minutes since midnight, at the shop."""
    n = now_local()
    return n.hour * 60 + n.minute


def today_date() -> date:
    """Today's calendar date at the shop (US Eastern)."""
    return now_local().date()


def today_label() -> str:
    """Today's date, spoken-friendly, e.g. "Monday, July 14, 2026"."""
    return now_local().strftime("%A, %B %d, %Y")


def resolve_day(day: str | None, *, today: date | None = None) -> date | None:
    """Turn a `day` argument into a real calendar date, or None if unparseable.

    Accepts "today"/"tonight", "tomorrow", or an ISO date "YYYY-MM-DD" (the LLM
    resolves phrases like "next Tuesday" to an ISO date using the known current
    date). An empty/None day means today. Returns None only when the string
    can't be parsed — range checking is separate (`within_booking_window`)."""
    base = today or today_date()
    if not day or not day.strip():
        return base
    d = day.strip().lower()
    if d in ("today", "tonight", "this afternoon", "this morning"):
        return base
    if d == "tomorrow":
        return base + timedelta(days=1)
    try:
        return date.fromisoformat(day.strip())
    except ValueError:
        return None


def within_booking_window(d: date, *, today: date | None = None) -> bool:
    """True if `d` is today or within the next MAX_ADVANCE_DAYS days (not past)."""
    base = today or today_date()
    return base <= d <= base + timedelta(days=MAX_ADVANCE_DAYS)


def is_today(d: date, *, today: date | None = None) -> bool:
    """True if `d` is the shop's current date."""
    return d == (today or today_date())


def date_label(d: date, *, today: date | None = None) -> str:
    """Spoken-friendly label for a booking date: "today", "tomorrow", or a full
    weekday+date like "Monday, July 21"."""
    base = today or today_date()
    if d == base:
        return "today"
    if d == base + timedelta(days=1):
        return "tomorrow"
    return d.strftime("%A, %B %d")


# Keyword -> service duration (minutes). First match wins; order matters.
_SERVICE_DURATIONS: list[tuple[tuple[str, ...], int]] = [
    (("no start", "won't start", "wont start", "tow", "no-start", "no crank"), 180),
    (("misfire", "check engine", "diagnostic", "diagnose", "warning light"), 120),
    (("a/c", "air condition", "coolant", "overheat", "radiator"), 120),
    (("brake", "rotor", "pad"), 90),
    (("alignment",), 60),
    (("tire", "tyre", "flat", "puncture"), 60),
    (("oil", "rotation"), 60),
    (("battery",), 45),
    (("inspection", "wiper", "filter", "bulb"), 30),
]


def duration_for(service: str | None) -> int:
    """Estimate how long a service will occupy a bay, from its description."""
    text = (service or "").lower()
    for keywords, minutes in _SERVICE_DURATIONS:
        if any(k in text for k in keywords):
            return minutes
    return DEFAULT_DURATION


def within_business_hours(start_min: int, duration: int) -> bool:
    """True if a `duration`-minute job starting at `start_min` fits inside the
    shop day (8 AM to 6 PM). The whole job must finish by close."""
    return start_min >= BUSINESS_START and start_min + duration <= BUSINESS_END


def parse_time(txt: str) -> int | None:
    """Parse a clock time like "9:30 AM" or "2 PM" into minutes from midnight."""
    if not txt:
        return None
    m = re.search(r"(\d{1,2}):(\d{2})\s*([ap])", txt, re.IGNORECASE)
    if m:
        hh = int(m.group(1)) % 12
        if m.group(3).lower() == "p":
            hh += 12
        return hh * 60 + int(m.group(2))
    m = re.search(r"(\d{1,2})\s*([ap])", txt, re.IGNORECASE)
    if m:
        hh = int(m.group(1)) % 12
        if m.group(2).lower() == "p":
            hh += 12
        return hh * 60
    return None


def fmt_time(minutes: int) -> str:
    """Render minutes-from-midnight as "9:30 AM"."""
    h, mm = divmod(minutes, 60)
    ap = "AM" if h < 12 else "PM"
    hh = h % 12 or 12
    return f"{hh}:{mm:02d} {ap}"


def _occupancy(scheduled: list[dict]) -> list[list[tuple[int, int]]]:
    occ: list[list[tuple[int, int]]] = [[] for _ in range(NUM_BAYS)]
    for j in scheduled:
        bay, start, dur = j.get("bay"), j.get("start_min"), j.get("duration_min")
        if bay is None or start is None or dur is None:
            continue
        if 0 <= bay < NUM_BAYS:
            occ[bay].append((start, start + dur))
    return occ


def _overlaps(intervals: list[tuple[int, int]], s: int, e: int) -> bool:
    return any(s < iv[1] and e > iv[0] for iv in intervals)


def find_open_slots(
    scheduled: list[dict],
    duration: int,
    *,
    from_min: int | None = None,
    limit: int = 5,
) -> list[tuple[int, int]]:
    """Return up to `limit` open (start_min, bay) slots of `duration` minutes,
    spread across the rest of the business day.

    Walks the day on `SLOT_STEP` boundaries and takes the first free bay at
    each time to build the full list of openings, then samples `limit` of them
    evenly across that list (always including the soonest and the latest).
    Without the spread, a bay that's busy all morning can exhaust the limit on
    a cluster of early-morning gaps and never surface the wide-open afternoon.
    """
    occ = _occupancy(scheduled)
    start = BUSINESS_START if from_min is None else max(from_min, BUSINESS_START)
    if start % SLOT_STEP:
        start += SLOT_STEP - (start % SLOT_STEP)

    candidates: list[tuple[int, int]] = []
    t = start
    while t + duration <= BUSINESS_END:
        for bay in range(NUM_BAYS):
            if not _overlaps(occ[bay], t, t + duration):
                candidates.append((t, bay))
                break
        t += SLOT_STEP

    if len(candidates) <= limit:
        return candidates
    if limit <= 1:
        return candidates[:limit]

    step = (len(candidates) - 1) / (limit - 1)
    indices = sorted({round(i * step) for i in range(limit)})
    return [candidates[i] for i in indices]


def assign_bay(scheduled: list[dict], start_min: int, duration: int) -> int | None:
    """Return a free bay for [start_min, start_min+duration], or None if full."""
    occ = _occupancy(scheduled)
    for bay in range(NUM_BAYS):
        if not _overlaps(occ[bay], start_min, start_min + duration):
            return bay
    return None


def _day_filter(for_date: date) -> str:
    """PostgREST filter selecting bookings that occupy bays on `for_date`.

    A row belongs to the day if its `booking_date` equals it, or — for legacy
    rows written before the column existed — if it has no `booking_date` and was
    created on that date (matching how the shop board dates undated rows)."""
    iso = for_date.isoformat()
    nxt = (for_date + timedelta(days=1)).isoformat()
    return (
        f"&or=(booking_date.eq.{iso},"
        f"and(booking_date.is.null,created_at.gte.{iso},created_at.lt.{nxt}))"
    )


async def get_scheduled(for_date: date | None = None) -> list[dict]:
    """Fetch bay-assigned bookings (bay/start_min/duration_min) for one day.

    Defaults to today. Best-effort: returns [] if scheduling isn't configured or
    the read fails, so the agent degrades gracefully rather than crashing a call.
    """
    cfg = dashboard._config()
    if cfg is None:
        return []
    base_url, key = cfg
    day = for_date or today_date()
    url = (
        f"{base_url}/rest/v1/demo_bookings"
        "?select=bay,start_min,duration_min,booking_date,created_at&bay=not.is.null"
        + _day_filter(day)
    )
    headers = {"apikey": key, "Authorization": f"Bearer {key}"}
    try:
        async with (
            aiohttp.ClientSession() as session,
            session.get(url, headers=headers) as resp,
        ):
            if resp.status >= 400:
                logger.warning("scheduling read failed (%s)", resp.status)
                return []
            data = await resp.json()
            return data if isinstance(data, list) else []
    except Exception:
        logger.exception("scheduling read errored")
        return []

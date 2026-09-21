"""Tow pricing, read live from the Supabase `tow_rates` catalog.

When a caller's vehicle can't be driven in, the agent quotes the right rate
(light vs medium duty by vehicle) and can arrange the tow. Rates live in the
database so they can be updated without a redeploy.
"""

import logging

import aiohttp

from integrations import dashboard

logger = logging.getLogger("agent.integrations.towing")

# Vehicles that fall into the medium-duty rate. Anything else is light duty.
_MEDIUM_KEYWORDS = (
    "box truck",
    "cargo van",
    "sprinter",
    "transit",
    "dually",
    "f-350",
    "f350",
    "f-450",
    "f450",
    "f-550",
    "medium duty",
    "flatbed",
    "u-haul",
    "uhaul",
    "rv",
    "motorhome",
    "shuttle",
    "heavy",
)


def classify(vehicle: str | None) -> str:
    """Classify a vehicle as 'light' or 'medium' duty for tow pricing."""
    text = (vehicle or "").lower()
    if any(k in text for k in _MEDIUM_KEYWORDS):
        return "medium"
    return "light"


def rate_for(rates: list[dict], duty_class: str) -> dict | None:
    """Pick the rate row for a duty class, falling back to the first row."""
    for r in rates:
        if r.get("class") == duty_class:
            return r
    return rates[0] if rates else None


async def get_rates() -> list[dict]:
    """Fetch active tow rates. Best-effort → [] so a quote never breaks a call."""
    cfg = dashboard._config()
    if cfg is None:
        return []
    base_url, key = cfg
    url = (
        f"{base_url}/rest/v1/tow_rates"
        "?select=class,label,base_price,base_miles,max_weight_lbs,note"
        "&active=eq.true&order=base_price"
    )
    headers = {"apikey": key, "Authorization": f"Bearer {key}"}
    try:
        async with (
            aiohttp.ClientSession() as session,
            session.get(url, headers=headers) as resp,
        ):
            if resp.status >= 400:
                logger.warning("tow_rates read failed (%s)", resp.status)
                return []
            data = await resp.json()
            return data if isinstance(data, list) else []
    except Exception:
        logger.exception("tow_rates read errored")
        return []

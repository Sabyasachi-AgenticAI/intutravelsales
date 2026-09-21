"""Current Midas coupons, read live from the Supabase `offers` catalog.

The agent mentions a relevant coupon during a booking; the frontend renders the
same rows. Keeping the catalog in the database (not code) means promos can be
updated without a redeploy, and expired ones drop off automatically.
"""

import datetime
import logging

import aiohttp

from integrations import dashboard

logger = logging.getLogger("agent.integrations.offers")

# Map a service description to an offers category. First keyword match wins.
_CATEGORY_KEYWORDS: list[tuple[tuple[str, ...], str]] = [
    (("brake", "rotor", "pad"), "brakes"),
    (
        ("battery", "batteries", "jump", "no start", "won't start", "wont start"),
        "batteries",
    ),
    (("a/c", "air condition", "coolant", "overheat", "refrigerant", "ac "), "ac"),
    (("tire", "tyre", "wheel", "alignment"), "tires"),
    (("oil", "rotation", "lube"), "oil"),
]


def category_for(service: str | None) -> str | None:
    """Best-guess offers category for a service description, or None."""
    text = (service or "").lower()
    for keywords, category in _CATEGORY_KEYWORDS:
        if any(k in text for k in keywords):
            return category
    return None


# Some coupons are conditional. The tire deals ("Free 4th Tire", "set of 4")
# only apply when the caller is buying a full set of four tires — never for a
# rotation, a single tire, or a repair. We detect that requirement from the
# coupon's own text so it stays correct if the catalog changes.
_FULL_SET_COUPON_MARKERS = (
    "4th tire",
    "set of 4",
    "set of four",
    "buy and install 4",
    "buy 4",
    "install 4",
    "four tires",
    "4 tires",
)
_FULL_SET_SERVICE_MARKERS = ("full set", "set of", "all four", "all 4", "new set")


def requires_full_set(coupon: dict) -> bool:
    """True if this coupon is contingent on buying a full set of four tires."""
    text = " ".join(str(coupon.get(k, "")) for k in ("headline", "title", "terms"))
    text = text.lower()
    return any(m in text for m in _FULL_SET_COUPON_MARKERS)


def service_is_full_set(service: str | None) -> bool:
    """True if the service description clearly means a full set of four tires."""
    t = (service or "").lower()
    if any(m in t for m in _FULL_SET_SERVICE_MARKERS):
        return True
    has_four = "4" in t or "four" in t
    tire_ctx = "tire" in t or "tyre" in t or "set" in t
    return has_four and tire_ctx


def is_eligible(coupon: dict, service: str | None) -> bool:
    """Whether `coupon` may be offered for `service`. A full-set tire deal is
    withheld unless the caller is actually replacing all four tires."""
    if requires_full_set(coupon):
        return service_is_full_set(service)
    return True


async def get_offers(category: str | None) -> list[dict]:
    """Fetch active, non-expired offers for a category. Best-effort → [].

    Returns [] if the category is unknown, scheduling isn't configured, or the
    read fails, so a coupon lookup never breaks a call.
    """
    cfg = dashboard._config()
    if cfg is None or not category:
        return []
    base_url, key = cfg
    today = datetime.date.today().isoformat()
    url = (
        f"{base_url}/rest/v1/offers"
        "?select=headline,title,terms,cta,code,expires_on"
        f"&category=eq.{category}&active=eq.true&expires_on=gte.{today}&order=sort"
    )
    headers = {"apikey": key, "Authorization": f"Bearer {key}"}
    try:
        async with (
            aiohttp.ClientSession() as session,
            session.get(url, headers=headers) as resp,
        ):
            if resp.status >= 400:
                logger.warning("offers read failed (%s)", resp.status)
                return []
            data = await resp.json()
            return data if isinstance(data, list) else []
    except Exception:
        logger.exception("offers read errored")
        return []

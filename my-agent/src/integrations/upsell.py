"""Deterministic, reason-first upsell recommendations.

Given the main service a caller is booking, pick the ONE most relevant add-on
AND the concrete, trust-building reason to lead with — "already on the ramp so
you save the labor and a second trip", "it's due at your mileage", or "while
we're already in there". Keeping the add-on and its rationale in code (not the
model) means every call gets the same honest, relevant pitch instead of an
improvised one.

A coupon, when one exists, is a *closer* the agent adds after the reason — never
the hook. The reason has to stand on its own; the deal only sweetens it.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Upsell:
    """One reason-first recommendation.

    `add_on` is the extra to offer, `reason` the value line to lead with, and
    `offer_category` the coupon bucket to check for a closer (None = lead on the
    reason alone; most add-ons have no standing coupon and that's fine)."""

    add_on: str
    reason: str
    offer_category: str | None = None


# Main-service keyword(s) -> the one relevant add-on + why. First match wins, so
# order matters: more specific services come before broader ones. Reasons are
# written spoken-friendly (no slashes or symbols) since the agent says them aloud.
_RULES: list[tuple[tuple[str, ...], Upsell]] = [
    (
        ("brake", "rotor", "pad"),
        Upsell(
            "a wheel alignment",
            "since we'll already have it up on the rack for the brakes, we can set "
            "the alignment at the same time — that saves you a second trip and the "
            "extra labor of putting it back on the rack another day",
            None,
        ),
    ),
    (
        ("strut", "shock", "suspension", "control arm"),
        Upsell(
            "a wheel alignment",
            "any time we touch the suspension the alignment has to be reset anyway, "
            "so it's a lot cheaper to do it now while it's already apart than to "
            "bring it back for it later",
            None,
        ),
    ),
    (
        ("tire", "tyre", "wheel"),
        Upsell(
            "a wheel alignment",
            "with a fresh set of tires, an alignment keeps them wearing evenly so "
            "they last a lot longer — and it's the perfect moment since the wheels "
            "are already off",
            None,
        ),
    ),
    (
        ("alignment",),
        Upsell(
            "a tire rotation",
            "while it's up on the alignment rack, we can rotate the tires too so "
            "they wear evenly — no separate visit for it",
            # No coupon: the "tires" coupons are tire-purchase deals, not a
            # rotation, so quoting one here would be a mismatch. Lead on reason.
            None,
        ),
    ),
    (
        ("oil", "lube"),
        Upsell(
            "a tire rotation",
            "since it's already up on the lift for the oil, we can rotate the tires "
            "at the same time, so you don't make a separate trip for it",
            None,  # tire-purchase coupons don't apply to a rotation — reason only
        ),
    ),
    (
        ("air condition", "a/c", "ac ", "refrigerant"),
        Upsell(
            "a cabin air filter",
            "while we're already in there for the air conditioning, the cabin air "
            "filter sits right behind the glove box — easy to swap while it's open, "
            "and it helps your airflow",
            None,
        ),
    ),
    (
        ("coolant", "overheat", "radiator", "cooling"),
        Upsell(
            "a belts and hoses check",
            "since the cooling system will already be open, it's a good moment to "
            "look over the belts and hoses for wear before one lets go on you",
            None,
        ),
    ),
    (
        ("battery", "charging", "no start", "won't start", "wont start", "alternator"),
        Upsell(
            "a charging-system check",
            "while we've got the electrical apart, a quick charging-system test "
            "makes sure the alternator isn't the real culprit — that saves you a "
            "comeback down the road",
            # No coupon: "batteries" coupons cover a battery purchase/install, not
            # a charging-system diagnostic, so it wouldn't apply. Reason only.
            None,
        ),
    ),
    (
        ("spark plug", "tune", "ignition", "misfire"),
        Upsell(
            "a new engine air filter",
            "while the engine's already open for the plugs, a fresh air filter "
            "helps everything run clean — it's the natural time to do it",
            None,
        ),
    ),
    (
        ("inspection",),
        Upsell(
            "an oil change",
            "if you're about due for an oil change, we can knock it out during the "
            "inspection so it's one visit instead of two",
            "oil",
        ),
    ),
    (
        ("wiper", "blade", "bulb"),
        Upsell(
            "a fresh set of wiper blades",
            "since you're already coming in, we can pop on new wiper blades while "
            "you're here so you're set for the season",
            None,
        ),
    ),
]

# Safe universal fallback when nothing specific fits — a due oil change is
# relevant to almost any vehicle and frames as saving a separate trip.
_DEFAULT = Upsell(
    "a due oil change",
    "if you're about due for an oil change, we could take care of it in the same "
    "visit and save you a separate trip",
    "oil",
)


def recommend(main_service: str | None) -> Upsell:
    """The one reason-first add-on to offer for `main_service`.

    Always returns a recommendation (falls back to a due oil change); deciding
    *whether* to offer it at all — the stress/time-pressure gate — is the agent's
    judgment, not this function's."""
    text = (main_service or "").lower()
    for keywords, rec in _RULES:
        if any(k in text for k in keywords):
            return rec
    return _DEFAULT

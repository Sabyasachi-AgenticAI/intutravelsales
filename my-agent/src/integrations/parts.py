from dataclasses import dataclass, field


@dataclass(frozen=True)
class Part:
    name: str
    part_number: str
    price_usd: float
    quantity_in_stock: int
    # Makes this part fits; empty list means universal/not make-specific.
    compatible_makes: list[str] = field(default_factory=list)


# Placeholder warehouse catalog. Replace with a real inventory/DMS integration —
# `find_parts` and `suggest_related_parts` are the seams to swap out.
PARTS_CATALOG: list[Part] = [
    Part("Front brake pads", "BP-1001", 45.99, 24, ["Honda", "Toyota"]),
    Part("Rear brake pads", "BP-1002", 42.99, 18, ["Honda", "Toyota"]),
    Part("Brake rotor", "BR-2001", 89.99, 12, ["Honda", "Toyota"]),
    Part("Car battery (Group 35)", "BAT-3001", 129.99, 30, []),
    Part("Battery terminal cleaner kit", "BAT-3002", 9.99, 50, []),
    Part("Engine air filter", "AF-4001", 24.99, 40, []),
    Part("Cabin air filter", "AF-4002", 19.99, 35, []),
    Part("Full synthetic motor oil (5qt)", "OIL-5001", 34.99, 60, []),
    Part("Oil filter", "OIL-5002", 8.99, 75, []),
    Part("Spark plug (set of 4)", "SP-6001", 39.99, 20, []),
    Part("Serpentine belt", "BLT-7001", 29.99, 15, []),
    Part("Wiper blade (pair)", "WB-8001", 22.99, 45, []),
]

# Naive keyword pairings used for upsell suggestions during diagnostics/service.
_UPSELL_KEYWORDS: dict[str, list[str]] = {
    "brake": ["BP-1001", "BP-1002", "BR-2001"],
    "battery": ["BAT-3001", "BAT-3002"],
    "oil": ["OIL-5001", "OIL-5002"],
    "air filter": ["AF-4001", "AF-4002"],
    "spark plug": ["SP-6001"],
    "misfire": ["SP-6001"],
    "belt": ["BLT-7001"],
    "squeal": ["BLT-7001", "BP-1001", "BP-1002"],
    "wiper": ["WB-8001"],
}


def find_parts(query: str, *, make: str | None = None) -> list[Part]:
    """Find catalog parts matching a free-text query, optionally filtered by make."""
    query_lower = query.strip().lower()
    matches = [p for p in PARTS_CATALOG if query_lower in p.name.lower()]
    if make:
        make_lower = make.strip().lower()
        matches = [
            p
            for p in matches
            if not p.compatible_makes
            or any(m.lower() == make_lower for m in p.compatible_makes)
        ]
    return matches


def suggest_related_parts(symptom_or_service: str) -> list[Part]:
    """Suggest parts commonly relevant to a symptom or service, for upsell prompts."""
    query_lower = symptom_or_service.strip().lower()
    part_numbers: set[str] = set()
    for keyword, numbers in _UPSELL_KEYWORDS.items():
        if keyword in query_lower:
            part_numbers.update(numbers)
    return [p for p in PARTS_CATALOG if p.part_number in part_numbers]

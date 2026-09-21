from dataclasses import dataclass, field
from typing import Literal


@dataclass(frozen=True)
class PCodeEntry:
    code: str  # e.g. "P0301"
    description: str
    likely_causes: list[str] = field(default_factory=list)
    common_symptoms: list[str] = field(default_factory=list)
    severity: Literal["low", "medium", "high"] = "medium"


# Placeholder OBD-II P-code reference. Covers a handful of the most common
# codes as a starting point — replace/extend with a full reference dataset.
PCODE_REFERENCE: list[PCodeEntry] = [
    PCodeEntry(
        code="P0300",
        description="Random/multiple cylinder misfire detected",
        likely_causes=["Worn spark plugs", "Faulty ignition coils", "Vacuum leak"],
        common_symptoms=["Engine shaking", "Rough idle", "Loss of power"],
        severity="high",
    ),
    PCodeEntry(
        code="P0301",
        description="Cylinder 1 misfire detected",
        likely_causes=[
            "Worn spark plug",
            "Faulty ignition coil",
            "Fuel injector issue",
        ],
        common_symptoms=["Engine shaking", "Rough idle", "Check engine light"],
        severity="medium",
    ),
    PCodeEntry(
        code="P0420",
        description="Catalyst system efficiency below threshold (Bank 1)",
        likely_causes=[
            "Failing catalytic converter",
            "Faulty oxygen sensor",
            "Exhaust leak",
        ],
        common_symptoms=["Check engine light", "Reduced fuel economy", "Sulfur smell"],
        severity="medium",
    ),
    PCodeEntry(
        code="P0128",
        description="Coolant thermostat below regulating temperature",
        likely_causes=[
            "Stuck-open thermostat",
            "Low coolant level",
            "Faulty coolant sensor",
        ],
        common_symptoms=["Poor heater performance", "Engine runs cooler than normal"],
        severity="low",
    ),
    PCodeEntry(
        code="P0217",
        description="Engine coolant over temperature condition",
        likely_causes=[
            "Low coolant",
            "Failed water pump",
            "Radiator blockage",
            "Blown head gasket",
        ],
        common_symptoms=[
            "Temperature gauge in red",
            "Steam from hood",
            "Engine shutdown warning",
        ],
        severity="high",
    ),
    PCodeEntry(
        code="P0171",
        description="System too lean (Bank 1)",
        likely_causes=["Vacuum leak", "Dirty mass airflow sensor", "Weak fuel pump"],
        common_symptoms=[
            "Rough idle",
            "Hesitation on acceleration",
            "Check engine light",
        ],
        severity="medium",
    ),
    PCodeEntry(
        code="P0562",
        description="System voltage low",
        likely_causes=[
            "Weak/failing battery",
            "Bad alternator",
            "Corroded battery terminals",
        ],
        common_symptoms=["Dim lights", "Slow cranking", "Battery warning light"],
        severity="medium",
    ),
]

_PCODE_BY_CODE = {entry.code: entry for entry in PCODE_REFERENCE}


def lookup_pcode(code: str) -> PCodeEntry | None:
    """Look up a P-code by exact code, e.g. 'P0301'."""
    return _PCODE_BY_CODE.get(code.strip().upper())


def find_codes_by_symptom(symptom_query: str) -> list[PCodeEntry]:
    """Find P-code entries whose description or common symptoms match a free-text query."""
    query_lower = symptom_query.strip().lower()
    return [
        entry
        for entry in PCODE_REFERENCE
        if query_lower in entry.description.lower()
        or any(query_lower in symptom.lower() for symptom in entry.common_symptoms)
    ]

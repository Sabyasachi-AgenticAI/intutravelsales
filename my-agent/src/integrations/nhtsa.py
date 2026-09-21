from typing import Any

import aiohttp

VPIC_BASE = "https://vpic.nhtsa.dot.gov/api/vehicles"
RECALLS_BASE = "https://api.nhtsa.gov/recalls"

# The vPIC flat-decode fields worth surfacing to a caller; the raw response
# has 100+ mostly-empty variables.
VIN_FIELDS = [
    "Make",
    "Model",
    "ModelYear",
    "Trim",
    "VehicleType",
    "BodyClass",
    "EngineCylinders",
    "DisplacementL",
    "FuelTypePrimary",
    "DriveType",
    "PlantCountry",
]


async def decode_vin(vin: str, model_year: int | None = None) -> dict[str, Any]:
    """Decode a VIN via NHTSA's free vPIC API. No API key required.

    Returns a dict with the fields in VIN_FIELDS (only non-empty ones), plus
    `error` if vPIC's own check-digit / format validation flagged an issue.
    """
    params = {"format": "json"}
    if model_year:
        params["modelyear"] = str(model_year)

    async with (
        aiohttp.ClientSession() as session,
        session.get(f"{VPIC_BASE}/DecodeVinValues/{vin}", params=params) as resp,
    ):
        resp.raise_for_status()
        data = await resp.json()

    results = data.get("Results") or []
    if not results:
        return {"error": "No decode results returned."}

    row = results[0]
    decoded = {field: row[field] for field in VIN_FIELDS if row.get(field)}

    error_code = row.get("ErrorCode", "0")
    if error_code and error_code != "0":
        decoded["error"] = row.get("ErrorText", f"vPIC error code {error_code}")

    return decoded


async def get_recalls(
    *, make: str, model: str, model_year: int
) -> list[dict[str, Any]]:
    """Look up open NHTSA recalls for a make/model/year. No API key required."""
    params = {"make": make, "model": model, "modelYear": str(model_year)}

    async with (
        aiohttp.ClientSession() as session,
        session.get(f"{RECALLS_BASE}/recallsByVehicle", params=params) as resp,
    ):
        resp.raise_for_status()
        data = await resp.json()

    return data.get("results") or []

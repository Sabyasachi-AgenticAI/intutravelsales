from dataclasses import dataclass
from urllib.parse import quote_plus


@dataclass(frozen=True)
class Location:
    name: str
    address: str


# The demo runs a single fixed Midas service center. `name` is what the
# caller can say; `address` is the full mailing address for the Maps link and
# for the advisor to read back on a booking.
LOCATIONS: list[Location] = [
    Location(
        name="Alpine View",
        address="3737 Alpine Ave NW, Comstock Park, MI 49321, USA",
    ),
    Location(
        name="Comstock Park",
        address="3737 Alpine Ave NW, Comstock Park, MI 49321, USA",
    ),
]


def find_location(query: str) -> Location | None:
    query_lower = query.strip().lower()
    for location in LOCATIONS:
        if query_lower in location.name.lower() or location.name.lower() in query_lower:
            return location
    return None


def maps_link(address: str) -> str:
    return f"https://www.google.com/maps/search/?api=1&query={quote_plus(address)}"

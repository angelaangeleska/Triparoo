from dataclasses import dataclass
from typing import Protocol


@dataclass
class PlaceSearchCriteria:
    city: str
    country: str = ""
    category: str = "tourist_attraction"  # tourist_attraction | restaurant | museum | park | landmark
    max_results: int = 10


@dataclass
class PlaceResult:
    place_id: str
    name: str
    category: str
    rating: float | None
    review_count: int | None
    price_level: str | None
    address: str
    photo_url: str
    maps_url: str
    editorial_summary: str = ""


class PlacesProvider(Protocol):
    async def search_places(self, criteria: PlaceSearchCriteria) -> list[PlaceResult]: ...

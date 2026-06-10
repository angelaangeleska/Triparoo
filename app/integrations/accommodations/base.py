from dataclasses import dataclass
from datetime import date
from typing import Protocol


@dataclass
class AccommodationSearchCriteria:
    destination_id: int
    check_in: date
    check_out: date
    party_size: int = 2


@dataclass
class AccommodationOffer:
    accommodation_id: int | None
    name: str
    type: str
    price_per_night: float
    total_price: float
    rating: float | None
    family_friendly: bool
    source: str = "mock"


class AccommodationProvider(Protocol):
    async def search(self, criteria: AccommodationSearchCriteria) -> list[AccommodationOffer]: ...

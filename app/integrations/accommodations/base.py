from dataclasses import dataclass, field
from datetime import date
from typing import Protocol


@dataclass
class AccommodationSearchCriteria:
    city: str
    check_in: date
    check_out: date
    adults: int = 2
    children: int = 0
    country: str = ""


@dataclass
class BookingSource:
    name: str
    price_per_night: float
    total_price: float
    currency: str
    url: str


@dataclass
class AccommodationOffer:
    name: str
    type: str
    hotel_class: str
    rating: float | None
    reviews_count: int | None
    price_per_night: float
    total_price: float
    currency: str
    family_friendly: bool
    image_url: str
    google_url: str
    booking_sources: list[BookingSource] = field(default_factory=list)
    amenities: list[str] = field(default_factory=list)
    check_in_time: str = ""
    check_out_time: str = ""
    source: str = "serpapi"


class AccommodationProvider(Protocol):
    async def search(self, criteria: AccommodationSearchCriteria) -> list[AccommodationOffer]: ...

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Protocol


@dataclass
class FlightSearchCriteria:
    origin_iata: str
    destination_iata: str
    departure_date: date
    party_size: int = 1
    return_date: date | None = None
    origin_airport_id: int | None = None
    destination_airport_id: int | None = None


@dataclass
class FlightOffer:
    origin_iata: str
    destination_iata: str
    departure_date: datetime
    arrival_date: datetime
    price: float
    airline: str
    airline_code: str
    flight_number: str
    duration_minutes: int
    cabin_class: str = "Economy"
    stops: int = 0
    currency: str = "EUR"
    seats_remaining: int | None = None
    source: str = "global"
    direction: str = "outbound"
    origin_airport_name: str = ""
    destination_airport_name: str = ""
    origin_city: str = ""
    destination_city: str = ""
    baggage: str = "1 personal item + cabin bag"
    origin_airport_id: int | None = None
    destination_airport_id: int | None = None
    return_leg: "FlightOffer | None" = None
    bundled_round_trip: bool = False


@dataclass
class FlightSearchResult:
    outbound: FlightOffer
    return_offer: FlightOffer | None = None
    alternatives: list[FlightOffer] = field(default_factory=list)


class FlightProvider(Protocol):
    async def search(self, criteria: FlightSearchCriteria) -> list[FlightOffer]: ...

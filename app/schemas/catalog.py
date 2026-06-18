from typing import Optional

from pydantic import BaseModel, ConfigDict


class CountryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str


class CityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    country_id: int


class AirportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    iata_code: str
    city_id: int
    city_name: Optional[str] = None


class AirportSearchResult(BaseModel):
    id: int
    name: str
    iata_code: str
    city_name: str
    country_name: str
    match_type: str
    distance_km: Optional[float] = None
    note: Optional[str] = None


class DestinationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    city_id: int
    description: Optional[str] = None
    family_friendliness_score: float
    popularity_score: float
    city: Optional[str] = None
    country: Optional[str] = None


class AttractionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    destination_id: int
    name: str
    category: str
    description: Optional[str] = None
    min_age: int
    max_age: int
    price: float
    family_friendly: bool
    tags: list[str] = []


class ActivityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    destination_id: int
    name: str
    category: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None


class AccommodationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    destination_id: int
    name: str
    type: str
    rating: Optional[float] = None
    price_per_night: float
    address: Optional[str] = None
    family_friendly: bool
    max_guests: int


class FlightRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    origin_airport_id: int
    destination_airport_id: int
    departure_date: str
    price: float
    airline: str
    seats_remaining: Optional[int] = None

from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.family import TripMemberInput


class RecommendRequest(BaseModel):
    members: list[TripMemberInput] = Field(min_length=1)
    budget: float = Field(gt=0)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    origin_location: Optional[str] = Field(
        default=None,
        description="City or country name, e.g. Skopje, France, Macedonia",
    )
    origin_airport_id: Optional[int] = None
    preferred_month: Optional[int] = Field(default=None, ge=1, le=12)


class ResolvedOriginRead(BaseModel):
    query: str
    location_type: str
    display_name: str
    primary_airport_id: Optional[int] = None
    airport_count: int
    message: str


class ScoreBreakdown(BaseModel):
    child_age: float = 0.0
    budget: float = 0.0
    season: float = 0.0
    popularity: float = 0.0
    family_friendly: float = 0.0
    activity: float = 0.0
    weather: float = 0.0


class AttractionSummary(BaseModel):
    id: int
    name: str
    category: str
    price: float
    min_age: int
    max_age: int


class FlightLegSummary(BaseModel):
    airline: str
    airline_code: str
    flight_number: str
    origin_iata: str
    origin_airport: str
    origin_city: str
    destination_iata: str
    destination_airport: str
    destination_city: str
    departure_date: str
    arrival_date: str
    duration_minutes: int
    duration: str
    cabin_class: str
    stops: int
    stops_label: str
    price: float
    price_per_person: float
    currency: str = "EUR"
    seats_remaining: int
    baggage: str = ""
    direction: str = "outbound"
    source: str = "serpapi"
    fare_note: str = ""


class FlightSummary(BaseModel):
    currency: str = "EUR"
    total_price: float
    total_price_per_person: float
    party_size: int = 1
    trip_type: str = "one_way"
    outbound: FlightLegSummary
    return_flight: Optional[FlightLegSummary] = None
    alternatives: list[FlightLegSummary] = []
    source: str = "serpapi"


class BookingSourceSummary(BaseModel):
    name: str
    price_per_night: float
    total_price: float
    currency: str = "USD"
    url: str


class AccommodationSummary(BaseModel):
    name: str
    type: str = ""
    hotel_class: str = ""
    rating: Optional[float] = None
    reviews_count: Optional[int] = None
    price_per_night: float
    total_price: float
    currency: str = "USD"
    family_friendly: bool = False
    image_url: str = ""
    google_url: str = ""
    booking_sources: list[BookingSourceSummary] = []
    amenities: list[str] = []
    check_in_time: str = ""
    check_out_time: str = ""
    source: str = "serpapi"


class DestinationRecommendation(BaseModel):
    destination_id: int
    city: str
    country: str
    rule_score: float
    llm_score: float
    final_score: float
    estimated_total_cost: float
    flight_cost: float = 0.0
    accommodation_cost: float = 0.0
    activity_cost: float = 0.0
    flight: Optional[FlightSummary] = None
    accommodation: Optional[AccommodationSummary] = None
    score_breakdown: ScoreBreakdown
    explanation: str
    suggested_attractions: list[AttractionSummary]


class RecommendResponse(BaseModel):
    origin_message: Optional[str] = None
    recommendations: list[DestinationRecommendation]


class CheapestDestinationsRequest(BaseModel):
    origin_location: Optional[str] = Field(
        default=None,
        description="City or country name",
    )
    origin_airport_id: int | None = None
    budget: float = Field(gt=0)
    start_date: date
    end_date: date
    party_size: int = Field(default=2, ge=1)


class CheapestDestinationResult(BaseModel):
    destination_id: int
    city: str
    country: str
    estimated_total_cost: float
    flight_cost: float
    accommodation_cost: float
    activity_cost: float
    nights: int
    flight: Optional[FlightSummary] = None


class CheapestDestinationsResponse(BaseModel):
    results: list[CheapestDestinationResult]


class CheapestDatesRequest(BaseModel):
    destination_id: int
    origin_location: Optional[str] = None
    origin_airport_id: Optional[int] = None
    party_size: int = Field(default=2, ge=1)


class CheapestPeriod(BaseModel):
    season: str
    month_start: int
    month_end: int
    avg_flight_price: float
    avg_accommodation_price: float
    estimated_total: float
    weather_score: float


class CheapestDatesResponse(BaseModel):
    destination_id: int
    city: str
    country: str
    cheapest_periods: list[CheapestPeriod]
    origin_message: Optional[str] = None


class ItineraryRequest(BaseModel):
    destination_id: int
    members: list[TripMemberInput] = Field(min_length=1)
    duration_days: int = Field(ge=1, le=30)
    budget: float = Field(gt=0)
    start_date: Optional[date] = None


class ItineraryDayItem(BaseModel):
    time: str
    activity: str
    description: Optional[str] = None
    estimated_cost: float = 0.0


class ItineraryDayRead(BaseModel):
    day_number: int
    title: str
    items: list[ItineraryDayItem]


class ItineraryResponse(BaseModel):
    destination_id: int
    city: str
    country: str
    total_estimated_cost: float
    days: list[ItineraryDayRead]


class ChildActivitiesRequest(BaseModel):
    destination_id: int
    age: int = Field(ge=0, le=17)
    gender: Optional[str] = None
    interests: list[str] = Field(default_factory=list)


class ChildActivityResult(BaseModel):
    id: int
    name: str
    category: str
    description: Optional[str] = None
    price: float
    match_score: float
    reason: str


class ChildActivitiesResponse(BaseModel):
    activities: list[ChildActivityResult]


class BudgetOptimizeRequest(BaseModel):
    destination_id: int
    origin_location: Optional[str] = None
    origin_airport_id: int | None = None
    members: list[TripMemberInput] = Field(min_length=1)
    budget: float = Field(gt=0)
    start_date: date
    end_date: date


class BudgetAlternative(BaseModel):
    type: str
    description: str
    estimated_savings: float
    new_total: float


class BudgetOptimizeResponse(BaseModel):
    current_estimate: float
    budget: float
    within_budget: bool
    alternatives: list[BudgetAlternative]

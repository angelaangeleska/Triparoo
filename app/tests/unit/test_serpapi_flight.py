from datetime import date, datetime, timedelta

from app.integrations.flights.serpapi_flight import (
    SerpApiFlightProvider,
    _parse_google_datetime,
    _resolve_arrival,
)
from app.integrations.flights.base import FlightSearchCriteria


def test_parse_google_datetime_full():
    assert _parse_google_datetime("2026-07-17 10:45") == datetime(2026, 7, 17, 10, 45)


def test_parse_google_datetime_with_ampm():
    assert _parse_google_datetime("2026-07-17 10:45 AM") == datetime(2026, 7, 17, 10, 45)


def test_parse_google_datetime_time_only_uses_ref_date():
    result = _parse_google_datetime("11:30 AM", ref_date=date(2026, 7, 17))
    assert result == datetime(2026, 7, 17, 11, 30)


def test_resolve_arrival_uses_duration_when_times_match():
    dep = datetime(2026, 7, 17, 10, 45)
    arr = datetime(2026, 7, 17, 10, 45)
    resolved = _resolve_arrival(dep, arr, duration_minutes=75)
    assert resolved == dep + timedelta(minutes=75)


def test_parse_flight_group_computes_arrival_from_duration():
    provider = SerpApiFlightProvider()
    criteria = FlightSearchCriteria(
        origin_iata="KRH",
        destination_iata="AMS",
        departure_date=date(2026, 7, 17),
        party_size=3,
    )
    group = {
        "flights": [
            {
                "departure_airport": {"id": "KRH", "time": "2026-07-17 10:45"},
                "arrival_airport": {"id": "AMS", "time": "2026-07-17 10:45"},
                "duration": 75,
                "airline": "Air France",
                "flight_number": "AF 1234",
                "travel_class": "Economy",
            }
        ],
        "total_duration": 75,
        "price": 256,
    }
    offer = provider._parse_flight_group(group, criteria, "outbound")
    assert offer is not None
    assert offer.departure_date == datetime(2026, 7, 17, 10, 45)
    assert offer.arrival_date == datetime(2026, 7, 17, 12, 0)
    assert offer.duration_minutes == 75
    assert offer.price == 256.0

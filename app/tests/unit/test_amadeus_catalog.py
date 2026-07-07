"""Unit tests for Amadeus destination, activity, and accommodation parsers."""

from datetime import date

import pytest

from app.integrations.accommodations.amadeus_accommodation import _parse_hotel_offer
from app.integrations.amadeus.activities import _parse_activity
from app.integrations.amadeus.destinations import (
    AmadeusDestination,
    _parse_city,
    _parse_flight_destination,
)
from app.integrations.flights.amadeus_flight import AmadeusFlightProvider
from app.integrations.flights.base import FlightSearchCriteria


SAMPLE_CITY = {
    "type": "location",
    "subType": "CITY",
    "name": "Paris",
    "iataCode": "PAR",
    "address": {"countryCode": "FR", "countryName": "France"},
    "geoCode": {"latitude": 48.8566, "longitude": 2.3522},
}

SAMPLE_ACTIVITY = {
    "id": "4615",
    "type": "activity",
    "name": "Family Zoo Visit",
    "shortDescription": "<p>Great for kids and families</p>",
    "geoCode": {"latitude": 48.85, "longitude": 2.35},
    "price": {"amount": "25.00", "currencyCode": "EUR"},
    "pictures": ["https://example.com/zoo.jpg"],
    "bookingLink": "https://example.com/book",
}

SAMPLE_HOTEL_OFFER = {
    "type": "hotel-offers",
    "hotel": {
        "hotelId": "HLPAR266",
        "name": "Hilton Paris Opera",
        "cityCode": "PAR",
    },
    "available": True,
    "offers": [
        {
            "id": "OFFER1",
            "checkInDate": "2026-08-01",
            "checkOutDate": "2026-08-06",
            "price": {"total": "750.00", "currency": "EUR"},
            "room": {"description": {"text": "Family room with pool access"}},
        }
    ],
}


def test_parse_city():
    dest = _parse_city(SAMPLE_CITY)
    assert dest is not None
    assert dest.city_code == "PAR"
    assert dest.city_name == "Paris"
    assert dest.country_code == "FR"
    assert dest.latitude == pytest.approx(48.8566)


def test_destination_stable_id():
    dest = AmadeusDestination(
        city_code="PAR",
        city_name="Paris",
        country_code="FR",
        country_name="France",
    )
    assert dest.id == AmadeusDestination(
        city_code="PAR",
        city_name="Paris",
        country_code="FR",
        country_name="France",
    ).id


def test_parse_flight_destination():
    item = {
        "type": "flight-destination",
        "origin": "MAD",
        "destination": "BCN",
        "departureDate": "2026-08-01",
        "returnDate": "2026-08-08",
        "price": {"total": "89.00", "currency": "EUR"},
    }
    dest = _parse_flight_destination(item)
    assert dest is not None
    assert dest.city_code == "BCN"


def test_parse_activity():
    act = _parse_activity(SAMPLE_ACTIVITY)
    assert act is not None
    assert act.name == "Family Zoo Visit"
    assert act.price == 25.0
    assert act.family_friendly is True
    assert act.booking_url == "https://example.com/book"


def test_parse_hotel_offer():
    offer = _parse_hotel_offer(SAMPLE_HOTEL_OFFER, nights=5)
    assert offer is not None
    assert offer.name == "Hilton Paris Opera"
    assert offer.price_per_night == 150.0
    assert offer.source == "amadeus"


def test_parse_amadeus_offer():
    provider = AmadeusFlightProvider()
    sample = {
        "type": "flight-offer",
        "id": "1",
        "price": {"total": "189.50", "currency": "EUR"},
        "numberOfBookableSeats": 4,
        "itineraries": [
            {
                "duration": "PT2H30M",
                "segments": [
                    {
                        "departure": {"iataCode": "SKP", "at": "2025-08-15T09:15:00"},
                        "arrival": {"iataCode": "CDG", "at": "2025-08-15T11:45:00"},
                        "carrierCode": "W6",
                        "number": "3847",
                    }
                ],
            }
        ],
        "travelerPricings": [
            {"fareDetailsBySegment": [{"cabin": "ECONOMY", "includedCheckedBags": {"quantity": 1}}]}
        ],
    }
    criteria = FlightSearchCriteria(
        origin_iata="SKP",
        destination_iata="CDG",
        departure_date=date(2025, 8, 15),
        party_size=2,
    )
    offer = provider._parse_offer(sample, criteria)
    assert offer is not None
    assert offer.source == "amadeus"
    assert offer.price == 189.50

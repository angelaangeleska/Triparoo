from datetime import date

import pytest

from app.integrations.flights.amadeus_flight import AmadeusFlightProvider
from app.integrations.flights.base import FlightSearchCriteria


SAMPLE_OFFER = {
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
        {
            "fareDetailsBySegment": [
                {
                    "cabin": "ECONOMY",
                    "includedCheckedBags": {"quantity": 1},
                }
            ]
        }
    ],
}


def test_parse_amadeus_offer():
    provider = AmadeusFlightProvider()
    criteria = FlightSearchCriteria(
        origin_iata="SKP",
        destination_iata="CDG",
        departure_date=date(2025, 8, 15),
        party_size=2,
    )
    offer = provider._parse_offer(SAMPLE_OFFER, criteria)
    assert offer is not None
    assert offer.source == "amadeus"
    assert offer.price == 189.50
    assert offer.origin_iata == "SKP"
    assert offer.destination_iata == "CDG"
    assert offer.airline_code == "W6"
    assert offer.stops == 0
    assert offer.cabin_class == "Economy"
    assert "3847" in offer.flight_number


def test_parse_amadeus_round_trip():
    provider = AmadeusFlightProvider()
    data = {
        **SAMPLE_OFFER,
        "price": {"total": "320.00", "currency": "EUR"},
        "itineraries": [
            SAMPLE_OFFER["itineraries"][0],
            {
                "duration": "PT2H20M",
                "segments": [
                    {
                        "departure": {"iataCode": "CDG", "at": "2025-08-22T14:00:00"},
                        "arrival": {"iataCode": "SKP", "at": "2025-08-22T16:20:00"},
                        "carrierCode": "W6",
                        "number": "3848",
                    }
                ],
            },
        ],
    }
    criteria = FlightSearchCriteria(
        origin_iata="SKP",
        destination_iata="CDG",
        departure_date=date(2025, 8, 15),
        return_date=date(2025, 8, 22),
        party_size=2,
    )
    offer = provider._parse_offer(data, criteria)
    assert offer is not None
    assert offer.bundled_round_trip is True
    assert offer.return_leg is not None
    assert offer.return_leg.direction == "return"
    assert offer.price == 320.0

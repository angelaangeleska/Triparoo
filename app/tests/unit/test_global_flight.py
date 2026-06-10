from datetime import date

import pytest

from app.integrations.flights.base import FlightSearchCriteria
from app.integrations.flights.global_flight import GlobalFlightProvider
from app.integrations.flights.serialize import build_flight_summary


@pytest.mark.asyncio
async def test_global_flight_skp_to_cdg():
    provider = GlobalFlightProvider(session=None)
    offers = await provider.search(
        FlightSearchCriteria(
            origin_iata="SKP",
            destination_iata="CDG",
            departure_date=date(2025, 8, 15),
            party_size=3,
        )
    )
    assert len(offers) >= 1
    best = offers[0]
    assert best.origin_iata == "SKP"
    assert best.destination_iata == "CDG"
    assert best.price > 0
    assert best.airline
    assert best.flight_number
    assert best.arrival_date > best.departure_date
    assert best.duration_minutes > 0

    summary = build_flight_summary(best, party_size=3, alternatives=offers[1:2])
    assert summary["outbound"]["airline"] == best.airline
    assert summary["total_price"] == round(best.price, 2)
    assert summary["outbound"]["departure_date"]
    assert summary["outbound"]["arrival_date"]


@pytest.mark.asyncio
async def test_same_airport_returns_empty():
    provider = GlobalFlightProvider(session=None)
    offers = await provider.search(
        FlightSearchCriteria(
            origin_iata="SKP",
            destination_iata="SKP",
            departure_date=date(2025, 8, 15),
            party_size=1,
        )
    )
    assert offers == []

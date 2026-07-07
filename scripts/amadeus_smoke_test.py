"""Run live smoke tests against the Amadeus test API.

Requires AMADEUS_CLIENT_ID and AMADEUS_CLIENT_SECRET in .env.
"""

import asyncio
from datetime import date, timedelta

from app.core.config import settings
from app.integrations.accommodations.base import AccommodationSearchCriteria
from app.integrations.accommodations.amadeus_accommodation import AmadeusAccommodationProvider
from app.integrations.amadeus.activities import AmadeusActivityService
from app.integrations.amadeus.destinations import AmadeusDestinationService
from app.integrations.flights.amadeus_flight import AmadeusFlightProvider
from app.integrations.flights.base import FlightSearchCriteria


async def main() -> None:
    if not settings.amadeus_configured():
        print("ERROR: Set AMADEUS_CLIENT_ID and AMADEUS_CLIENT_SECRET in .env")
        return

    print(f"Amadeus base URL: {settings.AMADEUS_BASE_URL}")
    print("--- Destinations (City Search: Paris) ---")
    dest_svc = AmadeusDestinationService()
    cities = await dest_svc.search_cities("Paris", max_results=3)
    for c in cities:
        print(f"  {c.city_code}: {c.city_name}, {c.country_name} ({c.latitude}, {c.longitude})")

    if not cities:
        print("  No cities returned")
        return

    paris = cities[0]
    print("\n--- Activities ---")
    act_svc = AmadeusActivityService()
    if paris.latitude and paris.longitude:
        activities = await act_svc.search(paris.latitude, paris.longitude, max_results=3)
        for a in activities:
            print(f"  {a.name}: {a.price} {a.currency}")

    print("\n--- Flights MAD→BCN ---")
    flight_svc = AmadeusFlightProvider()
    dep = date.today() + timedelta(days=60)
    flights = await flight_svc.search(
        FlightSearchCriteria(
            origin_iata="MAD",
            destination_iata="BCN",
            departure_date=dep,
            party_size=1,
        )
    )
    for f in flights[:3]:
        print(f"  {f.airline} {f.origin_iata}→{f.destination_iata}: {f.price} {f.currency}")

    print("\n--- Hotels in Paris ---")
    hotel_svc = AmadeusAccommodationProvider()
    check_in = date.today() + timedelta(days=60)
    check_out = check_in + timedelta(days=3)
    hotels = await hotel_svc.search(
        AccommodationSearchCriteria(
            city="Paris",
            check_in=check_in,
            check_out=check_out,
            adults=2,
            country="France",
        )
    )
    for h in hotels[:3]:
        print(f"  {h.name}: {h.price_per_night}/night ({h.currency})")

    print("\nDone.")


if __name__ == "__main__":
    asyncio.run(main())

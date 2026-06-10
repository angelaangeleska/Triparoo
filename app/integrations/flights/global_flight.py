"""Worldwide flight estimates for any IATA airport pair using open airport data."""

from datetime import timedelta

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.flights.base import FlightOffer, FlightSearchCriteria
from app.integrations.flights.details import (
    build_leg_times,
    estimate_duration_minutes,
    estimate_stops,
    flight_number,
    pick_airline,
)
from app.models.flight import Flight
from app.services.airport_catalog import CatalogAirport, get_airport_catalog
from app.utils.geo import haversine_km


class GlobalFlightProvider:
    """Search flights between any two IATA airports worldwide."""

    def __init__(self, session: AsyncSession | None = None):
        self.session = session
        self.catalog = get_airport_catalog()

    async def search(self, criteria: FlightSearchCriteria) -> list[FlightOffer]:
        origin = criteria.origin_iata.upper()
        dest = criteria.destination_iata.upper()
        if origin == dest:
            return []

        origin_ap = self.catalog.get(origin)
        dest_ap = self.catalog.get(dest)
        if not origin_ap or not dest_ap:
            return []

        month = criteria.departure_date.month
        seasonal = 1.15 if month in (6, 7, 8) else 0.92 if month in (1, 2, 11) else 1.0
        offers: list[FlightOffer] = []

        if self.session:
            offers.extend(await self._search_db(criteria, origin, dest, seasonal, origin_ap, dest_ap))

        distance_km = haversine_km(origin_ap.lat, origin_ap.lng, dest_ap.lat, dest_ap.lng)
        base_per_person = 35.0 + distance_km * 0.11
        if distance_km < 250:
            base_per_person = max(base_per_person, 65.0)
        elif distance_km > 4000:
            base_per_person += 80.0

        slots = [
            (8, 45, 1.0, "Economy"),
            (14, 20, 1.18, "Economy"),
            (6, 10, 1.35, "Premium Economy"),
        ]
        for slot, (hour, minute, mult, cabin) in enumerate(slots):
            airline_name, airline_code = pick_airline(origin, dest, slot)
            stops = estimate_stops(distance_km, origin, dest)
            duration = estimate_duration_minutes(distance_km, stops)
            dep, arr = build_leg_times(criteria.departure_date, hour, minute, duration, stops)
            price = round(base_per_person * seasonal * mult * criteria.party_size, 2)
            offers.append(
                self._build_offer(
                    origin_ap,
                    dest_ap,
                    dep,
                    arr,
                    price,
                    airline_name,
                    airline_code,
                    slot,
                    duration,
                    cabin,
                    stops,
                    criteria,
                )
            )

        return sorted(offers, key=lambda o: o.price)

    def _build_offer(
        self,
        origin_ap: CatalogAirport,
        dest_ap: CatalogAirport,
        dep,
        arr,
        price: float,
        airline_name: str,
        airline_code: str,
        slot: int,
        duration: int,
        cabin: str,
        stops: int,
        criteria: FlightSearchCriteria,
        direction: str = "outbound",
    ) -> FlightOffer:
        return FlightOffer(
            origin_iata=origin_ap.iata,
            destination_iata=dest_ap.iata,
            departure_date=dep,
            arrival_date=arr,
            price=price,
            airline=airline_name,
            airline_code=airline_code,
            flight_number=flight_number(airline_code, origin_ap.iata, dest_ap.iata, slot),
            duration_minutes=duration,
            cabin_class=cabin,
            stops=stops,
            currency="EUR",
            seats_remaining=18 + abs(hash(dest_ap.iata + str(slot))) % 75,
            source="global-estimate",
            direction=direction,
            origin_airport_name=origin_ap.name,
            destination_airport_name=dest_ap.name,
            origin_city=origin_ap.city,
            destination_city=dest_ap.city,
            origin_airport_id=criteria.origin_airport_id,
            destination_airport_id=criteria.destination_airport_id,
        )

    async def _search_db(
        self,
        criteria: FlightSearchCriteria,
        origin: str,
        dest: str,
        seasonal: float,
        origin_ap: CatalogAirport,
        dest_ap: CatalogAirport,
    ) -> list[FlightOffer]:
        from app.models.country import Airport

        result = await self.session.execute(
            select(Airport).where(Airport.iata_code.in_([origin, dest]))
        )
        airports = {a.iata_code.upper(): a for a in result.scalars().all()}
        if origin not in airports or dest not in airports:
            return []

        flights = await self.session.execute(
            select(Flight).where(
                and_(
                    Flight.origin_airport_id == airports[origin].id,
                    Flight.destination_airport_id == airports[dest].id,
                )
            )
        )
        offers = []
        for idx, flight in enumerate(flights.scalars().all()):
            dep = flight.departure_date
            duration = estimate_duration_minutes(
                haversine_km(origin_ap.lat, origin_ap.lng, dest_ap.lat, dest_ap.lng), 0
            )
            arr = dep + timedelta(minutes=duration)
            code = flight.airline[:2].upper() if len(flight.airline) >= 2 else "XX"
            offers.append(
                FlightOffer(
                    origin_iata=origin,
                    destination_iata=dest,
                    departure_date=dep,
                    arrival_date=arr,
                    price=round(flight.price * seasonal * criteria.party_size, 2),
                    airline=flight.airline,
                    airline_code=code,
                    flight_number=flight_number(code, origin, dest, idx),
                    duration_minutes=duration,
                    cabin_class="Economy",
                    stops=0,
                    currency="EUR",
                    seats_remaining=flight.seats_remaining,
                    source="seed-db",
                    direction="outbound",
                    origin_airport_name=origin_ap.name,
                    destination_airport_name=dest_ap.name,
                    origin_city=origin_ap.city,
                    destination_city=dest_ap.city,
                    origin_airport_id=flight.origin_airport_id,
                    destination_airport_id=flight.destination_airport_id,
                )
            )
        return offers

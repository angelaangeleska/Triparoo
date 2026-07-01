"""Seed cached flight and hotel offers for offline testing (USE_DB_PRICES=true)."""

from __future__ import annotations

import asyncio
import logging
from datetime import date, datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.db.session import AsyncSessionLocal
from app.models.accommodation import Accommodation
from app.models.country import Airport
from app.models.destination import Destination
from app.models.flight import Flight
from app.models.offer_cache import FlightOfferCache, HotelOfferCache

logger = logging.getLogger(__name__)

REFERENCE_DEPARTURE = date(2026, 7, 15)
REFERENCE_RETURN = date(2026, 7, 20)

# SOF -> destination IATA, round-trip USD price, airline
FLIGHT_ROUTES: list[tuple[str, str, str, float, str, str]] = [
    ("SOF", "PRG", "Prague", 420.0, "Lufthansa", "LH"),
    ("SOF", "CDG", "Paris", 520.0, "Air France", "AF"),
    ("SOF", "LHR", "London", 480.0, "British Airways", "BA"),
    ("SOF", "FCO", "Rome", 380.0, "Alitalia", "AZ"),
    ("SOF", "BCN", "Barcelona", 450.0, "Vueling", "VY"),
    ("SOF", "VIE", "Vienna", 350.0, "Austrian Airlines", "OS"),
    ("SOF", "AMS", "Amsterdam", 490.0, "KLM", "KL"),
    ("SOF", "BUD", "Budapest", 280.0, "Wizz Air", "W6"),
    ("SOF", "SKG", "Thessaloniki", 120.0, "Aegean Airlines", "A3"),
]

HOTELS: list[tuple[str, str, str, float, float, list[str]]] = [
    ("Prague", "Czech Republic", "Family Hotel Prague", 4.5, 89.0, ["Free Wi-Fi", "Family rooms", "Pool"]),
    ("Paris", "France", "Novotel Paris Centre", 4.3, 145.0, ["Family rooms", "Breakfast", "Wi-Fi"]),
    ("London", "United Kingdom", "Premier Inn London City", 4.2, 160.0, ["Family rooms", "Wi-Fi"]),
    ("Rome", "Italy", "Hotel Roma Garden", 4.4, 110.0, ["Pool", "Family rooms", "Breakfast"]),
    ("Barcelona", "Spain", "Barcelona Family Suites", 4.5, 120.0, ["Pool", "Kids club", "Wi-Fi"]),
    ("Vienna", "Austria", "Austria Trend Hotel", 4.3, 95.0, ["Family rooms", "Playground", "Wi-Fi"]),
    ("Amsterdam", "Netherlands", "NH Amsterdam Centre", 4.1, 130.0, ["Family rooms", "Wi-Fi"]),
    ("Sofia", "Bulgaria", "Grand Hotel Sofia", 4.6, 55.0, ["Pool", "Family rooms", "Wi-Fi"]),
    ("Budapest", "Hungary", "Danubius Hotel", 4.4, 70.0, ["Spa", "Family rooms", "Pool"]),
    ("Thessaloniki", "Greece", "Mediterranean Palace", 4.2, 65.0, ["Beach access", "Pool", "Wi-Fi"]),
]

_AIRPORT_NAMES: dict[str, tuple[str, str]] = {
    "SOF": ("Sofia Airport", "Sofia"),
    "PRG": ("Václav Havel Airport Prague", "Prague"),
    "CDG": ("Charles de Gaulle Airport", "Paris"),
    "LHR": ("Heathrow Airport", "London"),
    "FCO": ("Leonardo da Vinci–Fiumicino Airport", "Rome"),
    "BCN": ("Barcelona–El Prat Airport", "Barcelona"),
    "VIE": ("Vienna International Airport", "Vienna"),
    "AMS": ("Amsterdam Airport Schiphol", "Amsterdam"),
    "BUD": ("Budapest Ferenc Liszt International Airport", "Budapest"),
    "SKG": ("Thessaloniki Airport Makedonia", "Thessaloniki"),
}


def _flight_payload(
    origin: str,
    dest: str,
    dest_city: str,
    total_price: float,
    airline: str,
    airline_code: str,
) -> dict:
    origin_ap, origin_city = _AIRPORT_NAMES.get(origin, (origin, origin))
    dest_ap, _ = _AIRPORT_NAMES.get(dest, (dest, dest_city))
    alt_price = round(total_price * 1.12, 2)

    return {
        "currency": "USD",
        "total_price": total_price,
        "total_price_per_person": round(total_price / 2, 2),
        "party_size": 2,
        "trip_type": "round_trip",
        "source": "db",
        "outbound": {
            "airline": airline,
            "airline_code": airline_code,
            "flight_number": f"{airline_code} 100",
            "origin_iata": origin,
            "origin_airport": origin_ap,
            "origin_city": origin_city,
            "destination_iata": dest,
            "destination_airport": dest_ap,
            "destination_city": dest_city,
            "departure_date": f"{REFERENCE_DEPARTURE.isoformat()}T10:45:00",
            "arrival_date": f"{REFERENCE_DEPARTURE.isoformat()}T12:30:00",
            "duration_minutes": 105,
            "duration": "1h 45m",
            "cabin_class": "Economy",
            "stops": 0,
            "stops_label": "Direct",
            "price": total_price,
            "price_per_person": round(total_price / 2, 2),
            "currency": "USD",
            "seats_remaining": 9,
            "baggage": "1 personal item + cabin bag",
            "direction": "outbound",
            "source": "db",
        },
        "return_flight": {
            "airline": airline,
            "airline_code": airline_code,
            "flight_number": f"{airline_code} 101",
            "origin_iata": dest,
            "origin_airport": dest_ap,
            "origin_city": dest_city,
            "destination_iata": origin,
            "destination_airport": origin_ap,
            "destination_city": origin_city,
            "departure_date": f"{REFERENCE_RETURN.isoformat()}T14:10:00",
            "arrival_date": f"{REFERENCE_RETURN.isoformat()}T15:55:00",
            "duration_minutes": 105,
            "duration": "1h 45m",
            "cabin_class": "Economy",
            "stops": 0,
            "stops_label": "Direct",
            "price": 0.0,
            "price_per_person": 0.0,
            "currency": "USD",
            "seats_remaining": 9,
            "baggage": "Included in round-trip total",
            "direction": "return",
            "source": "db",
        },
        "alternatives": [
            {
                "airline": "Budget Air",
                "airline_code": "BA",
                "flight_number": "BA 9999",
                "origin_iata": origin,
                "destination_iata": dest,
                "departure_date": f"{REFERENCE_DEPARTURE.isoformat()}T06:30:00",
                "arrival_date": f"{REFERENCE_DEPARTURE.isoformat()}T08:15:00",
                "duration_minutes": 105,
                "duration": "1h 45m",
                "cabin_class": "Economy",
                "stops": 1,
                "stops_label": "1 stop",
                "price": alt_price,
                "currency": "USD",
                "direction": "outbound",
                "source": "db",
            }
        ],
    }


def _hotel_payload(city: str, country: str, name: str, rating: float, price: float, amenities: list[str]) -> dict:
    nights = max((REFERENCE_RETURN - REFERENCE_DEPARTURE).days, 1)
    total = round(price * nights, 2)
    slug = city.lower().replace(" ", "-")
    return {
        "name": name,
        "type": "Hotel",
        "hotel_class": "4-star hotel",
        "rating": rating,
        "reviews_count": 850,
        "price_per_night": price,
        "total_price": total,
        "currency": "USD",
        "family_friendly": True,
        "image_url": f"https://images.unsplash.com/photo-1566073771259-6a8506099945?w=400",
        "google_url": f"https://google.com/travel/hotels/{slug}",
        "booking_sources": [
            {
                "name": "Booking.com",
                "price_per_night": price,
                "total_price": total,
                "currency": "USD",
                "url": f"https://booking.com/hotel/{slug}",
            }
        ],
        "amenities": amenities,
        "check_in_time": "15:00",
        "check_out_time": "11:00",
        "source": "db",
    }


async def _sync_legacy_catalog(session) -> None:
    """Mirror cache rows into legacy flights/accommodations tables for DB browsing."""
    flight_count = await session.scalar(select(func.count()).select_from(Flight))
    if not flight_count:
        airport_rows = await session.execute(select(Airport))
        airports = {a.iata_code.upper(): a for a in airport_rows.scalars().all()}

        for origin, dest, _dest_city, price, airline, _code in FLIGHT_ROUTES:
            origin_ap = airports.get(origin)
            dest_ap = airports.get(dest)
            if not origin_ap or not dest_ap:
                continue
            session.add(
                Flight(
                    origin_airport_id=origin_ap.id,
                    destination_airport_id=dest_ap.id,
                    departure_date=datetime(
                        REFERENCE_DEPARTURE.year,
                        REFERENCE_DEPARTURE.month,
                        REFERENCE_DEPARTURE.day,
                        10,
                        45,
                        tzinfo=timezone.utc,
                    ),
                    price=price,
                    airline=airline,
                    seats_remaining=9,
                )
            )

    acc_count = await session.scalar(select(func.count()).select_from(Accommodation))
    if not acc_count:
        dest_rows = await session.execute(select(Destination).options(selectinload(Destination.city)))
        city_to_dest: dict[str, Destination] = {}
        for dest in dest_rows.scalars().all():
            if dest.city:
                city_to_dest[dest.city.name] = dest

        for city, _country, name, rating, price, _amenities in HOTELS:
            dest = city_to_dest.get(city)
            if not dest:
                continue
            session.add(
                Accommodation(
                    destination_id=dest.id,
                    name=name,
                    type="Hotel",
                    rating=rating,
                    price_per_night=price,
                    family_friendly=True,
                    max_guests=4,
                )
            )


async def seed_price_cache() -> None:
    async with AsyncSessionLocal() as session:
        flight_count = await session.scalar(select(func.count()).select_from(FlightOfferCache))
        hotel_count = await session.scalar(select(func.count()).select_from(HotelOfferCache))

        if not flight_count:
            for origin, dest, dest_city, price, airline, code in FLIGHT_ROUTES:
                session.add(
                    FlightOfferCache(
                        origin_iata=origin,
                        destination_iata=dest,
                        departure_date=REFERENCE_DEPARTURE,
                        return_date=REFERENCE_RETURN,
                        party_size=2,
                        payload=_flight_payload(origin, dest, dest_city, price, airline, code),
                    )
                )

        if not hotel_count:
            for city, country, name, rating, price, amenities in HOTELS:
                session.add(
                    HotelOfferCache(
                        city=city,
                        country=country,
                        check_in=REFERENCE_DEPARTURE,
                        check_out=REFERENCE_RETURN,
                        payload=_hotel_payload(city, country, name, rating, price, amenities),
                    )
                )

        await _sync_legacy_catalog(session)
        await session.commit()

        flight_count = await session.scalar(select(func.count()).select_from(FlightOfferCache))
        hotel_count = await session.scalar(select(func.count()).select_from(HotelOfferCache))
        legacy_flights = await session.scalar(select(func.count()).select_from(Flight))
        logger.info(
            "Price cache ready: %d flight offers, %d hotels (%d legacy flight rows synced)",
            flight_count,
            hotel_count,
            legacy_flights,
        )


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    asyncio.run(seed_price_cache())


if __name__ == "__main__":
    main()

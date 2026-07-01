"""Seed reference catalog data (destinations, attractions, seasons).

Flight and hotel prices are fetched live via SerpAPI/Amadeus — not stored here.
"""

from __future__ import annotations

import asyncio
import logging

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.models.attraction import Attraction
from app.models.country import Airport, City, Country
from app.models.destination import Destination
from app.models.destination_season import DestinationSeason
from app.models.user import User

logger = logging.getLogger(__name__)

DESTINATIONS = [
    {
        "city": "Paris",
        "country": "France",
        "code": "FRA",
        "lat": 48.8566,
        "lon": 2.3522,
        "airport": ("Charles de Gaulle Airport", "CDG"),
        "description": "The City of Light — world-class museums, parks, and Disneyland Paris nearby.",
        "family_score": 92.0,
        "popularity": 95.0,
        "seasons": [
            ("Spring", 3, 5, 14.0, 0.85, 1.0),
            ("Summer", 6, 8, 24.0, 0.75, 1.2),
            ("Autumn", 9, 11, 15.0, 0.88, 0.95),
            ("Winter", 12, 2, 6.0, 0.70, 0.85),
        ],
        "attractions": [
            ("Disneyland Paris", "theme_park", "Europe's most visited theme park.", 0, 99, 56.0, ["disney", "theme_park"]),
            ("Louvre Museum", "museum", "Home to the Mona Lisa and vast art collections.", 6, 99, 22.0, ["art", "museum"]),
            ("Eiffel Tower", "landmark", "Iconic iron lattice tower with summit views.", 0, 99, 29.0, ["landmark"]),
            ("Jardin du Luxembourg", "park", "Beautiful gardens with playgrounds for children.", 0, 12, 0.0, ["park", "outdoor"]),
        ],
    },
    {
        "city": "London",
        "country": "United Kingdom",
        "code": "GBR",
        "lat": 51.5074,
        "lon": -0.1278,
        "airport": ("Heathrow Airport", "LHR"),
        "description": "Historic capital with royal palaces, museums, and family attractions.",
        "family_score": 90.0,
        "popularity": 94.0,
        "seasons": [
            ("Spring", 3, 5, 12.0, 0.80, 1.0),
            ("Summer", 6, 8, 22.0, 0.78, 1.15),
            ("Autumn", 9, 11, 14.0, 0.82, 0.95),
            ("Winter", 12, 2, 5.0, 0.65, 0.90),
        ],
        "attractions": [
            ("Natural History Museum", "museum", "Free entry with dinosaurs and interactive exhibits.", 0, 99, 0.0, ["museum", "science"]),
            ("London Eye", "landmark", "Giant observation wheel on the South Bank.", 3, 99, 36.0, ["landmark"]),
            ("Warner Bros. Studio Tour", "theme_park", "Harry Potter film sets and props.", 5, 99, 49.0, ["harry_potter", "film"]),
            ("Hyde Park", "park", "Vast royal park with boating and playgrounds.", 0, 99, 0.0, ["park", "outdoor"]),
        ],
    },
    {
        "city": "Rome",
        "country": "Italy",
        "code": "ITA",
        "lat": 41.9028,
        "lon": 12.4964,
        "airport": ("Leonardo da Vinci–Fiumicino Airport", "FCO"),
        "description": "Ancient history, Italian cuisine, and open-air wonders for all ages.",
        "family_score": 85.0,
        "popularity": 91.0,
        "seasons": [
            ("Spring", 3, 5, 16.0, 0.90, 1.0),
            ("Summer", 6, 8, 28.0, 0.72, 1.25),
            ("Autumn", 9, 11, 18.0, 0.88, 0.95),
            ("Winter", 12, 2, 10.0, 0.75, 0.85),
        ],
        "attractions": [
            ("Colosseum", "landmark", "Ancient Roman amphitheatre — book family tours.", 0, 99, 18.0, ["history", "landmark"]),
            ("Vatican Museums", "museum", "Sistine Chapel and vast art collections.", 6, 99, 17.0, ["art", "museum"]),
            ("Explora Children Museum", "museum", "Interactive science museum for kids.", 0, 12, 9.0, ["science", "museum"]),
            ("Villa Borghese", "park", "Large park with bike rentals and a zoo.", 0, 99, 0.0, ["park", "outdoor"]),
        ],
    },
    {
        "city": "Barcelona",
        "country": "Spain",
        "code": "ESP",
        "lat": 41.3874,
        "lon": 2.1686,
        "airport": ("Barcelona–El Prat Airport", "BCN"),
        "description": "Mediterranean beaches, Gaudí architecture, and vibrant culture.",
        "family_score": 88.0,
        "popularity": 89.0,
        "seasons": [
            ("Spring", 3, 5, 17.0, 0.88, 1.0),
            ("Summer", 6, 8, 27.0, 0.80, 1.2),
            ("Autumn", 9, 11, 20.0, 0.90, 0.95),
            ("Winter", 12, 2, 11.0, 0.78, 0.85),
        ],
        "attractions": [
            ("Park Güell", "landmark", "Gaudí's colourful mosaic park with city views.", 0, 99, 10.0, ["gaudi", "park"]),
            ("Barcelona Aquarium", "museum", "One of Europe's largest aquariums.", 0, 12, 25.0, ["science", "marine"]),
            ("Barceloneta Beach", "park", "Sandy urban beach perfect for families.", 0, 99, 0.0, ["beach", "outdoor"]),
            ("CosmoCaixa Science Museum", "museum", "Hands-on science exhibits for all ages.", 0, 17, 6.0, ["science", "museum"]),
        ],
    },
    {
        "city": "Vienna",
        "country": "Austria",
        "code": "AUT",
        "lat": 48.2082,
        "lon": 16.3738,
        "airport": ("Vienna International Airport", "VIE"),
        "description": "Imperial palaces, classical music, and excellent public transport.",
        "family_score": 87.0,
        "popularity": 82.0,
        "seasons": [
            ("Spring", 3, 5, 13.0, 0.85, 1.0),
            ("Summer", 6, 8, 24.0, 0.82, 1.1),
            ("Autumn", 9, 11, 14.0, 0.86, 0.95),
            ("Winter", 12, 2, 2.0, 0.80, 0.90),
        ],
        "attractions": [
            ("Schönbrunn Palace", "landmark", "Imperial palace with a maze and zoo.", 0, 99, 22.0, ["history", "palace"]),
            ("Prater Amusement Park", "theme_park", "Historic funfair with the Giant Ferris Wheel.", 0, 99, 0.0, ["theme_park", "outdoor"]),
            ("Haus des Meeres", "museum", "Aquarium and terrarium in a converted flak tower.", 0, 12, 19.0, ["marine", "science"]),
            ("Vienna Zoo", "park", "World's oldest zoo in Schönbrunn grounds.", 0, 99, 26.0, ["animals", "outdoor"]),
        ],
    },
    {
        "city": "Prague",
        "country": "Czech Republic",
        "code": "CZE",
        "lat": 50.0755,
        "lon": 14.4378,
        "airport": ("Václav Havel Airport Prague", "PRG"),
        "description": "Fairytale architecture, affordable dining, and charming old town.",
        "family_score": 84.0,
        "popularity": 80.0,
        "seasons": [
            ("Spring", 3, 5, 12.0, 0.82, 0.95),
            ("Summer", 6, 8, 22.0, 0.85, 1.05),
            ("Autumn", 9, 11, 13.0, 0.88, 0.90),
            ("Winter", 12, 2, 0.0, 0.78, 0.80),
        ],
        "attractions": [
            ("Prague Castle", "landmark", "Largest ancient castle complex in the world.", 0, 99, 15.0, ["history", "landmark"]),
            ("Prague Zoo", "park", "Consistently ranked among the world's best zoos.", 0, 99, 18.0, ["animals", "outdoor"]),
            ("National Technical Museum", "museum", "Trains, planes, and interactive exhibits.", 4, 99, 12.0, ["science", "museum"]),
            ("Petřín Hill", "park", "Funicular ride, mirror maze, and panoramic views.", 0, 99, 5.0, ["park", "outdoor"]),
        ],
    },
    {
        "city": "Amsterdam",
        "country": "Netherlands",
        "code": "NLD",
        "lat": 52.3676,
        "lon": 4.9041,
        "airport": ("Amsterdam Airport Schiphol", "AMS"),
        "description": "Canals, cycling culture, and world-class museums.",
        "family_score": 86.0,
        "popularity": 88.0,
        "seasons": [
            ("Spring", 3, 5, 11.0, 0.88, 1.0),
            ("Summer", 6, 8, 20.0, 0.85, 1.15),
            ("Autumn", 9, 11, 13.0, 0.82, 0.95),
            ("Winter", 12, 2, 4.0, 0.70, 0.85),
        ],
        "attractions": [
            ("NEMO Science Museum", "museum", "Hands-on science on a striking waterfront building.", 0, 17, 17.5, ["science", "museum"]),
            ("ARTIS Zoo", "park", "Historic zoo in the heart of the city.", 0, 99, 25.0, ["animals", "outdoor"]),
            ("Van Gogh Museum", "museum", "Largest collection of Van Gogh paintings.", 6, 99, 22.0, ["art", "museum"]),
            ("Vondelpark", "park", "Amsterdam's most popular park with playgrounds.", 0, 99, 0.0, ["park", "outdoor"]),
        ],
    },
    {
        "city": "Sofia",
        "country": "Bulgaria",
        "code": "BGR",
        "lat": 42.6977,
        "lon": 23.3219,
        "airport": ("Sofia Airport", "SOF"),
        "description": "Affordable Balkan capital with parks, museums, and easy day trips to Vitosha Mountain.",
        "family_score": 82.0,
        "popularity": 72.0,
        "seasons": [
            ("Spring", 3, 5, 14.0, 0.88, 0.90),
            ("Summer", 6, 8, 26.0, 0.90, 1.0),
            ("Autumn", 9, 11, 15.0, 0.86, 0.85),
            ("Winter", 12, 2, 2.0, 0.72, 0.75),
        ],
        "attractions": [
            ("Sofia Zoo", "park", "Large zoo with playgrounds and picnic areas.", 0, 99, 8.0, ["animals", "outdoor"]),
            ("Muzeiko", "museum", "Bulgaria's largest hands-on science centre for children.", 0, 14, 12.0, ["science", "museum"]),
            ("Borisova Gradina", "park", "Central park with lakes, playgrounds, and bike paths.", 0, 99, 0.0, ["park", "outdoor"]),
            ("National History Museum", "museum", "Treasures from Thracian gold to communist-era exhibits.", 6, 99, 10.0, ["history", "museum"]),
        ],
    },
    {
        "city": "Budapest",
        "country": "Hungary",
        "code": "HUN",
        "lat": 47.4979,
        "lon": 19.0402,
        "airport": ("Budapest Ferenc Liszt International Airport", "BUD"),
        "description": "Thermal baths, Danube views, and excellent value for family city breaks.",
        "family_score": 86.0,
        "popularity": 78.0,
        "seasons": [
            ("Spring", 3, 5, 14.0, 0.85, 0.95),
            ("Summer", 6, 8, 25.0, 0.88, 1.05),
            ("Autumn", 9, 11, 14.0, 0.84, 0.90),
            ("Winter", 12, 2, 1.0, 0.70, 0.80),
        ],
        "attractions": [
            ("Budapest Zoo", "park", "Historic zoo and botanical garden in City Park.", 0, 99, 15.0, ["animals", "outdoor"]),
            ("Palace of Wonders", "museum", "Interactive science playhouse for younger children.", 0, 12, 14.0, ["science", "museum"]),
            ("Margaret Island", "park", "Car-free island park with playgrounds and pools.", 0, 99, 0.0, ["park", "outdoor"]),
            ("Buda Castle", "landmark", "Castle district with funicular rides and panoramic views.", 0, 99, 12.0, ["history", "landmark"]),
        ],
    },
    {
        "city": "Thessaloniki",
        "country": "Greece",
        "code": "GRC",
        "lat": 40.6401,
        "lon": 22.9444,
        "airport": ("Thessaloniki Airport Makedonia", "SKG"),
        "description": "Coastal Greek city with Roman ruins, waterfront promenades, and nearby beaches.",
        "family_score": 83.0,
        "popularity": 74.0,
        "seasons": [
            ("Spring", 3, 5, 16.0, 0.86, 0.95),
            ("Summer", 6, 8, 28.0, 0.90, 1.1),
            ("Autumn", 9, 11, 18.0, 0.88, 0.90),
            ("Winter", 12, 2, 8.0, 0.75, 0.80),
        ],
        "attractions": [
            ("NOESIS Science Centre", "museum", "Planetarium and interactive science exhibits.", 0, 17, 8.0, ["science", "museum"]),
            ("Thessaloniki Zoo", "park", "Compact zoo popular with local families.", 0, 12, 7.0, ["animals", "outdoor"]),
            ("White Tower", "landmark", "Iconic waterfront tower with city history exhibits.", 0, 99, 8.0, ["history", "landmark"]),
            ("Aristotelous Square", "park", "Lively seafront square with cafés and street performers.", 0, 99, 0.0, ["outdoor"]),
        ],
    },
]

DEMO_USER = {
    "email": "demo@familytrip.com",
    "username": "demo",
    "password": "DemoPass123!",
    "first_name": "Demo",
    "last_name": "User",
}


async def seed() -> None:
    async with AsyncSessionLocal() as session:
        existing = await session.execute(select(Destination).limit(1))
        if existing.scalar_one_or_none():
            logger.info("Catalog already seeded — checking for new destinations")
            await _seed_missing_destinations(session)
            await _ensure_demo_user(session)
            await session.commit()
            from app.utils.seed_price_cache import seed_price_cache

            await seed_price_cache()
            return

        await _seed_all_destinations(session)
        await _ensure_demo_user(session)
        await session.commit()
        logger.info("Seeded %d destinations with attractions and seasons", len(DESTINATIONS))

        from app.utils.seed_price_cache import seed_price_cache

        await seed_price_cache()


async def _seed_all_destinations(session) -> None:
    country_cache: dict[str, Country] = {}
    for entry in DESTINATIONS:
        await _insert_destination(session, entry, country_cache)


async def _seed_missing_destinations(session) -> None:
    result = await session.execute(select(City.name))
    existing_cities = {row[0] for row in result.all()}
    country_cache: dict[str, Country] = {}
    added = 0
    for entry in DESTINATIONS:
        if entry["city"] in existing_cities:
            continue
        await _insert_destination(session, entry, country_cache)
        added += 1
    if added:
        logger.info("Added %d new destinations to catalog", added)


async def _insert_destination(session, entry: dict, country_cache: dict[str, Country]) -> None:
    country = country_cache.get(entry["code"])
    if not country:
        result = await session.execute(select(Country).where(Country.code == entry["code"]))
        country = result.scalar_one_or_none()
    if not country:
        country = Country(name=entry["country"], code=entry["code"])
        session.add(country)
        await session.flush()
    country_cache[entry["code"]] = country

    city = City(
        name=entry["city"],
        country_id=country.id,
        latitude=entry["lat"],
        longitude=entry["lon"],
    )
    session.add(city)
    await session.flush()

    ap_name, iata = entry["airport"]
    session.add(Airport(city_id=city.id, name=ap_name, iata_code=iata))

    dest = Destination(
        city_id=city.id,
        description=entry["description"],
        family_friendliness_score=entry["family_score"],
        popularity_score=entry["popularity"],
        latitude=entry["lat"],
        longitude=entry["lon"],
    )
    session.add(dest)
    await session.flush()

    for season, m_start, m_end, temp, weather, mult in entry["seasons"]:
        session.add(
            DestinationSeason(
                destination_id=dest.id,
                season=season,
                month_start=m_start,
                month_end=m_end,
                avg_temp_c=temp,
                weather_score=weather,
                price_multiplier=mult,
            )
        )

    for name, category, desc, min_age, max_age, price, tags in entry["attractions"]:
        session.add(
            Attraction(
                destination_id=dest.id,
                name=name,
                category=category,
                description=desc,
                min_age=min_age,
                max_age=max_age,
                price=price,
                family_friendly=True,
                tags=tags,
            )
        )


async def _ensure_demo_user(session) -> None:
    result = await session.execute(select(User).where(User.email == DEMO_USER["email"]))
    if result.scalar_one_or_none():
        return
    session.add(
        User(
            email=DEMO_USER["email"],
            username=DEMO_USER["username"],
            hashed_password=hash_password(DEMO_USER["password"]),
            first_name=DEMO_USER["first_name"],
            last_name=DEMO_USER["last_name"],
            is_active=True,
        )
    )


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    asyncio.run(seed())


if __name__ == "__main__":
    main()

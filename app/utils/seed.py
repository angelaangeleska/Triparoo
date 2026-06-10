"""Seed realistic travel data for Family Trip Planner."""

import asyncio
from datetime import datetime, timezone

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import AsyncSessionLocal, engine
from app.models.accommodation import Accommodation
from app.models.activity import Activity
from app.models.attraction import Attraction
from app.models.country import Airport, City, Country
from app.models.destination import Destination
from app.models.destination_season import DestinationSeason
from app.models.flight import Flight
from app.models.user import User

DEMO_EMAIL = "demo@familytrip.com"
DEMO_PASSWORD = "DemoPass123!"

DESTINATIONS = [
    {
        "city": "Paris",
        "country": "France",
        "code": "FRA",
        "airport": ("Charles de Gaulle Airport", "CDG"),
        "description": "The City of Light — iconic landmarks, world-class museums, and Disneyland Paris nearby.",
        "family_score": 92.0,
        "popularity": 95.0,
        "lat": 48.8566,
        "lng": 2.3522,
        "attractions": [
            ("Disneyland Paris", "theme_park", "Europe's most magical theme park, perfect for families.", 6, 14, 56.0, ["theme_park", "disney", "family"]),
            ("Eiffel Tower", "landmark", "Iconic iron lattice tower with stunning city views.", 0, 99, 28.0, ["landmark", "sightseeing"]),
            ("Louvre Museum", "museum", "World's largest art museum with family audio guides.", 8, 99, 22.0, ["museum", "culture", "art"]),
            ("Cité des Sciences", "museum", "Interactive science museum ideal for curious children.", 5, 16, 12.0, ["museum", "science", "interactive"]),
            ("Jardin du Luxembourg", "park", "Beautiful park with puppet shows and playgrounds.", 0, 12, 0.0, ["park", "outdoor"]),
        ],
        "accommodations": [
            ("Hotel Le Family Paris", "hotel", 4.3, 145.0, True, 4),
            ("Novotel Paris Centre", "hotel", 4.1, 120.0, True, 5),
            ("Paris Budget Stay", "hostel", 3.5, 65.0, False, 2),
        ],
    },
    {
        "city": "London",
        "country": "United Kingdom",
        "code": "GBR",
        "airport": ("Heathrow Airport", "LHR"),
        "description": "Historic capital with royal palaces, museums, and family attractions.",
        "family_score": 88.0,
        "popularity": 93.0,
        "lat": 51.5074,
        "lng": -0.1278,
        "attractions": [
            ("London Eye", "landmark", "Giant observation wheel with panoramic views.", 4, 99, 32.0, ["landmark", "sightseeing"]),
            ("Natural History Museum", "museum", "Free museum with dinosaur exhibits kids love.", 3, 16, 0.0, ["museum", "science", "dinosaurs"]),
            ("Warner Bros Studio Tour", "theme_park", "Harry Potter studio experience.", 8, 99, 45.0, ["harry_potter", "film"]),
            ("Tower of London", "landmark", "Historic castle with crown jewels.", 6, 99, 33.0, ["history", "castle"]),
            ("Hyde Park", "park", "Vast royal park with boating and playgrounds.", 0, 99, 0.0, ["park", "outdoor"]),
        ],
        "accommodations": [
            ("Premier Inn London", "hotel", 4.0, 130.0, True, 4),
            ("The Z Hotel", "hotel", 3.8, 95.0, True, 3),
        ],
    },
    {
        "city": "Rome",
        "country": "Italy",
        "code": "ITA",
        "airport": ("Leonardo da Vinci Airport", "FCO"),
        "description": "Eternal City blending ancient history with vibrant Italian culture.",
        "family_score": 82.0,
        "popularity": 90.0,
        "lat": 41.9028,
        "lng": 12.4964,
        "attractions": [
            ("Colosseum", "landmark", "Ancient amphitheatre — a must-see for history lovers.", 6, 99, 18.0, ["history", "ancient"]),
            ("Explora Children Museum", "museum", "Interactive museum designed for kids.", 3, 12, 8.0, ["museum", "interactive", "science"]),
            ("Villa Borghese", "park", "Large park with zoo and rowing lake.", 0, 99, 0.0, ["park", "zoo", "outdoor"]),
            ("Vatican Museums", "museum", "Art and history — best for older children.", 10, 99, 17.0, ["museum", "art", "religion"]),
        ],
        "accommodations": [
            ("Hotel Roma Family", "hotel", 4.2, 110.0, True, 4),
            ("Roma Guest House", "bnb", 4.0, 75.0, True, 3),
        ],
    },
    {
        "city": "Barcelona",
        "country": "Spain",
        "code": "ESP",
        "airport": ("Barcelona-El Prat Airport", "BCN"),
        "description": "Mediterranean city with Gaudí architecture, beaches, and parks.",
        "family_score": 86.0,
        "popularity": 88.0,
        "lat": 41.3874,
        "lng": 2.1686,
        "attractions": [
            ("Park Güell", "park", "Whimsical Gaudí park with mosaic creatures.", 0, 99, 10.0, ["park", "gaudi", "art"]),
            ("CosmoCaixa Science Museum", "museum", "Outstanding interactive science museum.", 5, 16, 6.0, ["museum", "science", "interactive"]),
            ("Barcelona Aquarium", "aquarium", "Large aquarium with shark tunnel.", 3, 14, 21.0, ["aquarium", "marine"]),
            ("Barceloneta Beach", "beach", "Urban beach perfect for summer family days.", 0, 99, 0.0, ["beach", "outdoor"]),
        ],
        "accommodations": [
            ("Barcelona Family Hotel", "hotel", 4.1, 105.0, True, 4),
            ("Apartments BCN", "apartment", 4.0, 90.0, True, 6),
        ],
    },
    {
        "city": "Vienna",
        "country": "Austria",
        "code": "AUT",
        "airport": ("Vienna International Airport", "VIE"),
        "description": "Imperial city with palaces, music, and excellent public transport.",
        "family_score": 85.0,
        "popularity": 80.0,
        "lat": 48.2082,
        "lng": 16.3738,
        "attractions": [
            ("Schönbrunn Zoo", "zoo", "World's oldest zoo within imperial palace grounds.", 0, 99, 22.0, ["zoo", "animals"]),
            ("House of Music", "museum", "Interactive music museum for all ages.", 4, 99, 13.0, ["museum", "music", "interactive"]),
            ("Prater Amusement Park", "theme_park", "Historic amusement park with giant Ferris wheel.", 3, 99, 0.0, ["theme_park", "rides"]),
            ("Schönbrunn Palace", "landmark", "Baroque palace with maze garden.", 5, 99, 20.0, ["history", "palace"]),
        ],
        "accommodations": [
            ("Hotel Vienna Central", "hotel", 4.2, 115.0, True, 4),
            ("Pension Mozart", "bnb", 3.9, 70.0, True, 3),
        ],
    },
    {
        "city": "Prague",
        "country": "Czech Republic",
        "code": "CZE",
        "airport": ("Václav Havel Airport Prague", "PRG"),
        "description": "Fairytale city with castle, bridges, and affordable family travel.",
        "family_score": 84.0,
        "popularity": 78.0,
        "lat": 50.0755,
        "lng": 14.4378,
        "attractions": [
            ("Prague Castle", "landmark", "Largest ancient castle complex in the world.", 5, 99, 15.0, ["history", "castle"]),
            ("Techmania Science Centre", "museum", "Hands-on science centre in Pilsen (day trip).", 6, 16, 10.0, ["museum", "science"]),
            ("Petřín Hill", "park", "Hill with mirror maze and observation tower.", 3, 99, 5.0, ["park", "outdoor"]),
            ("Lego Exhibition", "museum", "Seasonal LEGO displays popular with kids.", 4, 14, 12.0, ["lego", "interactive"]),
        ],
        "accommodations": [
            ("Prague Family Inn", "hotel", 4.0, 80.0, True, 4),
            ("Old Town Apartments", "apartment", 4.1, 65.0, True, 5),
        ],
    },
    {
        "city": "Amsterdam",
        "country": "Netherlands",
        "code": "NLD",
        "airport": ("Amsterdam Schiphol Airport", "AMS"),
        "description": "Canals, bikes, and world-class museums in a compact city.",
        "family_score": 83.0,
        "popularity": 85.0,
        "lat": 52.3676,
        "lng": 4.9041,
        "attractions": [
            ("NEMO Science Museum", "museum", "Ship-shaped science museum — very hands-on.", 4, 16, 17.0, ["museum", "science", "interactive"]),
            ("Artis Zoo", "zoo", "Historic zoo in the city centre.", 0, 99, 25.0, ["zoo", "animals"]),
            ("Van Gogh Museum", "museum", "Colourful art museum — best for older kids.", 10, 99, 20.0, ["museum", "art"]),
            ("Vondelpark", "park", "Popular park with playgrounds and open-air theatre.", 0, 99, 0.0, ["park", "outdoor"]),
        ],
        "accommodations": [
            ("Amsterdam Family Hotel", "hotel", 4.0, 125.0, True, 4),
            ("Canal View B&B", "bnb", 4.2, 100.0, True, 3),
        ],
    },
]

SEASONS = [
    ("spring", 3, 5, 14.0, 0.75, 1.0),
    ("summer", 6, 8, 24.0, 0.90, 1.3),
    ("autumn", 9, 11, 12.0, 0.70, 0.9),
    ("winter", 12, 2, 4.0, 0.50, 0.8),
]

EXTRA_AIRPORTS = [
    {"country": "Germany", "code": "DEU", "city": "Frankfurt", "lat": 50.1109, "lng": 8.6821, "airport": ("Frankfurt Airport", "FRA")},
    {"country": "Germany", "code": "DEU", "city": "Munich", "lat": 48.1351, "lng": 11.5820, "airport": ("Munich Airport", "MUC")},
    {"country": "Germany", "code": "DEU", "city": "Berlin", "lat": 52.5200, "lng": 13.4050, "airport": ("Berlin Brandenburg Airport", "BER")},
    {"country": "Belgium", "code": "BEL", "city": "Brussels", "lat": 50.8503, "lng": 4.3517, "airport": ("Brussels Airport", "BRU")},
    {"country": "Italy", "code": "ITA", "city": "Milan", "lat": 45.4642, "lng": 9.1900, "airport": ("Milan Malpensa Airport", "MXP")},
    {"country": "Spain", "code": "ESP", "city": "Madrid", "lat": 40.4168, "lng": -3.7038, "airport": ("Madrid-Barajas Airport", "MAD")},
    {"country": "France", "code": "FRA", "city": "Nice", "lat": 43.7102, "lng": 7.2620, "airport": ("Nice Côte d'Azur Airport", "NCE")},
    {"country": "United Kingdom", "code": "GBR", "city": "Manchester", "lat": 53.4808, "lng": -2.2426, "airport": ("Manchester Airport", "MAN")},
    {"country": "Switzerland", "code": "CHE", "city": "Zurich", "lat": 47.3769, "lng": 8.5417, "airport": ("Zurich Airport", "ZRH")},
    {"country": "Denmark", "code": "DNK", "city": "Copenhagen", "lat": 55.6761, "lng": 12.5683, "airport": ("Copenhagen Airport", "CPH")},
    {"country": "Portugal", "code": "PRT", "city": "Lisbon", "lat": 38.7223, "lng": -9.1393, "airport": ("Lisbon Airport", "LIS")},
    {"country": "Ireland", "code": "IRL", "city": "Dublin", "lat": 53.3498, "lng": -6.2603, "airport": ("Dublin Airport", "DUB")},
]


async def seed() -> None:
    async with AsyncSessionLocal() as session:
        existing = await session.execute(select(Destination).limit(1))
        if existing.scalar_one_or_none():
            print("Database already seeded, skipping.")
            return

        country_map: dict[str, Country] = {}
        city_map: dict[str, City] = {}
        airport_map: dict[str, Airport] = {}
        dest_map: dict[str, Destination] = {}

        for d in DESTINATIONS:
            if d["code"] not in country_map:
                country = Country(name=d["country"], code=d["code"])
                session.add(country)
                await session.flush()
                country_map[d["code"]] = country
            country = country_map[d["code"]]

            city = City(
                country_id=country.id,
                name=d["city"],
                latitude=d["lat"],
                longitude=d["lng"],
            )
            session.add(city)
            await session.flush()
            city_map[d["city"]] = city

            ap_name, iata = d["airport"]
            airport = Airport(city_id=city.id, name=ap_name, iata_code=iata)
            session.add(airport)
            await session.flush()
            airport_map[iata] = airport

            dest = Destination(
                city_id=city.id,
                description=d["description"],
                family_friendliness_score=d["family_score"],
                popularity_score=d["popularity"],
                latitude=d["lat"],
                longitude=d["lng"],
            )
            session.add(dest)
            await session.flush()
            dest_map[d["city"]] = dest

            for season, ms, me, temp, weather, mult in SEASONS:
                session.add(
                    DestinationSeason(
                        destination_id=dest.id,
                        season=season,
                        month_start=ms,
                        month_end=me,
                        avg_temp_c=temp,
                        weather_score=weather,
                        price_multiplier=mult,
                    )
                )

            for name, cat, desc, min_a, max_a, price, tags in d["attractions"]:
                session.add(
                    Attraction(
                        destination_id=dest.id,
                        name=name,
                        category=cat,
                        description=desc,
                        min_age=min_a,
                        max_age=max_a,
                        price=price,
                        family_friendly=True,
                        tags=tags,
                    )
                )
                session.add(
                    Activity(
                        destination_id=dest.id,
                        name=name,
                        category=cat,
                        description=desc,
                        price=price,
                    )
                )

            for name, typ, rating, price, ff, guests in d["accommodations"]:
                session.add(
                    Accommodation(
                        destination_id=dest.id,
                        name=name,
                        type=typ,
                        rating=rating,
                        price_per_night=price,
                        family_friendly=ff,
                        max_guests=guests,
                    )
                )

        # Sample flights from CDG hub to all destinations
        cdg = airport_map["CDG"]
        for city, dest in dest_map.items():
            if city == "Paris":
                continue
            iata = next(d["airport"][1] for d in DESTINATIONS if d["city"] == city)
            ap = airport_map[iata]
            session.add(
                Flight(
                    origin_airport_id=cdg.id,
                    destination_airport_id=ap.id,
                    departure_date=datetime(2025, 8, 15, 10, 0, tzinfo=timezone.utc),
                    price=80.0 + len(city) * 5,
                    airline="Air Europe",
                    seats_remaining=120,
                )
            )
            session.add(
                Flight(
                    origin_airport_id=ap.id,
                    destination_airport_id=cdg.id,
                    departure_date=datetime(2025, 8, 22, 14, 0, tzinfo=timezone.utc),
                    price=85.0 + len(city) * 5,
                    airline="Air Europe",
                    seats_remaining=120,
                )
            )

        demo = User(
            email=DEMO_EMAIL,
            username="demo",
            hashed_password=hash_password(DEMO_PASSWORD),
            first_name="Demo",
            last_name="User",
            is_active=True,
        )
        session.add(demo)
        await session.commit()
        print("Seed completed: 7 destinations, attractions, accommodations, flights, demo user.")


async def ensure_extra_airports() -> None:
    """Add regional hub airports and sync city coordinates (safe to re-run)."""
    async with AsyncSessionLocal() as session:
        added = 0
        for entry in EXTRA_AIRPORTS:
            result = await session.execute(select(Country).where(Country.code == entry["code"]))
            country = result.scalar_one_or_none()
            if not country:
                country = Country(name=entry["country"], code=entry["code"])
                session.add(country)
                await session.flush()

            result = await session.execute(
                select(City).where(City.name == entry["city"], City.country_id == country.id)
            )
            city = result.scalar_one_or_none()
            if not city:
                city = City(
                    country_id=country.id,
                    name=entry["city"],
                    latitude=entry["lat"],
                    longitude=entry["lng"],
                )
                session.add(city)
                await session.flush()
            else:
                city.latitude = entry["lat"]
                city.longitude = entry["lng"]

            ap_name, iata = entry["airport"]
            result = await session.execute(select(Airport).where(Airport.iata_code == iata))
            if not result.scalar_one_or_none():
                session.add(Airport(city_id=city.id, name=ap_name, iata_code=iata))
                added += 1

        # Backfill coordinates on destination cities from Destination table
        result = await session.execute(
            select(City, Destination.latitude, Destination.longitude)
            .join(Destination, Destination.city_id == City.id)
            .where(City.latitude.is_(None))
        )
        for city, lat, lng in result.all():
            if lat is not None and lng is not None:
                city.latitude = lat
                city.longitude = lng

        await session.commit()
        if added:
            print(f"Added {added} extra regional airports.")


async def ensure_demo_user() -> None:
    """Create or update the demo account (runs even when catalog data already exists)."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.username == "demo"))
        user = result.scalar_one_or_none()
        if user:
            if user.email != DEMO_EMAIL:
                user.email = DEMO_EMAIL
                user.hashed_password = hash_password(DEMO_PASSWORD)
                user.is_active = True
                await session.commit()
                print(f"Demo user email updated to {DEMO_EMAIL}")
            return

        result = await session.execute(select(User).where(User.email == DEMO_EMAIL))
        if result.scalar_one_or_none():
            return

        session.add(
            User(
                email=DEMO_EMAIL,
                username="demo",
                hashed_password=hash_password(DEMO_PASSWORD),
                first_name="Demo",
                last_name="User",
                is_active=True,
            )
        )
        await session.commit()
        print(f"Demo user created: {DEMO_EMAIL}")


async def main() -> None:
    from app.services.airport_catalog import ensure_catalog_file

    ensure_catalog_file()
    await seed()
    await ensure_extra_airports()
    await ensure_demo_user()
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())

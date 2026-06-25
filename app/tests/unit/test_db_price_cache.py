from datetime import date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.integrations.accommodations.base import AccommodationSearchCriteria
from app.integrations.accommodations.db_accommodation import DbAccommodationProvider
from app.integrations.flights.base import FlightSearchCriteria
from app.integrations.flights.db_flight import DbFlightProvider, _offers_from_payload
from app.models.offer_cache import FlightOfferCache, HotelOfferCache
from app.utils.seed_price_cache import _flight_payload, _hotel_payload, seed_price_cache

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def session():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(
            lambda sync_conn: FlightOfferCache.__table__.create(sync_conn, checkfirst=True)
        )
        await conn.run_sync(
            lambda sync_conn: HotelOfferCache.__table__.create(sync_conn, checkfirst=True)
        )
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as sess:
        yield sess
    await engine.dispose()


def test_offers_from_payload_round_trip():
    payload = _flight_payload("SOF", "PRG", "Prague", 420.0, "Lufthansa", "LH")
    criteria = FlightSearchCriteria(
        origin_iata="SOF",
        destination_iata="PRG",
        departure_date=date(2026, 7, 15),
        party_size=2,
        return_date=date(2026, 7, 20),
    )
    offers = _offers_from_payload(payload, criteria)
    assert len(offers) >= 2
    assert offers[0].price == 420.0
    assert offers[0].return_leg is not None
    assert offers[0].bundled_round_trip is True


@pytest.mark.asyncio
async def test_db_flight_provider_search(session):
    payload = _flight_payload("SOF", "PRG", "Prague", 420.0, "Lufthansa", "LH")
    session.add(
        FlightOfferCache(
            origin_iata="SOF",
            destination_iata="PRG",
            departure_date=date(2026, 7, 15),
            return_date=date(2026, 7, 20),
            party_size=2,
            payload=payload,
        )
    )
    await session.commit()

    provider = DbFlightProvider(session)
    offers = await provider.search(
        FlightSearchCriteria(
            origin_iata="SOF",
            destination_iata="PRG",
            departure_date=date(2026, 7, 15),
            party_size=2,
            return_date=date(2026, 7, 20),
        )
    )
    assert len(offers) >= 1
    assert offers[0].airline == "Lufthansa"


@pytest.mark.asyncio
async def test_db_accommodation_provider_search(session):
    session.add(
        HotelOfferCache(
            city="Prague",
            country="Czech Republic",
            payload=_hotel_payload("Prague", "Czech Republic", "Family Hotel Prague", 4.5, 89.0, ["Pool"]),
        )
    )
    await session.commit()

    provider = DbAccommodationProvider(session)
    offers = await provider.search(
        AccommodationSearchCriteria(
            city="Prague",
            check_in=date(2026, 7, 15),
            check_out=date(2026, 7, 20),
            country="Czech Republic",
        )
    )
    assert len(offers) == 1
    assert offers[0].name == "Family Hotel Prague"
    assert offers[0].total_price == 445.0

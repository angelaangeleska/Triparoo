"""Merge SerpAPI travel destinations with DB catalog metadata."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.integrations.destinations.serpapi_travel_explore import (
    SerpApiDestination,
    SerpApiTravelExploreProvider,
    get_serpapi_destination_cache,
)
from app.repositories.catalog import DestinationRepository
from app.schemas.catalog import DestinationRead


def _db_to_read(dest) -> DestinationRead:
    return DestinationRead(
        id=dest.id,
        city_id=dest.city_id,
        description=dest.description,
        family_friendliness_score=dest.family_friendliness_score,
        popularity_score=dest.popularity_score,
        city=dest.city.name if dest.city else None,
        country=dest.city.country.name if dest.city and dest.city.country else None,
        source="db",
    )


def _serpapi_to_read(dest: SerpApiDestination, db_id: int | None = None) -> DestinationRead:
    return DestinationRead(
        id=db_id if db_id is not None else dest.id,
        city_id=0,
        description=dest.description,
        family_friendliness_score=dest.family_friendliness_score,
        popularity_score=dest.popularity_score,
        city=dest.city,
        country=dest.country,
        thumbnail=dest.thumbnail or None,
        flight_price=dest.flight_price,
        hotel_price=dest.hotel_price,
        start_date=dest.start_date,
        end_date=dest.end_date,
        airline=dest.airline,
        destination_airport_code=dest.destination_airport_code,
        source="serpapi",
    )


class DestinationCatalogService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = DestinationRepository(session)
        self.serpapi = SerpApiTravelExploreProvider()

    async def list_destinations(
        self,
        *,
        departure_iata: str = "SOF",
        adults: int = 2,
        children: int = 0,
        month: int = 0,
    ) -> list[DestinationRead]:
        db_destinations = await self.repo.list_with_relations()
        db_by_city = {
            (d.city.name or "").strip().lower(): d
            for d in db_destinations
            if d.city and d.city.name
        }

        if settings.SERPAPI_API_KEY:
            scraped = await self.serpapi.search(
                departure_iata,
                adults=adults,
                children=children,
                month=month,
            )
            if scraped:
                results: list[DestinationRead] = []
                seen_cities: set[str] = set()
                for item in scraped:
                    city_key = item.city.strip().lower()
                    if city_key in seen_cities:
                        continue
                    seen_cities.add(city_key)
                    db_match = db_by_city.get(city_key)
                    if db_match:
                        read = _db_to_read(db_match)
                        read.thumbnail = item.thumbnail or read.thumbnail
                        read.flight_price = item.flight_price
                        read.hotel_price = item.hotel_price
                        read.start_date = item.start_date
                        read.end_date = item.end_date
                        read.airline = item.airline
                        read.destination_airport_code = item.destination_airport_code
                        read.source = "serpapi"
                        if item.description and not read.description:
                            read.description = item.description
                    else:
                        read = _serpapi_to_read(item)
                    results.append(read)

                for db_dest in db_destinations:
                    city_key = (db_dest.city.name or "").strip().lower()
                    if city_key and city_key not in seen_cities:
                        results.append(_db_to_read(db_dest))
                return results

        return [_db_to_read(d) for d in db_destinations]

    async def get_destination(self, destination_id: int) -> DestinationRead | None:
        db_dest = await self.repo.get_with_relations(destination_id)
        if db_dest:
            return _db_to_read(db_dest)

        cached = get_serpapi_destination_cache().get_by_id(destination_id)
        if cached:
            db_match = None
            if cached.city:
                all_db = await self.repo.list_with_relations()
                for d in all_db:
                    if d.city and d.city.name and d.city.name.lower() == cached.city.lower():
                        db_match = d
                        break
            if db_match:
                read = _db_to_read(db_match)
                read.thumbnail = cached.thumbnail or read.thumbnail
                read.flight_price = cached.flight_price
                read.hotel_price = cached.hotel_price
                read.start_date = cached.start_date
                read.end_date = cached.end_date
                read.airline = cached.airline
                read.destination_airport_code = cached.destination_airport_code
                read.source = "serpapi"
                return read
            return _serpapi_to_read(cached)
        return None

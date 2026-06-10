from dataclasses import dataclass
from typing import Literal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.country import Airport, City
from app.services.airport_catalog import get_airport_catalog

MatchType = Literal["direct", "closest", "country", "iata"]


@dataclass
class AirportSearchResult:
    id: int
    name: str
    iata_code: str
    city_name: str
    country_name: str
    match_type: MatchType
    distance_km: float | None = None
    note: str | None = None


class AirportSearchService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.catalog = get_airport_catalog()

    async def _db_iata_map(self) -> dict[str, int]:
        result = await self.session.execute(select(Airport.iata_code, Airport.id))
        return {row[0].upper(): row[1] for row in result.all()}

    def _result_id(self, iata: str, db_map: dict[str, int]) -> int:
        if iata in db_map:
            return db_map[iata]
        # Stable synthetic id for airports not in the trip-destination database
        return 1_000_000_000 + abs(hash(iata)) % 900_000_000

    async def search(self, query: str, limit: int = 20) -> list[AirportSearchResult]:
        q = query.strip()
        if len(q) < 2:
            return []

        db_map = await self._db_iata_map()
        catalog_hits = self.catalog.search(q, limit=limit)
        results: list[AirportSearchResult] = []

        for ap, match_type, distance_km, note in catalog_hits:
            results.append(
                AirportSearchResult(
                    id=self._result_id(ap.iata, db_map),
                    name=ap.name,
                    iata_code=ap.iata,
                    city_name=ap.city or ap.name,
                    country_name=ap.country,
                    match_type=match_type,  # type: ignore[arg-type]
                    distance_km=round(distance_km, 1) if distance_km is not None else None,
                    note=note,
                )
            )

        if results:
            priority = {"iata": 0, "direct": 1, "closest": 2, "country": 3}
            results.sort(
                key=lambda r: (
                    priority.get(r.match_type, 9),
                    r.distance_km or 0,
                    r.city_name,
                )
            )
            return results[:limit]

        # Legacy DB-only fallback (destination seed airports)
        airport_result = await self.session.execute(
            select(Airport).options(selectinload(Airport.city).selectinload(City.country))
        )
        q_lower = q.lower()
        for airport in airport_result.scalars().unique().all():
            city = airport.city
            country = city.country if city else None
            if (
                q_lower in airport.iata_code.lower()
                or q_lower in airport.name.lower()
                or (city and q_lower in city.name.lower())
            ):
                results.append(
                    AirportSearchResult(
                        id=airport.id,
                        name=airport.name,
                        iata_code=airport.iata_code,
                        city_name=city.name if city else "",
                        country_name=country.name if country else "",
                        match_type="direct",
                    )
                )
        return results[:limit]

    async def iata_for_id(self, airport_id: int) -> str | None:
        if airport_id >= 1_000_000_000:
            for iata, db_id in (await self._db_iata_map()).items():
                if db_id == airport_id:
                    return iata
            for ap in self.catalog.airports:
                if self._result_id(ap.iata, await self._db_iata_map()) == airport_id:
                    return ap.iata
            return None
        result = await self.session.execute(select(Airport.iata_code).where(Airport.id == airport_id))
        row = result.first()
        return row[0].upper() if row else None

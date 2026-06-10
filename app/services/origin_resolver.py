from dataclasses import dataclass
from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.airport_search import AirportSearchService

LocationType = Literal["city", "country", "airport"]


@dataclass
class ResolvedOrigin:
    query: str
    location_type: LocationType
    display_name: str
    airport_iatas: list[str]
    airport_ids: list[int]
    primary_airport_id: int | None
    primary_iata: str | None
    message: str


class OriginResolverService:
    """Resolve a city or country name to usable airport(s) worldwide."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.search = AirportSearchService(session)

    async def resolve(self, query: str) -> ResolvedOrigin | None:
        q = query.strip()
        if len(q) < 2:
            return None

        results = await self.search.search(q, limit=30)
        if not results:
            return None

        country_hits = [r for r in results if r.match_type == "country"]
        if country_hits:
            country_name = country_hits[0].country_name
            return ResolvedOrigin(
                query=q,
                location_type="country",
                display_name=country_name,
                airport_iatas=[r.iata_code for r in country_hits],
                airport_ids=[r.id for r in country_hits],
                primary_airport_id=country_hits[0].id,
                primary_iata=country_hits[0].iata_code,
                message=f"Departing from {country_name} — comparing flights from {len(country_hits)} airport(s)",
            )

        direct = [r for r in results if r.match_type in ("direct", "iata")]
        if direct:
            best = direct[0]
            # Group airports that belong to the same city as the top result
            same_city = [r for r in direct if r.city_name.lower() == best.city_name.lower()]
            if len(same_city) > 1:
                iata_list = ", ".join(r.iata_code for r in same_city)
                msg = f"Departing from {best.city_name} — {len(same_city)} airports ({iata_list})"
            else:
                msg = f"Departing from {best.city_name} ({best.iata_code})"
            return ResolvedOrigin(
                query=q,
                location_type="airport",
                display_name=f"{best.city_name}, {best.country_name}",
                airport_iatas=[r.iata_code for r in direct],
                airport_ids=[r.id for r in direct],
                primary_airport_id=best.id,
                primary_iata=best.iata_code,
                message=msg,
            )

        closest = [r for r in results if r.match_type == "closest"]
        if closest:
            best = closest[0]
            dist = f"{best.distance_km:.0f} km" if best.distance_km else "nearby"
            return ResolvedOrigin(
                query=q,
                location_type="city",
                display_name=best.city_name,
                airport_iatas=[r.iata_code for r in closest[:5]],
                airport_ids=[r.id for r in closest[:5]],
                primary_airport_id=best.id,
                primary_iata=best.iata_code,
                message=(
                    f"No airport in {q.title()} — using {best.name} ({best.iata_code}) "
                    f"in {best.city_name}, {dist} away"
                ),
            )

        best = results[0]
        return ResolvedOrigin(
            query=q,
            location_type="city",
            display_name=best.city_name,
            airport_iatas=[r.iata_code for r in results[:5]],
            airport_ids=[r.id for r in results[:5]],
            primary_airport_id=best.id,
            primary_iata=best.iata_code,
            message=f"Departing near {q.title()} via {best.city_name} ({best.iata_code})",
        )

    async def resolve_airports(
        self,
        origin_location: str | None = None,
        origin_airport_id: int | None = None,
    ) -> tuple[list[str], list[int], str | None]:
        if origin_location:
            resolved = await self.resolve(origin_location)
            if resolved:
                return resolved.airport_iatas, resolved.airport_ids, resolved.message
        if origin_airport_id:
            iata = await self.search.iata_for_id(origin_airport_id)
            if iata:
                return [iata], [origin_airport_id], None
            result = await self.search.search(str(origin_airport_id), limit=1)
            if result:
                return [result[0].iata_code], [origin_airport_id], None
        return [], [], None

    async def resolve_airport_ids(
        self,
        origin_location: str | None = None,
        origin_airport_id: int | None = None,
    ) -> tuple[list[int], str | None]:
        iatas, ids, message = await self.resolve_airports(origin_location, origin_airport_id)
        return ids, message

    def get_excluded_destination_ids(
        self,
        destinations: list,
        origin_airport_ids: list[int],
        resolved: ResolvedOrigin | None = None,
        origin_iatas: list[str] | None = None,
    ) -> set[int]:
        """Exclude destinations in the same city as a city/airport departure point."""
        excluded: set[int] = set()
        origin_iata_set = {i.upper() for i in (origin_iatas or [])}
        if resolved:
            origin_iata_set.update(i.upper() for i in resolved.airport_iatas)

        if not origin_airport_ids and not origin_iata_set:
            return excluded

        origin_city_names: set[str] = set()
        if resolved and resolved.location_type != "country":
            origin_city_names.add(resolved.display_name.split(",")[0].strip().lower())

        for dest in destinations:
            if not dest.city:
                continue
            city_name = dest.city.name.lower()
            if city_name in origin_city_names:
                excluded.add(dest.id)
                continue
            if resolved and resolved.location_type == "country":
                continue
            if dest.city.airports:
                for ap in dest.city.airports:
                    if ap.id in origin_airport_ids or ap.iata_code.upper() in origin_iata_set:
                        excluded.add(dest.id)
                        break
        return excluded

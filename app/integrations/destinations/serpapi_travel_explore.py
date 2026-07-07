"""Google Travel Explore destinations via SerpAPI."""

from __future__ import annotations

import asyncio
import hashlib
import logging
import time
from dataclasses import dataclass, field

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

_SERPAPI_URL = "https://serpapi.com/search"
_EUROPE_AREA_KGMID = "/m/02j9z"
_CACHE_TTL_SECONDS = 3600
_SUPPLEMENT_DEPARTURES = ("CDG", "FRA", "LHR", "AMS", "BCN", "MAD", "JFK")


@dataclass
class SerpApiDestination:
    city: str
    country: str
    description: str
    family_friendliness_score: float
    popularity_score: float
    thumbnail: str = ""
    flight_price: float | None = None
    hotel_price: float | None = None
    start_date: str | None = None
    end_date: str | None = None
    airline: str | None = None
    destination_airport_code: str | None = None
    gps_coordinates: dict = field(default_factory=dict)
    link: str = ""
    source: str = "serpapi"

    @property
    def id(self) -> int:
        key = f"{self.city}:{self.country}".lower()
        return int(hashlib.md5(key.encode()).hexdigest()[:8], 16)


class SerpApiDestinationCache:
    """In-memory cache for SerpAPI destination lookups."""

    def __init__(self) -> None:
        self._by_id: dict[int, SerpApiDestination] = {}
        self._list_cache: dict[str, tuple[float, list[SerpApiDestination]]] = {}

    def store(self, destinations: list[SerpApiDestination]) -> None:
        for dest in destinations:
            self._by_id[dest.id] = dest

    def get_by_id(self, destination_id: int) -> SerpApiDestination | None:
        return self._by_id.get(destination_id)

    def get_list(self, cache_key: str) -> list[SerpApiDestination] | None:
        entry = self._list_cache.get(cache_key)
        if not entry:
            return None
        ts, items = entry
        if time.time() - ts > _CACHE_TTL_SECONDS:
            return None
        return items

    def set_list(self, cache_key: str, items: list[SerpApiDestination]) -> None:
        if not items:
            return
        self._list_cache[cache_key] = (time.time(), items)
        self.store(items)


_cache = SerpApiDestinationCache()


def get_serpapi_destination_cache() -> SerpApiDestinationCache:
    return _cache


def _parse_destination(item: dict) -> SerpApiDestination | None:
    try:
        name = (item.get("name") or "").strip()
        country = (item.get("country") or "").strip()
        if not name:
            return None

        flight_price = item.get("flight_price")
        hotel_price = item.get("hotel_price")
        if isinstance(flight_price, str):
            flight_price = float(flight_price.replace(",", "").replace("$", "").replace("€", "") or 0) or None
        if isinstance(hotel_price, str):
            hotel_price = float(hotel_price.replace(",", "").replace("$", "").replace("€", "") or 0) or None

        airport = item.get("destination_airport") or {}
        airport_code = airport.get("code") if isinstance(airport, dict) else None

        price_hint = ""
        if flight_price:
            price_hint = f" Flights from €{float(flight_price):.0f}."
        if hotel_price:
            price_hint += f" Stays from €{float(hotel_price):.0f}."
        airline = item.get("airline")
        if airline:
            price_hint += f" via {airline}."

        popularity = 70.0
        if flight_price and float(flight_price) < 150:
            popularity += 10
        if hotel_price and float(hotel_price) < 100:
            popularity += 5

        return SerpApiDestination(
            city=name,
            country=country,
            description=f"Explore {name}, {country}.{price_hint}".strip(),
            family_friendliness_score=min(95.0, 72.0 + (10 if "disney" in name.lower() else 0)),
            popularity_score=min(99.0, popularity),
            thumbnail=item.get("thumbnail") or "",
            flight_price=float(flight_price) if flight_price else None,
            hotel_price=float(hotel_price) if hotel_price else None,
            start_date=item.get("start_date"),
            end_date=item.get("end_date"),
            airline=airline,
            destination_airport_code=airport_code,
            gps_coordinates=item.get("gps_coordinates") or {},
            link=item.get("link") or "",
        )
    except (KeyError, TypeError, ValueError) as exc:
        logger.debug("Failed to parse SerpAPI destination: %s", exc)
        return None


class SerpApiTravelExploreProvider:
    @property
    def enabled(self) -> bool:
        return bool(settings.SERPAPI_API_KEY)

    @staticmethod
    def _query_params(
        departure_id: str,
        *,
        adults: int,
        children: int,
        month: int,
        max_price: int | None,
        arrival_area_id: str | None = None,
    ) -> dict:
        params: dict = {
            "departure_id": departure_id.upper(),
            "adults": adults,
        }
        if children > 0:
            params["children"] = children
        if month > 0:
            params["month"] = month
        if max_price:
            params["max_price"] = max_price
        if arrival_area_id:
            params["arrival_area_id"] = arrival_area_id
        return params

    async def _fetch_page(self, params: dict) -> list[SerpApiDestination]:
        if not self.enabled:
            return []

        base = {
            "engine": "google_travel_explore",
            "currency": "EUR",
            "hl": "en",
            "gl": "us",
            "travel_duration": "2",
            "type": "1",
            "api_key": settings.SERPAPI_API_KEY,
        }
        base.update(params)

        try:
            async with httpx.AsyncClient(timeout=35.0) as client:
                resp = await client.get(_SERPAPI_URL, params=base)
            data = resp.json()
            if "error" in data:
                logger.warning("SerpAPI travel explore error: %s", data["error"])
                return []
            if resp.status_code != 200:
                logger.warning("SerpAPI travel explore %s: %s", resp.status_code, resp.text[:200])
                return []

            results: list[SerpApiDestination] = []
            for item in data.get("destinations") or []:
                parsed = _parse_destination(item)
                if parsed:
                    results.append(parsed)
            return results
        except httpx.HTTPError as exc:
            logger.error("SerpAPI travel explore HTTP error: %s", exc)
        except Exception as exc:
            logger.error("SerpAPI travel explore failed: %s", exc)
        return []

    async def search(
        self,
        departure_id: str = "SOF",
        *,
        adults: int = 2,
        children: int = 0,
        month: int = 0,
        max_price: int | None = None,
    ) -> list[SerpApiDestination]:
        if not self.enabled:
            return []

        cache_key = f"v2:{departure_id}:{adults}:{children}:{month}:{max_price or 0}"
        cached = get_serpapi_destination_cache().get_list(cache_key)
        if cached is not None:
            return cached

        primary = departure_id.upper()
        query_kw = dict(adults=adults, children=children, month=month, max_price=max_price)

        primary_tasks = [
            self._fetch_page(
                self._query_params(primary, arrival_area_id=_EUROPE_AREA_KGMID, **query_kw)
            ),
            self._fetch_page(self._query_params(primary, **query_kw)),
        ]
        hub_tasks = [
            self._fetch_page(
                self._query_params(hub, arrival_area_id=_EUROPE_AREA_KGMID, **query_kw)
            )
            for hub in _SUPPLEMENT_DEPARTURES
            if hub != primary
        ]
        all_results = await asyncio.gather(*primary_tasks, *hub_tasks)

        seen: set[str] = set()
        merged: list[SerpApiDestination] = []
        for batch in all_results[: len(primary_tasks)]:
            for dest in batch:
                key = f"{dest.city}|{dest.country}".lower()
                if key in seen:
                    continue
                seen.add(key)
                merged.append(dest)

        for batch in all_results[len(primary_tasks) :]:
            for dest in batch:
                key = f"{dest.city}|{dest.country}".lower()
                if key in seen:
                    continue
                seen.add(key)
                merged.append(
                    SerpApiDestination(
                        city=dest.city,
                        country=dest.country,
                        description=dest.description,
                        family_friendliness_score=dest.family_friendliness_score,
                        popularity_score=dest.popularity_score,
                        thumbnail=dest.thumbnail,
                        hotel_price=dest.hotel_price,
                        destination_airport_code=dest.destination_airport_code,
                        gps_coordinates=dest.gps_coordinates,
                        link=dest.link,
                    )
                )

        if merged:
            get_serpapi_destination_cache().set_list(cache_key, merged)
            logger.info(
                "SerpAPI: %d travel explore destinations (primary %s)",
                len(merged),
                primary,
            )
        return merged

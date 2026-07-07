"""Amadeus destination discovery — City Search and Flight Inspiration."""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass

from app.integrations.amadeus.client import get_amadeus_client

logger = logging.getLogger(__name__)

# Popular city keywords for browse-without-search; Amadeus City Search needs 3+ chars.
POPULAR_CITY_KEYWORDS = (
    "Paris",
    "Rome",
    "Barcelona",
    "London",
    "Amsterdam",
    "Prague",
    "Vienna",
    "Lisbon",
    "Dublin",
    "Athens",
    "Berlin",
    "Madrid",
)


@dataclass
class AmadeusDestination:
    city_code: str
    city_name: str
    country_code: str
    country_name: str
    latitude: float | None = None
    longitude: float | None = None
    description: str | None = None
    iata_code: str | None = None

    @property
    def id(self) -> int:
        key = f"{self.city_code}:{self.country_code}".upper()
        return int(hashlib.md5(key.encode()).hexdigest()[:8], 16)

    @property
    def name(self) -> str:
        return self.city_name

    @property
    def country(self) -> str:
        return self.country_name


def _parse_city(item: dict) -> AmadeusDestination | None:
    try:
        city_code = item.get("iataCode") or item.get("cityCode") or ""
        name = item.get("name") or ""
        if not city_code or not name:
            return None
        address = item.get("address") or {}
        geo = item.get("geoCode") or {}
        return AmadeusDestination(
            city_code=city_code.upper(),
            city_name=name,
            country_code=(address.get("countryCode") or "").upper(),
            country_name=address.get("countryName") or address.get("countryCode") or "",
            latitude=float(geo["latitude"]) if geo.get("latitude") is not None else None,
            longitude=float(geo["longitude"]) if geo.get("longitude") is not None else None,
            iata_code=city_code.upper(),
            description=f"{name}, {address.get('countryName') or address.get('countryCode', '')}".strip(", "),
        )
    except (KeyError, TypeError, ValueError) as exc:
        logger.debug("Failed to parse Amadeus city: %s", exc)
        return None


def _parse_flight_destination(item: dict) -> AmadeusDestination | None:
    try:
        dest = item.get("destination") or ""
        if not dest:
            return None
        price = item.get("price") or {}
        return AmadeusDestination(
            city_code=dest.upper(),
            city_name=dest.upper(),
            country_code="",
            country_name="",
            description=f"Flights from {item.get('origin', '')} from {price.get('total', '?')} {price.get('currency', 'EUR')}",
            iata_code=dest.upper(),
        )
    except (KeyError, TypeError, ValueError) as exc:
        logger.debug("Failed to parse flight destination: %s", exc)
        return None


class AmadeusDestinationService:
    def __init__(self) -> None:
        self.client = get_amadeus_client()

    @property
    def enabled(self) -> bool:
        return self.client.enabled

    async def search_cities(
        self,
        keyword: str,
        *,
        country_code: str = "",
        max_results: int = 20,
    ) -> list[AmadeusDestination]:
        if not self.enabled or len(keyword) < 3:
            return []

        params: dict = {"keyword": keyword[:10], "max": max_results}
        if country_code:
            params["countryCode"] = country_code.upper()

        data = await self.client.get_json("/v1/reference-data/locations/cities", params=params)
        seen: set[str] = set()
        results: list[AmadeusDestination] = []
        for item in data.get("data") or []:
            dest = _parse_city(item)
            if dest and dest.city_code not in seen:
                seen.add(dest.city_code)
                results.append(dest)
        return results

    async def list_popular(self, max_results: int = 20) -> list[AmadeusDestination]:
        seen: set[str] = set()
        results: list[AmadeusDestination] = []
        for keyword in POPULAR_CITY_KEYWORDS:
            if len(results) >= max_results:
                break
            for dest in await self.search_cities(keyword, max_results=3):
                if dest.city_code not in seen:
                    seen.add(dest.city_code)
                    results.append(dest)
        return results[:max_results]

    async def flight_inspiration(
        self,
        origin_iata: str,
        *,
        max_price: int | None = None,
        max_results: int = 20,
    ) -> list[AmadeusDestination]:
        if not self.enabled:
            return []

        params: dict = {"origin": origin_iata.upper()}
        if max_price:
            params["maxPrice"] = max_price

        data = await self.client.get_json("/v1/shopping/flight-destinations", params=params)
        results: list[AmadeusDestination] = []
        for item in (data.get("data") or [])[:max_results]:
            dest = _parse_flight_destination(item)
            if dest:
                enriched = await self.search_cities(dest.city_code, max_results=1)
                if enriched:
                    dest = enriched[0]
                results.append(dest)
        return results

    async def get_by_id(self, destination_id: int) -> AmadeusDestination | None:
        for dest in await self.list_popular(max_results=50):
            if dest.id == destination_id:
                return dest
        return None

    async def get_by_city_code(self, city_code: str) -> AmadeusDestination | None:
        cities = await self.search_cities(city_code, max_results=1)
        return cities[0] if cities else None

"""Amadeus Tours and Activities API."""

from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass

from app.integrations.amadeus.client import get_amadeus_client

logger = logging.getLogger(__name__)


@dataclass
class AmadeusActivity:
    activity_id: str
    name: str
    category: str
    description: str
    price: float
    currency: str
    family_friendly: bool
    min_age: int
    max_age: int
    tags: list[str]
    booking_url: str
    image_url: str
    latitude: float | None = None
    longitude: float | None = None

    @property
    def id(self) -> int:
        return int(hashlib.md5(self.activity_id.encode()).hexdigest()[:8], 16)


def _parse_price(raw: dict | None) -> tuple[float, str]:
    if not raw:
        return 0.0, "EUR"
    amount = raw.get("amount") or raw.get("total") or "0"
    try:
        return float(amount), raw.get("currencyCode") or raw.get("currency") or "EUR"
    except (TypeError, ValueError):
        return 0.0, "EUR"


def _family_friendly(name: str, description: str, category: str) -> bool:
    text = f"{name} {description} {category}".lower()
    family_words = ("family", "kids", "children", "kid", "child", "zoo", "aquarium", "park", "museum")
    return any(w in text for w in family_words)


def _parse_activity(item: dict) -> AmadeusActivity | None:
    try:
        name = (item.get("name") or "").strip()
        if not name:
            return None

        geo = item.get("geoCode") or {}
        price_block = item.get("price") or {}
        price, currency = _parse_price(price_block)

        pictures = item.get("pictures") or []
        image_url = pictures[0] if pictures else ""

        category = "activity"
        if item.get("type"):
            category = str(item["type"]).lower().replace("_", " ")

        description = (item.get("shortDescription") or item.get("description") or "").strip()
        description = re.sub(r"<[^>]+>", "", description)

        return AmadeusActivity(
            activity_id=str(item.get("id") or name),
            name=name,
            category=category,
            description=description,
            price=price,
            currency=currency,
            family_friendly=_family_friendly(name, description, category),
            min_age=0,
            max_age=99,
            tags=[category] if category else [],
            booking_url=item.get("bookingLink") or item.get("link") or "",
            image_url=image_url,
            latitude=float(geo["latitude"]) if geo.get("latitude") is not None else None,
            longitude=float(geo["longitude"]) if geo.get("longitude") is not None else None,
        )
    except (KeyError, TypeError, ValueError) as exc:
        logger.debug("Failed to parse Amadeus activity: %s", exc)
        return None


class AmadeusActivityService:
    def __init__(self) -> None:
        self.client = get_amadeus_client()

    @property
    def enabled(self) -> bool:
        return self.client.enabled

    async def search(
        self,
        latitude: float,
        longitude: float,
        *,
        radius: int = 5,
        max_results: int = 20,
    ) -> list[AmadeusActivity]:
        if not self.enabled:
            return []

        params = {
            "latitude": latitude,
            "longitude": longitude,
            "radius": radius,
        }
        data = await self.client.get_json("/v1/shopping/activities", params=params)
        results: list[AmadeusActivity] = []
        for item in (data.get("data") or [])[:max_results]:
            activity = _parse_activity(item)
            if activity:
                results.append(activity)
        return results

    async def search_by_city(
        self,
        city_code: str,
        *,
        latitude: float | None = None,
        longitude: float | None = None,
        max_results: int = 20,
    ) -> list[AmadeusActivity]:
        if latitude is not None and longitude is not None:
            return await self.search(latitude, longitude, max_results=max_results)

        from app.integrations.amadeus.destinations import AmadeusDestinationService

        dest_svc = AmadeusDestinationService()
        dest = await dest_svc.get_by_city_code(city_code)
        if dest and dest.latitude is not None and dest.longitude is not None:
            return await self.search(dest.latitude, dest.longitude, max_results=max_results)
        return []

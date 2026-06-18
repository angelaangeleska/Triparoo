"""Real-time hotel search via SerpAPI Google Hotels engine."""

from __future__ import annotations

import logging
import re

import httpx

from app.core.config import settings
from app.integrations.accommodations.base import (
    AccommodationOffer,
    AccommodationSearchCriteria,
    BookingSource,
)

logger = logging.getLogger(__name__)

_SERPAPI_URL = "https://serpapi.com/search"
_FAMILY_KEYWORDS = {"pool", "kids", "family", "children", "playground", "babysit", "crib"}


def _extract_image_url(prop: dict) -> str:
    """Pick the best loadable hotel photo from SerpAPI / Google Hotels fields."""
    top_level = prop.get("thumbnail") or prop.get("image")
    if isinstance(top_level, str) and top_level.startswith("http"):
        return top_level

    images = prop.get("images") or []
    for img in images:
        if isinstance(img, str) and img.startswith("http"):
            return img
        if not isinstance(img, dict):
            continue
        for key in ("original", "thumbnail", "image", "url", "link"):
            val = img.get(key)
            if isinstance(val, str) and val.startswith("http"):
                return val
    return ""


def _price(value) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    cleaned = re.sub(r"[^\d.]", "", str(value))
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def parse_hotel_property(prop: dict, nights: int) -> AccommodationOffer | None:
    name = prop.get("name", "").strip()
    if not name:
        return None

    rate_block = prop.get("rate_per_night") or {}
    total_block = prop.get("total_rate") or {}

    price_per_night = (
        _price(rate_block.get("extracted_lowest"))
        or _price(rate_block.get("lowest"))
        or _price(prop.get("price"))
    )
    total_price = (
        _price(total_block.get("extracted_lowest"))
        or _price(total_block.get("lowest"))
        or _price(prop.get("total_price"))
        or round(price_per_night * nights, 2)
    )
    if price_per_night == 0 and total_price > 0:
        price_per_night = round(total_price / nights, 2)
    if price_per_night == 0:
        return None

    amenities: list[str] = prop.get("amenities") or []
    family_friendly = any(k in " ".join(amenities).lower() for k in _FAMILY_KEYWORDS)

    booking_sources: list[BookingSource] = []
    for p in (prop.get("prices") or [])[:5]:
        link = p.get("link", "")
        if not link:
            continue
        sp = _price(p.get("extracted_rate_per_night")) or _price(p.get("rate_per_night")) or price_per_night
        st = _price(p.get("extracted_total_rate")) or _price(p.get("total_rate")) or total_price
        booking_sources.append(
            BookingSource(
                name=p.get("source", "Book"),
                price_per_night=round(sp, 2),
                total_price=round(st, 2),
                currency="USD",
                url=link,
            )
        )

    image_url = _extract_image_url(prop)
    rating_raw = prop.get("overall_rating")

    return AccommodationOffer(
        name=name,
        type=prop.get("type", "Hotel"),
        hotel_class=prop.get("hotel_class", ""),
        rating=float(rating_raw) if rating_raw else None,
        reviews_count=prop.get("reviews"),
        price_per_night=round(price_per_night, 2),
        total_price=round(total_price, 2),
        currency="USD",
        family_friendly=family_friendly,
        image_url=image_url,
        google_url=prop.get("link", ""),
        booking_sources=booking_sources,
        amenities=amenities[:10],
        check_in_time=prop.get("check_in_time", ""),
        check_out_time=prop.get("check_out_time", ""),
        source="serpapi",
    )


class SerpApiAccommodationProvider:
    """Fetch real-time Google Hotels data via SerpAPI."""

    @property
    def enabled(self) -> bool:
        return bool(settings.SERPAPI_API_KEY)

    async def search(self, criteria: AccommodationSearchCriteria) -> list[AccommodationOffer]:
        if not self.enabled:
            logger.warning("SERPAPI_API_KEY not set — hotel search unavailable")
            return []

        nights = max((criteria.check_out - criteria.check_in).days, 1)
        if criteria.country:
            query = f"Hotels in {criteria.city}, {criteria.country}"
        else:
            query = f"hotels in {criteria.city}"
        params: dict = {
            "engine": "google_hotels",
            "q": query,
            "check_in_date": criteria.check_in.isoformat(),
            "check_out_date": criteria.check_out.isoformat(),
            "adults": criteria.adults,
            "currency": "USD",
            "sort_by": "3",
            "hl": "en",
            "api_key": settings.SERPAPI_API_KEY,
        }
        if criteria.children > 0:
            params["children"] = criteria.children

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(_SERPAPI_URL, params=params)

            data = resp.json()
            if resp.status_code == 429 or "run out of searches" in data.get("error", ""):
                logger.warning("SerpAPI hotel quota exhausted")
                return []
            if "error" in data:
                logger.warning("SerpAPI hotel error: %s", data["error"])
                return []
            if resp.status_code != 200:
                logger.warning("SerpAPI hotels %s: %s", resp.status_code, resp.text[:300])
                return []

            properties = data.get("properties") or data.get("local_results") or []
            hotels = [h for p in properties[:20] if (h := parse_hotel_property(p, nights)) is not None]
            if hotels:
                logger.info(
                    "SerpAPI: %d live hotels in %s (%s → %s)",
                    len(hotels),
                    criteria.city,
                    criteria.check_in,
                    criteria.check_out,
                )
            return sorted(hotels, key=lambda h: h.price_per_night)[:12]

        except httpx.HTTPError as exc:
            logger.error("SerpAPI hotel HTTP error: %s", exc)
        except Exception as exc:
            logger.error("SerpAPI hotel search failed: %s", exc)

        return []

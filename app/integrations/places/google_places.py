"""Live attractions/restaurants/landmarks via Google Places API (New).

Self-serve substitute for the TripAdvisor Content API, which requires a
partner/business agreement with no public signup — this covers the same
attractions/restaurants/landmarks/reviews/ratings/photos requirement using a
key any developer can generate in Google Cloud Console.

Photo URLs are resolved server-side with `skipHttpRedirect=true`, which
returns a plain googleusercontent.com CDN link instead of a URL containing
our API key — the key is never exposed to the frontend/browser.
"""

from __future__ import annotations

import logging

import httpx

from app.core.config import settings
from app.integrations.places.base import PlaceResult, PlaceSearchCriteria

logger = logging.getLogger(__name__)

_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
_PHOTO_BASE_URL = "https://places.googleapis.com/v1"
_FIELD_MASK = (
    "places.id,places.displayName,places.rating,places.userRatingCount,"
    "places.priceLevel,places.formattedAddress,places.photos,places.googleMapsUri,"
    "places.editorialSummary"
)
_CATEGORY_QUERIES = {
    "restaurant": "best family-friendly restaurants",
    "tourist_attraction": "top tourist attractions",
    "museum": "family-friendly museums",
    "park": "parks and playgrounds",
    "landmark": "famous landmarks",
}
_PRICE_LEVELS = {
    "PRICE_LEVEL_FREE": "Free",
    "PRICE_LEVEL_INEXPENSIVE": "$",
    "PRICE_LEVEL_MODERATE": "$$",
    "PRICE_LEVEL_EXPENSIVE": "$$$",
    "PRICE_LEVEL_VERY_EXPENSIVE": "$$$$",
}


def parse_place(place: dict, category: str) -> PlaceResult | None:
    name = (place.get("displayName") or {}).get("text")
    if not name:
        return None
    return PlaceResult(
        place_id=place.get("id", ""),
        name=name,
        category=category,
        rating=place.get("rating"),
        review_count=place.get("userRatingCount"),
        price_level=_PRICE_LEVELS.get(place.get("priceLevel", "")),
        address=place.get("formattedAddress", ""),
        photo_url="",
        maps_url=place.get("googleMapsUri", ""),
        editorial_summary=(place.get("editorialSummary") or {}).get("text", ""),
    )


class GooglePlacesProvider:
    """Fetch real attractions/restaurants/landmarks from Google Places API (New)."""

    @property
    def enabled(self) -> bool:
        return bool(settings.GOOGLE_PLACES_API_KEY)

    async def _resolve_photo_url(self, client: httpx.AsyncClient, photo_name: str) -> str:
        try:
            resp = await client.get(
                f"{_PHOTO_BASE_URL}/{photo_name}/media",
                params={"maxWidthPx": 800, "skipHttpRedirect": "true"},
                headers={"X-Goog-Api-Key": settings.GOOGLE_PLACES_API_KEY},
            )
            if resp.status_code == 200:
                return resp.json().get("photoUri", "")
        except httpx.HTTPError:
            pass
        return ""

    async def search_places(self, criteria: PlaceSearchCriteria) -> list[PlaceResult]:
        if not self.enabled:
            logger.warning("Google Places disabled — set GOOGLE_PLACES_API_KEY in ..env")
            return []

        query_phrase = _CATEGORY_QUERIES.get(criteria.category, "top attractions")
        location = f"{criteria.city}, {criteria.country}" if criteria.country else criteria.city

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.post(
                    _SEARCH_URL,
                    json={
                        "textQuery": f"{query_phrase} in {location}",
                        "maxResultCount": min(criteria.max_results, 20),
                    },
                    headers={
                        "Content-Type": "application/json",
                        "X-Goog-Api-Key": settings.GOOGLE_PLACES_API_KEY,
                        "X-Goog-FieldMask": _FIELD_MASK,
                    },
                )
                if resp.status_code != 200:
                    logger.warning("Google Places %s: %s", resp.status_code, resp.text[:300])
                    return []

                places = resp.json().get("places") or []
                results: list[PlaceResult] = []
                for place in places[: criteria.max_results]:
                    parsed = parse_place(place, criteria.category)
                    if not parsed:
                        continue
                    photos = place.get("photos") or []
                    if photos and photos[0].get("name"):
                        parsed.photo_url = await self._resolve_photo_url(client, photos[0]["name"])
                    results.append(parsed)

                if results:
                    logger.info("Google Places: %d %s results for %s", len(results), criteria.category, location)
                return results

        except httpx.HTTPError as exc:
            logger.error("Google Places HTTP error: %s", exc)
        except Exception as exc:
            logger.error("Google Places search failed: %s", exc)

        return []

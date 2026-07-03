"""Live hotel offers via the Amadeus Hotel Search API (v3).

Flow: resolve the destination city to an Amadeus IATA city code, list hotels
in that city, then price a batch of them for the requested dates.
"""

from __future__ import annotations

import logging
from urllib.parse import quote_plus

import httpx

from app.core.config import settings
from app.integrations.accommodations.base import (
    AccommodationOffer,
    AccommodationSearchCriteria,
    BookingSource,
)
from app.integrations.amadeus_auth import get_amadeus_access_token, invalidate_amadeus_token

logger = logging.getLogger(__name__)

_FAMILY_KEYWORDS = {"pool", "kids", "family", "children", "playground", "babysit", "crib", "childcare"}

# In-memory cache: city name (lowercased) -> Amadeus IATA city code.
_city_code_cache: dict[str, str | None] = {}


class AmadeusAccommodationProvider:
    """Fetch real-time hotel offers from Amadeus."""

    @property
    def enabled(self) -> bool:
        return bool(settings.AMADEUS_CLIENT_ID and settings.AMADEUS_CLIENT_SECRET)

    async def _resolve_city_code(self, client: httpx.AsyncClient, token: str, city: str) -> str | None:
        key = city.lower()
        if key in _city_code_cache:
            return _city_code_cache[key]

        resp = await client.get(
            f"{settings.AMADEUS_BASE_URL}/v1/reference-data/locations",
            params={"subType": "CITY", "keyword": city, "page[limit]": 1},
            headers={"Authorization": f"Bearer {token}"},
        )
        code = None
        if resp.status_code == 200:
            results = resp.json().get("data") or []
            if results:
                code = results[0].get("iataCode")
        _city_code_cache[key] = code
        return code

    async def _list_hotel_ids(self, client: httpx.AsyncClient, token: str, city_code: str) -> list[dict]:
        resp = await client.get(
            f"{settings.AMADEUS_BASE_URL}/v1/reference-data/locations/hotels/by-city",
            params={"cityCode": city_code},
            headers={"Authorization": f"Bearer {token}"},
        )
        if resp.status_code != 200:
            logger.warning("Amadeus hotel list %s: %s", resp.status_code, resp.text[:200])
            return []
        return resp.json().get("data") or []

    def _family_friendly(self, amenities: list[str]) -> bool:
        joined = " ".join(amenities).lower()
        return any(keyword in joined for keyword in _FAMILY_KEYWORDS)

    def _parse_offer_item(self, item: dict, hotel_meta: dict, nights: int) -> AccommodationOffer | None:
        hotel = item.get("hotel") or {}
        offers = item.get("offers") or []
        if not offers:
            return None

        best = min(offers, key=lambda o: float(o.get("price", {}).get("total", "inf") or "inf"))
        price = best.get("price") or {}
        try:
            total_price = float(price["total"])
        except (KeyError, TypeError, ValueError):
            return None
        currency = price.get("currency", "EUR")
        price_per_night = round(total_price / nights, 2)

        name = hotel.get("name") or hotel_meta.get("name") or "Hotel"
        amenities = [a.replace("_", " ").title() for a in (hotel_meta.get("amenities") or [])]
        rating = hotel.get("rating")
        maps_query = f"{name} {hotel_meta.get('address', {}).get('cityName', '')}".strip()
        maps_url = f"https://www.google.com/maps/search/?api=1&query={quote_plus(maps_query)}"
        policies = best.get("policies") or {}

        return AccommodationOffer(
            name=name,
            type="Hotel",
            hotel_class=f"{int(rating)}-star" if rating else "",
            rating=float(rating) if rating else None,
            reviews_count=None,
            price_per_night=price_per_night,
            total_price=round(total_price, 2),
            currency=currency,
            family_friendly=self._family_friendly(amenities),
            image_url="",
            google_url=maps_url,
            booking_sources=[
                BookingSource(
                    name="Amadeus",
                    price_per_night=price_per_night,
                    total_price=round(total_price, 2),
                    currency=currency,
                    url=maps_url,
                )
            ],
            amenities=amenities[:10],
            check_in_time=policies.get("checkInOut", {}).get("checkIn", "") if policies else "",
            check_out_time=policies.get("checkInOut", {}).get("checkOut", "") if policies else "",
            source="amadeus",
        )

    async def search(self, criteria: AccommodationSearchCriteria) -> list[AccommodationOffer]:
        if not self.enabled:
            logger.warning("Amadeus credentials missing — set AMADEUS_CLIENT_ID and AMADEUS_CLIENT_SECRET in ..env")
            return []

        nights = max((criteria.check_out - criteria.check_in).days, 1)

        try:
            async with httpx.AsyncClient(timeout=25.0) as client:
                token = await get_amadeus_access_token(client)

                city_code = await self._resolve_city_code(client, token, criteria.city)
                if not city_code:
                    logger.warning("Amadeus: could not resolve city code for %s", criteria.city)
                    return []

                hotels = await self._list_hotel_ids(client, token, city_code)
                if not hotels:
                    return []

                hotel_ids = [h["hotelId"] for h in hotels if h.get("hotelId")][:20]
                hotel_meta_by_id = {h["hotelId"]: h for h in hotels if h.get("hotelId")}
                if not hotel_ids:
                    return []

                resp = await client.get(
                    f"{settings.AMADEUS_BASE_URL}/v3/shopping/hotel-offers",
                    params={
                        "hotelIds": ",".join(hotel_ids),
                        "checkInDate": criteria.check_in.isoformat(),
                        "checkOutDate": criteria.check_out.isoformat(),
                        "adults": max(criteria.adults, 1),
                        "currency": "EUR",
                        "bestRateOnly": "true",
                    },
                    headers={"Authorization": f"Bearer {token}"},
                )

                if resp.status_code == 401:
                    invalidate_amadeus_token()
                    logger.error("Amadeus token expired or invalid")
                    return []
                if resp.status_code != 200:
                    logger.warning("Amadeus hotel-offers %s: %s", resp.status_code, resp.text[:300])
                    return []

                offers: list[AccommodationOffer] = []
                for item in resp.json().get("data") or []:
                    hotel_id = (item.get("hotel") or {}).get("hotelId")
                    meta = hotel_meta_by_id.get(hotel_id, {})
                    parsed = self._parse_offer_item(item, meta, nights)
                    if parsed:
                        offers.append(parsed)

                if offers:
                    logger.info("Amadeus: %d live hotels in %s", len(offers), criteria.city)
                return sorted(offers, key=lambda o: o.price_per_night)[:12]

        except httpx.HTTPError as exc:
            logger.error("Amadeus hotel HTTP error: %s", exc)
        except Exception as exc:
            logger.error("Amadeus hotel search failed: %s", exc)

        return []

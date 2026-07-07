"""Live hotel offers via Amadeus Hotel List + Hotel Offers Search v3."""

from __future__ import annotations

import logging

from app.core.config import settings
from app.integrations.accommodations.base import (
    AccommodationOffer,
    AccommodationSearchCriteria,
    BookingSource,
)
from app.integrations.amadeus.client import get_amadeus_client
from app.integrations.amadeus.destinations import AmadeusDestinationService

logger = logging.getLogger(__name__)

_FAMILY_KEYWORDS = {"pool", "kids", "family", "children", "playground", "babysit", "crib"}


def _parse_hotel_offer(item: dict, nights: int) -> AccommodationOffer | None:
    try:
        hotel = item.get("hotel") or {}
        name = (hotel.get("name") or "").strip()
        if not name:
            return None

        offers = item.get("offers") or []
        if not offers:
            return None

        best = offers[0]
        price_block = best.get("price") or {}
        total = float(price_block.get("total") or price_block.get("base") or 0)
        currency = price_block.get("currency") or "EUR"
        if total <= 0:
            return None

        price_per_night = round(total / max(nights, 1), 2)
        room = (best.get("room") or {}).get("description") or {}
        room_text = room.get("text", "") if isinstance(room, dict) else str(room)

        amenities: list[str] = []
        if room_text:
            amenities.append(room_text[:120])

        family_friendly = any(k in room_text.lower() for k in _FAMILY_KEYWORDS)

        return AccommodationOffer(
            name=name,
            type="Hotel",
            hotel_class="",
            rating=None,
            reviews_count=None,
            price_per_night=price_per_night,
            total_price=round(total, 2),
            currency=currency,
            family_friendly=family_friendly,
            image_url="",
            google_url=best.get("self") or "",
            booking_sources=[
                BookingSource(
                    name="Amadeus",
                    price_per_night=price_per_night,
                    total_price=round(total, 2),
                    currency=currency,
                    url=best.get("self") or "",
                )
            ],
            amenities=amenities,
            check_in_time=best.get("checkInDate") or "",
            check_out_time=best.get("checkOutDate") or "",
            source="amadeus",
        )
    except (KeyError, TypeError, ValueError) as exc:
        logger.debug("Failed to parse Amadeus hotel offer: %s", exc)
        return None


class AmadeusAccommodationProvider:
    """Fetch hotel availability and pricing from Amadeus test/production APIs."""

    def __init__(self) -> None:
        self.client = get_amadeus_client()
        self.destinations = AmadeusDestinationService()

    @property
    def enabled(self) -> bool:
        return self.client.enabled

    async def _resolve_city_code(self, criteria: AccommodationSearchCriteria) -> str | None:
        if criteria.city and len(criteria.city) >= 3:
            cities = await self.destinations.search_cities(criteria.city, max_results=1)
            if cities:
                return cities[0].city_code
        return None

    async def search(self, criteria: AccommodationSearchCriteria) -> list[AccommodationOffer]:
        if not self.enabled:
            logger.warning(
                "Amadeus credentials missing — set AMADEUS_CLIENT_ID and AMADEUS_CLIENT_SECRET"
            )
            return []

        city_code = await self._resolve_city_code(criteria)
        if not city_code:
            logger.warning("Could not resolve city code for %s", criteria.city)
            return []

        nights = max((criteria.check_out - criteria.check_in).days, 1)

        try:
            list_data = await self.client.get_json(
                "/v1/reference-data/locations/hotels/by-city",
                params={"cityCode": city_code},
            )
            hotel_ids = [
                h.get("hotelId")
                for h in (list_data.get("data") or [])[:20]
                if h.get("hotelId")
            ]
            if not hotel_ids:
                return []

            offers_data = await self.client.get_json(
                "/v3/shopping/hotel-offers",
                params={
                    "hotelIds": ",".join(hotel_ids[:10]),
                    "adults": criteria.adults,
                    "checkInDate": criteria.check_in.isoformat(),
                    "checkOutDate": criteria.check_out.isoformat(),
                    "roomQuantity": 1,
                    "currency": "EUR",
                },
                timeout=30.0,
            )

            hotels: list[AccommodationOffer] = []
            for item in offers_data.get("data") or []:
                parsed = _parse_hotel_offer(item, nights)
                if parsed:
                    hotels.append(parsed)

            if hotels:
                logger.info(
                    "Amadeus: %d hotel offers in %s (%s → %s)",
                    len(hotels),
                    criteria.city,
                    criteria.check_in,
                    criteria.check_out,
                )
            return sorted(hotels, key=lambda h: h.price_per_night)[:12]

        except Exception as exc:
            logger.error("Amadeus hotel search failed: %s", exc)
            return []

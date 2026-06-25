"""Hotel offers loaded from PostgreSQL cache (temporary SerpAPI substitute)."""

from __future__ import annotations

import logging

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.accommodations.base import (
    AccommodationOffer,
    AccommodationSearchCriteria,
    BookingSource,
)
from app.models.offer_cache import HotelOfferCache

logger = logging.getLogger(__name__)


def _offer_from_payload(payload: dict, nights: int) -> AccommodationOffer:
    price_per_night = float(payload.get("price_per_night") or 0)
    total_price = round(price_per_night * nights, 2) if price_per_night else float(payload.get("total_price") or 0)

    booking_sources = [
        BookingSource(
            name=s.get("name", "Book"),
            price_per_night=float(s.get("price_per_night") or price_per_night),
            total_price=round(float(s.get("price_per_night") or price_per_night) * nights, 2),
            currency=s.get("currency", "USD"),
            url=s.get("url", ""),
        )
        for s in (payload.get("booking_sources") or [])
    ]

    return AccommodationOffer(
        name=payload.get("name", ""),
        type=payload.get("type", "Hotel"),
        hotel_class=payload.get("hotel_class", ""),
        rating=payload.get("rating"),
        reviews_count=payload.get("reviews_count"),
        price_per_night=round(price_per_night, 2),
        total_price=total_price,
        currency=payload.get("currency", "USD"),
        family_friendly=bool(payload.get("family_friendly", False)),
        image_url=payload.get("image_url", ""),
        google_url=payload.get("google_url", ""),
        booking_sources=booking_sources,
        amenities=list(payload.get("amenities") or [])[:10],
        check_in_time=payload.get("check_in_time", ""),
        check_out_time=payload.get("check_out_time", ""),
        source="db",
    )


class DbAccommodationProvider:
    """Serve cached hotel offers from the database."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def _find_rows(self, criteria: AccommodationSearchCriteria) -> list[HotelOfferCache]:
        city_lower = criteria.city.strip().lower()
        country_lower = criteria.country.strip().lower()

        query = select(HotelOfferCache).where(func.lower(HotelOfferCache.city) == city_lower)
        if country_lower:
            query = query.where(func.lower(HotelOfferCache.country) == country_lower)

        result = await self.session.execute(query.order_by(HotelOfferCache.id))
        rows = list(result.scalars().all())
        if rows:
            return rows

        fallback = await self.session.execute(
            select(HotelOfferCache).where(func.lower(HotelOfferCache.city) == city_lower)
        )
        return list(fallback.scalars().all())

    async def search(self, criteria: AccommodationSearchCriteria) -> list[AccommodationOffer]:
        nights = max((criteria.check_out - criteria.check_in).days, 1)
        rows = await self._find_rows(criteria)
        if not rows:
            logger.info("DB cache: no hotels for %s, %s", criteria.city, criteria.country)
            return []

        offers = [_offer_from_payload(row.payload, nights) for row in rows]
        offers = sorted(offers, key=lambda h: h.price_per_night)[:12]
        logger.info("DB cache: %d hotels in %s", len(offers), criteria.city)
        return offers

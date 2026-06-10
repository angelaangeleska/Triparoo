from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.accommodations.base import (
    AccommodationOffer,
    AccommodationProvider,
    AccommodationSearchCriteria,
)
from app.models.accommodation import Accommodation


class MockAccommodationProvider:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def search(self, criteria: AccommodationSearchCriteria) -> list[AccommodationOffer]:
        nights = max((criteria.check_out - criteria.check_in).days, 1)
        month = criteria.check_in.month
        seasonal = 1.25 if month in (6, 7, 8) else 0.9 if month in (1, 2, 11) else 1.0

        result = await self.session.execute(
            select(Accommodation).where(Accommodation.destination_id == criteria.destination_id)
        )
        accommodations = list(result.scalars().all())
        if not accommodations:
            base = 80.0 + (criteria.destination_id % 5) * 15
            price = round(base * seasonal, 2)
            return [
                AccommodationOffer(
                    accommodation_id=None,
                    name="Family Comfort Hotel",
                    type="hotel",
                    price_per_night=price,
                    total_price=round(price * nights, 2),
                    rating=4.0,
                    family_friendly=True,
                    source="mock-synthetic",
                )
            ]

        offers = []
        for acc in accommodations:
            if acc.max_guests < criteria.party_size and not acc.family_friendly:
                continue
            nightly = round(acc.price_per_night * seasonal, 2)
            offers.append(
                AccommodationOffer(
                    accommodation_id=acc.id,
                    name=acc.name,
                    type=acc.type,
                    price_per_night=nightly,
                    total_price=round(nightly * nights, 2),
                    rating=acc.rating,
                    family_friendly=acc.family_friendly,
                    source="mock-db",
                )
            )
        return sorted(offers, key=lambda o: o.total_price)

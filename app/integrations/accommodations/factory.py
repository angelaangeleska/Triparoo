from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.integrations.accommodations.db_accommodation import DbAccommodationProvider
from app.integrations.accommodations.serpapi_accommodation import SerpApiAccommodationProvider


def get_accommodation_provider(session: AsyncSession | None = None):
    if settings.should_use_db_prices():
        if session is None:
            raise ValueError("Database session required when using DB price cache")
        return DbAccommodationProvider(session)
    return SerpApiAccommodationProvider()

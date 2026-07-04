from app.core.config import settings
from app.integrations.places.base import PlaceSearchCriteria, PlacesProvider
from app.integrations.places.google_places import GooglePlacesProvider


class NullPlacesProvider:
    """No-op provider used when GOOGLE_PLACES_API_KEY is not configured."""

    async def search_places(self, criteria: PlaceSearchCriteria):
        return []


def get_places_provider() -> PlacesProvider:
    if settings.GOOGLE_PLACES_API_KEY:
        return GooglePlacesProvider()
    return NullPlacesProvider()

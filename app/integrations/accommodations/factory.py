from app.core.config import settings
from app.integrations.accommodations.serpapi_accommodation import SerpApiAccommodationProvider


def get_accommodation_provider() -> SerpApiAccommodationProvider:
    mode = settings.ACCOMMODATION_PROVIDER.lower()
    if mode in ("serpapi", "auto", "live"):
        return SerpApiAccommodationProvider()
    return SerpApiAccommodationProvider()

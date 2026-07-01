from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.integrations.flights.amadeus_flight import AmadeusFlightProvider
from app.integrations.flights.db_flight import DbFlightProvider
from app.integrations.flights.serpapi_flight import SerpApiFlightProvider


def get_flight_provider(session: AsyncSession):
    if settings.should_use_db_prices():
        return DbFlightProvider(session)

    mode = settings.FLIGHT_PROVIDER.lower()

    if mode in ("amadeus", "live"):
        return AmadeusFlightProvider(session)
    if mode == "serpapi":
        return SerpApiFlightProvider(session)

    # auto: prefer SerpAPI > Amadeus
    if settings.SERPAPI_API_KEY:
        return SerpApiFlightProvider(session)
    if settings.AMADEUS_CLIENT_ID and settings.AMADEUS_CLIENT_SECRET:
        return AmadeusFlightProvider(session)
    return DbFlightProvider(session)


def flight_provider_label() -> str:
    if settings.should_use_db_prices():
        return "db"
    mode = settings.FLIGHT_PROVIDER.lower()
    if mode in ("amadeus", "live"):
        return "amadeus"
    if mode == "serpapi":
        return "serpapi"
    if settings.SERPAPI_API_KEY:
        return "serpapi"
    if settings.AMADEUS_CLIENT_ID and settings.AMADEUS_CLIENT_SECRET:
        return "amadeus"
    return "db"

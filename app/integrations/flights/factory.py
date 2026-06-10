from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.integrations.flights.amadeus_flight import AmadeusFlightProvider
from app.integrations.flights.global_flight import GlobalFlightProvider
from app.integrations.flights.mock_flight import MockFlightProvider


def get_flight_provider(session: AsyncSession):
    mode = settings.FLIGHT_PROVIDER.lower()

    if mode == "mock":
        return MockFlightProvider(session)
    if mode == "global":
        return GlobalFlightProvider(session)
    if mode == "amadeus" or mode == "live":
        return AmadeusFlightProvider(session)

    # auto: prefer live Amadeus when credentials exist
    if settings.AMADEUS_CLIENT_ID and settings.AMADEUS_CLIENT_SECRET:
        return AmadeusFlightProvider(session)
    return GlobalFlightProvider(session)


def flight_provider_label() -> str:
    mode = settings.FLIGHT_PROVIDER.lower()
    if mode in ("amadeus", "live"):
        return "amadeus"
    if mode == "auto" and settings.AMADEUS_CLIENT_ID and settings.AMADEUS_CLIENT_SECRET:
        return "amadeus"
    if mode == "global":
        return "global-estimate"
    return mode

from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.flights.amadeus_flight import AmadeusFlightProvider


def get_flight_provider(session: AsyncSession) -> AmadeusFlightProvider:
    return AmadeusFlightProvider(session)


def flight_provider_label() -> str:
    return "amadeus"

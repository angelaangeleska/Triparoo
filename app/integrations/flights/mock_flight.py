from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.flights.base import FlightSearchCriteria, FlightOffer
from app.integrations.flights.global_flight import GlobalFlightProvider


class MockFlightProvider(GlobalFlightProvider):
    """Legacy alias — delegates to worldwide global flight provider."""

    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def search(self, criteria: FlightSearchCriteria) -> list[FlightOffer]:
        offers = await super().search(criteria)
        for offer in offers:
            if offer.source == "global-estimate":
                offer.source = "mock"
        return offers

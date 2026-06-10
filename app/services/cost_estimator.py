from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.accommodations.base import AccommodationSearchCriteria
from app.integrations.accommodations.mock_accommodation import MockAccommodationProvider
from app.integrations.flights.base import FlightOffer, FlightSearchCriteria
from app.integrations.flights.factory import get_flight_provider
from app.integrations.flights.serialize import build_flight_summary
from app.models.destination import Destination
from app.services.origin_resolver import OriginResolverService


class CostEstimatorService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.flight_provider = get_flight_provider(session)
        self.accommodation_provider = MockAccommodationProvider(session)
        self.origin_resolver = OriginResolverService(session)

    async def _best_round_trip(
        self,
        origin_iata: str,
        dest_iata: str,
        start_date: date,
        end_date: date | None,
        party_size: int,
        origin_airport_id: int | None,
        dest_airport_id: int,
    ) -> tuple[FlightOffer | None, FlightOffer | None, list[FlightOffer]]:
        round_trip = end_date and end_date > start_date
        offers = await self.flight_provider.search(
            FlightSearchCriteria(
                origin_iata=origin_iata.upper(),
                destination_iata=dest_iata.upper(),
                departure_date=start_date,
                party_size=party_size,
                return_date=end_date if round_trip else None,
                origin_airport_id=origin_airport_id,
                destination_airport_id=dest_airport_id,
            )
        )
        if not offers:
            return None, None, []

        best = offers[0]
        alternatives = offers[1:3]

        if best.return_leg and best.bundled_round_trip:
            return best, best.return_leg, alternatives

        return_offer = None
        if round_trip:
            return_offers = await self.flight_provider.search(
                FlightSearchCriteria(
                    origin_iata=dest_iata.upper(),
                    destination_iata=origin_iata.upper(),
                    departure_date=end_date,
                    party_size=party_size,
                    origin_airport_id=dest_airport_id,
                    destination_airport_id=origin_airport_id,
                )
            )
            if return_offers:
                return_offer = return_offers[0]
                return_offer.direction = "return"

        return best, return_offer, alternatives

    def _trip_flight_cost(self, outbound: FlightOffer, return_offer: FlightOffer | None) -> float:
        if outbound.bundled_round_trip and outbound.return_leg:
            return outbound.price
        return outbound.price + (return_offer.price if return_offer else 0.0)

    async def estimate_trip(
        self,
        destination: Destination,
        party_size: int,
        start_date: date | None,
        end_date: date | None,
        origin_location: str | None = None,
        origin_airport_id: int | None = None,
    ) -> dict:
        if not start_date:
            start_date = date.today() + timedelta(days=30)
        if not end_date:
            end_date = start_date + timedelta(days=5)
        nights = max((end_date - start_date).days, 1)

        flight_cost = 0.0
        flight_offer_data = None
        same_origin = False

        origin_iatas, origin_ids, origin_message = await self.origin_resolver.resolve_airports(
            origin_location, origin_airport_id
        )

        if origin_iatas and destination.city and destination.city.airports:
            dest_airport = destination.city.airports[0]
            dest_iata = dest_airport.iata_code.upper()

            if dest_iata in {i.upper() for i in origin_iatas}:
                same_origin = True
            else:
                best_out = None
                best_return = None
                best_alts: list[FlightOffer] = []
                for idx, origin_iata in enumerate(origin_iatas):
                    out, ret, alts = await self._best_round_trip(
                        origin_iata,
                        dest_iata,
                        start_date,
                        end_date,
                        party_size,
                        origin_ids[idx] if idx < len(origin_ids) else None,
                        dest_airport.id,
                    )
                    if not out:
                        continue
                    total = self._trip_flight_cost(out, ret)
                    best_total = self._trip_flight_cost(best_out, best_return) if best_out else None
                    if best_out is None or (best_total is not None and total < best_total):
                        best_out, best_return, best_alts = out, ret, alts

                if best_out:
                    flight_cost = self._trip_flight_cost(best_out, best_return)
                    flight_offer_data = build_flight_summary(best_out, party_size, best_return, best_alts)

        acc_offers = await self.accommodation_provider.search(
            AccommodationSearchCriteria(
                destination_id=destination.id,
                check_in=start_date,
                check_out=end_date,
                party_size=party_size,
            )
        )
        accommodation_cost = acc_offers[0].total_price if acc_offers else 100.0 * nights
        acc_name = acc_offers[0].name if acc_offers else "Estimated hotel"

        activity_cost = 0.0
        if destination.attractions:
            top = sorted(destination.attractions, key=lambda a: a.price)[:3]
            activity_cost = sum(a.price * party_size for a in top)
            activity_cost = min(activity_cost, 300.0 * party_size)

        total = round(flight_cost + accommodation_cost + activity_cost, 2)
        return {
            "flight": round(flight_cost, 2),
            "accommodation": round(accommodation_cost, 2),
            "activity": round(activity_cost, 2),
            "total": total,
            "nights": nights,
            "origin_message": origin_message,
            "same_origin": same_origin,
            "flight_offer": flight_offer_data,
            "accommodation_name": acc_name,
        }

"""Flight offers loaded from PostgreSQL cache (temporary SerpAPI substitute)."""

from __future__ import annotations

import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.flights.base import FlightOffer, FlightSearchCriteria
from app.models.offer_cache import FlightOfferCache

logger = logging.getLogger(__name__)


def _parse_dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)


def _leg_to_offer(
    leg: dict,
    price: float,
    criteria: FlightSearchCriteria,
    direction: str,
) -> FlightOffer:
    return FlightOffer(
        origin_iata=leg.get("origin_iata", criteria.origin_iata),
        destination_iata=leg.get("destination_iata", criteria.destination_iata),
        departure_date=_parse_dt(leg["departure_date"]),
        arrival_date=_parse_dt(leg["arrival_date"]),
        price=round(float(price), 2),
        airline=leg.get("airline", "Unknown Airline"),
        airline_code=leg.get("airline_code", "XX"),
        flight_number=leg.get("flight_number", ""),
        duration_minutes=int(leg.get("duration_minutes") or 60),
        cabin_class=leg.get("cabin_class", "Economy"),
        stops=int(leg.get("stops") or 0),
        currency=leg.get("currency", "USD"),
        seats_remaining=leg.get("seats_remaining"),
        source="db",
        direction=direction,
        origin_airport_name=leg.get("origin_airport", ""),
        destination_airport_name=leg.get("destination_airport", ""),
        origin_city=leg.get("origin_city", ""),
        destination_city=leg.get("destination_city", ""),
        baggage=leg.get("baggage", "1 personal item + cabin bag"),
        origin_airport_id=criteria.origin_airport_id,
        destination_airport_id=criteria.destination_airport_id,
    )


def _offers_from_payload(payload: dict, criteria: FlightSearchCriteria) -> list[FlightOffer]:
    outbound_leg = payload.get("outbound")
    if not outbound_leg:
        return []

    bundled = payload.get("trip_type") == "round_trip" and payload.get("return_flight")
    total = float(payload.get("total_price") or outbound_leg.get("price") or 0)
    outbound_price = total if bundled else float(outbound_leg.get("price") or total)

    outbound = _leg_to_offer(outbound_leg, outbound_price, criteria, "outbound")

    return_leg = payload.get("return_flight")
    if return_leg and criteria.return_date:
        ret_price = 0.0 if bundled else float(return_leg.get("price") or 0)
        return_offer = _leg_to_offer(return_leg, ret_price, criteria, "return")
        outbound.return_leg = return_offer
        outbound.bundled_round_trip = bundled

    offers = [outbound]
    for alt in payload.get("alternatives") or []:
        alt_offer = _leg_to_offer(alt, float(alt.get("price") or 0), criteria, "outbound")
        offers.append(alt_offer)

    return sorted(offers, key=lambda o: o.price)


class DbFlightProvider:
    """Serve cached flight offers from the database."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def _find_cache(self, criteria: FlightSearchCriteria) -> FlightOfferCache | None:
        origin = criteria.origin_iata.upper()
        dest = criteria.destination_iata.upper()

        exact = await self.session.execute(
            select(FlightOfferCache)
            .where(
                FlightOfferCache.origin_iata == origin,
                FlightOfferCache.destination_iata == dest,
                FlightOfferCache.departure_date == criteria.departure_date,
            )
            .limit(1)
        )
        row = exact.scalar_one_or_none()
        if row:
            return row

        fallback = await self.session.execute(
            select(FlightOfferCache)
            .where(
                FlightOfferCache.origin_iata == origin,
                FlightOfferCache.destination_iata == dest,
            )
            .order_by(FlightOfferCache.departure_date)
            .limit(1)
        )
        return fallback.scalar_one_or_none()

    async def _find_reverse_return(self, criteria: FlightSearchCriteria) -> FlightOfferCache | None:
        """When searching return leg separately, reuse outbound cache's return_flight."""
        origin = criteria.origin_iata.upper()
        dest = criteria.destination_iata.upper()
        result = await self.session.execute(
            select(FlightOfferCache)
            .where(
                FlightOfferCache.origin_iata == dest,
                FlightOfferCache.destination_iata == origin,
            )
            .order_by(FlightOfferCache.departure_date)
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def search(self, criteria: FlightSearchCriteria) -> list[FlightOffer]:
        if criteria.origin_iata.upper() == criteria.destination_iata.upper():
            return []

        cache = await self._find_cache(criteria)
        if cache:
            offers = _offers_from_payload(cache.payload, criteria)
            if offers:
                logger.info(
                    "DB cache: %d flight offers %s→%s on %s",
                    len(offers),
                    criteria.origin_iata,
                    criteria.destination_iata,
                    criteria.departure_date,
                )
                return offers[:10]

        reverse = await self._find_reverse_return(criteria)
        if reverse and reverse.payload.get("return_flight"):
            ret_leg = reverse.payload["return_flight"]
            if (
                ret_leg.get("origin_iata", "").upper() == criteria.origin_iata.upper()
                and ret_leg.get("destination_iata", "").upper() == criteria.destination_iata.upper()
            ):
                offer = _leg_to_offer(
                    ret_leg,
                    float(ret_leg.get("price") or reverse.payload.get("total_price") or 0),
                    criteria,
                    "return",
                )
                return [offer]

        logger.info(
            "DB cache: no flights for %s→%s on %s",
            criteria.origin_iata,
            criteria.destination_iata,
            criteria.departure_date,
        )
        return []

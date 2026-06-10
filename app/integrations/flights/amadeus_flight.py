"""Live flight offers via the Amadeus Flight Offers Search API."""

from __future__ import annotations

import logging
from datetime import datetime

import httpx

from app.core.config import settings
from app.integrations.flights.airline_names import airline_name
from app.integrations.flights.base import FlightOffer, FlightSearchCriteria
from app.services.airport_catalog import get_airport_catalog

logger = logging.getLogger(__name__)


class AmadeusFlightProvider:
    """Fetch real flight prices and schedules from Amadeus."""

    def __init__(self, session=None):
        self.session = session
        self._token: str | None = None
        self.catalog = get_airport_catalog()

    @property
    def enabled(self) -> bool:
        return bool(settings.AMADEUS_CLIENT_ID and settings.AMADEUS_CLIENT_SECRET)

    async def _get_token(self, client: httpx.AsyncClient) -> str:
        if self._token:
            return self._token
        resp = await client.post(
            f"{settings.AMADEUS_BASE_URL}/v1/security/oauth2/token",
            data={
                "grant_type": "client_credentials",
                "client_id": settings.AMADEUS_CLIENT_ID,
                "client_secret": settings.AMADEUS_CLIENT_SECRET,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        resp.raise_for_status()
        self._token = resp.json()["access_token"]
        return self._token

    @staticmethod
    def _parse_iso_datetime(value: str) -> datetime:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))

    @staticmethod
    def _parse_iso_duration(value: str) -> int | None:
        if not value or not value.startswith("PT"):
            return None
        hours = minutes = 0
        num = ""
        for ch in value[2:]:
            if ch.isdigit():
                num += ch
            elif ch == "H" and num:
                hours = int(num)
                num = ""
            elif ch == "M" and num:
                minutes = int(num)
                num = ""
        return hours * 60 + minutes if hours or minutes else None

    def _airport_meta(self, iata: str) -> tuple[str, str]:
        ap = self.catalog.get(iata)
        if ap:
            return ap.name, ap.city
        return iata, iata

    def _parse_itinerary(
        self,
        itinerary: dict,
        item: dict,
        criteria: FlightSearchCriteria,
        direction: str,
        leg_price: float,
    ) -> FlightOffer | None:
        segments = itinerary.get("segments") or []
        if not segments:
            return None

        first = segments[0]
        last = segments[-1]
        carrier = first.get("carrierCode", "XX")
        operating = first.get("operating", {}).get("carrierCode")
        name = airline_name(carrier, operating)
        dep = self._parse_iso_datetime(first["departure"]["at"])
        arr = self._parse_iso_datetime(last["arrival"]["at"])
        duration_minutes = self._parse_iso_duration(itinerary.get("duration", "")) or int(
            (arr - dep).total_seconds() / 60
        )
        origin = first["departure"]["iataCode"]
        dest = last["arrival"]["iataCode"]
        origin_name, origin_city = self._airport_meta(origin)
        dest_name, dest_city = self._airport_meta(dest)

        cabin = "Economy"
        baggage = "See airline fare rules"
        traveler_pricings = item.get("travelerPricings") or []
        if traveler_pricings:
            fare_segments = traveler_pricings[0].get("fareDetailsBySegment") or []
            if fare_segments:
                cabin = fare_segments[0].get("cabin", "ECONOMY").title().replace("_", " ")
                included = fare_segments[0].get("includedCheckedBags")
                if included and included.get("quantity") is not None:
                    qty = included["quantity"]
                    baggage = f"{qty} checked bag{'s' if qty != 1 else ''} included"

        flight_nums = ", ".join(
            f"{s.get('carrierCode', carrier)} {str(s.get('number', '')).strip()}"
            for s in segments
            if s.get("number")
        )

        return FlightOffer(
            origin_iata=origin,
            destination_iata=dest,
            departure_date=dep,
            arrival_date=arr,
            price=round(leg_price, 2),
            airline=name,
            airline_code=carrier,
            flight_number=flight_nums or f"{carrier} {first.get('number', '')}".strip(),
            duration_minutes=duration_minutes,
            cabin_class=cabin,
            stops=max(0, len(segments) - 1),
            currency=item.get("price", {}).get("currency", "EUR"),
            seats_remaining=item.get("numberOfBookableSeats"),
            source="amadeus",
            direction=direction,
            origin_airport_name=origin_name,
            destination_airport_name=dest_name,
            origin_city=origin_city,
            destination_city=dest_city,
            baggage=baggage,
            origin_airport_id=criteria.origin_airport_id,
            destination_airport_id=criteria.destination_airport_id,
        )

    def _parse_offer(self, item: dict, criteria: FlightSearchCriteria) -> FlightOffer | None:
        try:
            itineraries = item.get("itineraries") or []
            if not itineraries:
                return None

            total_price = float(item["price"]["total"])
            outbound = self._parse_itinerary(
                itineraries[0], item, criteria, "outbound", total_price
            )
            if not outbound:
                return None

            if len(itineraries) > 1:
                return_leg = self._parse_itinerary(
                    itineraries[1], item, criteria, "return", 0.0
                )
                if return_leg:
                    outbound.return_leg = return_leg
                    outbound.bundled_round_trip = True
            return outbound
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            logger.debug("Failed to parse Amadeus offer: %s", exc)
            return None

    async def search(self, criteria: FlightSearchCriteria) -> list[FlightOffer]:
        if not self.enabled:
            logger.warning("Amadeus credentials missing — set AMADEUS_CLIENT_ID and AMADEUS_CLIENT_SECRET in .env")
            return []

        origin = criteria.origin_iata.upper()
        dest = criteria.destination_iata.upper()
        if origin == dest:
            return []

        try:
            async with httpx.AsyncClient(timeout=25.0) as client:
                token = await self._get_token(client)
                params: dict = {
                    "originLocationCode": origin,
                    "destinationLocationCode": dest,
                    "departureDate": criteria.departure_date.isoformat(),
                    "adults": criteria.party_size,
                    "max": 8,
                    "currencyCode": "EUR",
                    "nonStop": "false",
                }
                if criteria.return_date:
                    params["returnDate"] = criteria.return_date.isoformat()

                resp = await client.get(
                    f"{settings.AMADEUS_BASE_URL}/v2/shopping/flight-offers",
                    params=params,
                    headers={"Authorization": f"Bearer {token}"},
                )

                if resp.status_code == 401:
                    self._token = None
                    logger.error("Amadeus token expired or invalid")
                elif resp.status_code != 200:
                    logger.warning("Amadeus API error %s: %s", resp.status_code, resp.text[:200])

                if resp.status_code == 200:
                    data = resp.json()
                    offers: list[FlightOffer] = []
                    for item in data.get("data", [])[:8]:
                        parsed = self._parse_offer(item, criteria)
                        if parsed:
                            offers.append(parsed)
                    if offers:
                        logger.info(
                            "Amadeus: %d live offers %s→%s on %s",
                            len(offers),
                            origin,
                            dest,
                            criteria.departure_date,
                        )
                        return sorted(offers, key=lambda o: o.price)
        except httpx.HTTPError as exc:
            logger.error("Amadeus HTTP error: %s", exc)
        except Exception as exc:
            logger.error("Amadeus search failed: %s", exc)

        return []

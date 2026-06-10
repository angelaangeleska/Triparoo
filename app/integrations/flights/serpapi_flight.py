"""Real-time flight search via SerpAPI Google Flights engine."""

from __future__ import annotations

import logging
from datetime import datetime

import httpx

from app.core.config import settings
from app.integrations.flights.base import FlightOffer, FlightSearchCriteria
from app.services.airport_catalog import get_airport_catalog

logger = logging.getLogger(__name__)

_SERPAPI_URL = "https://serpapi.com/search"


class SerpApiFlightProvider:
    """Fetch real-time Google Flights data via SerpAPI."""

    def __init__(self, session=None):
        self.session = session
        self.catalog = get_airport_catalog()

    @property
    def enabled(self) -> bool:
        return bool(settings.SERPAPI_API_KEY)

    def _airport_meta(self, iata: str) -> tuple[str, str]:
        ap = self.catalog.get(iata)
        if ap:
            return ap.name, ap.city
        return iata, iata

    def _parse_flight_group(
        self,
        group: dict,
        criteria: FlightSearchCriteria,
        direction: str,
    ) -> FlightOffer | None:
        """Parse one flight option (best_flights or other_flights entry)."""
        try:
            legs: list[dict] = group.get("flights", [])
            if not legs:
                return None

            first = legs[0]
            last = legs[-1]

            # Departure / arrival datetimes
            dep_str = first.get("departure_airport", {}).get("time", "")
            arr_str = last.get("arrival_airport", {}).get("time", "")
            dep_dt = _parse_google_datetime(dep_str)
            arr_dt = _parse_google_datetime(arr_str)
            if dep_dt is None or arr_dt is None:
                return None

            origin_iata = first.get("departure_airport", {}).get("id", criteria.origin_iata)
            dest_iata = last.get("arrival_airport", {}).get("id", criteria.destination_iata)
            origin_name, origin_city = self._airport_meta(origin_iata)
            dest_name, dest_city = self._airport_meta(dest_iata)

            airline = first.get("airline", "Unknown Airline")
            airline_code = first.get("airline_logo", "").split("/")[-1].split(".")[0].upper() or "XX"
            flight_number = first.get("flight_number", "")
            duration_minutes: int = group.get("total_duration") or int(
                (arr_dt - dep_dt).total_seconds() / 60
            )
            stops = max(0, len(legs) - 1)

            # Price — top-level price is per-person total for this itinerary group
            price_raw = group.get("price")
            total_price = float(price_raw) if price_raw else 0.0
            # Price from SerpAPI is already per-person for the full trip
            per_person = total_price / max(criteria.party_size, 1)

            cabin_class = _map_travel_class(first.get("travel_class", ""))
            extensions: list[str] = group.get("extensions", []) or []
            baggage = _extract_baggage(extensions)

            return FlightOffer(
                origin_iata=origin_iata,
                destination_iata=dest_iata,
                departure_date=dep_dt,
                arrival_date=arr_dt,
                price=round(per_person, 2),
                airline=airline,
                airline_code=airline_code[:2] if len(airline_code) >= 2 else airline_code,
                flight_number=flight_number,
                duration_minutes=duration_minutes,
                cabin_class=cabin_class,
                stops=stops,
                currency="USD",
                seats_remaining=None,
                source="serpapi",
                direction=direction,
                origin_airport_name=origin_name,
                destination_airport_name=dest_name,
                origin_city=origin_city,
                destination_city=dest_city,
                baggage=baggage,
                origin_airport_id=criteria.origin_airport_id,
                destination_airport_id=criteria.destination_airport_id,
            )
        except (KeyError, TypeError, ValueError) as exc:
            logger.debug("Failed to parse SerpAPI flight group: %s", exc)
            return None

    async def search(self, criteria: FlightSearchCriteria) -> list[FlightOffer]:
        if not self.enabled:
            logger.warning("SERPAPI_API_KEY not set — falling back to estimates")
            return []

        origin = criteria.origin_iata.upper()
        dest = criteria.destination_iata.upper()
        if origin == dest:
            return []

        params: dict = {
            "engine": "google_flights",
            "departure_id": origin,
            "arrival_id": dest,
            "outbound_date": criteria.departure_date.isoformat(),
            "adults": criteria.party_size,
            "currency": "USD",
            "hl": "en",
            "api_key": settings.SERPAPI_API_KEY,
        }
        if criteria.return_date:
            params["return_date"] = criteria.return_date.isoformat()
            params["type"] = "1"  # round-trip
        else:
            params["type"] = "2"  # one-way

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(_SERPAPI_URL, params=params)

                if resp.status_code != 200:
                    logger.warning("SerpAPI error %s: %s", resp.status_code, resp.text[:300])
                    return []

                data = resp.json()

                if "error" in data:
                    logger.warning("SerpAPI returned error: %s", data["error"])
                    return []

                offers: list[FlightOffer] = []

                # Parse best_flights first, then other_flights
                for group in (data.get("best_flights") or []) + (data.get("other_flights") or []):
                    offer = self._parse_flight_group(group, criteria, "outbound")
                    if offer:
                        # Attach return leg when SerpAPI bundles it
                        return_flights = group.get("return_flights") or []
                        if return_flights:
                            return_offer = self._parse_flight_group(
                                return_flights[0], criteria, "return"
                            )
                            if return_offer:
                                offer.return_leg = return_offer
                                offer.bundled_round_trip = True
                        offers.append(offer)

                if offers:
                    logger.info(
                        "SerpAPI: %d live offers %s→%s on %s",
                        len(offers),
                        origin,
                        dest,
                        criteria.departure_date,
                    )
                    return sorted(offers, key=lambda o: o.price)[:10]

                logger.info("SerpAPI returned no flights for %s→%s", origin, dest)
        except httpx.HTTPError as exc:
            logger.error("SerpAPI HTTP error: %s", exc)
        except Exception as exc:
            logger.error("SerpAPI search failed: %s", exc)

        return []


# ── helpers ──────────────────────────────────────────────────────────────────

def _parse_google_datetime(value: str) -> datetime | None:
    """Parse Google Flights datetime strings like '2024-06-15 08:30'."""
    if not value:
        return None
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M", "%Y-%m-%d %I:%M %p"):
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            continue
    return None


def _map_travel_class(raw: str) -> str:
    mapping = {
        "economy": "Economy",
        "premium economy": "Premium Economy",
        "business": "Business",
        "first": "First",
    }
    return mapping.get(raw.lower(), "Economy") if raw else "Economy"


def _extract_baggage(extensions: list[str]) -> str:
    for ext in extensions:
        lower = ext.lower()
        if "bag" in lower or "luggage" in lower or "carry" in lower:
            return ext
    return "See airline fare rules"

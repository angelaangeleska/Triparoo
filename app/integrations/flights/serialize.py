from app.integrations.flights.base import FlightOffer
from app.integrations.flights.details import format_duration


def offer_to_leg(offer: FlightOffer, party_size: int) -> dict:
    leg_price = offer.price
    if offer.bundled_round_trip and offer.direction == "outbound":
        leg_price = offer.price
    elif offer.direction == "return" and offer.price == 0 and not offer.bundled_round_trip:
        leg_price = 0.0

    return {
        "airline": offer.airline,
        "airline_code": offer.airline_code,
        "flight_number": offer.flight_number,
        "origin_iata": offer.origin_iata,
        "origin_airport": offer.origin_airport_name,
        "origin_city": offer.origin_city,
        "destination_iata": offer.destination_iata,
        "destination_airport": offer.destination_airport_name,
        "destination_city": offer.destination_city,
        "departure_date": offer.departure_date.isoformat(),
        "arrival_date": offer.arrival_date.isoformat(),
        "duration_minutes": offer.duration_minutes,
        "duration": format_duration(offer.duration_minutes),
        "cabin_class": offer.cabin_class,
        "stops": offer.stops,
        "stops_label": "Direct" if offer.stops == 0 else f"{offer.stops} stop{'s' if offer.stops > 1 else ''}",
        "price": round(leg_price, 2),
        "price_per_person": round(leg_price / party_size, 2) if leg_price else 0.0,
        "currency": offer.currency,
        "seats_remaining": offer.seats_remaining or 0,
        "baggage": offer.baggage,
        "direction": offer.direction,
        "source": offer.source,
        "fare_note": (
            "Included in round-trip total"
            if offer.direction == "return" and offer.price == 0 and offer.source == "amadeus"
            else ""
        ),
    }


def build_flight_summary(
    outbound: FlightOffer,
    party_size: int,
    return_offer: FlightOffer | None = None,
    alternatives: list[FlightOffer] | None = None,
) -> dict:
    if outbound.return_leg and outbound.bundled_round_trip:
        return_offer = outbound.return_leg
        total = outbound.price
    elif return_offer:
        total = outbound.price + return_offer.price
    else:
        total = outbound.price

    return {
        "currency": outbound.currency,
        "total_price": round(total, 2),
        "total_price_per_person": round(total / party_size, 2),
        "party_size": party_size,
        "trip_type": "round_trip" if return_offer else "one_way",
        "outbound": offer_to_leg(outbound, party_size),
        "return_flight": offer_to_leg(return_offer, party_size) if return_offer else None,
        "alternatives": [offer_to_leg(o, party_size) for o in (alternatives or [])],
        "source": outbound.source,
    }

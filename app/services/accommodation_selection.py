from app.integrations.accommodations.base import AccommodationOffer
from app.integrations.accommodations.serialize import accommodation_to_dict
from app.schemas.trip_planner import AccommodationSummary, BookingSourceSummary


def offer_to_summary(offer: AccommodationOffer) -> AccommodationSummary:
    data = accommodation_to_dict(offer)
    sources = [BookingSourceSummary(**s) for s in data.get("booking_sources") or []]
    return AccommodationSummary(
        name=data.get("name", ""),
        type=data.get("type", ""),
        hotel_class=data.get("hotel_class", ""),
        rating=data.get("rating"),
        reviews_count=data.get("reviews_count"),
        price_per_night=data.get("price_per_night", 0.0),
        total_price=data.get("total_price", 0.0),
        currency=data.get("currency", "USD"),
        family_friendly=data.get("family_friendly", False),
        image_url=data.get("image_url", ""),
        google_url=data.get("google_url", ""),
        booking_sources=sources,
        amenities=data.get("amenities") or [],
        check_in_time=data.get("check_in_time", ""),
        check_out_time=data.get("check_out_time", ""),
        source=data.get("source", "serpapi"),
    )


def summary_total(acc: AccommodationSummary | None) -> float:
    return acc.total_price if acc else 0.0


def same_accommodation(a: AccommodationSummary | None, b: AccommodationSummary | None) -> bool:
    if not a or not b:
        return False
    return a.name.strip().lower() == b.name.strip().lower() and abs(a.total_price - b.total_price) < 0.01

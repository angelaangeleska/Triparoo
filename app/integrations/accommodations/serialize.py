from app.integrations.accommodations.base import AccommodationOffer


def accommodation_to_dict(offer: AccommodationOffer) -> dict:
    return {
        "name": offer.name,
        "type": offer.type,
        "hotel_class": offer.hotel_class,
        "rating": offer.rating,
        "reviews_count": offer.reviews_count,
        "price_per_night": offer.price_per_night,
        "total_price": offer.total_price,
        "currency": offer.currency,
        "family_friendly": offer.family_friendly,
        "image_url": offer.image_url,
        "google_url": offer.google_url,
        "booking_sources": [
            {
                "name": s.name,
                "price_per_night": s.price_per_night,
                "total_price": s.total_price,
                "currency": s.currency,
                "url": s.url,
            }
            for s in offer.booking_sources
        ],
        "amenities": offer.amenities,
        "check_in_time": offer.check_in_time,
        "check_out_time": offer.check_out_time,
        "source": offer.source,
    }

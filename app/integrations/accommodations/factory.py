from app.integrations.accommodations.amadeus_accommodation import AmadeusAccommodationProvider


def get_accommodation_provider() -> AmadeusAccommodationProvider:
    return AmadeusAccommodationProvider()

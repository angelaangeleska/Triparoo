from app.integrations.accommodations.amadeus_accommodation import AmadeusAccommodationProvider

SAMPLE_HOTEL_META = {
    "hotelId": "MCLONGHM",
    "name": "Family Suites Hotel",
    "address": {"cityName": "London"},
    "amenities": ["SWIMMING_POOL", "WIFI", "PARKING"],
}

SAMPLE_OFFER_ITEM = {
    "hotel": {"hotelId": "MCLONGHM", "name": "Family Suites Hotel", "rating": "4"},
    "offers": [
        {
            "price": {"total": "445.00", "currency": "EUR"},
            "policies": {"checkInOut": {"checkIn": "15:00", "checkOut": "11:00"}},
        }
    ],
}


def test_parse_offer_item_basic():
    provider = AmadeusAccommodationProvider()
    offer = provider._parse_offer_item(SAMPLE_OFFER_ITEM, SAMPLE_HOTEL_META, nights=5)
    assert offer is not None
    assert offer.name == "Family Suites Hotel"
    assert offer.total_price == 445.0
    assert offer.price_per_night == 89.0
    assert offer.currency == "EUR"
    assert offer.family_friendly is True
    assert offer.source == "amadeus"
    assert offer.check_in_time == "15:00"
    assert len(offer.booking_sources) == 1


def test_parse_offer_item_no_offers_returns_none():
    provider = AmadeusAccommodationProvider()
    assert provider._parse_offer_item({"hotel": {}, "offers": []}, {}, nights=3) is None


def test_family_friendly_detection():
    provider = AmadeusAccommodationProvider()
    assert provider._family_friendly(["Swimming Pool", "Wifi"]) is True
    assert provider._family_friendly(["Business Center", "Wifi"]) is False

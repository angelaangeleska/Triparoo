from app.integrations.accommodations.serpapi_accommodation import _extract_image_url, parse_hotel_property


def test_parse_hotel_property_basic():
    prop = {
        "name": "Family Hotel Prague",
        "type": "Hotel",
        "hotel_class": "4-star hotel",
        "overall_rating": 4.5,
        "reviews": 1200,
        "rate_per_night": {"extracted_lowest": 89.0},
        "total_rate": {"extracted_lowest": 445.0},
        "amenities": ["Free Wi-Fi", "Family rooms", "Pool"],
        "link": "https://google.com/hotel/example",
        "images": [{"thumbnail": "https://example.com/img.jpg"}],
        "prices": [
            {
                "source": "Booking.com",
                "link": "https://booking.com/hotel",
                "extracted_rate_per_night": 89.0,
                "extracted_total_rate": 445.0,
            }
        ],
    }
    offer = parse_hotel_property(prop, nights=5)
    assert offer is not None
    assert offer.name == "Family Hotel Prague"
    assert offer.price_per_night == 89.0
    assert offer.total_price == 445.0
    assert offer.family_friendly is True
    assert offer.source == "serpapi"
    assert len(offer.booking_sources) == 1


def test_extract_image_url_prefers_original():
    url = _extract_image_url(
        {
            "images": [
                {"thumbnail": "https://example.com/thumb.jpg", "original": "https://example.com/full.jpg"}
            ]
        }
    )
    assert url == "https://example.com/full.jpg"


def test_extract_image_url_top_level_thumbnail():
    url = _extract_image_url({"thumbnail": "https://example.com/top.jpg"})
    assert url == "https://example.com/top.jpg"


def test_parse_hotel_property_skips_zero_price():
    assert parse_hotel_property({"name": "No Price Hotel"}, nights=3) is None

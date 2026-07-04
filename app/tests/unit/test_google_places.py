from app.integrations.places.google_places import parse_place


def test_parse_place_basic():
    place = {
        "id": "ChIJ123",
        "displayName": {"text": "Le Petit Bistro"},
        "rating": 4.6,
        "userRatingCount": 812,
        "priceLevel": "PRICE_LEVEL_MODERATE",
        "formattedAddress": "12 Rue de Paris, Paris, France",
        "googleMapsUri": "https://maps.google.com/?cid=123",
        "editorialSummary": {"text": "Cozy neighborhood bistro"},
    }
    result = parse_place(place, category="restaurant")
    assert result is not None
    assert result.name == "Le Petit Bistro"
    assert result.category == "restaurant"
    assert result.rating == 4.6
    assert result.review_count == 812
    assert result.price_level == "$$"
    assert result.editorial_summary == "Cozy neighborhood bistro"
    assert result.photo_url == ""


def test_parse_place_missing_name_returns_none():
    assert parse_place({"id": "x"}, category="restaurant") is None


def test_parse_place_unknown_price_level_is_none():
    place = {"id": "y", "displayName": {"text": "Mystery Cafe"}}
    result = parse_place(place, category="restaurant")
    assert result is not None
    assert result.price_level is None

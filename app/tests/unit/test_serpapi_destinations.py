from app.integrations.destinations.serpapi_travel_explore import _parse_destination


def test_parse_serpapi_destination():
    item = {
        "name": "Paris",
        "country": "France",
        "thumbnail": "https://example.com/paris.jpg",
        "flight_price": 89,
        "hotel_price": 120,
        "start_date": "2026-08-01",
        "end_date": "2026-08-08",
        "airline": "Air France",
        "destination_airport": {"code": "CDG"},
        "gps_coordinates": {"latitude": 48.8566, "longitude": 2.3522},
    }
    dest = _parse_destination(item)
    assert dest is not None
    assert dest.city == "Paris"
    assert dest.country == "France"
    assert dest.flight_price == 89.0
    assert dest.hotel_price == 120.0
    assert dest.destination_airport_code == "CDG"
    assert dest.thumbnail == "https://example.com/paris.jpg"
    assert dest.id > 0


def test_parse_serpapi_destination_skips_empty_name():
    assert _parse_destination({"country": "France"}) is None

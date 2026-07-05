from app.services.tour_service import (
    _category_from_tags,
    _description_from_tags,
    _parse_osm_element,
)


def test_category_from_tags_prefers_tourism():
    assert _category_from_tags({"tourism": "museum", "leisure": "park"}) == "museum"


def test_category_from_tags_historic():
    assert _category_from_tags({"historic": "castle"}) == "castle"


def test_parse_osm_node():
    element = {
        "type": "node",
        "id": 1,
        "lat": 48.86,
        "lon": 2.35,
        "tags": {
            "name": "City Museum",
            "tourism": "museum",
            "description": "Interactive exhibits for all ages.",
        },
    }
    parsed = _parse_osm_element(element)
    assert parsed is not None
    assert parsed["name"] == "City Museum"
    assert parsed["category"] == "museum"
    assert parsed["latitude"] == 48.86
    assert parsed["longitude"] == 2.35
    assert "Interactive" in parsed["description"]


def test_parse_osm_way_uses_center():
    element = {
        "type": "way",
        "id": 2,
        "center": {"lat": 50.1, "lon": 14.4},
        "tags": {"name:en": "Central Park", "leisure": "park"},
    }
    parsed = _parse_osm_element(element)
    assert parsed is not None
    assert parsed["name"] == "Central Park"
    assert parsed["category"] == "park"


def test_parse_osm_element_skips_missing_name():
    assert _parse_osm_element({"lat": 1, "lon": 2, "tags": {"tourism": "museum"}}) is None


def test_description_from_opening_hours():
    desc = _description_from_tags({"opening_hours": "Mo-Fr 09:00-17:00"})
    assert "Opening hours" in desc

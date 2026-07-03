from app.services.ai_trip_guide_service import AITripGuideService, _valid_item


def test_valid_item_requires_title():
    assert _valid_item({"title": "Local market", "description": "..."}) is True
    assert _valid_item({"description": "no title here"}) is False
    assert _valid_item("not a dict") is False


def test_parse_extracts_json_object():
    content = (
        '```json\n'
        '{"attractions": [{"title": "Old Town", "description": "Historic center", '
        '"why_recommended": "Walkable with kids"}], "restaurants": [], "hidden_gems": [], '
        '"local_tips": [], "transportation_tips": []}\n'
        '```'
    )
    data = AITripGuideService._parse(content)
    assert data["attractions"][0]["title"] == "Old Town"


def test_parse_invalid_json_returns_empty_dict():
    assert AITripGuideService._parse("not json") == {}


def test_parse_non_object_json_returns_empty_dict():
    assert AITripGuideService._parse("[1, 2, 3]") == {}

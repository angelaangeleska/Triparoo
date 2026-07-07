from app.integrations.accommodations.filters import (
    encode_amenities,
    encode_property_types,
    normalize_filter_keys,
    AMENITY_IDS,
    PROPERTY_TYPE_IDS,
)


def test_encode_property_types():
    assert encode_property_types(["resort", "boutique"]) == "17,13"
    assert encode_property_types(["unknown"]) == ""


def test_encode_amenities():
    assert encode_amenities(["pool", "free_parking", "wifi"]) == "6,1,35"


def test_normalize_filter_keys():
    assert normalize_filter_keys(["Pool", "free-parking"], AMENITY_IDS) == ["pool", "free_parking"]
    assert normalize_filter_keys(["resort"], PROPERTY_TYPE_IDS) == ["resort"]

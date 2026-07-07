"""User-facing accommodation filters mapped to SerpAPI Google Hotels parameters."""

from __future__ import annotations

from dataclasses import dataclass

# SerpAPI property_types IDs (hotels)
PROPERTY_TYPE_IDS: dict[str, int] = {
    "beach": 12,
    "boutique": 13,
    "hostel": 14,
    "inn": 15,
    "motel": 16,
    "resort": 17,
    "spa": 18,
    "bed_and_breakfast": 19,
    "apartment_hotel": 21,
}

# SerpAPI amenities IDs
AMENITY_IDS: dict[str, int] = {
    "free_parking": 1,
    "parking": 3,
    "indoor_pool": 4,
    "outdoor_pool": 5,
    "pool": 6,
    "fitness": 7,
    "restaurant": 8,
    "free_breakfast": 9,
    "spa": 10,
    "beach_access": 11,
    "child_friendly": 12,
    "bar": 15,
    "pet_friendly": 19,
    "room_service": 22,
    "wifi": 35,
    "air_conditioning": 40,
    "all_inclusive": 52,
    "wheelchair": 53,
    "ev_charger": 61,
}

PROPERTY_TYPE_LABELS: dict[str, str] = {
    "beach": "Beach hotels",
    "boutique": "Boutique hotels",
    "hostel": "Hostels",
    "inn": "Inns",
    "motel": "Motels",
    "resort": "Resorts",
    "spa": "Spa hotels",
    "bed_and_breakfast": "Bed & breakfast",
    "apartment_hotel": "Apartment hotels",
}

AMENITY_LABELS: dict[str, str] = {
    "free_parking": "Free parking",
    "parking": "Parking",
    "indoor_pool": "Indoor pool",
    "outdoor_pool": "Outdoor pool",
    "pool": "Pool",
    "fitness": "Fitness center",
    "restaurant": "Restaurant",
    "free_breakfast": "Free breakfast",
    "spa": "Spa",
    "beach_access": "Beach access",
    "child_friendly": "Child-friendly",
    "bar": "Bar",
    "pet_friendly": "Pet-friendly",
    "room_service": "Room service",
    "wifi": "Free Wi-Fi",
    "air_conditioning": "Air conditioning",
    "all_inclusive": "All-inclusive",
    "wheelchair": "Wheelchair accessible",
    "ev_charger": "EV charger",
}

STAY_KIND_LABELS: dict[str, str] = {
    "hotel": "Hotels",
    "vacation_rental": "Apartments & vacation rentals",
}


@dataclass
class FilterOption:
    id: str
    label: str


def accommodation_filter_options() -> dict:
    return {
        "stay_kinds": [FilterOption(k, v).__dict__ for k, v in STAY_KIND_LABELS.items()],
        "property_types": [FilterOption(k, v).__dict__ for k, v in PROPERTY_TYPE_LABELS.items()],
        "amenities": [FilterOption(k, v).__dict__ for k, v in AMENITY_LABELS.items()],
        "hotel_classes": [
            {"id": 2, "label": "2-star"},
            {"id": 3, "label": "3-star"},
            {"id": 4, "label": "4-star"},
            {"id": 5, "label": "5-star"},
        ],
        "min_ratings": [
            {"id": 7, "label": "3.5+"},
            {"id": 8, "label": "4.0+"},
            {"id": 9, "label": "4.5+"},
        ],
    }


def encode_property_types(keys: list[str]) -> str:
    ids = [str(PROPERTY_TYPE_IDS[k]) for k in keys if k in PROPERTY_TYPE_IDS]
    return ",".join(ids)


def encode_amenities(keys: list[str]) -> str:
    ids = [str(AMENITY_IDS[k]) for k in keys if k in AMENITY_IDS]
    return ",".join(ids)


def normalize_filter_keys(raw: list[str] | None, allowed: dict[str, int]) -> list[str]:
    if not raw:
        return []
    out: list[str] = []
    for item in raw:
        key = item.strip().lower().replace("-", "_").replace(" ", "_")
        if key in allowed and key not in out:
            out.append(key)
    return out

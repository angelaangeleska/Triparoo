from app.models.attraction import Attraction

# Maps UI interest keys to attraction tags and categories.
_INTEREST_ALIASES: dict[str, set[str]] = {
    "disney": {"disney"},
    "science": {"science", "marine"},
    "museum": {"museum"},
    "art": {"art"},
    "outdoor": {"outdoor", "park"},
    "beach": {"beach"},
    "history": {"history", "landmark", "palace"},
    "animals": {"animals", "marine", "zoo"},
    "theme_park": {"theme_park"},
}

_CATEGORY_INTERESTS: dict[str, set[str]] = {
    "museum": {"museum", "science", "art"},
    "theme_park": {"theme_park", "disney"},
    "park": {"outdoor", "animals"},
    "landmark": {"history", "outdoor"},
}


def _normalized_tags(att: Attraction) -> set[str]:
    return {t.lower() for t in (att.tags or [])}


def attraction_matches_interest(att: Attraction, interest: str) -> bool:
    """Return True when an attraction fits a selected child interest."""
    key = interest.lower().strip()
    if not key:
        return False

    tags = _normalized_tags(att)
    category = att.category.lower()
    name = att.name.lower()
    description = (att.description or "").lower()
    haystack = f"{name} {description}"

    aliases = _INTEREST_ALIASES.get(key, {key})
    if tags & aliases:
        return True

    category_hits = _CATEGORY_INTERESTS.get(category, set())
    if key in category_hits:
        return True

    if key == "museum" and category == "museum":
        return True
    if key == "theme_park" and category == "theme_park":
        return True
    if key == "outdoor" and category == "park":
        return True
    if key == "history" and category == "landmark":
        return True
    if key == "animals" and ("zoo" in haystack or "aquarium" in haystack):
        return True
    if key == "disney" and "disney" in haystack:
        return True
    if key == "science" and ("science" in haystack or "technical" in haystack):
        return True
    if key == "art" and ("art" in haystack or "gallery" in haystack):
        return True
    if key == "beach" and ("beach" in haystack or category == "beach"):
        return True

    return False


def attraction_matches_interests(att: Attraction, interests: list[str]) -> bool:
    """When interests are selected, require at least one match."""
    selected = [i.strip() for i in interests if i and i.strip()]
    if not selected:
        return True
    return any(attraction_matches_interest(att, interest) for interest in selected)

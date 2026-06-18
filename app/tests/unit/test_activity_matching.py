from types import SimpleNamespace

from app.services.activity_matching import attraction_matches_interest, attraction_matches_interests


def _att(name, category, tags, min_age=0, max_age=99, family_friendly=True):
    return SimpleNamespace(
        name=name,
        category=category,
        tags=tags,
        min_age=min_age,
        max_age=max_age,
        family_friendly=family_friendly,
        description="",
    )


def test_outdoor_matches_park_tags():
    hill = _att("Petřín Hill", "park", ["park", "outdoor"])
    museum = _att("National Technical Museum", "museum", ["science", "museum"])
    assert attraction_matches_interest(hill, "outdoor")
    assert not attraction_matches_interest(museum, "outdoor")


def test_museum_interest_matches_category():
    museum = _att("National Technical Museum", "museum", ["science", "museum"])
    park = _att("Petřín Hill", "park", ["park", "outdoor"])
    assert attraction_matches_interest(museum, "museum")
    assert not attraction_matches_interest(park, "museum")


def test_filter_requires_any_selected_interest():
    hill = _att("Petřín Hill", "park", ["park", "outdoor"])
    museum = _att("Lego Exhibition", "museum", ["museum"])
    castle = _att("Prague Castle", "landmark", ["history", "landmark"])
    assert attraction_matches_interests(hill, ["outdoor"])
    assert not attraction_matches_interests(museum, ["outdoor"])
    assert not attraction_matches_interests(castle, ["outdoor"])


def test_beach_does_not_match_park_or_museum():
    park = _att("Petřín Hill", "park", ["park", "outdoor"])
    museum = _att("Techmania Science Centre", "museum", ["science", "museum"])
    beach = _att("Barceloneta Beach", "park", ["beach", "outdoor"])
    assert not attraction_matches_interest(park, "beach")
    assert not attraction_matches_interest(museum, "beach")
    assert attraction_matches_interest(beach, "beach")


def test_empty_interests_matches_all():
    museum = _att("National Technical Museum", "museum", ["science", "museum"])
    assert attraction_matches_interests(museum, [])

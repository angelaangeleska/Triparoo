from app.models.attraction import Attraction
from app.recommendation.base import MemberContext, RecommendationContext
from app.recommendation.rule_engine import RuleBasedScorer


def _attr(name: str, fit_score_tags: list[str] | None = None) -> Attraction:
    att = Attraction(
        id=1,
        destination_id=1,
        name=name,
        category="museum",
        description="",
        min_age=0,
        max_age=99,
        price=10.0,
        family_friendly=True,
        tags=fit_score_tags or [],
    )
    return att


def test_pick_attractions_rotates_on_regenerate():
    scorer = RuleBasedScorer()
    children = [MemberContext(age=10, interests=["museums"])]
    attractions = [_attr(f"Place {i}") for i in range(6)]

    first = scorer._pick_attractions(children, attractions, regenerate_count=0)
    second = scorer._pick_attractions(children, attractions, regenerate_count=1)

    assert first != second
    assert len(first) == 5
    assert len(second) == 5

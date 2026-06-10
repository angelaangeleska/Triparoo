from types import SimpleNamespace

import pytest

from app.recommendation.base import MemberContext, RecommendationContext
from app.recommendation.rule_engine import RuleBasedScorer


def _make_destination(city_name: str = "Paris", family_score: float = 92.0):
    return SimpleNamespace(
        id=1,
        city_id=1,
        family_friendliness_score=family_score,
        popularity_score=90.0,
        city=SimpleNamespace(name=city_name, country=SimpleNamespace(name="France")),
        seasons=[
            SimpleNamespace(
                season="summer",
                month_start=6,
                month_end=8,
                avg_temp_c=24.0,
                weather_score=0.9,
                price_multiplier=1.3,
            )
        ],
        attractions=[
            SimpleNamespace(
                id=1,
                name="Disneyland Paris",
                category="theme_park",
                min_age=6,
                max_age=14,
                price=56.0,
                family_friendly=True,
                tags=["theme_park", "disney"],
            ),
            SimpleNamespace(
                id=2,
                name="Louvre Museum",
                category="museum",
                min_age=8,
                max_age=99,
                price=22.0,
                family_friendly=True,
                tags=["museum", "art"],
            ),
        ],
        accommodations=[],
    )


def test_rule_scorer_child_age_boost():
    scorer = RuleBasedScorer()
    dest = _make_destination()
    context = RecommendationContext(
        members=[
            MemberContext(age=35),
            MemberContext(age=33),
            MemberContext(age=11, gender="female", interests=["disney"]),
        ],
        budget=1500.0,
        preferred_month=8,
    )
    result = scorer.score_destination(dest, context, estimated_cost=1200.0, attractions=dest.attractions)
    assert result.total > 50
    assert result.breakdown["child_age"] > 0
    assert any(a.name == "Disneyland Paris" for a in result.suggested_attractions)


def test_rule_scorer_budget_penalty():
    scorer = RuleBasedScorer()
    dest = _make_destination()
    context = RecommendationContext(
        members=[MemberContext(age=30), MemberContext(age=10)],
        budget=500.0,
        preferred_month=8,
    )
    affordable = scorer.score_destination(dest, context, 450.0, dest.attractions)
    expensive = scorer.score_destination(dest, context, 900.0, dest.attractions)
    assert affordable.breakdown["budget"] > expensive.breakdown["budget"]


@pytest.mark.asyncio
async def test_mock_llm_provider():
    from app.recommendation.base import ScoredDestination
    from app.recommendation.mock_llm import MockLLMProvider

    provider = MockLLMProvider()
    context = RecommendationContext(
        members=[MemberContext(age=11)],
        budget=1500.0,
        preferred_month=8,
    )
    candidates = [
        ScoredDestination(
            destination_id=1,
            city="Paris",
            country="France",
            rule_score=85.0,
            score_breakdown={},
            estimated_total_cost=1200.0,
        )
    ]
    explanations = await provider.explain_recommendations(context, candidates)
    assert len(explanations) == 1
    assert "Paris" in explanations[0].explanation
    assert explanations[0].llm_score > 0

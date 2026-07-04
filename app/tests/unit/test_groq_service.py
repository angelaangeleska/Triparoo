from app.recommendation.base import ScoredDestination
from app.services.groq_service import GroqRecommendationProvider, _parse_narratives, _strip_code_fence


def _candidate(dest_id: int, rule_score: float = 70.0) -> ScoredDestination:
    return ScoredDestination(
        destination_id=dest_id,
        city="Paris",
        country="France",
        rule_score=rule_score,
        score_breakdown={},
        estimated_total_cost=1200.0,
    )


def test_disabled_without_api_key():
    provider = GroqRecommendationProvider()
    assert provider.enabled is False


def test_strip_code_fence_removes_markdown():
    text = "```json\n[1, 2, 3]\n```"
    assert _strip_code_fence(text) == "[1, 2, 3]"


def test_fallback_uses_rule_score_and_empty_highlights():
    candidates = [_candidate(1, 80.0), _candidate(2, 60.0)]
    results = GroqRecommendationProvider._fallback(candidates)
    assert len(results) == 2
    assert results[0].llm_score == 80.0
    assert results[0].highlights == []
    assert "Paris, France" in results[0].explanation


def test_parse_response_matches_by_destination_id():
    provider = GroqRecommendationProvider()
    candidates = [_candidate(1, 70.0), _candidate(2, 50.0)]
    content = (
        '[{"destination_id": 1, "match_score": 92, "explanation": "Great fit", '
        '"highlights": ["Kid-friendly", "Great weather"]}]'
    )
    results = provider._parse_response(content, candidates)
    by_id = {r.destination_id: r for r in results}
    assert by_id[1].llm_score == 92.0
    assert by_id[1].explanation == "Great fit"
    assert by_id[1].highlights == ["Kid-friendly", "Great weather"]
    # candidate 2 wasn't in the LLM response — falls back to rule score
    assert by_id[2].llm_score == 50.0


def test_parse_response_invalid_json_falls_back():
    provider = GroqRecommendationProvider()
    candidates = [_candidate(1, 65.0)]
    results = provider._parse_response("not json at all", candidates)
    assert results[0].llm_score == 65.0


def test_parse_narratives_basic():
    content = '[{"day_number": 1, "narrative": "A gentle first stroll through the old town."}]'
    result = _parse_narratives(content)
    assert result[1] == "A gentle first stroll through the old town."


def test_parse_narratives_invalid_returns_empty():
    assert _parse_narratives("no json here") == {}

from app.recommendation.hybrid import _fallback_llm_scores


def test_fallback_llm_scores_change_on_regenerate():
    destinations = [
        {"city": "Paris", "country": "France", "estimated_total_cost": 1000},
        {"city": "Rome", "country": "Italy", "estimated_total_cost": 900},
        {"city": "Barcelona", "country": "Spain", "estimated_total_cost": 800},
    ]
    first = _fallback_llm_scores(destinations, regenerate_count=1)
    second = _fallback_llm_scores(destinations, regenerate_count=2)
    assert first[0]["llm_score"] != second[0]["llm_score"]
    assert first[0]["city"] == "Paris"

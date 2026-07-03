from app.core.config import settings
from app.recommendation.base import (
    RecommendationContext,
    RecommendationExplanation,
    RecommendationProvider,
    ScoredDestination,
)


class NullRecommendationProvider:
    """No-op provider used when GROQ_API_KEY is not configured.

    Mirrors the original rule-only behavior: llm_score equals rule_score and
    no natural-language explanation is generated.
    """

    async def explain_recommendations(
        self, context: RecommendationContext, candidates: list[ScoredDestination]
    ) -> list[RecommendationExplanation]:
        return [
            RecommendationExplanation(destination_id=c.destination_id, llm_score=c.rule_score, explanation="")
            for c in candidates
        ]


def get_recommendation_provider() -> RecommendationProvider:
    if settings.GROQ_API_KEY:
        from app.services.groq_service import GroqRecommendationProvider

        return GroqRecommendationProvider()
    return NullRecommendationProvider()

from app.core.config import settings
from app.recommendation.base import RecommendationContext, ScoredDestination
from app.recommendation.mock_llm import MockLLMProvider
from app.recommendation.rule_engine import RuleBasedScorer


class HybridRecommendationService:
    def __init__(
        self,
        rule_scorer: RuleBasedScorer | None = None,
        llm_provider: MockLLMProvider | None = None,
    ):
        self.rule_scorer = rule_scorer or RuleBasedScorer()
        self.llm_provider = llm_provider or MockLLMProvider()

    def _origin_flight_boost(self, context: RecommendationContext, flight_cost: float) -> float:
        if not context.origin_airport_id or flight_cost <= 0:
            return 0.0
        ratio = flight_cost / max(context.budget, 1.0)
        return max(0.0, min(12.0, 12.0 - ratio * 15.0))

    async def rank(
        self,
        context: RecommendationContext,
        destinations: list,
        cost_estimator,
    ) -> list[dict]:
        scored: list[ScoredDestination] = []
        for dest in destinations:
            cost = await cost_estimator(dest)
            if cost.get("same_origin"):
                continue

            result = self.rule_scorer.score_destination(
                dest, context, cost["total"], dest.attractions or []
            )
            rule_score = min(
                100.0,
                result.total + self._origin_flight_boost(context, cost.get("flight", 0.0)),
            )
            scored.append(
                ScoredDestination(
                    destination_id=dest.id,
                    city=dest.city.name if dest.city else "",
                    country=dest.city.country.name if dest.city and dest.city.country else "",
                    rule_score=round(rule_score, 2),
                    score_breakdown=result.breakdown,
                    estimated_total_cost=cost["total"],
                    suggested_attraction_ids=[a.id for a in result.suggested_attractions],
                    flight_cost=cost.get("flight", 0.0),
                    accommodation_cost=cost.get("accommodation", 0.0),
                    activity_cost=cost.get("activity", 0.0),
                    flight_offer=cost.get("flight_offer"),
                )
            )

        scored.sort(key=lambda s: (s.rule_score, -s.estimated_total_cost), reverse=True)
        top = scored[:10]
        explanations = await self.llm_provider.explain_recommendations(context, top)
        expl_map = {e.destination_id: e for e in explanations}

        results = []
        for s in top:
            expl = expl_map.get(s.destination_id)
            llm_score = expl.llm_score if expl else s.rule_score
            final = (
                settings.HYBRID_RULE_WEIGHT * s.rule_score + settings.HYBRID_LLM_WEIGHT * llm_score
            )
            results.append(
                {
                    "destination_id": s.destination_id,
                    "city": s.city,
                    "country": s.country,
                    "rule_score": s.rule_score,
                    "llm_score": llm_score,
                    "final_score": round(final, 2),
                    "estimated_total_cost": s.estimated_total_cost,
                    "flight_cost": s.flight_cost,
                    "accommodation_cost": s.accommodation_cost,
                    "activity_cost": s.activity_cost,
                    "flight_offer": s.flight_offer,
                    "score_breakdown": s.score_breakdown,
                    "explanation": expl.explanation if expl else "",
                    "suggested_attraction_ids": s.suggested_attraction_ids,
                }
            )
        results.sort(key=lambda r: r["final_score"], reverse=True)
        return results

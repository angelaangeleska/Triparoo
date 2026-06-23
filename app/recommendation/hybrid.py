from app.core.config import settings
from app.recommendation.base import RecommendationContext, ScoredDestination
from app.recommendation.rule_engine import RuleBasedScorer


class HybridRecommendationService:
    def __init__(
        self,
        rule_scorer: RuleBasedScorer | None = None,
    ):
        self.rule_scorer = rule_scorer or RuleBasedScorer()

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
            if cost["total"] > context.budget:
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
                    accommodation_offer=cost.get("accommodation_offer"),
                )
            )

        scored.sort(key=lambda s: (s.rule_score, -s.estimated_total_cost), reverse=True)
        top = scored[:10]

        results = []
        for s in top:
            results.append(
                {
                    "destination_id": s.destination_id,
                    "city": s.city,
                    "country": s.country,
                    "rule_score": s.rule_score,
                    "llm_score": s.rule_score,
                    "final_score": round(s.rule_score, 2),
                    "estimated_total_cost": s.estimated_total_cost,
                    "flight_cost": s.flight_cost,
                    "accommodation_cost": s.accommodation_cost,
                    "activity_cost": s.activity_cost,
                    "flight_offer": s.flight_offer,
                    "accommodation_offer": s.accommodation_offer,
                    "score_breakdown": s.score_breakdown,
                    "explanation": "",
                    "suggested_attraction_ids": s.suggested_attraction_ids,
                }
            )
        results.sort(key=lambda r: r["final_score"], reverse=True)
        return results

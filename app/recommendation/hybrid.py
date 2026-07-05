from app.recommendation.base import RecommendationContext, ScoredDestination
from app.recommendation.rule_engine import RuleBasedScorer
from app.services.groq_service import score_destinations_with_ai


class HybridRecommendationService:
    def __init__(
        self,
        rule_scorer: RuleBasedScorer | None = None,
    ):
        self.rule_scorer = rule_scorer or RuleBasedScorer()

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
            rule_score = min(100.0, result.total)
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

        scored.sort(key=lambda s: s.rule_score, reverse=True)
        top = scored[:10]

        members_payload = [
            {
                "age": m.age,
                "gender": m.gender,
                "interests": m.interests or [],
            }
            for m in context.members
        ]
        dest_payload = [
            {
                "city": s.city,
                "country": s.country,
                "estimated_total_cost": s.estimated_total_cost,
            }
            for s in top
        ]
        ai_scores = await score_destinations_with_ai(
            members=members_payload,
            budget=context.budget,
            travel_month=context.preferred_month,
            start_date=context.start_date,
            end_date=context.end_date,
            destinations=dest_payload,
            regenerate_count=context.regenerate_count,
        )
        ai_by_city = {item["city"].lower(): item for item in ai_scores}

        results = []
        for s in top:
            ai = ai_by_city.get(s.city.lower())
            if ai:
                llm_score = ai["llm_score"]
                explanation = ai.get("reason", "")
                final_score = round(0.7 * s.rule_score + 0.3 * llm_score, 2)
            else:
                llm_score = s.rule_score
                explanation = ""
                final_score = round(s.rule_score, 2)

            results.append(
                {
                    "destination_id": s.destination_id,
                    "city": s.city,
                    "country": s.country,
                    "rule_score": s.rule_score,
                    "llm_score": llm_score,
                    "final_score": final_score,
                    "estimated_total_cost": s.estimated_total_cost,
                    "flight_cost": s.flight_cost,
                    "accommodation_cost": s.accommodation_cost,
                    "activity_cost": s.activity_cost,
                    "flight_offer": s.flight_offer,
                    "accommodation_offer": s.accommodation_offer,
                    "score_breakdown": s.score_breakdown,
                    "explanation": explanation,
                    "suggested_attraction_ids": s.suggested_attraction_ids,
                }
            )
        results.sort(key=lambda r: r["final_score"], reverse=True)
        return results

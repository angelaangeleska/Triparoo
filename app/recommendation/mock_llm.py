from app.recommendation.base import (
    RecommendationContext,
    RecommendationExplanation,
    ScoredDestination,
)


class MockLLMProvider:
    async def explain_recommendations(
        self, context: RecommendationContext, candidates: list[ScoredDestination]
    ) -> list[RecommendationExplanation]:
        explanations = []
        children = [m for m in context.members if m.age < 18]
        child_ages = [c.age for c in children]

        for candidate in candidates:
            highlights = []
            if candidate.flight_offer and candidate.flight_offer.get("outbound"):
                ob = candidate.flight_offer["outbound"]
                trip = "round trip" if candidate.flight_offer.get("return_flight") else "one way"
                highlights.append(
                    f"{ob['airline']} {ob['flight_number']}: {ob['origin_iata']} → {ob['destination_iata']} "
                    f"({trip}, €{candidate.flight_offer['total_price_per_person']:.2f}/person)"
                )
            elif context.origin_airport_id:
                highlights.append("No direct flight found — estimate uses accommodation and activities only")

            if any(6 <= age <= 14 for age in child_ages):
                if "Paris" in candidate.city:
                    highlights.append("Disneyland Paris is ideal for school-age children")
                highlights.append("Interactive museums and theme parks match child interests")
            if context.budget >= candidate.estimated_total_cost:
                highlights.append("Estimated cost fits within your family budget")
            else:
                highlights.append("May require budget adjustments for peak season travel")

            month = context.preferred_month or (context.start_date.month if context.start_date else None)
            if month in (6, 7, 8):
                highlights.append("Summer travel offers long daylight hours for family activities")

            origin_part = ""
            if context.origin_label:
                origin_part = f"From {context.origin_label}, "

            explanation = (
                f"{origin_part}{candidate.city} scores highly for your family profile "
                f"(rule score: {candidate.rule_score:.1f}/100). "
            )
            if children:
                ages_str = ", ".join(str(a) for a in child_ages)
                explanation += f"With children aged {ages_str}, the destination offers age-appropriate attractions. "
            explanation += " ".join(highlights)

            llm_score = min(100.0, candidate.rule_score * 0.9 + (10 if highlights else 0))
            explanations.append(
                RecommendationExplanation(
                    destination_id=candidate.destination_id,
                    llm_score=round(llm_score, 2),
                    explanation=explanation,
                    highlights=highlights,
                )
            )
        return explanations

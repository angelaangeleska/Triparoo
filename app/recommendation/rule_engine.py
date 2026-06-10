from dataclasses import dataclass

from app.core.config import settings
from app.models.attraction import Attraction
from app.models.destination import Destination
from app.recommendation.base import MemberContext, RecommendationContext


@dataclass
class RuleScoreResult:
    total: float
    breakdown: dict[str, float]
    suggested_attractions: list[Attraction]


class RuleBasedScorer:
    def score_destination(
        self,
        destination: Destination,
        context: RecommendationContext,
        estimated_cost: float,
        attractions: list[Attraction],
    ) -> RuleScoreResult:
        children = [m for m in context.members if m.age < 18]
        adults = [m for m in context.members if m.age >= 18]
        party_size = len(context.members)

        child_age_score = self._score_child_age(children, attractions)
        budget_score = self._score_budget(context.budget, estimated_cost)
        season_score, weather_score = self._score_season(destination, context)
        popularity_score = min(destination.popularity_score, 100.0)
        family_score = min(destination.family_friendliness_score, 100.0)
        activity_score = self._score_activities(children, attractions)

        weights = {
            "child_age": settings.WEIGHT_CHILD_AGE,
            "budget": settings.WEIGHT_BUDGET,
            "season": settings.WEIGHT_SEASON,
            "popularity": settings.WEIGHT_POPULARITY,
            "family_friendly": settings.WEIGHT_FAMILY_FRIENDLY,
            "activity": settings.WEIGHT_ACTIVITY,
            "weather": settings.WEIGHT_WEATHER,
        }
        breakdown = {
            "child_age": child_age_score,
            "budget": budget_score,
            "season": season_score,
            "popularity": popularity_score,
            "family_friendly": family_score,
            "activity": activity_score,
            "weather": weather_score,
        }
        total = sum(breakdown[k] * weights[k] for k in breakdown) / sum(weights.values()) * 100

        if party_size > 4 and not any(a.family_friendly for a in destination.accommodations):
            total *= 0.9

        suggested = self._pick_attractions(children, attractions)
        return RuleScoreResult(total=round(total, 2), breakdown=breakdown, suggested_attractions=suggested)

    def _score_child_age(self, children: list[MemberContext], attractions: list[Attraction]) -> float:
        if not children:
            return 70.0
        matches = 0
        for child in children:
            for att in attractions:
                if att.min_age <= child.age <= att.max_age:
                    matches += 1
                    if "theme_park" in att.tags or "disney" in att.name.lower():
                        matches += 1
        max_possible = len(children) * max(len(attractions), 1)
        return min(100.0, (matches / max_possible) * 100 + 20)

    def _score_budget(self, budget: float, estimated_cost: float) -> float:
        if estimated_cost <= 0:
            return 50.0
        ratio = budget / estimated_cost
        if ratio >= 1.2:
            return 100.0
        if ratio >= 1.0:
            return 90.0
        if ratio >= 0.85:
            return 70.0
        if ratio >= 0.7:
            return 45.0
        return 20.0

    def _score_season(self, destination: Destination, context: RecommendationContext) -> tuple[float, float]:
        month = context.preferred_month
        if not month and context.start_date:
            month = context.start_date.month
        if not month:
            return 60.0, 60.0

        for season in destination.seasons:
            if season.month_start <= month <= season.month_end:
                season_score = season.weather_score * (2.0 - min(season.price_multiplier, 2.0)) * 50
                return min(season_score, 100.0), min(season.weather_score * 100, 100.0)
        return 50.0, 50.0

    def _score_activities(self, children: list[MemberContext], attractions: list[Attraction]) -> float:
        if not attractions:
            return 30.0
        child_friendly = [a for a in attractions if a.family_friendly]
        base = len(child_friendly) / len(attractions) * 80
        if children:
            interest_tags = {i.lower() for c in children for i in c.interests}
            tag_matches = sum(
                1 for a in child_friendly if any(t in interest_tags for t in (a.tags or []))
            )
            base += min(tag_matches * 10, 20)
        return min(base, 100.0)

    def _pick_attractions(self, children: list[MemberContext], attractions: list[Attraction]) -> list[Attraction]:
        if not children:
            return sorted(attractions, key=lambda a: a.price)[:5]
        scored = []
        for att in attractions:
            fit = sum(1 for c in children if att.min_age <= c.age <= att.max_age)
            scored.append((fit, att))
        scored.sort(key=lambda x: (-x[0], x[1].price))
        return [a for _, a in scored[:5]]

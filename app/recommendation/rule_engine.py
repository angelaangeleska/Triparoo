from dataclasses import dataclass
from datetime import timedelta

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
            "budget": 100.0 if estimated_cost <= context.budget else 0.0,
            "season": season_score,
            "popularity": popularity_score,
            "family_friendly": family_score,
            "activity": activity_score,
            "weather": weather_score,
        }
        total = sum(breakdown[k] * weights[k] for k in breakdown) / sum(weights.values()) * 100

        if party_size > 4 and not any(a.family_friendly for a in destination.accommodations):
            total *= 0.9

        suggested = self._pick_attractions(children, attractions, context.regenerate_count)
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

    def _trip_months(self, context: RecommendationContext) -> list[int]:
        if context.start_date and context.end_date:
            months: set[int] = set()
            current = context.start_date
            while current <= context.end_date:
                months.add(current.month)
                current += timedelta(days=1)
            return sorted(months)
        if context.preferred_month:
            return [context.preferred_month]
        if context.start_date:
            return [context.start_date.month]
        return []

    def _season_for_month(self, destination: Destination, month: int) -> tuple[float, float]:
        for season in destination.seasons or []:
            if season.month_start <= month <= season.month_end:
                weather = min(season.weather_score * 100, 100.0)
                return weather, weather
        return 50.0, 50.0

    def _score_season(self, destination: Destination, context: RecommendationContext) -> tuple[float, float]:
        months = self._trip_months(context)
        if not months:
            return 60.0, 60.0

        season_scores: list[float] = []
        weather_scores: list[float] = []
        for month in months:
            season_score, weather_score = self._season_for_month(destination, month)
            season_scores.append(season_score)
            weather_scores.append(weather_score)
        return (
            sum(season_scores) / len(season_scores),
            sum(weather_scores) / len(weather_scores),
        )

    def _attraction_interest_score(self, child: MemberContext, attraction: Attraction) -> float:
        if not (attraction.min_age <= child.age <= attraction.max_age):
            return 0.0
        interests = [i.lower().strip() for i in (child.interests or []) if i.strip()]
        if not interests:
            return 1.0 if attraction.family_friendly else 0.5

        haystack = " ".join(
            [
                attraction.name.lower(),
                attraction.category.lower(),
                " ".join((attraction.tags or [])).lower(),
            ]
        )
        tags = {t.lower() for t in (attraction.tags or [])}
        score = 0.0
        for interest in interests:
            if interest in haystack or interest in tags:
                score += 3.0
            elif any(interest in tag or tag in interest for tag in tags):
                score += 2.0
            elif any(word in haystack for word in interest.split()):
                score += 1.0
        return score

    def _score_activities(self, children: list[MemberContext], attractions: list[Attraction]) -> float:
        if not attractions:
            return 30.0
        if not children:
            child_friendly = [a for a in attractions if a.family_friendly]
            return min(len(child_friendly) / len(attractions) * 80, 100.0)

        total = 0.0
        max_possible = len(children) * len(attractions) * 3.0
        for child in children:
            for att in attractions:
                total += self._attraction_interest_score(child, att)
        return min(100.0, (total / max(max_possible, 1)) * 100 + 20)

    def _pick_attractions(
        self,
        children: list[MemberContext],
        attractions: list[Attraction],
        regenerate_count: int = 0,
    ) -> list[Attraction]:
        if not children:
            picks = attractions[:5]
        else:
            scored = []
            for att in attractions:
                fit = sum(self._attraction_interest_score(c, att) for c in children)
                scored.append((fit, att))
            scored.sort(key=lambda x: -x[0])
            picks = [a for _, a in scored]
        if regenerate_count > 0 and len(picks) > 1:
            offset = (regenerate_count * 2) % len(picks)
            picks = picks[offset:] + picks[:offset]
        return picks[:5]

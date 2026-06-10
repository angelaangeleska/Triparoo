from dataclasses import dataclass, field
from datetime import date
from typing import Protocol


@dataclass
class MemberContext:
    age: int
    gender: str | None = None
    interests: list[str] = field(default_factory=list)


@dataclass
class RecommendationContext:
    members: list[MemberContext]
    budget: float
    start_date: date | None = None
    end_date: date | None = None
    preferred_month: int | None = None
    origin_airport_id: int | None = None
    origin_label: str | None = None


@dataclass
class ScoredDestination:
    destination_id: int
    city: str
    country: str
    rule_score: float
    score_breakdown: dict[str, float]
    estimated_total_cost: float
    suggested_attraction_ids: list[int] = field(default_factory=list)
    flight_cost: float = 0.0
    accommodation_cost: float = 0.0
    activity_cost: float = 0.0
    flight_offer: dict | None = None


@dataclass
class RecommendationExplanation:
    destination_id: int
    llm_score: float
    explanation: str
    highlights: list[str] = field(default_factory=list)


class RecommendationProvider(Protocol):
    async def explain_recommendations(
        self, context: RecommendationContext, candidates: list[ScoredDestination]
    ) -> list[RecommendationExplanation]: ...

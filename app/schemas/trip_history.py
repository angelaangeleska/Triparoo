from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class TripHistoryMemberRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    age: int
    gender: Optional[str] = None
    interests: list[str] = []


class TripHistoryRecommendationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    entity_id: Optional[int] = None
    rule_score: float
    llm_score: float
    final_score: float
    explanation: dict
    created_at: datetime


class TripHistoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    origin_airport_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    budget: Optional[float] = None
    status: str
    created_at: datetime
    members: list[TripHistoryMemberRead] = []
    recommendations: list[TripHistoryRecommendationRead] = []

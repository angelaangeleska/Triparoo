from datetime import date
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.family import TripMemberInput


class AITripGuideRequest(BaseModel):
    destination_id: int
    members: list[TripMemberInput] = Field(min_length=1)
    budget: float = Field(gt=0)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    interests: list[str] = Field(default_factory=list)


class AIGuideItem(BaseModel):
    title: str
    description: str = ""
    why_recommended: str = ""


class AITripGuideResponse(BaseModel):
    destination_id: int
    city: str
    country: str
    available: bool = True
    attractions: list[AIGuideItem] = Field(default_factory=list)
    restaurants: list[AIGuideItem] = Field(default_factory=list)
    hidden_gems: list[AIGuideItem] = Field(default_factory=list)
    local_tips: list[AIGuideItem] = Field(default_factory=list)
    transportation_tips: list[AIGuideItem] = Field(default_factory=list)

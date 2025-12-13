from datetime import datetime, date
from typing import Optional, List

from pydantic import BaseModel, Field

from app.models.trip_member import TripMember


class TripRequest(BaseModel):
    id: int
    user_id: int
    created_at: datetime
    destination_preference_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    budget: Optional[float] = None

    members: List[TripMember] = Field(default_factory=list)
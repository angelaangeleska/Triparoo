from datetime import datetime
from typing import Literal, Any, Optional

from pydantic import BaseModel

RecommendationType = Literal["destination", "flight", "accommodation", "activity"]


class Recommendation(BaseModel):
    id: int
    trip_request_id: int
    user_id: int
    type: RecommendationType
    data_id: Optional[Any] = None # recommender response snapshot
    created_at: datetime
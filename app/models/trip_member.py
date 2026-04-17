from typing import Optional

from pydantic import BaseModel


class TripMember(BaseModel):
    id: int
    trip_request_id: int
    age: int
    gender: Optional[str] = None

from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class FamilyMemberInput(BaseModel):
    age: int = Field(ge=0, le=120)
    gender: Optional[str] = None
    interests: list[str] = Field(default_factory=list)


class FamilyMemberCreate(FamilyMemberInput):
    name: Optional[str] = None
    relation_type: Optional[str] = None


class FamilyMemberRead(FamilyMemberCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int


class TripMemberInput(FamilyMemberInput):
    pass


class TripMemberRead(TripMemberInput):
    model_config = ConfigDict(from_attributes=True)

    id: int
    trip_request_id: int

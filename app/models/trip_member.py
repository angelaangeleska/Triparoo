from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.trip_request import TripRequest


class TripMember(Base):
    __tablename__ = "trip_members"

    id: Mapped[int] = mapped_column(primary_key=True)
    trip_request_id: Mapped[int] = mapped_column(ForeignKey("trip_requests.id", ondelete="CASCADE"))
    age: Mapped[int] = mapped_column(Integer)
    gender: Mapped[Optional[str]] = mapped_column(String(20))
    interests: Mapped[list] = mapped_column(JSON, default=list)

    trip_request: Mapped["TripRequest"] = relationship(back_populates="members")

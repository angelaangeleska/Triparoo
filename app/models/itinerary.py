from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.trip_request import TripRequest
    from app.models.user import User


class ItineraryDay(Base):
    __tablename__ = "itinerary_days"

    id: Mapped[int] = mapped_column(primary_key=True)
    trip_request_id: Mapped[int] = mapped_column(ForeignKey("trip_requests.id", ondelete="CASCADE"))
    day_number: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(200))
    items: Mapped[list] = mapped_column(JSON, default=list)

    trip_request: Mapped["TripRequest"] = relationship(back_populates="itinerary_days")


class SavedTrip(Base, TimestampMixin):
    __tablename__ = "saved_trips"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    trip_request_id: Mapped[int] = mapped_column(ForeignKey("trip_requests.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(200))
    notes: Mapped[str] = mapped_column(Text, default="")

    user: Mapped["User"] = relationship(back_populates="saved_trips")
    trip_request: Mapped["TripRequest"] = relationship()

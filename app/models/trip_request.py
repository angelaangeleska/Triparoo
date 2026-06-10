from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.budget_profile import BudgetProfile
    from app.models.country import Airport
    from app.models.destination import Destination
    from app.models.itinerary import ItineraryDay
    from app.models.recommendation import Recommendation
    from app.models.trip_member import TripMember
    from app.models.user import User


class TripRequest(Base, TimestampMixin):
    __tablename__ = "trip_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    origin_airport_id: Mapped[Optional[int]] = mapped_column(ForeignKey("airports.id"))
    destination_id: Mapped[Optional[int]] = mapped_column(ForeignKey("destinations.id"))
    start_date: Mapped[Optional[date]] = mapped_column(Date)
    end_date: Mapped[Optional[date]] = mapped_column(Date)
    budget: Mapped[Optional[float]] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(30), default="draft")

    user: Mapped["User"] = relationship(back_populates="trip_requests")
    origin_airport: Mapped[Optional["Airport"]] = relationship()
    destination: Mapped[Optional["Destination"]] = relationship()
    members: Mapped[list["TripMember"]] = relationship(back_populates="trip_request", cascade="all, delete-orphan")
    recommendations: Mapped[list["Recommendation"]] = relationship(back_populates="trip_request")
    budget_profile: Mapped[Optional["BudgetProfile"]] = relationship(back_populates="trip_request")
    itinerary_days: Mapped[list["ItineraryDay"]] = relationship(back_populates="trip_request")

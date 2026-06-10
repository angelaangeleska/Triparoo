from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.trip_request import TripRequest


class BudgetProfile(Base):
    __tablename__ = "budget_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    trip_request_id: Mapped[int] = mapped_column(ForeignKey("trip_requests.id", ondelete="CASCADE"), unique=True)
    total_budget: Mapped[float] = mapped_column(Float)
    flight_budget: Mapped[float] = mapped_column(Float, default=0.0)
    accommodation_budget: Mapped[float] = mapped_column(Float, default=0.0)
    activity_budget: Mapped[float] = mapped_column(Float, default=0.0)

    trip_request: Mapped["TripRequest"] = relationship(back_populates="budget_profile")

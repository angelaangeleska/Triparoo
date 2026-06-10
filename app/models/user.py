from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.family_member import FamilyMember
    from app.models.refresh_token import RefreshToken
    from app.models.saved_trip import SavedTrip
    from app.models.travel_preference import TravelPreference
    from app.models.trip_request import TripRequest


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    hashed_password: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(100))
    last_name: Mapped[Optional[str]] = mapped_column(String(100))
    passport_number: Mapped[Optional[str]] = mapped_column(String(50))
    google_sub: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    family_members: Mapped[list["FamilyMember"]] = relationship(back_populates="user")
    trip_requests: Mapped[list["TripRequest"]] = relationship(back_populates="user")
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(back_populates="user")
    travel_preference: Mapped[Optional["TravelPreference"]] = relationship(back_populates="user")
    saved_trips: Mapped[list["SavedTrip"]] = relationship(back_populates="user")

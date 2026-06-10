from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.country import Airport


class Flight(Base):
    __tablename__ = "flights"

    id: Mapped[int] = mapped_column(primary_key=True)
    origin_airport_id: Mapped[int] = mapped_column(ForeignKey("airports.id"))
    destination_airport_id: Mapped[int] = mapped_column(ForeignKey("airports.id"))
    departure_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    price: Mapped[float] = mapped_column(Float)
    airline: Mapped[str] = mapped_column(String(100))
    seats_remaining: Mapped[Optional[int]] = mapped_column(Integer)

    origin_airport: Mapped["Airport"] = relationship(foreign_keys=[origin_airport_id])
    destination_airport: Mapped["Airport"] = relationship(foreign_keys=[destination_airport_id])

from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.destination import Destination


class Accommodation(Base):
    __tablename__ = "accommodations"

    id: Mapped[int] = mapped_column(primary_key=True)
    destination_id: Mapped[int] = mapped_column(ForeignKey("destinations.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(200))
    type: Mapped[str] = mapped_column(String(30))
    rating: Mapped[Optional[float]] = mapped_column(Float)
    price_per_night: Mapped[float] = mapped_column(Float)
    address: Mapped[Optional[str]] = mapped_column(String(300))
    family_friendly: Mapped[bool] = mapped_column(Boolean, default=True)
    max_guests: Mapped[int] = mapped_column(Integer, default=4)

    destination: Mapped["Destination"] = relationship(back_populates="accommodations")

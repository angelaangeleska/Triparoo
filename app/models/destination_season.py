from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.destination import Destination


class DestinationSeason(Base):
    __tablename__ = "destination_seasons"

    id: Mapped[int] = mapped_column(primary_key=True)
    destination_id: Mapped[int] = mapped_column(ForeignKey("destinations.id", ondelete="CASCADE"))
    season: Mapped[str] = mapped_column(String(20))
    month_start: Mapped[int] = mapped_column(Integer)
    month_end: Mapped[int] = mapped_column(Integer)
    avg_temp_c: Mapped[float] = mapped_column(Float)
    weather_score: Mapped[float] = mapped_column(Float, default=0.0)
    price_multiplier: Mapped[float] = mapped_column(Float, default=1.0)

    destination: Mapped["Destination"] = relationship(back_populates="seasons")

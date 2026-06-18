from typing import TYPE_CHECKING, Optional

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.accommodation import Accommodation
    from app.models.activity import Activity
    from app.models.attraction import Attraction
    from app.models.city import City
    from app.models.destination_season import DestinationSeason


class Destination(Base):
    __tablename__ = "destinations"

    id: Mapped[int] = mapped_column(primary_key=True)
    city_id: Mapped[int] = mapped_column(ForeignKey("cities.id"))
    description: Mapped[Optional[str]] = mapped_column(Text)
    family_friendliness_score: Mapped[float] = mapped_column(Float, default=0.0)
    popularity_score: Mapped[float] = mapped_column(Float, default=0.0)
    latitude: Mapped[Optional[float]] = mapped_column(Float)
    longitude: Mapped[Optional[float]] = mapped_column(Float)

    city: Mapped["City"] = relationship(back_populates="destinations")
    seasons: Mapped[list["DestinationSeason"]] = relationship(back_populates="destination")
    attractions: Mapped[list["Attraction"]] = relationship(back_populates="destination")
    activities: Mapped[list["Activity"]] = relationship(back_populates="destination")
    accommodations: Mapped[list["Accommodation"]] = relationship(back_populates="destination")

    @property
    def name(self) -> str:
        return self.city.name if self.city else ""

    @property
    def country_name(self) -> str:
        return self.city.country.name if self.city and self.city.country else ""

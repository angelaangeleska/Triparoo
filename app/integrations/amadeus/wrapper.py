"""Wrap Amadeus destination data for services that expect ORM-shaped objects."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.integrations.amadeus.destinations import AmadeusDestination


@dataclass
class _Country:
    name: str


@dataclass
class _Airport:
    id: int
    iata_code: str


@dataclass
class _City:
    name: str
    country: _Country
    airports: list[_Airport] = field(default_factory=list)


@dataclass
class AmadeusDestinationWrapper:
    """Minimal Destination stand-in backed by Amadeus city data."""

    amadeus: AmadeusDestination
    city: _City
    id: int = 0
    description: str | None = None
    family_friendliness_score: float = 0.75
    popularity_score: float = 0.8
    latitude: float | None = None
    longitude: float | None = None
    seasons: list = field(default_factory=list)
    attractions: list = field(default_factory=list)
    accommodations: list = field(default_factory=list)

    @classmethod
    def from_amadeus(cls, dest: AmadeusDestination) -> "AmadeusDestinationWrapper":
        iata = dest.iata_code or dest.city_code
        return cls(
            amadeus=dest,
            id=dest.id,
            description=dest.description,
            latitude=dest.latitude,
            longitude=dest.longitude,
            city=_City(
                name=dest.city_name,
                country=_Country(name=dest.country_name),
                airports=[_Airport(id=0, iata_code=iata)] if iata else [],
            ),
        )

    @property
    def name(self) -> str:
        return self.amadeus.city_name

    @property
    def country_name(self) -> str:
        return self.amadeus.country_name

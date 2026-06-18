"""Worldwide airport catalog loaded from open IATA data (~8k commercial airports)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from app.utils.geo import haversine_km

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "global_airports.json"

_MINOR = {"heliport", "helipad", "seaplane", "glider", "ultralight", "airstrip", "airfield"}
_MAJOR = {"international", "intercontinental"}

# Country codes that get priority when multiple countries share a city name.
# Covers EU/EEA + common travel destinations so "Rome" → Italy, "London" → UK.
_PRIORITY_COUNTRIES = {
    "al", "ad", "at", "be", "ba", "bg", "hr", "cy", "cz", "dk", "ee", "fi",
    "fr", "de", "gr", "hu", "is", "ie", "it", "xk", "lv", "li", "lt", "lu",
    "mt", "md", "mc", "me", "nl", "mk", "no", "pl", "pt", "ro", "sm", "rs",
    "sk", "si", "es", "se", "ch", "tr", "ua", "gb", "va",
    # popular non-EU travel destinations
    "ae", "eg", "ma", "tn", "th", "jp", "sg", "mx", "br", "au", "nz",
}

# Local vs English city names that refer to the same place.
_CITY_ALIAS_GROUPS: tuple[frozenset[str], ...] = (
    frozenset({"rome", "roma"}),
    frozenset({"milan", "milano"}),
    frozenset({"florence", "firenze"}),
    frozenset({"naples", "napoli"}),
    frozenset({"venice", "venezia"}),
    frozenset({"munich", "munchen", "muenchen"}),
    frozenset({"cologne", "koln", "koeln"}),
    frozenset({"vienna", "wien"}),
    frozenset({"prague", "praha"}),
    frozenset({"warsaw", "warszawa"}),
    frozenset({"lisbon", "lisboa"}),
    frozenset({"athens", "athina"}),
    frozenset({"brussels", "bruxelles"}),
    frozenset({"copenhagen", "kobenhavn", "københavn"}),
)


def _city_equivalent_keys(city: str) -> set[str]:
    key = city.lower()
    keys = {key}
    for group in _CITY_ALIAS_GROUPS:
        if key in group:
            keys.update(group)
    return keys


def cities_equivalent(city_a: str, city_b: str) -> bool:
    """True when two city names refer to the same place (e.g. Rome / Roma)."""
    return bool(_city_equivalent_keys(city_a) & _city_equivalent_keys(city_b))


def _prominence(name: str) -> int:
    """0 = international, 1 = regular, 2 = minor. Lower is better."""
    n = name.lower()
    if any(k in n for k in _MAJOR):
        return 0
    if any(k in n for k in _MINOR):
        return 2
    return 1


def _country_priority(country_code: str) -> int:
    """0 = priority country, 1 = other. Lower is better."""
    return 0 if country_code.lower() in _PRIORITY_COUNTRIES else 1


def _parse_city_country(query: str) -> tuple[str, str | None]:
    """Split 'Rome, Italy' into ('Rome', 'Italy'). Returns (query, None) if no country part."""
    if "," not in query:
        return query, None
    city_part, country_part = (p.strip() for p in query.split(",", 1))
    if city_part and country_part:
        return city_part, country_part
    return query, None


def _matches_country(airport: "CatalogAirport", country_query: str) -> bool:
    cq = country_query.lower()
    if airport.country_code.lower() == cq:
        return True
    country_lower = airport.country.lower()
    if country_lower == cq or country_lower.startswith(cq):
        return True
    # e.g. "united states" → "United States of America", "usa" → US code handled above
    return cq in country_lower


def ensure_catalog_file() -> None:
    if DATA_PATH.exists() and DATA_PATH.stat().st_size > 10_000:
        return
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    from app.utils.build_airport_catalog import main
    main()


@dataclass(frozen=True)
class CatalogAirport:
    iata: str
    name: str
    city: str
    country: str
    country_code: str
    lat: float
    lng: float


@dataclass
class AirportCatalog:
    airports: list[CatalogAirport]
    by_iata: dict[str, CatalogAirport]
    by_city: dict[str, list[CatalogAirport]]      # city.lower() → airports, sorted by prominence
    by_country: dict[str, list[CatalogAirport]]   # country/code.lower() → airports

    @classmethod
    def load(cls) -> AirportCatalog:
        ensure_catalog_file()
        raw = json.loads(DATA_PATH.read_text(encoding="utf-8"))
        airports = [
            CatalogAirport(
                iata=r["iata"],
                name=r["name"],
                city=r.get("city") or "",
                country=r.get("country") or r.get("country_code", ""),
                country_code=r.get("country_code", ""),
                lat=r["lat"],
                lng=r["lng"],
            )
            for r in raw
        ]

        by_iata: dict[str, CatalogAirport] = {a.iata: a for a in airports}

        by_city: dict[str, list[CatalogAirport]] = {}
        for a in airports:
            if a.city:
                for key in _city_equivalent_keys(a.city):
                    by_city.setdefault(key, []).append(a)
        # dedupe and sort each city bucket: priority country first, then by prominence, then name
        for key, bucket in by_city.items():
            seen: set[str] = set()
            deduped: list[CatalogAirport] = []
            for ap in bucket:
                if ap.iata not in seen:
                    seen.add(ap.iata)
                    deduped.append(ap)
            deduped.sort(key=lambda a: (_country_priority(a.country_code), _prominence(a.name), a.name))
            by_city[key] = deduped

        by_country: dict[str, list[CatalogAirport]] = {}
        for a in airports:
            by_country.setdefault(a.country.lower(), []).append(a)
            if a.country_code:
                by_country.setdefault(a.country_code.lower(), []).append(a)

        return cls(airports=airports, by_iata=by_iata, by_city=by_city, by_country=by_country)

    def get(self, iata: str) -> CatalogAirport | None:
        return self.by_iata.get(iata.upper())

    def search(
        self,
        query: str,
        limit: int = 20,
    ) -> list[tuple[CatalogAirport, str, float | None, str | None]]:
        """Return list of (airport, match_type, distance_km, note).

        Match priority:
          1. Exact IATA code
          2. Exact country name / ISO code
          3. City + country (e.g. "Rome, Italy")
          4. Exact city name  ← O(1) dict lookup, sorted by prominence
          5. City name starts-with (prefix)
          6. Geo centroid fallback
        Airport *names* are intentionally never searched to avoid false
        positives (e.g. 'Madrid' matching 'de la Madrid Airport' in Mexico).
        """
        q = query.strip()
        if len(q) < 2:
            return []

        city_part, country_part = _parse_city_country(q)
        q_lower = city_part.lower()
        q_upper = city_part.upper()

        # 1. Exact IATA code
        if not country_part and len(q_upper) == 3 and q_upper in self.by_iata:
            ap = self.by_iata[q_upper]
            return [(ap, "iata", None, None)]

        # 2. Exact country match (name or ISO code) — only when no city part specified
        if not country_part:
            country_bucket = self.by_country.get(q_lower)
            if country_bucket:
                ranked = sorted(country_bucket, key=lambda a: (_prominence(a.name), a.city, a.name))
                return [(ap, "country", None, f"Airport in {ap.country}") for ap in ranked[:limit]]

        # 3. City + country (e.g. "Rome, Italy" or "Rome, US")
        if country_part:
            city_bucket = self.by_city.get(q_lower)
            if city_bucket:
                filtered = [ap for ap in city_bucket if _matches_country(ap, country_part)]
                if filtered:
                    return [(ap, "direct", None, None) for ap in filtered[:limit]]
            return []

        # 4. Exact city name match — single dict lookup, pre-sorted by prominence
        city_bucket = self.by_city.get(q_lower)
        if city_bucket:
            return [(ap, "direct", None, None) for ap in city_bucket[:limit]]

        # 5. City prefix match (e.g. "new y" → "New York", "amst" → "Amsterdam")
        prefix_hits: list[CatalogAirport] = []
        seen: set[str] = set()
        for city_key, bucket in self.by_city.items():
            if city_key.startswith(q_lower):
                for ap in bucket:
                    if ap.iata not in seen:
                        seen.add(ap.iata)
                        prefix_hits.append(ap)
        if prefix_hits:
            prefix_hits.sort(key=lambda a: (len(a.city), _prominence(a.name), a.name))
            return [(ap, "direct", None, None) for ap in prefix_hits[:limit]]

        # 6. Geo centroid: average position of all cities containing the query
        #    as a substring (last resort for partial / misspelled input)
        city_matches = [ap for ap in self.airports if ap.city and q_lower in ap.city.lower()]
        if city_matches:
            lat = sum(a.lat for a in city_matches) / len(city_matches)
            lng = sum(a.lng for a in city_matches) / len(city_matches)
            ranked = sorted(self.airports, key=lambda a: haversine_km(lat, lng, a.lat, a.lng))
            results = []
            for ap in ranked[:limit]:
                dist = haversine_km(lat, lng, ap.lat, ap.lng)
                results.append((ap, "closest", dist, f"Nearest airport ({dist:.0f} km)"))
            return results

        return []

    def closest_to(self, lat: float, lng: float, limit: int = 5) -> list[tuple[CatalogAirport, float]]:
        ranked = sorted(self.airports, key=lambda a: haversine_km(lat, lng, a.lat, a.lng))
        return [(ap, haversine_km(lat, lng, ap.lat, ap.lng)) for ap in ranked[:limit]]


@lru_cache(maxsize=1)
def get_airport_catalog() -> AirportCatalog:
    return AirportCatalog.load()

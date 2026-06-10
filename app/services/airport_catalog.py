"""Worldwide airport catalog loaded from open IATA data (~8k commercial airports)."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from app.utils.geo import haversine_km

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "global_airports.json"


def ensure_catalog_file() -> None:
    """Download open airport data if the bundled file is missing."""
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
    by_country: dict[str, list[CatalogAirport]]

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
        by_iata = {a.iata: a for a in airports}
        by_country: dict[str, list[CatalogAirport]] = {}
        for a in airports:
            by_country.setdefault(a.country.lower(), []).append(a)
            if a.country_code:
                by_country.setdefault(a.country_code.lower(), []).append(a)
        return cls(airports=airports, by_iata=by_iata, by_country=by_country)

    def get(self, iata: str) -> CatalogAirport | None:
        return self.by_iata.get(iata.upper())

    def search(
        self,
        query: str,
        limit: int = 20,
    ) -> list[tuple[CatalogAirport, str, float | None, str | None]]:
        """Return (airport, match_type, distance_km, note)."""
        q = query.strip()
        if len(q) < 2:
            return []

        q_lower = q.lower()
        q_upper = q.upper()
        results: list[tuple[CatalogAirport, str, float | None, str | None]] = []
        seen: set[str] = set()

        def add(ap: CatalogAirport, match_type: str, distance: float | None = None, note: str | None = None):
            if ap.iata in seen:
                return
            seen.add(ap.iata)
            results.append((ap, match_type, distance, note))

        # 1. IATA code
        if len(q_upper) == 3 and q_upper in self.by_iata:
            add(self.by_iata[q_upper], "iata")
            return results[:limit]

        # 2. Country
        country_airports = self.by_country.get(q_lower)
        if country_airports:
            for ap in sorted(country_airports, key=lambda a: (a.city, a.name))[:limit]:
                add(ap, "country", note=f"Airport in {ap.country}")
            return results[:limit]

        for country_key, aps in self.by_country.items():
            if q_lower in country_key:
                for ap in sorted(aps, key=lambda a: (a.city, a.name)):
                    add(ap, "country", note=f"Airport in {ap.country}")
                if results:
                    return results[:limit]

        # 3. City / airport name (direct)
        city_matches: list[CatalogAirport] = []
        for ap in self.airports:
            city_l = ap.city.lower()
            name_l = ap.name.lower()
            if q_lower == city_l or q_lower == name_l:
                add(ap, "direct")
            elif q_lower in city_l or q_lower in name_l:
                city_matches.append(ap)

        for ap in sorted(city_matches, key=lambda a: (len(a.city), a.name))[:limit]:
            add(ap, "direct")

        if results:
            return results[:limit]

        # 4. Fuzzy token match (e.g. "alexander" -> SKP)
        tokens = [t for t in re.split(r"[\s,]+", q_lower) if len(t) >= 3]
        if tokens:
            for ap in self.airports:
                hay = f"{ap.city} {ap.name} {ap.country}".lower()
                if all(t in hay for t in tokens):
                    add(ap, "direct")

        if results:
            return results[:limit]

        # 5. Closest airport to query centroid (unknown place)
        centroid = self._centroid_for_query(q_lower)
        if centroid:
            lat, lng, label = centroid
            ranked = sorted(
                self.airports,
                key=lambda a: haversine_km(lat, lng, a.lat, a.lng),
            )
            for ap in ranked[:limit]:
                dist = haversine_km(lat, lng, ap.lat, ap.lng)
                add(
                    ap,
                    "closest",
                    dist,
                    f"Nearest airport to {label} ({dist:.0f} km)",
                )

        return results[:limit]

    def _centroid_for_query(self, q_lower: str) -> tuple[float, float, str] | None:
        """Average coordinates of airports whose city matches the query."""
        matches = [ap for ap in self.airports if q_lower in ap.city.lower()]
        if not matches:
            return None
        lat = sum(a.lat for a in matches) / len(matches)
        lng = sum(a.lng for a in matches) / len(matches)
        return lat, lng, matches[0].city or q_lower.title()

    def closest_to(self, lat: float, lng: float, limit: int = 5) -> list[tuple[CatalogAirport, float]]:
        ranked = sorted(self.airports, key=lambda a: haversine_km(lat, lng, a.lat, a.lng))
        return [(ap, haversine_km(lat, lng, ap.lat, ap.lng)) for ap in ranked[:limit]]


@lru_cache(maxsize=1)
def get_airport_catalog() -> AirportCatalog:
    return AirportCatalog.load()

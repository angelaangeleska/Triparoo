import logging

import httpx

logger = logging.getLogger(__name__)

_OVERPASS_URL = "https://overpass-api.de/api/interpreter"
_USER_AGENT = "Triparoo/1.0 (family trip planner; contact: dev@localhost)"
_DEFAULT_RADIUS_M = 8000
_RESULT_LIMIT = 30

_TOURISM_TYPES = "museum|attraction|zoo|aquarium|theme_park|gallery|viewpoint|artwork"
_LEISURE_TYPES = "park|playground|nature_reserve|water_park"

_CATEGORY_LABELS = {
    "museum": "museum",
    "attraction": "attraction",
    "zoo": "zoo",
    "aquarium": "aquarium",
    "theme_park": "theme park",
    "gallery": "gallery",
    "viewpoint": "viewpoint",
    "artwork": "artwork",
    "park": "park",
    "playground": "playground",
    "nature_reserve": "nature reserve",
    "water_park": "water park",
}


def _build_overpass_query(latitude: float, longitude: float, radius_m: int) -> str:
    return f"""[out:json][timeout:25];
(
  node["name"]["tourism"~"^({_TOURISM_TYPES})$"](around:{radius_m},{latitude},{longitude});
  way["name"]["tourism"~"^({_TOURISM_TYPES})$"](around:{radius_m},{latitude},{longitude});
  node["name"]["leisure"~"^({_LEISURE_TYPES})$"](around:{radius_m},{latitude},{longitude});
  way["name"]["leisure"~"^({_LEISURE_TYPES})$"](around:{radius_m},{latitude},{longitude});
  node["name"]["historic"](around:{radius_m},{latitude},{longitude});
  way["name"]["historic"](around:{radius_m},{latitude},{longitude});
);
out center tags {_RESULT_LIMIT};"""


def _category_from_tags(tags: dict) -> str:
    for key in ("tourism", "leisure", "historic"):
        value = tags.get(key)
        if value:
            return _CATEGORY_LABELS.get(value, value.replace("_", " "))
    return "attraction"


def _description_from_tags(tags: dict) -> str:
    for key in ("description:en", "description", "note:en", "note"):
        value = tags.get(key)
        if value:
            return str(value).strip()[:500]
    opening_hours = tags.get("opening_hours")
    if opening_hours:
        return f"Opening hours: {opening_hours}"[:500]
    return ""


def _parse_osm_element(element: dict) -> dict | None:
    tags = element.get("tags") or {}
    name = (tags.get("name:en") or tags.get("name") or "").strip()
    if not name:
        return None

    lat = element.get("lat")
    lon = element.get("lon")
    if lat is None or lon is None:
        center = element.get("center") or {}
        lat = center.get("lat")
        lon = center.get("lon")
    if lat is None or lon is None:
        return None

    return {
        "name": name,
        "description": _description_from_tags(tags),
        "category": _category_from_tags(tags),
        "latitude": float(lat),
        "longitude": float(lon),
    }


async def fetch_family_attractions(
    city: str,
    latitude: float | None,
    longitude: float | None,
    *,
    radius_m: int = _DEFAULT_RADIUS_M,
) -> list[dict]:
    """Fetch family-friendly attractions near a destination from OpenStreetMap (Overpass API)."""
    if latitude is None or longitude is None:
        logger.info("No coordinates for %s — skipping OSM attraction lookup", city)
        return []

    query = _build_overpass_query(latitude, longitude, radius_m)
    headers = {"User-Agent": _USER_AGENT}

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                _OVERPASS_URL,
                data={"data": query},
                headers=headers,
            )
            if resp.status_code == 429:
                logger.warning("Overpass API rate limited for %s — try again shortly", city)
                return []
            if resp.status_code != 200:
                logger.warning(
                    "Overpass API error %s for %s: %s",
                    resp.status_code,
                    city,
                    resp.text[:300],
                )
                return []

            data = resp.json()
            elements = data.get("elements")
            if not isinstance(elements, list):
                logger.warning("Overpass returned unexpected payload for %s", city)
                return []

            results: list[dict] = []
            seen_names: set[str] = set()
            for element in elements:
                parsed = _parse_osm_element(element)
                if not parsed:
                    continue
                key = parsed["name"].lower()
                if key in seen_names:
                    continue
                seen_names.add(key)
                results.append(parsed)

            logger.info("OpenStreetMap: %d family attractions for %s", len(results), city)
            return results

    except httpx.HTTPError as exc:
        logger.warning("Overpass API HTTP error for %s: %s", city, exc)
    except Exception as exc:
        logger.warning("OSM attraction fetch failed for %s: %s", city, exc)

    return []

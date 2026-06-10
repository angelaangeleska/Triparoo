from datetime import date, datetime, timedelta, timezone

from app.integrations.flights.airlines import AIRLINES
from app.services.airport_catalog import CatalogAirport


def pick_airline(origin: str, dest: str, slot: int = 0) -> tuple[str, str]:
    idx = abs(hash(f"{origin}{dest}{slot}")) % len(AIRLINES)
    return AIRLINES[idx]


def estimate_duration_minutes(distance_km: float, stops: int) -> int:
    flight_hours = distance_km / 780.0
    ground = 35 + stops * 55
    return max(45, int(flight_hours * 60 + ground))


def estimate_stops(distance_km: float, origin: str, dest: str) -> int:
    if distance_km < 2200:
        return 0
    if distance_km < 4500:
        return 1 if abs(hash(origin + dest)) % 3 == 0 else 0
    return 1 if abs(hash(dest)) % 2 == 0 else 2


def flight_number(airline_code: str, origin: str, dest: str, slot: int) -> str:
    num = 100 + abs(hash(f"{airline_code}{origin}{dest}{slot}")) % 8900
    return f"{airline_code} {num}"


def format_duration(minutes: int) -> str:
    hours, mins = divmod(minutes, 60)
    if hours:
        return f"{hours}h {mins}m"
    return f"{mins}m"


def build_leg_times(
    travel_date: date,
    hour: int,
    minute: int,
    duration_minutes: int,
    stops: int,
) -> tuple[datetime, datetime]:
    dep = datetime.combine(travel_date, datetime.min.time().replace(hour=hour, minute=minute), tzinfo=timezone.utc)
    arr = dep + timedelta(minutes=duration_minutes)
    return dep, arr

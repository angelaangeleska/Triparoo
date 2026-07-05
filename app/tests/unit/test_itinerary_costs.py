from app.services.itinerary_service import ItineraryService
from app.schemas.trip_planner import ItineraryDayItem, ItineraryDayRead


class _FakeAttraction:
    def __init__(self, name: str, price: float):
        self.name = name
        self.price = price


def test_estimate_item_cost_matches_db_attraction():
    cost = ItineraryService._estimate_item_cost(
        "Morning: Visit Colosseum and forum",
        [_FakeAttraction("Colosseum", 18.0)],
        [],
        party_size=3,
    )
    assert cost == 54.0


def test_estimate_item_cost_uses_osm_category():
    cost = ItineraryService._estimate_item_cost(
        "Afternoon at City Zoo",
        [],
        [{"name": "City Zoo", "category": "zoo"}],
        party_size=2,
    )
    assert cost == 44.0


def test_estimate_item_cost_meal():
    cost = ItineraryService._estimate_item_cost(
        "Evening: Relax and dinner in Trastevere",
        [],
        [],
        party_size=4,
    )
    assert cost == 72.0


def test_rotate_attractions_changes_order():
    items = ["a", "b", "c", "d"]
    rotated = ItineraryService._rotate_attractions(items, regenerate_count=1, seed=42)
    assert rotated != items
    assert sorted(rotated) == sorted(items)


def test_rotate_attractions_noop_on_zero():
    items = ["a", "b", "c"]
    assert ItineraryService._rotate_attractions(items, regenerate_count=0, seed=1) == items


def test_apply_itinerary_costs_sums_items():
    days = [
        ItineraryDayRead(
            day_number=1,
            title="Day 1",
            items=[
                ItineraryDayItem(time="", activity="Visit Colosseum", estimated_cost=0),
                ItineraryDayItem(time="", activity="Family dinner (~€60)", estimated_cost=0),
            ],
        )
    ]
    total = ItineraryService._apply_itinerary_costs(
        days,
        [_FakeAttraction("Colosseum", 18.0)],
        [],
        party_size=2,
    )
    assert total == 96.0  # 36 + 60 inline
    assert days[0].items[0].estimated_cost == 36.0
    assert days[0].items[1].estimated_cost == 60.0

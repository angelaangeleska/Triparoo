from app.schemas.trip_planner import AccommodationSummary, BookingSourceSummary
from app.services.accommodation_selection import same_accommodation, summary_total


def test_summary_total_none():
    assert summary_total(None) == 0.0


def test_summary_total_hotel():
    acc = AccommodationSummary(name="Test Hotel", price_per_night=50, total_price=250, currency="EUR")
    assert summary_total(acc) == 250.0


def test_same_accommodation():
    a = AccommodationSummary(name="Hotel A", price_per_night=80, total_price=400, currency="EUR")
    b = AccommodationSummary(name="Hotel A", price_per_night=80, total_price=400, currency="EUR")
    c = AccommodationSummary(name="Hotel B", price_per_night=60, total_price=300, currency="EUR")
    assert same_accommodation(a, b) is True
    assert same_accommodation(a, c) is False

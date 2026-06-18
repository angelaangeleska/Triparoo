from types import SimpleNamespace

from app.services.origin_resolver import OriginResolverService, ResolvedOrigin


def _dest(city_name: str, dest_id: int, airport_ids: list[int], iata: str):
    airports = [SimpleNamespace(id=aid, iata_code=iata) for aid in airport_ids]
    return SimpleNamespace(
        id=dest_id,
        city=SimpleNamespace(name=city_name, airports=airports),
    )


def test_excludes_same_city_airport_departure():
    resolver = OriginResolverService(session=None)  # type: ignore[arg-type]
    rome = _dest("Rome", 3, [10], "FCO")
    paris = _dest("Paris", 1, [1], "CDG")
    resolved = ResolvedOrigin(
        query="Rome",
        location_type="airport",
        display_name="Rome, Italy",
        airport_iatas=["FCO"],
        airport_ids=[10],
        primary_airport_id=10,
        primary_iata="FCO",
        message="Departing from Rome (FCO)",
    )
    excluded = resolver.get_excluded_destination_ids(
        [rome, paris], [10], resolved, origin_iatas=["FCO"]
    )
    assert 3 in excluded
    assert 1 not in excluded


def test_country_origin_does_not_exclude_paris():
    resolver = OriginResolverService(session=None)  # type: ignore[arg-type]
    paris = _dest("Paris", 1, [1], "CDG")
    rome = _dest("Rome", 3, [10], "FCO")
    resolved = ResolvedOrigin(
        query="France",
        location_type="country",
        display_name="France",
        airport_iatas=["CDG", "ORY", "NCE"],
        airport_ids=[1, 2, 3],
        primary_airport_id=1,
        primary_iata="CDG",
        message="Departing from France",
    )
    excluded = resolver.get_excluded_destination_ids(
        [paris, rome], [1, 2, 3], resolved, origin_iatas=["CDG", "ORY", "NCE"]
    )
    assert 1 not in excluded
    assert 3 not in excluded

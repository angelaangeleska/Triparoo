import pytest

from app.services.airport_search import AirportSearchService


@pytest.mark.asyncio
async def test_search_by_country(session):
    service = AirportSearchService(session)
    results = await service.search("France")
    assert len(results) >= 1
    assert all(r.country_name == "France" for r in results)
    assert results[0].match_type == "country"


@pytest.mark.asyncio
async def test_search_skopje_direct(session):
    service = AirportSearchService(session)
    results = await service.search("Skopje")
    assert len(results) >= 1
    assert results[0].iata_code == "SKP"
    assert results[0].match_type in ("direct", "iata")
    assert results[0].city_name.lower() == "skopje"


@pytest.mark.asyncio
async def test_search_iata_code(session):
    service = AirportSearchService(session)
    results = await service.search("JFK")
    assert len(results) == 1
    assert results[0].iata_code == "JFK"
    assert results[0].match_type == "iata"


@pytest.mark.asyncio
async def test_search_lyon_has_airports(session):
    service = AirportSearchService(session)
    results = await service.search("Lyon")
    assert len(results) >= 1
    assert any("Lyon" in r.city_name or "lyon" in r.name.lower() for r in results)


@pytest.mark.asyncio
async def test_search_rome_italy(session):
    service = AirportSearchService(session)
    results = await service.search("Rome, Italy")
    assert len(results) >= 2
    iatas = {r.iata_code for r in results}
    assert "FCO" in iatas
    assert "CIA" in iatas
    assert all(r.country_name == "Italy" for r in results)


@pytest.mark.asyncio
async def test_search_rome_usa(session):
    service = AirportSearchService(session)
    results = await service.search("Rome, United States")
    assert len(results) >= 1
    assert all("United States" in r.country_name for r in results)
    assert all(r.city_name.lower() == "rome" for r in results)


@pytest.mark.asyncio
async def test_search_rome_defaults_to_priority_country(session):
    service = AirportSearchService(session)
    results = await service.search("Rome")
    assert len(results) >= 1
    assert results[0].country_name == "Italy"
    assert results[0].iata_code == "FCO"

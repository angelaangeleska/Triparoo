import pytest

from app.services.origin_resolver import OriginResolverService


@pytest.mark.asyncio
async def test_resolve_rome_italy(session):
    service = OriginResolverService(session)
    resolved = await service.resolve("Rome, Italy")
    assert resolved is not None
    assert resolved.primary_iata == "FCO"
    assert set(resolved.airport_iatas) == {"FCO", "CIA"}
    assert "Italy" in resolved.message
    assert "2 airports" in resolved.message


@pytest.mark.asyncio
async def test_resolve_rome_without_country_prefers_italy(session):
    service = OriginResolverService(session)
    resolved = await service.resolve("Rome")
    assert resolved is not None
    assert resolved.primary_iata == "FCO"
    assert set(resolved.airport_iatas) == {"FCO", "CIA"}
    assert "Italy" in resolved.message
    assert "United States" not in resolved.message


@pytest.mark.asyncio
async def test_resolve_rome_usa(session):
    service = OriginResolverService(session)
    resolved = await service.resolve("Rome, US")
    assert resolved is not None
    assert "FCO" not in resolved.airport_iatas
    assert len(resolved.airport_iatas) >= 1
    assert "United States" in resolved.message
